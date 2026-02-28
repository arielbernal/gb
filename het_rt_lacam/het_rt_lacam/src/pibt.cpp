#include "../include/pibt.hpp"
#include <cassert>

HetPIBT::HetPIBT(const Instance *_ins, const DistTable *_D, int seed,
                 bool _goal_lock)
    : ins(_ins),
      MT(std::mt19937(seed)),
      N(ins->N),
      D(_D),
      NO_AGENT(N),
      goal_lock(_goal_lock),
      base_size(ins->base_width * ins->base_height),
      base_occupied_now(base_size, NO_AGENT),
      base_occupied_next(base_size, NO_AGENT),
      max_fleet_vertices(0),
      recent_cells(ins->N),
      bfs_default_depth(2),
      st_res_(nullptr)
{
  for (int f = 0; f < ins->num_fleets; ++f) {
    int sz = ins->fleet_graphs[f].size();
    if (sz > max_fleet_vertices) max_fleet_vertices = sz;
  }

  // Candidates buffer: BFS may produce more candidates than 1-step
  C_next.resize(N);
  for (int i = 0; i < N; ++i) C_next[i].reserve(10);

  tie_breakers.assign(max_fleet_vertices, 0);
}

HetPIBT::~HetPIBT() {}

// ---------------------------------------------------------------------------
// Base-grid footprint helpers
// ---------------------------------------------------------------------------
void HetPIBT::mark_base_now(int agent_id, Vertex *v)
{
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];
  auto cells = to_base_cells(v->index, fg.width, cs, ins->base_width);
  for (int bc : cells) base_occupied_now[bc] = agent_id;
}

void HetPIBT::mark_base_next(int agent_id, Vertex *v)
{
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];
  auto cells = to_base_cells(v->index, fg.width, cs, ins->base_width);
  for (int bc : cells) {
    base_occupied_next[bc] = agent_id;
  }
}

void HetPIBT::clear_base_now(int agent_id, Vertex *v)
{
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];
  auto cells = to_base_cells(v->index, fg.width, cs, ins->base_width);
  for (int bc : cells) {
    if (base_occupied_now[bc] == agent_id) base_occupied_now[bc] = NO_AGENT;
  }
}

void HetPIBT::clear_base_next(int agent_id, Vertex *v)
{
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];
  auto cells = to_base_cells(v->index, fg.width, cs, ins->base_width);
  for (int bc : cells) {
    if (base_occupied_next[bc] == agent_id) base_occupied_next[bc] = NO_AGENT;
  }
}

bool HetPIBT::base_next_free(int agent_id, Vertex *v) const
{
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];
  auto cells = to_base_cells(v->index, fg.width, cs, ins->base_width);
  for (int bc : cells) {
    if (base_occupied_next[bc] != NO_AGENT &&
        base_occupied_next[bc] != agent_id)
      return false;
  }
  return true;
}

