/*
 * Heuristics overview — CORE vs EXTENSIONS
 *
 * CORE (from PIBT paper):
 *   - Elapsed counter: priority += 1 per step, reset to 0 at goal.
 *     Ensures agents that haven't reached their goal recently get planned first.
 *   - Per-agent tie_breakers: random float in [0,1) added to priority for
 *     ordering jitter, preventing systematic starvation at equal priority.
 *   - Same-fleet BFS depth = 1: vanilla PIBT one-step lookahead.
 *   - Cross-fleet adaptive BFS depth = ceil(parent_cs / agent_cs): lets smaller
 *     agents escape a larger agent's footprint when pushed.
 *   - BFS neighbor shuffling: randomized expansion order so agents don't all
 *     pick the same path through equal-cost intersections.
 *
 * EXTENSIONS (our additions for non-biconnected graphs):
 *   - Stuck counter acceleration: tracks whether each agent's distance-to-goal
 *     decreased. If not, stuck_count increments. Priority formula becomes
 *     elapsed + stuck_count, giving quadratic priority growth for stuck agents
 *     vs linear for progressing ones. Needed because room-64-64-8 doorways are
 *     bridge edges (not biconnected), so the paper's Theorem 1 guarantee does
 *     not hold.
 *   - Congestion penalty min(nb,3): added to BFS heuristic cost. Steers agents
 *     away from cells with many parked blockers, preventing chokepoint funneling
 *     caused by identical distance-table gradients. Capped at 3 to avoid
 *     over-penalizing in dense but passable areas.
 *   - Minimum BFS depth 2: all agents get at least 2-step lookahead (paper
 *     uses 1). On non-biconnected graphs with single-cell doorways (bridges),
 *     1-step lookahead can't see past the doorway, causing agents to oscillate
 *     at room entrances.
 *   - Oscillation penalty: in low-density areas (<=2 blockers), penalize BFS
 *     candidates that revisit the agent's last 10 positions (+2 per revisit).
 *     Without this, agents oscillate between the same 2-3 cells even with high
 *     priority — stuck_count fixes planning ORDER but not PATH SELECTION.
 *     Density-gated to avoid penalizing necessary revisits in crowded areas.
 *   - Goal locking (--goal-lock): permanently locks agents at their goals,
 *     matching pibt_rs behavior. Locked agents cannot be pushed; other agents'
 *     BFS treats locked cells as impassable. Improves scenarios with overlapping
 *     goal footprints but can cause regressions on non-biconnected graphs.
 */

#include "../include/planner.hpp"

#include <algorithm>

Planner::Planner(const HetInstance* _ins, const Deadline* _deadline,
                 std::mt19937* _mt, int _verbose, bool _goal_lock)
    : ins(_ins),
      deadline(_deadline),
      MT(_mt),
      verbose(_verbose),
      goal_lock(_goal_lock),
      N(_ins->N),
      V_size(_ins->base_grid.size()),
      D(*_ins),
      P(&_ins->cc, &_ins->fleets)
{
  // initialize tie-breakers
  tie_breakers.resize(N);
  for (int i = 0; i < N; ++i) {
    tie_breakers[i] = get_random_float(MT, 0, 1);
  }

  // CORE: paper's elapsed counter
  elapsed.resize(N, 0);

  // EXTENSION: stuck counter + distance tracking
  last_dist.resize(N, 0);
  stuck_count.resize(N, 0);
  for (int i = 0; i < N; ++i) {
    if (ins->starts[i] != nullptr) {
      last_dist[i] = D.get(i, ins->starts[i]->id);
    }
  }

  // EXTENSION: position history for anti-oscillation
  recent_cells.resize(N);

  // initial reservation: every agent occupies its start cell at t=0
  for (int i = 0; i < N; ++i) {
    if (ins->starts[i] == nullptr) continue;
    Trajectory init_traj;
    init_traj.agent_id = i;
    init_traj.fleet_id = ins->agents[i]->fleet_id;
    init_traj.start_time = 0;
    init_traj.positions = {ins->starts[i]->index};
    P.reserve(init_traj);
  }
}

