/*
 * fast collision checking, used in refiner and SIPP
 * Adapted from lacam3: constructor takes (graph_size, N) instead of Instance*
 */
#pragma once

#include "graph.hpp"
#include "utils.hpp"

struct CollisionTable {
  // vertex, time, agents
  std::vector<std::vector<std::vector<int>>> body;
  std::vector<std::vector<int>> body_last;
  int collision_cnt;
  int N;

  CollisionTable(int graph_size, int N_);
  ~CollisionTable();

  int getCollisionCost(const Vertex *v_from, const Vertex *v_to,
                       const int t_from);
  void enrollPath(const int i, Path &path);
  void clearPath(const int i, Path &path);
  void shrink();
};
