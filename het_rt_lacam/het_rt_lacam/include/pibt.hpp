/*
 * Heterogeneous PIBT — footprint-aware, speed-gated configuration generator
 *
 * Key differences from lacam3 PIBT:
 * - Speed gating: agents with kappa > 0 must stay in place
 * - Base-grid occupancy bitmap for cross-fleet footprint collision
 * - Works with HetConfig (positions + kappa)
 */
#pragma once
#include <deque>
#include <queue>
#include "dist_table.hpp"
#include "graph.hpp"
#include "instance.hpp"
#include "utils.hpp"

struct HetPIBT {
  const Instance *ins;
  std::mt19937 MT;

  const int N;
  const DistTable *D;
  const int NO_AGENT;
  bool goal_lock;

  // Base-grid occupancy: base_cell_index -> agent_id or NO_AGENT
  int base_size;  // base_width * base_height
  std::vector<int> base_occupied_now;
  std::vector<int> base_occupied_next;

  // Candidates buffer
  std::vector<std::vector<Vertex *>> C_next;
  std::vector<float> tie_breakers;  // per fleet vertex (max across fleets)
  int max_fleet_vertices;

  // BFS lookahead
  std::vector<std::deque<int>> recent_cells;  // oscillation history per agent
  int bfs_default_depth;                       // default BFS depth (2)

  HetPIBT(const Instance *_ins, const DistTable *_D, int seed = 0,
          bool _goal_lock = false);
  ~HetPIBT();

  // Main entry: generate a new HetConfig from Q_from, filling Q_to.
  // Pre-filled entries in Q_to.positions are hard constraints.
  // Returns true on success.
  bool set_new_config(const HetConfig &Q_from, HetConfig &Q_to,
                      const std::vector<int> &order);

  // Recursive push adapted from hetpibt's push_agent.
  // keep_out: base-cell indices the agent must avoid (pusher's destination)
  // in_chain: agents already in the current push chain (cycle detection)
  // max_depth: remaining recursion depth (decremented per push level)
  bool funcPIBT(const int i, const HetConfig &Q_from, HetConfig &Q_to,
                std::unordered_set<int> &keep_out,
                std::unordered_set<int> &in_chain,
                int max_depth);

  // BFS candidate generation (replaces 1-step neighbor enumeration)
  void bfs_get_candidates(int agent_id, const HetConfig &Q_from, int depth);

  // Footprint helpers
  void mark_base_now(int agent_id, Vertex *v);
  void mark_base_next(int agent_id, Vertex *v);
  void clear_base_now(int agent_id, Vertex *v);
  void clear_base_next(int agent_id, Vertex *v);
  bool base_next_free(int agent_id, Vertex *v) const;
  bool check_swap_conflict(int agent_i, Vertex *from_i, Vertex *to_i,
                           const HetConfig &Q_from, const HetConfig &Q_to) const;
};
