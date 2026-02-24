#include "../include/reservation.hpp"

// --- Trajectory ---

int Trajectory::end_time() const
{
  return start_time + static_cast<int>(positions.size()) - 1;
}

int Trajectory::cell_at(int t) const
{
  int idx = t - start_time;
  if (idx < 0) return positions.front();
  if (idx >= static_cast<int>(positions.size())) return positions.back();
  return positions[idx];
}

// --- ReservationTable ---

ReservationTable::ReservationTable() : cc(nullptr), fleets(nullptr) {}

ReservationTable::ReservationTable(const CollisionChecker* _cc,
                                   const Fleets* _fleets)
    : cc(_cc), fleets(_fleets)
{
}

std::vector<int> ReservationTable::get_all_base_cells(int fleet_id,
                                                      int cell_index) const
{
  auto* fleet = (*fleets)[fleet_id];
  int fw = fleet->G.width;
  // get base cells for this fleet cell
  auto base_cells = cc->to_base_cells(fleet_id, cell_index, fw);

  // also get cells on other fleet graphs that overlap (for ghost
  // reservations) — we project through base grid for consistency
  return base_cells;
}

void ReservationTable::update_parked_index(int agent_id,
                                           const AgentEndpoint* old_ep,
                                           const AgentEndpoint* new_ep)
{
  // remove old parked cells
  if (old_ep && old_ep->fleet_id >= 0) {
    auto* pf = (*fleets)[old_ep->fleet_id];
    int pfw = pf->G.width;
    auto old_base = cc->to_base_cells(old_ep->fleet_id, old_ep->cell_index, pfw);
    for (int bc : old_base) {
      auto it = parked_at_cell.find(bc);
      if (it != parked_at_cell.end()) {
        auto& vec = it->second;
        vec.erase(std::remove(vec.begin(), vec.end(), agent_id), vec.end());
        if (vec.empty()) parked_at_cell.erase(it);
      }
    }
  }
  // add new parked cells
  if (new_ep && new_ep->fleet_id >= 0) {
    auto* pf = (*fleets)[new_ep->fleet_id];
    int pfw = pf->G.width;
    auto new_base = cc->to_base_cells(new_ep->fleet_id, new_ep->cell_index, pfw);
    for (int bc : new_base) {
      parked_at_cell[bc].push_back(agent_id);
    }
  }
}

void ReservationTable::insert_cell(int agent_id, int fleet_id, int cell_index,
                                   int time)
{
  auto* fleet = (*fleets)[fleet_id];
  int fw = fleet->G.width;

  // project to base grid cells
  auto base_cells = cc->to_base_cells(fleet_id, cell_index, fw);
  for (int bc : base_cells) {
    auto key = pack_key(time, bc);
    st_map[key].push_back(agent_id);
    agent_cells[agent_id].push_back(key);
  }
}

bool ReservationTable::is_occupied(int fleet_id, int cell_index, int time,
                                   int exclude_agent,
                                   bool include_parked) const
{
  auto* fleet = (*fleets)[fleet_id];
  int fw = fleet->G.width;
  auto base_cells = cc->to_base_cells(fleet_id, cell_index, fw);

  // check explicit reservations in the spatial-temporal map
  for (int bc : base_cells) {
    auto key = pack_key(time, bc);
    auto it = st_map.find(key);
    if (it != st_map.end()) {
      for (int aid : it->second) {
        if (aid != exclude_agent) return true;
      }
    }
  }

  // check parked agents via spatial index: O(1) per base cell
  if (include_parked) {
    for (int bc : base_cells) {
      auto it = parked_at_cell.find(bc);
      if (it != parked_at_cell.end()) {
        for (int aid : it->second) {
          if (aid == exclude_agent) continue;
          auto ep_it = agent_last.find(aid);
          if (ep_it != agent_last.end() && ep_it->second.end_time < time) {
            return true;
          }
        }
      }
    }
  }

  return false;
}

bool ReservationTable::move_collides(int fleet_id, int from, int to, int time,
                                     int agent_id,
                                     bool include_parked) const
{
  // vertex conflict: is `to` occupied at time+1?
  if (is_occupied(fleet_id, to, time + 1, agent_id, include_parked))
    return true;

  // swap conflict: is there an agent at `to` at time `time` that moves
  // to `from` at time+1?
  // Check via base cells: if any base cell of `to` at time `time` is
  // occupied by agent X, and any base cell of `from` at time+1 is also
  // occupied by agent X, that's a swap.
  auto* fleet = (*fleets)[fleet_id];
  int fw = fleet->G.width;
  auto to_base = cc->to_base_cells(fleet_id, to, fw);
  auto from_base = cc->to_base_cells(fleet_id, from, fw);

  // collect agents at `to` at current time
  std::unordered_set<int> agents_at_to;
  for (int bc : to_base) {
    auto key = pack_key(time, bc);
    auto it = st_map.find(key);
    if (it != st_map.end()) {
      for (int aid : it->second) {
        if (aid != agent_id) agents_at_to.insert(aid);
      }
    }
  }

  // check if any of those agents will be at `from` at time+1
  for (int bc : from_base) {
    auto key = pack_key(time + 1, bc);
    auto it = st_map.find(key);
    if (it != st_map.end()) {
      for (int aid : it->second) {
        if (agents_at_to.count(aid)) return true;
      }
    }
  }

  return false;
}