// Check if agent_i moving from from_i to to_i would create a swap conflict.
// A swap conflict occurs when another agent j is currently at to_i's footprint
// and has been assigned to move to from_i's footprint.
bool HetPIBT::check_swap_conflict(int agent_i, Vertex *from_i, Vertex *to_i,
                                   const HetConfig &Q_from,
                                   const HetConfig &Q_to) const
{
  int fid_i = ins->agents[agent_i].fleet_id;
  int cs_i = ins->fleet_cell_sizes[fid_i];
  auto &fg_i = ins->fleet_graphs[fid_i];

  // Get base cells of where i wants to go
  auto to_base = to_base_cells(to_i->index, fg_i.width, cs_i, ins->base_width);
  // Get base cells of where i is now
  auto from_base = to_base_cells(from_i->index, fg_i.width, cs_i, ins->base_width);
  std::unordered_set<int> from_set(from_base.begin(), from_base.end());

  // Find agents currently occupying to_i's base cells
  std::unordered_set<int> agents_at_target;
  for (int bc : to_base) {
    int j = base_occupied_now[bc];
    if (j != NO_AGENT && j != agent_i) agents_at_target.insert(j);
  }

  // Check if any of those agents are assigned to move into from_i's base cells
  for (int j : agents_at_target) {
    if (Q_to.positions[j] == nullptr) continue;
    int fid_j = ins->agents[j].fleet_id;
    int cs_j = ins->fleet_cell_sizes[fid_j];
    auto &fg_j = ins->fleet_graphs[fid_j];
    auto j_next_base = to_base_cells(Q_to.positions[j]->index, fg_j.width,
                                     cs_j, ins->base_width);
    for (int bc : j_next_base) {
      if (from_set.count(bc)) return true;  // swap conflict!
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Main configuration generator
// ---------------------------------------------------------------------------
static int _snc_calls = 0;
static int _snc_fail_step2 = 0;
static int _snc_fail_step25 = 0;
static int _snc_fail_step3 = 0;
static int _snc_fail_verify = 0;
static int _snc_ok = 0;

bool HetPIBT::set_new_config(const HetConfig &Q_from, HetConfig &Q_to,
                              const std::vector<int> &order)
{
  bool success = true;
  ++_snc_calls;
  int fail_stage = 0;

  // 0. Create ephemeral space-time reservation table for this config call.
  //    Seeded with Q_from positions at t=0. Used by st_bfs_get_candidates()
  //    inside funcPIBT. Accumulates reservations as agents are assigned.
  STReservation st_res(ins, N);
  st_res.seed_transient(Q_from);
  st_res_ = &st_res;

  // 1. Setup occupancy for current positions
  for (int i = 0; i < N; ++i) {
    mark_base_now(i, Q_from.positions[i]);
  }

  // 2. Process pre-constrained agents (hard constraints from LNode)
  for (int i = 0; i < N; ++i) {
    if (Q_to.positions[i] != nullptr) {
      // Kappa: advance only on movement (use speed_period, not cell_size)
      int sp = ins->speed_period(i);
      if (Q_from.kappa[i] != 0) {
        Q_to.kappa[i] = (Q_from.kappa[i] + 1) % sp;
      } else if (Q_to.positions[i] != Q_from.positions[i] && sp > 1) {
        Q_to.kappa[i] = 1;
      } else {
        Q_to.kappa[i] = 0;
      }

      // Check footprint collision on base grid
      if (!base_next_free(i, Q_to.positions[i])) {
        success = false;
        fail_stage = 2;
        break;
      }
      // Check swap conflict
      if (check_swap_conflict(i, Q_from.positions[i], Q_to.positions[i],
                              Q_from, Q_to)) {
        success = false;
        fail_stage = 2;
        break;
      }
      mark_base_next(i, Q_to.positions[i]);
    }
  }

  // 2.25. Pre-reserve goal-locked agents: agents at goal with kappa=0
  //       are permanently locked — they stay in place and cannot be pushed.
  if (success && goal_lock) {
    for (int i = 0; i < N; ++i) {
      if (Q_to.positions[i] != nullptr) continue;  // already constrained
      if (Q_from.positions[i] != ins->goals[i]) continue;
      if (Q_from.kappa[i] != 0) continue;
      auto *stay = Q_from.positions[i];
      if (!base_next_free(i, stay)) {
        success = false;
        fail_stage = 2;
        break;
      }
      Q_to.positions[i] = stay;
      Q_to.kappa[i] = 0;
      mark_base_next(i, stay);
      st_res.reserve_stay(i, ins->agents[i].fleet_id, stay->index, 0, 2);
      st_res.mark_processed(i);
    }
  }

  // 2.5. Pre-reserve speed-gated agents (kappa > 0) not already constrained.
  //      These agents MUST stay in place — reserve them now so free-moving
  //      agents won't collide with them.
  if (success) {
    for (int i = 0; i < N; ++i) {
      if (Q_to.positions[i] != nullptr) continue;  // already constrained
      if (Q_from.kappa[i] == 0) continue;           // not speed-gated

      auto *stay = Q_from.positions[i];
      if (!base_next_free(i, stay)) {
        success = false;
        fail_stage = 25;
        break;
      }
      int sp = ins->speed_period(i);
      Q_to.positions[i] = stay;
      Q_to.kappa[i] = (Q_from.kappa[i] + 1) % sp;
      mark_base_next(i, stay);
      st_res.reserve_stay(i, ins->agents[i].fleet_id, stay->index, 0, 2);
      st_res.mark_processed(i);
    }
  }

  // 3. Run PIBT for unconstrained agents in priority order.
  //    Each top-level agent starts a fresh push chain (keep_out + in_chain).
  //    max_depth=6 matches hetpibt's attempt_solve_for_agent.
  if (success) {
    for (int k : order) {
      if (Q_to.positions[k] == nullptr) {
        std::unordered_set<int> keep_out;
        std::unordered_set<int> in_chain;
        funcPIBT(k, Q_from, Q_to, keep_out, in_chain, 6);
      }
    }
    // Ensure all agents got assigned. Try funcPIBT again for unassigned
    // agents (different state than first pass since other agents moved).
    for (int i = 0; i < N; ++i) {
      if (Q_to.positions[i] == nullptr) {
        std::unordered_set<int> keep_out;
        std::unordered_set<int> in_chain;
        funcPIBT(i, Q_from, Q_to, keep_out, in_chain, 6);
        if (Q_to.positions[i] == nullptr) {
          success = false;
          fail_stage = 3;
          break;
        }
      }
    }
  }

  // 3.5. Update oscillation history (only on successful configs)
  if (success) {
    for (int i = 0; i < N; ++i) {
      if (Q_to.positions[i] != nullptr) {
        recent_cells[i].push_back(Q_to.positions[i]->index);
        if (static_cast<int>(recent_cells[i].size()) > 10)
          recent_cells[i].pop_front();
      }
    }
  }

  // 4. Cleanup occupancy
  for (int i = 0; i < N; ++i) {
    clear_base_now(i, Q_from.positions[i]);
    if (Q_to.positions[i] != nullptr) clear_base_next(i, Q_to.positions[i]);
  }

  if (!success) {
    if (fail_stage == 2) ++_snc_fail_step2;
    else if (fail_stage == 25) ++_snc_fail_step25;
    else if (fail_stage == 3) ++_snc_fail_step3;
    else if (fail_stage == 4) ++_snc_fail_verify;
  } else {
    ++_snc_ok;
  }
  if (_snc_calls % 50000 == 0) {
    fprintf(stderr, "[PIBT diag] calls=%d ok=%d fail_s2=%d fail_s25=%d"
            " fail_s3=%d fail_verify=%d\n",
            _snc_calls, _snc_ok, _snc_fail_step2, _snc_fail_step25,
            _snc_fail_step3, _snc_fail_verify);
  }

  st_res_ = nullptr;  // ephemeral table goes out of scope
  return success;
}

// ---------------------------------------------------------------------------
// BFS multi-step lookahead for candidate generation.
// Explores agent's fleet graph up to `depth` steps, computing
// cost = steps + h(endpoint) + congestion + oscillation_penalty.
// Groups results by first-step vertex and populates C_next[agent_id].
// ---------------------------------------------------------------------------
void HetPIBT::bfs_get_candidates(int agent_id, const HetConfig &Q_from,
                                  int depth)
{
  C_next[agent_id].clear();

  auto *v_now = Q_from.positions[agent_id];
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];

  // BFS state: (cost, depth, cell_index)
  using Node = std::tuple<int, int, int>;
  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> pq;
  std::unordered_map<int, int> best_cost;    // cell -> best cost seen
  std::unordered_map<int, int> parent;       // cell -> parent cell

  int h_start = D->get(agent_id, v_now);
  pq.push({h_start, 0, v_now->index});
  best_cost[v_now->index] = h_start;

  while (!pq.empty()) {
    auto [cost, d, cell] = pq.top();
    pq.pop();

    if (d >= depth) continue;
    // Skip if we've found a better path to this cell already
    if (cost > best_cost[cell]) continue;

    auto *v = fg.U[cell];
    if (!v) continue;

    // Expand neighbors + stay-in-place
    std::vector<int> next_cells;
    for (auto *u : v->neighbor) next_cells.push_back(u->index);
    // Shuffle neighbors for diversity (matches hetpibt)
    if (next_cells.size() > 1) {
      std::shuffle(next_cells.begin(), next_cells.end(), MT);
    }
    next_cells.push_back(cell);  // stay option last

    for (int nc : next_cells) {
      auto *nv = fg.U[nc];
      if (!nv) continue;

      int h = D->get(agent_id, nv);
      if (h >= static_cast<int>(fg.V.size())) continue;  // unreachable

      // Congestion: count other agents at this cell's base footprint
      auto nc_base = to_base_cells(nc, fg.width, cs, ins->base_width);
      int nb = 0;
      bool goal_blocked = false;
      for (int bc : nc_base) {
        int occ = base_occupied_now[bc];
        if (occ != NO_AGENT && occ != agent_id) {
          // Check if goal-locked agent — treat as hard obstacle
          if (goal_lock && Q_from.positions[occ] == ins->goals[occ] &&
              Q_from.kappa[occ] == 0) {
            goal_blocked = true;
            break;
          }
          ++nb;
        }
      }
      if (goal_blocked) continue;
      int congestion = std::min(nb, 3);

      // Oscillation penalty: penalize revisiting recent cells (low-congestion only)
      int osc_penalty = 0;
      if (nb <= 2) {
        for (int rc : recent_cells[agent_id]) {
          if (rc == nc) osc_penalty += 2;
        }
      }

      int new_cost = (d + 1) + h + congestion + osc_penalty;

      auto it = best_cost.find(nc);
      if (it == best_cost.end() || new_cost < it->second) {
        best_cost[nc] = new_cost;
        parent[nc] = cell;
        pq.push({new_cost, d + 1, nc});
      }
    }
  }

  // Trace back to first-step vertices.
  // For each visited cell, find which neighbor of v_now it was reached through.
  // Group by first-step, keep the minimum endpoint cost per group.
  std::unordered_map<int, int> first_step_cost;  // first_step cell -> best cost

  for (auto &[cell, cost] : best_cost) {
    if (cell == v_now->index) continue;  // skip start

    // Trace parent chain to find first step
    int cur = cell;
    while (true) {
      auto pit = parent.find(cur);
      if (pit == parent.end()) break;  // shouldn't happen
      if (pit->second == v_now->index) break;  // cur is the first step
      cur = pit->second;
    }

    auto it = first_step_cost.find(cur);
    if (it == first_step_cost.end() || cost < it->second) {
      first_step_cost[cur] = cost;
    }
  }

  // Also add stay option with its direct cost
  first_step_cost[v_now->index] = h_start;

  // Build sorted candidate list
  struct CandInfo {
    Vertex *v;
    int cost;
  };
  std::vector<CandInfo> cands;
  for (auto &[cell, cost] : first_step_cost) {
    auto *v = fg.U[cell];
    if (v) cands.push_back({v, cost});
  }

  // Sort by cost (ascending)
  std::sort(cands.begin(), cands.end(),
            [](const CandInfo &a, const CandInfo &b) {
              return a.cost < b.cost;
            });

  // Populate C_next with sorted candidates and assign tie-breakers
  for (auto &ci : cands) {
    C_next[agent_id].push_back(ci.v);
    tie_breakers[ci.v->id] = ci.cost + get_random_float(MT);
  }
}

// ---------------------------------------------------------------------------
// Space-time BFS candidate generation using reservation table.
// Explores (time, cell) states, using res.move_collides() to prune edges
// and res.get_occupants() for congestion/blocker identification.
// Returns up to 5 ProposedPath candidates sorted by cost.
// Mirrors hetpibt's get_next_locations() (planner.cpp:131-292).
// ---------------------------------------------------------------------------
std::vector<ProposedPath> HetPIBT::st_bfs_get_candidates(
    int agent_id, STReservation &res, int depth)
{
  int fid = ins->agents[agent_id].fleet_id;
  int cs = ins->fleet_cell_sizes[fid];
  auto &fg = ins->fleet_graphs[fid];

  auto &ep = res.agent_endpoints[agent_id];
  if (ep.fleet_id < 0) return {};
  int start_cell = ep.cell_index;

  // Space-time BFS: (cost, num_blocking, time, cell_index)
  using Node = std::tuple<int, int, int, int>;
  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> pq;

  // came_from: pack_key(time, cell) -> pack_key(time, cell) for path reconstruction
  std::unordered_map<uint64_t, uint64_t> came_from;
  std::unordered_set<uint64_t> visited;

  const int t0 = 0;  // BFS starts at t=0 (relative to current config)
  pq.push({0, 0, t0, start_cell});
  visited.insert(pack_key(t0, start_cell));

  std::vector<ProposedPath> results;

  while (!pq.empty()) {
    auto [cost, n_block, cur_t, cur_cell] = pq.top();
    pq.pop();

    // Emit a candidate if we've moved at least one step from the start
    if (cur_t > t0) {
      // Reconstruct path from came_from chain
      std::vector<int> path;
      uint64_t key = pack_key(cur_t, cur_cell);
      while (true) {
        int cell = static_cast<int>(key & 0xFFFFFFFF);
        path.push_back(cell);
        auto it = came_from.find(key);
        if (it == came_from.end()) break;
        key = it->second;
      }
      std::reverse(path.begin(), path.end());

      // Collect blocking agents along the path (parked agents in the way)
      std::vector<int> blocking;
      std::unordered_set<int> blocking_set;
      for (size_t i = 0; i < path.size(); ++i) {
        int pt = t0 + static_cast<int>(i);
        auto occupants = res.get_occupants(fid, path[i], pt);
        for (int occ : occupants) {
          if (occ == agent_id) continue;
          if (blocking_set.count(occ)) continue;
          // Only count as blocking if parked (endpoint at or before this time)
          auto &occ_ep = res.agent_endpoints[occ];
          if (occ_ep.fleet_id >= 0 && occ_ep.end_time <= pt) {
            blocking.push_back(occ);
            blocking_set.insert(occ);
          }
        }
      }

      // first_step: the cell to move to at t=1 (path[1] if path has >1 entry,
      // else path[0] for wait-in-place)
      int fs = (path.size() > 1) ? path[1] : path[0];

      results.push_back({std::move(path), std::move(blocking), fs, cost});
      if (results.size() >= 15) break;  // collect extra for first_step dedup
    }

    // Don't expand beyond depth limit
    if (cur_t - t0 >= depth) continue;

    auto *v = fg.U[cur_cell];
    if (!v) continue;

    // Expand: wait-in-place first, then shuffled neighbors
    std::vector<int> next_cells;
    next_cells.push_back(cur_cell);  // wait in place
    for (auto *u : v->neighbor) next_cells.push_back(u->index);

    // Shuffle move-neighbors (indices 1..end) for diversity
    if (next_cells.size() > 2) {
      std::shuffle(next_cells.begin() + 1, next_cells.end(), MT);
    }

    for (int nc : next_cells) {
      int nt = cur_t + 1;
      uint64_t nkey = pack_key(nt, nc);
      if (visited.count(nkey)) continue;

      // Prune if move collides with existing reservations
      if (res.move_collides(fid, cur_cell, nc, cur_t, agent_id)) continue;

      auto *nv = fg.U[nc];
      if (!nv) continue;

      int h = D->get(agent_id, nv);
      if (h >= static_cast<int>(fg.V.size())) continue;  // unreachable

      // Count blocking agents at (nc, nt): parked agents in the way
      int nb = 0;
      bool goal_blocked = false;
      auto occupants = res.get_occupants(fid, nc, nt);
      for (int occ : occupants) {
        if (occ == agent_id) continue;
        // Goal-locked agents are hard obstacles — skip this cell entirely
        if (goal_lock && ins->starts.size() > 0) {
          auto &occ_ep = res.agent_endpoints[occ];
          if (occ_ep.fleet_id >= 0) {
            auto *goal_v = ins->goals[occ];
            if (goal_v && occ_ep.cell_index == goal_v->index) {
              goal_blocked = true;
              break;
            }
          }
        }
        auto &occ_ep = res.agent_endpoints[occ];
        if (occ_ep.fleet_id >= 0 && occ_ep.end_time <= nt) ++nb;
      }
      if (goal_blocked) continue;

      // Congestion penalty (cap at 3, same as spatial BFS)
      int congestion = std::min(nb, 3);

      // Oscillation penalty: penalize revisiting recent cells in low-density areas
      int osc_penalty = 0;
      if (nb <= 2) {
        for (int rc : recent_cells[agent_id]) {
          if (rc == nc) osc_penalty += 2;
        }
      }

      visited.insert(nkey);
      came_from[nkey] = pack_key(cur_t, cur_cell);
      pq.push({h + congestion + osc_penalty, nb, nt, nc});
    }
  }

  // Deduplicate by first_step: keep only the best candidate per distinct
  // first step (lowest endpoint heuristic). Matches old BFS grouping behavior.
  std::sort(results.begin(), results.end(),
            [this, agent_id, &fg](const ProposedPath &a,
                                   const ProposedPath &b) {
              auto *va = fg.U[a.path.back()];
              auto *vb = fg.U[b.path.back()];
              int da = D->get(agent_id, va);
              int db = D->get(agent_id, vb);
              if (da != db) return da < db;
              return a.blocking_agents.size() < b.blocking_agents.size();
            });

  std::unordered_set<int> seen_fs;
  std::vector<ProposedPath> deduped;
  for (auto &pp : results) {
    if (seen_fs.insert(pp.first_step).second) {
      deduped.push_back(std::move(pp));
    }
  }
  results = std::move(deduped);

  // Update costs after sort for consistent ordering info
  for (size_t i = 0; i < results.size(); ++i) {
    auto *vend = fg.U[results[i].path.back()];
    results[i].cost = D->get(agent_id, vend)
                    + static_cast<int>(results[i].blocking_agents.size());
  }

  return results;
}

// ---------------------------------------------------------------------------
// Recursive push adapted from hetpibt's push_agent.
//
// Uses space-time BFS candidates (st_bfs_get_candidates) instead of
// spatial-only BFS. The reservation table (st_res_) is created in
// set_new_config and accumulates reservations as agents are assigned.
//
// On success: reserves the agent's multi-step BFS path in st_res_
// (so subsequent agents' BFS routes around it) and assigns the
// first step to Q_to (one-step config transition).
//
// On push failure: reservations from the failed cascade are NOT undone
// (Option 3 — matches hetpibt). Q_to and base_occupied_next ARE undone.
// ---------------------------------------------------------------------------
bool HetPIBT::funcPIBT(const int i, const HetConfig &Q_from, HetConfig &Q_to,
                         std::unordered_set<int> &keep_out,
                         std::unordered_set<int> &in_chain,
                         int max_depth)
{
  if (max_depth <= 0) return false;
  if (in_chain.count(i)) return false;

  // Goal-locked agents cannot be pushed — they are permanent obstacles.
  if (goal_lock && Q_from.positions[i] == ins->goals[i] &&
      Q_from.kappa[i] == 0) {
    return false;
  }

  int sp = ins->speed_period(i);
  int fid_i = ins->agents[i].fleet_id;
  int cs_i = ins->fleet_cell_sizes[fid_i];
  auto &fg_i = ins->fleet_graphs[fid_i];

  // Speed gating: if kappa > 0, agent MUST stay in place (mid-phase).
  // NOTE: speed-gated agents should be pre-reserved in step 2.5 of
  // set_new_config. This path only runs if called via priority inheritance.
  if (Q_from.kappa[i] != 0) {
    int next_kappa = (Q_from.kappa[i] + 1) % sp;
    auto *stay = Q_from.positions[i];
    if (!base_next_free(i, stay)) return false;
    mark_base_next(i, stay);
    Q_to.positions[i] = stay;
    Q_to.kappa[i] = next_kappa;
    st_res_->reserve_stay(i, fid_i, stay->index, 0, 2);
    st_res_->mark_processed(i);
    return true;
  }

  in_chain.insert(i);

  // kappa == 0: agent CAN move. Build candidates via space-time BFS.
  auto *v_now = Q_from.positions[i];
  int bfs_depth = std::max(bfs_default_depth, cs_i);

  // Fix endpoint to match actual position. A prior failed push cascade
  // may have moved this agent's endpoint to a stale cell.
  st_res_->agent_endpoints[i] = {fid_i, v_now->index, 0};

  auto candidates = st_bfs_get_candidates(i, *st_res_, bfs_depth);

  for (auto &pp : candidates) {
    // Convert fleet-cell index to Vertex*
    auto *u = fg_i.U[pp.first_step];
    if (!u) continue;

    // Secondary footprint check on base_occupied_next bitmap
    if (!base_next_free(i, u)) continue;

    // Swap conflict check (against already-assigned agents in Q_to)
    if (check_swap_conflict(i, v_now, u, Q_from, Q_to)) continue;

    // Keep-out check: skip if any base cell of u overlaps keep_out.
    // This prevents pushed agents from landing on the pusher's destination.
    if (!keep_out.empty()) {
      auto u_base = to_base_cells(u->index, fg_i.width, cs_i, ins->base_width);
      bool in_ko = false;
      for (int bc : u_base) {
        if (keep_out.count(bc)) { in_ko = true; break; }
      }
      if (in_ko) continue;
    }

    // Tentatively assign i to u (so pushed agents see i as taken
    // and don't try to re-push us). DON'T mark base_occupied_next yet —
    // this lets small agents inside a large agent's footprint freely
    // escape to adjacent cells instead of being trapped.
    Q_to.positions[i] = u;

    // Priority inheritance: push blocking agents at target footprint.
    if (u != v_now) {
      auto u_base = to_base_cells(u->index, fg_i.width, cs_i, ins->base_width);

      // Collect all unassigned blockers from base_occupied_now (deduplicated)
      std::vector<int> blockers;
      for (int bc : u_base) {
        int j = base_occupied_now[bc];
        if (j != NO_AGENT && j != i && Q_to.positions[j] == nullptr) {
          blockers.push_back(j);
        }
      }
      std::sort(blockers.begin(), blockers.end());
      blockers.erase(std::unique(blockers.begin(), blockers.end()),
                     blockers.end());

      if (!blockers.empty()) {
        // Build new keep_out: destination cells of this agent.
        // Pushed agents must not land here — mirrors hetpibt's push_agent.
        auto new_ko = keep_out;
        for (int bc : u_base) new_ko.insert(bc);

        // Save in_chain for backtracking between candidates
        auto saved_chain = in_chain;

        // Snapshot: which agents are unassigned before this cascade
        std::vector<int> unassigned_before;
        for (int a = 0; a < N; ++a) {
          if (Q_to.positions[a] == nullptr) unassigned_before.push_back(a);
        }

        bool all_pushed = true;
        for (int j : blockers) {
          if (Q_to.positions[j] != nullptr) continue;  // pushed by earlier cascade

          // Cross-fleet depth scaling: small blocker pushed by large agent
          // needs extra depth to escape the larger footprint.
          // Matches hetpibt: sub_depth = max(depth-1, ceil(cs_i / cs_j))
          int cs_j = ins->fleet_cell_sizes[ins->agents[j].fleet_id];
          int sub_depth = max_depth - 1;
          if (cs_i > cs_j) {
            sub_depth = std::max(sub_depth, (cs_i + cs_j - 1) / cs_j);
          }

          if (!funcPIBT(j, Q_from, Q_to, new_ko, in_chain, sub_depth)) {
            all_pushed = false;
            break;
          }

          // Add pushed agent's new position to keep_out so subsequent
          // blockers avoid it (matches hetpibt push_agent lines 407-413)
          if (Q_to.positions[j] != nullptr) {
            int fid_j = ins->agents[j].fleet_id;
            int cs_j2 = ins->fleet_cell_sizes[fid_j];
            auto j_base = to_base_cells(Q_to.positions[j]->index,
                                        ins->fleet_graphs[fid_j].width,
                                        cs_j2, ins->base_width);
            for (int bc : j_base) new_ko.insert(bc);
          }
        }

        // Verify i's footprint is clear after all pushes
        if (all_pushed && !base_next_free(i, u)) {
          all_pushed = false;
        }

        if (!all_pushed) {
          // Undo Q_to and base_occupied_next for failed cascade.
          // Stale st_map entries from failed pushes are left (Option 3),
          // but endpoints and parked_at_cell are reset to Q_from.
          for (int a : unassigned_before) {
            if (Q_to.positions[a] != nullptr) {
              clear_base_next(a, Q_to.positions[a]);
              Q_to.positions[a] = nullptr;
              int fid_a = ins->agents[a].fleet_id;
              st_res_->reset_agent(a, fid_a,
                                   Q_from.positions[a]->index);
            }
          }
          // Restore in_chain so next candidate can try the same agents
          in_chain = saved_chain;
          Q_to.positions[i] = nullptr;
          continue;
        }
      }
    }

    // All pushes succeeded (or no pushes needed). Mark bitmap and reserve.
    mark_base_next(i, u);
    st_res_->reserve_path(i, fid_i, 0, pp.path);
    st_res_->mark_processed(i);

    // Kappa model: only advance on actual movement.
    if (u != v_now && sp > 1) {
      Q_to.kappa[i] = 1;
    } else {
      Q_to.kappa[i] = 0;
    }

    return true;
  }

  // All candidates exhausted — remove from chain so caller can try alternatives.
  in_chain.erase(i);

  // Last resort: stay in place, kappa stays 0 (no movement)
  if (base_next_free(i, v_now)) {
    mark_base_next(i, v_now);
    Q_to.positions[i] = v_now;
    Q_to.kappa[i] = 0;
    st_res_->reserve_stay(i, fid_i, v_now->index, 0, 2);
    st_res_->mark_processed(i);
  }
  // If not free, leave Q_to.positions[i] as nullptr — caller handles it.
  return false;
}