Planner::~Planner() {}

void Planner::update_priorities(int step)
{
  for (int i = 0; i < N; ++i) {
    if (goal_reached.count(i)) {
      // CORE: reset elapsed at goal
      elapsed[i] = 0;
      // EXTENSION: reset stuck counter at goal
      stuck_count[i] = 0;
      ins->agents[i]->priority = 0.0f;
      continue;
    }

    // CORE: elapsed counter increments every step
    elapsed[i]++;

    // EXTENSION: stuck counter — did agent make progress toward goal?
    auto ep = P.get_endpoint(i);
    if (ep.fleet_id >= 0) {
      auto* fleet = ins->get_fleet(i);
      auto* v = fleet->G.U[ep.cell_index];
      int cur_dist = (v != nullptr) ? D.get(i, v->id) : last_dist[i];
      if (cur_dist < last_dist[i]) {
        stuck_count[i] = 0;  // made progress
        last_dist[i] = cur_dist;
      } else {
        stuck_count[i]++;
      }
    }

    // CORE + EXTENSION: accumulative priority.
    // Base +1 per step (paper's elapsed) + stuck_count acceleration.
    // Progressing agents: priority grows linearly (just +1/step).
    // Stuck agents: priority grows quadratically (+1+sc/step, sc increasing).
    // This ensures stuck agents rapidly outprioritize progressing ones.
    ins->agents[i]->priority += 1.0f + stuck_count[i];
  }
}

