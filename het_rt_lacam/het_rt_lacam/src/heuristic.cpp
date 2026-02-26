#include "../include/heuristic.hpp"

Heuristic::Heuristic(const Instance *_ins, const DistTable *_D)
    : ins(_ins), D(_D)
{
}

int Heuristic::get(const HetConfig &C) const
{
  int cost = 0;
  for (uint i = 0; i < ins->N; ++i) {
    int d = D->get(i, C.positions[i]);
    // Each fleet-graph step takes speed_period wall-clock ticks.
    // Remaining kappa steps (phase not yet zero) add partial cost.
    int sp = ins->speed_period(i);
    cost += d * sp + C.kappa[i];
  }
  return cost;
}
