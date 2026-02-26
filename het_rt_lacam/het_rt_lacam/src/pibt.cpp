#include "../include/pibt.hpp"
#include <cassert>

HetPIBT::HetPIBT(const Instance *_ins, const DistTable *_D, int seed)
    : ins(_ins),
      MT(std::mt19937(seed)),
      N(ins->N),
      D(_D),
      NO_AGENT(N),
      base_size(ins->base_width * ins->base_height),
      base_occupied_now(base_size, NO_AGENT),
      base_occupied_next(base_size, NO_AGENT),
      max_fleet_vertices(0)
{
  // Per-fleet occupancy arrays
  fleet_occupied_now.resize(ins->num_fleets);
  fleet_occupied_next.resize(ins->num_fleets);
  for (int f = 0; f < ins->num_fleets; ++f) {
    int sz = ins->fleet_graphs[f].size();
    fleet_occupied_now[f].assign(sz, NO_AGENT);
    fleet_occupied_next[f].assign(sz, NO_AGENT);
    if (sz > max_fleet_vertices) max_fleet_vertices = sz;
  }

  // Candidates buffer: max 4 neighbors + stay = 5
  C_next.resize(N);
  for (int i = 0; i < N; ++i) C_next[i].reserve(5);

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

  return success;
}

// ---------------------------------------------------------------------------
// Recursive push adapted from hetpibt's push_agent.
//
// Key differences from the vanilla funcPIBT this replaces:
//   - max_depth limit prevents exponential blowup in push chains
//   - keep_out prevents pushed agents from landing on the pusher's destination
//   - in_chain prevents circular push loops (explicit set, not just Q_to check)
//   - Cross-fleet depth scaling: small agents pushed by large agents get
//     extra recursion depth to escape the larger footprint
//   - Save/restore of in_chain enables trying alternative candidates
//
// What is NOT changed (collision checking stays untouched):
//   - base_occupied_now / base_occupied_next bitmap model
//   - base_next_free(), mark_base_next(), clear_base_next()
//   - check_swap_conflict()
//   - Kappa (speed-phase) model
// ---------------------------------------------------------------------------
bool HetPIBT::funcPIBT(const int i, const HetConfig &Q_from, HetConfig &Q_to,
                         std::unordered_set<int> &keep_out,
                         std::unordered_set<int> &in_chain,
                         int max_depth)
{
  if (max_depth <= 0) return false;
  if (in_chain.count(i)) return false;

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
    return true;
  }

  in_chain.insert(i);

  // kappa == 0: agent CAN move. Build candidates.
  auto *v_now = Q_from.positions[i];
  C_next[i].clear();
  for (auto *u : v_now->neighbor) {
    C_next[i].push_back(u);
    tie_breakers[u->id] = get_random_float(MT);
  }
  C_next[i].push_back(v_now);  // stay option
  tie_breakers[v_now->id] = get_random_float(MT);

  // Sort by distance-to-goal + tie-breaker
  std::sort(C_next[i].begin(), C_next[i].end(),
            [&](Vertex *const a, Vertex *const b) {
              return D->get(i, a) + tie_breakers[a->id] <
                     D->get(i, b) + tie_breakers[b->id];
            });

  for (auto *u : C_next[i]) {
    // Footprint collision check on base grid
    if (!base_next_free(i, u)) continue;

    // Swap conflict check
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

      // Collect all unassigned blockers (deduplicated)
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
          // Undo ALL assignments made during this cascade
          for (int a : unassigned_before) {
            if (Q_to.positions[a] != nullptr) {
              clear_base_next(a, Q_to.positions[a]);
              Q_to.positions[a] = nullptr;
            }
          }
          // Restore in_chain so next candidate can try the same agents
          in_chain = saved_chain;
          Q_to.positions[i] = nullptr;
          continue;
        }
      }
    }

    // All pushes succeeded (or no pushes needed). Mark i's footprint.
    mark_base_next(i, u);

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
  }
  // If not free, leave Q_to.positions[i] as nullptr — caller handles it.
  return false;
}
