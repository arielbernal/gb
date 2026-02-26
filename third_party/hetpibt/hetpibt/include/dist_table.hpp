/*
 * distance table — per-agent lazy BFS from goal
 *
 * Each agent's distance is computed on its fleet's graph via BFS from
 * the goal vertex.  Distances are lazily evaluated: BFS is only expanded
 * when a distance is requested for a vertex not yet reached.
 *
 * Supports recalculation treating goal-reached agents as obstacles
 * (matching the Rust reference approach).
 */
#pragma once
#include "instance.hpp"

struct DistTable {
  const int N;  // number of agents
  // table[agent_id][vertex_id on fleet graph] = BFS distance to goal
  std::vector<std::vector<int>> table;
  std::vector<std::queue<Vertex*>> OPEN;  // BFS frontiers, one per agent

  DistTable(const HetInstance& ins);

  int get(int agent_id, int vertex_id);
  int get(int agent_id, Vertex* v);

  // full recalculation for one agent, treating blocked_cells as obstacles
  void recalculate(int agent_id, const HetInstance& ins,
                   const std::unordered_set<int>& blocked_cells);

 private:
  void setup(const HetInstance& ins);
  // per-fleet graph sizes for bounds
  std::vector<int> fleet_graph_sizes;
};