// Algorithm 2: per-agent space-time BFS
std::vector<ProposedPath> Planner::get_next_locations(
    int agent_id, int time, const std::unordered_set<int>& keep_out,
    int depth)
{
  auto* fleet = ins->get_fleet(agent_id);
  auto ep = P.get_endpoint(agent_id);
  if (ep.fleet_id < 0) return {};

  int start_cell = ep.cell_index;
  int fw = fleet->G.width;

  // space-time BFS priority queue: (cost, num_blocking, time, cell_index)
  using Node = std::tuple<int, int, int, int>;
  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> pq;

  // came_from: (time, cell) -> (time, cell) for path reconstruction
  std::unordered_map<uint64_t, uint64_t> came_from;
  std::unordered_set<uint64_t> visited;

  auto encode = [](int t, int c) -> uint64_t { return pack_key(t, c); };

  pq.push({0, 0, time, start_cell});
  visited.insert(encode(time, start_cell));

  std::vector<ProposedPath> results;

  while (!pq.empty()) {
    auto [cost, n_block, cur_t, cur_cell] = pq.top();
    pq.pop();

    // check if this is a valid solution (outside keep_out zone)
    // a fleet cell's base cells
    auto base_cells = ins->cc.to_base_cells(fleet->id, cur_cell, fw);
    bool in_keep_out = false;
    for (int bc : base_cells) {
      if (keep_out.count(bc)) {
        in_keep_out = true;
        break;
      }
    }

    if (!in_keep_out && cur_t > time) {
      // reconstruct path
      Path path;
      uint64_t key = encode(cur_t, cur_cell);
      while (true) {
        int cell = static_cast<int>(key & 0xFFFFFFFF);
        path.push_back(cell);
        auto it = came_from.find(key);
        if (it == came_from.end()) break;
        key = it->second;
      }
      std::reverse(path.begin(), path.end());

      // find blocking agents along the path
      std::vector<int> blocking;
      std::unordered_set<int> blocking_set;
      for (size_t i = 0; i < path.size(); ++i) {
        int pt = time + static_cast<int>(i);
        auto occupants = P.get_occupants(fleet->id, path[i], pt);
        for (int occ : occupants) {
          if (occ != agent_id && !blocking_set.count(occ)) {
            // only count as blocking if they are "parked" (unassigned)
            auto occ_ep = P.get_endpoint(occ);
            if (occ_ep.end_time <= pt) {
              blocking.push_back(occ);
              blocking_set.insert(occ);
            }
          }
        }
      }

      results.push_back({path, blocking});
      if (results.size() >= 5) break;  // enough candidates
    }

    // don't expand beyond depth
    if (cur_t - time >= depth) continue;

    // expand neighbors + wait-in-place
    auto* v = fleet->G.U[cur_cell];
    if (v == nullptr) continue;

    std::vector<int> next_cells;
    next_cells.push_back(cur_cell);  // wait in place
    for (auto* u : v->neighbor) {
      next_cells.push_back(u->index);
    }

    // shuffle move-neighbors (indices 1..end) so agents don't all pick
    // the same path through equal-cost intersections
    if (next_cells.size() > 2) {
      std::shuffle(next_cells.begin() + 1, next_cells.end(), *MT);
    }

    for (int nc : next_cells) {
      int nt = cur_t + 1;
      uint64_t nkey = encode(nt, nc);
      if (visited.count(nkey)) continue;

      // skip if moving there collides with reserved trajectories
      if (P.move_collides(fleet->id, cur_cell, nc, cur_t, agent_id)) {
        continue;
      }

      // compute heuristic cost
      auto* nv = fleet->G.U[nc];
      if (nv == nullptr) continue;
      int h = D.get(agent_id, nv->id);
      if (h >= static_cast<int>(fleet->G.V.size())) continue;  // unreachable

      // count blocking agents at the new cell (parked agents in the way)
      // with goal_lock: skip cells occupied by goal-locked agents
      int nb = 0;
      bool goal_blocked = false;
      auto occupants = P.get_occupants(fleet->id, nc, nt);
      for (int occ : occupants) {
        if (occ != agent_id) {
          if (goal_lock && goal_reached.count(occ)) {
            goal_blocked = true;
            break;
          }
          auto occ_ep = P.get_endpoint(occ);
          if (occ_ep.end_time <= nt) ++nb;
        }
      }
      if (goal_blocked) continue;

      // EXTENSION: congestion penalty — steer away from crowded cells
      int congestion = std::min(nb, 3);

      // EXTENSION: oscillation penalty — in low-density areas (nb<=2),
      // penalize revisiting cells from the agent's recent history.
      // Breaks 2-cell oscillation patterns in corridors/doorways without
      // affecting dense areas where revisits are unavoidable.
      int osc_penalty = 0;
      if (nb <= 2) {
        for (int rc : recent_cells[agent_id]) {
          if (rc == nc) osc_penalty += 2;
        }
      }

      visited.insert(nkey);
      came_from[nkey] = encode(cur_t, cur_cell);
      pq.push({h + congestion + osc_penalty, nb, nt, nc});
    }
  }

  // sort by (distance to goal at end, then number of blocking agents)
  std::sort(results.begin(), results.end(),
            [this, agent_id, fleet](const ProposedPath& a,
                                   const ProposedPath& b) {
              auto* va = fleet->G.U[a.path.back()];
              auto* vb = fleet->G.U[b.path.back()];
              int da = D.get(agent_id, va);
              int db = D.get(agent_id, vb);
              if (da != db) return da < db;
              return a.blocking_agents.size() < b.blocking_agents.size();
            });

  return results;
}

