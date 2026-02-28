#include "../include/st_reservation.hpp"

STReservation::STReservation(const Instance* _ins, int num_agents)
    : ins(_ins)
{
  // initialize all endpoints as invalid (fleet_id = -1)
  agent_endpoints.resize(num_agents, {-1, -1, -1});
  processed_.assign(num_agents, false);
}

void STReservation::seed(const HetConfig& config)
{
  for (size_t i = 0; i < config.positions.size(); ++i) {
    if (config.positions[i] == nullptr) continue;
    int fid = ins->agents[i].fleet_id;
    int cell = config.positions[i]->index;
    reserve_stay(static_cast<int>(i), fid, cell, 0, 0);
    processed_[i] = true;  // seeded agents block future times
  }
}

void STReservation::seed_transient(const HetConfig& config)
{
  for (size_t i = 0; i < config.positions.size(); ++i) {
    if (config.positions[i] == nullptr) continue;
    int fid = ins->agents[i].fleet_id;
    int cell = config.positions[i]->index;
    // Insert into st_map at t=0 only (so BFS sees current positions)
    // but do NOT add to parked_at_cell (so unprocessed agents don't
    // block BFS at future times). Set endpoint for BFS start cell.
    insert_cell(static_cast<int>(i), fid, cell, 0);
    agent_endpoints[i] = {fid, cell, 0};
  }
}

void STReservation::reset_agent(int agent_id, int fleet_id, int cell_index)
{
  auto& ep = agent_endpoints[agent_id];
  bool had_old = (ep.fleet_id >= 0);
  update_parked(agent_id, ep.fleet_id, ep.cell_index, had_old,
                fleet_id, cell_index);
  ep = {fleet_id, cell_index, 0};
}

std::vector<int> STReservation::fleet_to_base(int fleet_id,
                                               int cell_index) const
{
  int cs = ins->fleet_cell_sizes[fleet_id];
  int fw = ins->fleet_graphs[fleet_id].width;
  return to_base_cells(cell_index, fw, cs, ins->base_width);
}

void STReservation::insert_cell(int agent_id, int fleet_id, int cell_index,
                                 int time)
{
  auto base_cells = fleet_to_base(fleet_id, cell_index);
  for (int bc : base_cells) {
    auto key = pack_key(time, bc);
    st_map[key].push_back(agent_id);
  }
}

