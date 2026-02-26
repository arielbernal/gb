/*
 * Per-fleet distance table — each agent's BFS runs on its fleet's graph
 */
#pragma once

#include "graph.hpp"
#include "instance.hpp"
#include "utils.hpp"

struct DistTable {
  const Instance *ins;
  // table[i][v_id] = BFS distance from agent i's goal to vertex v on fleet graph
  std::vector<std::vector<int>> table;

  DistTable(const Instance *ins);

  int get(const int i, const int v_id) const;
  int get(const int i, const Vertex *v) const;
};