// Recursive push: move agent_id at time `time`, pushing blockers first.
bool Planner::push_agent(int agent_id, int time,
                          const std::unordered_set<int>& keep_out,
                          std::unordered_set<int>& in_chain, int max_depth,
                          int min_bfs_depth)
{
  if (max_depth <= 0) return false;
  if (in_chain.count(agent_id)) return false;

  // goal-locked agents are permanently fixed — refuse to push them.
  // This matches pibt_rs behavior: once at goal, agent becomes a static
  // obstacle and other agents must route around it.
  if (goal_lock && goal_reached.count(agent_id)) return false;

  in_chain.insert(agent_id);

  auto* fleet = ins->get_fleet(agent_id);
  int fw = fleet->G.width;

  // BFS depth per the paper:
  //   same-fleet or top-level: depth = 1 (vanilla PIBT)
  //   cross-fleet push where parent is larger: depth = ceil(parent_cs / agent_cs)
  //     so smaller agent can escape the larger agent's footprint
  int bfs_depth = std::max(min_bfs_depth, fleet->cell_size);
  auto candidates = get_next_locations(agent_id, time, keep_out, bfs_depth);

  for (auto& pp : candidates) {
    // check all blockers are pushable (quick reject)
    bool all_ok = true;
    for (int ba : pp.blocking_agents) {
      if (in_chain.count(ba)) {
        all_ok = false;
        break;
      }
    }
    if (!all_ok) continue;

    // limit multi-blocker to avoid combinatorial explosion
    if (pp.blocking_agents.size() > 4) continue;

    if (pp.blocking_agents.empty()) {
      // free path — reserve immediately
      Trajectory traj;
      traj.agent_id = agent_id;
      traj.fleet_id = fleet->id;
      traj.positions = pp.path;

      auto ep = P.get_endpoint(agent_id);
      traj.start_time = std::max(time, ep.end_time);

      while (!P.try_reserve(traj)) {
        traj.start_time++;
        if (traj.start_time > time + 50) break;
      }
      if (traj.start_time <= time + 50) {
        // if displaced from goal without locking, allow re-planning
        if (!goal_lock && goal_reached.count(agent_id)) {
          goal_reached.erase(agent_id);
          goal_time.erase(agent_id);
        }
        return true;
      }
      continue;
    }

    // build keep-out: only the DESTINATION cells (last position in path)
    // The start cells are being vacated, so pushed agents can move there
    // at later timesteps. Swap conflicts are caught by try_reserve.
    auto new_ko = keep_out;
    if (!pp.path.empty()) {
      int dest_cell = pp.path.back();
      auto bcs = ins->cc.to_base_cells(fleet->id, dest_cell, fw);
      for (int bc : bcs) new_ko.insert(bc);
    }

    // save in_chain state for backtracking between candidates
    auto saved_chain = in_chain;

    // push each blocker
    bool all_pushed = true;
    for (int ba : pp.blocking_agents) {
      auto* ba_fleet = ins->get_fleet(ba);
      int depth = max_depth - 1;

      // cross-fleet: smaller blocker needs enough BFS depth to escape
      // the larger agent's footprint: ceil(parent_cs / blocker_cs)
      int sub_bfs_depth = 1;
      if (fleet->cell_size > ba_fleet->cell_size) {
        sub_bfs_depth = (fleet->cell_size + ba_fleet->cell_size - 1)
                        / ba_fleet->cell_size;
        depth = std::max(depth, sub_bfs_depth);
      }

      if (!push_agent(ba, time, new_ko, in_chain, depth, sub_bfs_depth)) {
        all_pushed = false;
        break;
      }

      // add pushed agent's new endpoint to keep-out
      auto ba_ep = P.get_endpoint(ba);
      if (ba_ep.fleet_id >= 0) {
        auto* pf = ins->fleets[ba_ep.fleet_id];
        auto ba_bcs = ins->cc.to_base_cells(ba_ep.fleet_id, ba_ep.cell_index,
                                             pf->G.width);
        for (int bc : ba_bcs) new_ko.insert(bc);
      }
    }

    if (!all_pushed) {
      // restore in_chain so next candidate can try the same blockers
      in_chain = saved_chain;
      continue;
    }

    // all blockers pushed — reserve our path
    Trajectory traj;
    traj.agent_id = agent_id;
    traj.fleet_id = fleet->id;
    traj.positions = pp.path;

    auto ep = P.get_endpoint(agent_id);
    traj.start_time = std::max(time, ep.end_time);

    while (!P.try_reserve(traj)) {
      traj.start_time++;
      if (traj.start_time > time + 50) break;
    }
    if (traj.start_time <= time + 50) {
      if (!goal_lock && goal_reached.count(agent_id)) {
        goal_reached.erase(agent_id);
        goal_time.erase(agent_id);
      }
      return true;
    }

    // reserve failed despite pushes — restore chain for next candidate
    in_chain = saved_chain;
  }

  // push failed — remove agent from chain so caller can try alternatives
  in_chain.erase(agent_id);
  return false;
}