std::vector<int> ReservationTable::get_occupants(int fleet_id, int cell_index,
                                                 int time) const
{
  auto* fleet = (*fleets)[fleet_id];
  int fw = fleet->G.width;
  auto base_cells = cc->to_base_cells(fleet_id, cell_index, fw);

  std::unordered_set<int> seen;
  std::vector<int> result;

  // explicit reservations in st_map
  for (int bc : base_cells) {
    auto key = pack_key(time, bc);
    auto it = st_map.find(key);
    if (it != st_map.end()) {
      for (int aid : it->second) {
        if (seen.insert(aid).second) {
          result.push_back(aid);
        }
      }
    }
  }

  // parked agents via spatial index: O(1) per base cell
  for (int bc : base_cells) {
    auto it = parked_at_cell.find(bc);
    if (it != parked_at_cell.end()) {
      for (int aid : it->second) {
        auto ep_it = agent_last.find(aid);
        if (ep_it != agent_last.end() && ep_it->second.end_time < time) {
          if (seen.insert(aid).second) {
            result.push_back(aid);
          }
        }
      }
    }
  }

  return result;
}

void ReservationTable::reserve(const Trajectory& traj)
{
  // fill timing gap if agent has a prior trajectory
  auto ep_it = agent_last.find(traj.agent_id);
  if (ep_it != agent_last.end()) {
    auto& ep = ep_it->second;
    for (int t = ep.end_time + 1; t < traj.start_time; ++t) {
      insert_cell(traj.agent_id, ep.fleet_id, ep.cell_index, t);
      // log the gap-fill as holding position
      traj_log[traj.agent_id].push_back({t, ep.cell_index});
    }
  }

  // reserve each timestep of the trajectory
  for (size_t i = 0; i < traj.positions.size(); ++i) {
    int t = traj.start_time + static_cast<int>(i);
    insert_cell(traj.agent_id, traj.fleet_id, traj.positions[i], t);
    // log this position
    traj_log[traj.agent_id].push_back({t, traj.positions[i]});
  }

  // update endpoint and parked index
  auto old_it = agent_last.find(traj.agent_id);
  AgentEndpoint* old_ep = (old_it != agent_last.end()) ? &old_it->second : nullptr;
  AgentEndpoint new_ep = {traj.fleet_id, traj.positions.back(), traj.end_time()};
  update_parked_index(traj.agent_id, old_ep, &new_ep);
  agent_last[traj.agent_id] = new_ep;
}

bool ReservationTable::try_reserve(const Trajectory& traj)
{
  // check trajectory positions for collisions (include_parked=true to
  // prevent reserving trajectories that overlap with parked agents)
  for (size_t i = 0; i < traj.positions.size(); ++i) {
    int t = traj.start_time + static_cast<int>(i);
    if (is_occupied(traj.fleet_id, traj.positions[i], t, traj.agent_id,
                    true)) {
      return false;
    }
    // check swap conflict with previous position
    if (i > 0) {
      if (move_collides(traj.fleet_id, traj.positions[i - 1],
                        traj.positions[i], t - 1, traj.agent_id, true)) {
        return false;
      }
    }
  }

  // endpoint future-conflict check: verify that parking at the final
  // position won't collide with existing explicit reservations at future
  // timesteps (prevents gap-fill collisions when the agent is parked)
  {
    int last_cell = traj.positions.back();
    int end_t = traj.end_time();
    auto* fleet = (*fleets)[traj.fleet_id];
    int fw = fleet->G.width;
    auto last_base = cc->to_base_cells(traj.fleet_id, last_cell, fw);
    // check a small window of future timesteps (enough to catch
    // imminent conflicts without over-restricting in congested areas)
    for (int ft = end_t + 1; ft <= end_t + 10; ++ft) {
      for (int bc : last_base) {
        auto key = pack_key(ft, bc);
        auto it = st_map.find(key);
        if (it != st_map.end()) {
          for (int aid : it->second) {
            if (aid != traj.agent_id) return false;
          }
        }
      }
    }
  }

  reserve(traj);
  return true;
}

void ReservationTable::remove_agent(int agent_id)
{
  auto it = agent_cells.find(agent_id);
  if (it != agent_cells.end()) {
    for (auto key : it->second) {
      auto map_it = st_map.find(key);
      if (map_it != st_map.end()) {
        auto& vec = map_it->second;
        vec.erase(std::remove(vec.begin(), vec.end(), agent_id), vec.end());
        if (vec.empty()) st_map.erase(map_it);
      }
    }
    agent_cells.erase(it);
  }
  auto ep_it = agent_last.find(agent_id);
  if (ep_it != agent_last.end()) {
    update_parked_index(agent_id, &ep_it->second, nullptr);
    agent_last.erase(ep_it);
  }
}

ReservationTable::AgentEndpoint ReservationTable::get_endpoint(
    int agent_id) const
{
  auto it = agent_last.find(agent_id);
  if (it != agent_last.end()) return it->second;
  return {-1, -1, -1};
}

void ReservationTable::clear()
{
  st_map.clear();
  agent_cells.clear();
  agent_last.clear();
  traj_log.clear();
  parked_at_cell.clear();
}