void STReservation::update_parked(int agent_id, int old_fleet, int old_cell,
                                   bool had_old, int new_fleet, int new_cell)
{
  // remove old parked cells
  if (had_old && old_fleet >= 0) {
    auto old_base = fleet_to_base(old_fleet, old_cell);
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
  if (new_fleet >= 0) {
    auto new_base = fleet_to_base(new_fleet, new_cell);
    for (int bc : new_base) {
      parked_at_cell[bc].push_back(agent_id);
    }
  }
}

void STReservation::reserve_path(int agent_id, int fleet_id, int start_time,
                                  const std::vector<int>& positions)
{
  if (positions.empty()) return;

  auto& ep = agent_endpoints[agent_id];
  bool had_old = (ep.fleet_id >= 0);

  // fill timing gap if agent has a prior endpoint
  if (had_old) {
    for (int t = ep.end_time + 1; t < start_time; ++t) {
      insert_cell(agent_id, ep.fleet_id, ep.cell_index, t);
    }
  }

  // reserve each timestep of the path
  for (size_t i = 0; i < positions.size(); ++i) {
    int t = start_time + static_cast<int>(i);
    insert_cell(agent_id, fleet_id, positions[i], t);
  }

  // update endpoint and parked index
  int new_cell = positions.back();
  int new_end = start_time + static_cast<int>(positions.size()) - 1;
  update_parked(agent_id, ep.fleet_id, ep.cell_index, had_old,
                fleet_id, new_cell);
  ep = {fleet_id, new_cell, new_end};
  processed_[agent_id] = true;  // explicitly reserved agents block future times
}

void STReservation::reserve_stay(int agent_id, int fleet_id, int cell_index,
                                  int start_time, int end_time)
{
  std::vector<int> positions;
  positions.reserve(end_time - start_time + 1);
  for (int t = start_time; t <= end_time; ++t) {
    positions.push_back(cell_index);
  }
  reserve_path(agent_id, fleet_id, start_time, positions);
}

bool STReservation::is_occupied(int base_cell, int time,
                                 int exclude_agent) const
{
  // check explicit reservations
  auto key = pack_key(time, base_cell);
  auto it = st_map.find(key);
  if (it != st_map.end()) {
    for (int aid : it->second) {
      if (aid != exclude_agent) return true;
    }
  }

  // check parked agents (beyond their last explicit reservation)
  // only processed agents block future timesteps
  auto pit = parked_at_cell.find(base_cell);
  if (pit != parked_at_cell.end()) {
    for (int aid : pit->second) {
      if (aid == exclude_agent) continue;
      if (!processed_[aid]) continue;  // unprocessed agents don't block
      auto& ep = agent_endpoints[aid];
      if (ep.fleet_id >= 0 && ep.end_time < time) {
        return true;
      }
    }
  }

  return false;
}

bool STReservation::move_collides(int fleet_id, int from_cell, int to_cell,
                                   int time, int agent_id) const
{
  // 1. vertex conflict: is any base cell of `to` occupied at time+1?
  auto to_base = fleet_to_base(fleet_id, to_cell);
  for (int bc : to_base) {
    if (is_occupied(bc, time + 1, agent_id)) return true;
  }

  // 2. swap conflict: is there an agent at `to` at time that moves to
  //    `from` at time+1?
  auto from_base = fleet_to_base(fleet_id, from_cell);

  // collect agents at `to` at current time (excluding self)
  std::unordered_set<int> agents_at_to;
  for (int bc : to_base) {
    auto key = pack_key(time, bc);
    auto it = st_map.find(key);
    if (it != st_map.end()) {
      for (int aid : it->second) {
        if (aid != agent_id) agents_at_to.insert(aid);
      }
    }
    // also check parked agents (only processed ones)
    auto pit = parked_at_cell.find(bc);
    if (pit != parked_at_cell.end()) {
      for (int aid : pit->second) {
        if (aid == agent_id) continue;
        if (!processed_[aid]) continue;  // unprocessed agents don't block
        auto& ep = agent_endpoints[aid];
        if (ep.fleet_id >= 0 && ep.end_time < time) {
          agents_at_to.insert(aid);
        }
      }
    }
  }

  if (agents_at_to.empty()) return false;

  // check if any of those agents will be at `from` at time+1
  for (int bc : from_base) {
    auto key = pack_key(time + 1, bc);
    auto it = st_map.find(key);
    if (it != st_map.end()) {
      for (int aid : it->second) {
        if (agents_at_to.count(aid)) return true;
      }
    }
    // parked agents stay in place — if they're parked at `to` and
    // `to` overlaps `from`, they won't be at `from` at t+1 unless
    // to == from. But that's already handled by vertex conflict.
  }

  return false;
}

std::vector<int> STReservation::get_occupants(int fleet_id, int cell_index,
                                               int time) const
{
  auto base_cells = fleet_to_base(fleet_id, cell_index);

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

  // parked agents (only processed ones block future times)
  for (int bc : base_cells) {
    auto pit = parked_at_cell.find(bc);
    if (pit != parked_at_cell.end()) {
      for (int aid : pit->second) {
        if (!processed_[aid]) continue;  // unprocessed agents don't block
        auto& ep = agent_endpoints[aid];
        if (ep.fleet_id >= 0 && ep.end_time < time) {
          if (seen.insert(aid).second) {
            result.push_back(aid);
          }
        }
      }
    }
  }

  return result;
}