// Algorithm 1: priority traversal search for one agent
bool Planner::attempt_solve_for_agent(int agent_id, int time)
{
  std::unordered_set<int> in_chain;
  std::unordered_set<int> keep_out;

  // EXTENSION: min_bfs_depth=2 gives all agents at least 2-step lookahead,
  // helping them escape single-cell doorways on non-biconnected graphs.
  // Paper's vanilla PIBT uses depth=1 (CORE).
  if (push_agent(agent_id, time, keep_out, in_chain, 6, 2)) {
    return true;
  }

  // failed — agent stays put (reserve in-place trajectory)
  auto ep = P.get_endpoint(agent_id);
  if (ep.fleet_id >= 0) {
    Trajectory stay;
    stay.agent_id = agent_id;
    stay.fleet_id = ep.fleet_id;
    stay.start_time = ep.end_time;
    stay.positions = {ep.cell_index};
    P.reserve(stay);
  }
  return false;
}

Solution Planner::solve(int max_timesteps)
{
  info(1, verbose, "HetPIBT solver started, N=", N);

  // CORE: all agents start with elapsed = 0
  // EXTENSION: stuck_count = 0, last_dist = initial distance (constructor)

  for (int step = 1; step <= max_timesteps; ++step) {
    if (is_expired(deadline)) {
      info(1, verbose, "timeout at step ", step);
      break;
    }

    // check if all agents reached their goals
    if (static_cast<int>(goal_reached.size()) == N) {
      info(1, verbose, "all agents reached goals at step ", step);
      break;
    }

    update_priorities(step);

    // sort agents by priority (descending — highest priority first)
    // tie_breakers add randomized jitter to prevent systematic starvation
    std::vector<int> order(N);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [this](int a, int b) {
      float pa = ins->agents[a]->priority + tie_breakers[a];
      float pb = ins->agents[b]->priority + tie_breakers[b];
      return pa > pb;
    });

    for (int aid : order) {
      if (goal_reached.count(aid)) continue;

      // skip if agent already has reservations beyond this step
      auto ep = P.get_endpoint(aid);
      if (ep.end_time > step) continue;

      // check if agent is at goal
      if (ins->goals[aid] != nullptr && ep.cell_index == ins->goals[aid]->index) {
        goal_reached.insert(aid);
        goal_time[aid] = step;
        info(2, verbose, "agent ", aid, " reached goal, step ", step);
        continue;
      }

      attempt_solve_for_agent(aid, step);
    }

    // EXTENSION: update recent position history for anti-oscillation
    for (int i = 0; i < N; ++i) {
      auto ep = P.get_endpoint(i);
      if (ep.fleet_id >= 0) {
        recent_cells[i].push_back(ep.cell_index);
        if (static_cast<int>(recent_cells[i].size()) > 10) {
          recent_cells[i].pop_front();
        }
      }
    }
  }

  // build solution from reservation table
  Solution sol(N);
  for (int i = 0; i < N; ++i) {
    sol[i].agent_id = i;
    sol[i].fleet_id = ins->agents[i]->fleet_id;
    sol[i].start_time = 0;
    // reconstruct from reservation table endpoints
    // for now, the trajectories are embedded in the reservation table
    auto ep = P.get_endpoint(i);
    sol[i].positions = {ep.cell_index};  // simplified; full trajectory in P
  }

  info(1, verbose, "solver finished, goal_reached=", goal_reached.size(),
       "/", N);

  return sol;
}

// convenience entry point
Solution solve(const HetInstance& ins, int verbose, const Deadline* deadline,
               std::mt19937* MT, int max_timesteps, bool goal_lock)
{
  auto default_mt = std::mt19937(0);
  if (MT == nullptr) MT = &default_mt;
  Planner planner(&ins, deadline, MT, verbose, goal_lock);
  return planner.solve(max_timesteps);
}
