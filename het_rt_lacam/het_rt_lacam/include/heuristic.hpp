/*
 * heuristic — sum of per-agent distances, weighted by cell_size for speed
 */
#pragma once
#include "dist_table.hpp"
#include "graph.hpp"
#include "instance.hpp"

struct Heuristic {
  const Instance *ins;
  const DistTable *D;

  Heuristic(const Instance *_ins, const DistTable *_D);
  int get(const HetConfig &C) const;
};
