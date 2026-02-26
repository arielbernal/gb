#include "../include/dist_table.hpp"

DistTable::DistTable(const HetInstance& ins) : N(ins.N)
{
  setup(ins);
}

void DistTable::setup(const HetInstance& ins)
{
  fleet_graph_sizes.resize(ins.fleets.size(), 0);
  for (auto* f : ins.fleets) {
    if (f != nullptr) fleet_graph_sizes[f->id] = f->G.size();
  }

  table.resize(N);
  OPEN.resize(N);

  for (uint i = 0; i < ins.N; ++i) {
    auto* fleet = ins.get_fleet(i);
    int K = fleet->G.size();
    table[i].assign(K, K);  // initialize to K (unreachable sentinel)

    if (ins.goals[i] != nullptr) {
      table[i][ins.goals[i]->id] = 0;
      OPEN[i].push(ins.goals[i]);
    }
  }
}

int DistTable::get(int agent_id, int vertex_id)
{
  if (vertex_id < 0 ||
      vertex_id >= static_cast<int>(table[agent_id].size())) {
    return INT_MAX;
  }

  // if already computed, return
  int K = static_cast<int>(table[agent_id].size());
  if (table[agent_id][vertex_id] < K) return table[agent_id][vertex_id];

  // lazy BFS expansion until we find the requested vertex
  while (!OPEN[agent_id].empty()) {
    auto* v = OPEN[agent_id].front();
    OPEN[agent_id].pop();
    int d = table[agent_id][v->id] + 1;
    for (auto* u : v->neighbor) {
      if (table[agent_id][u->id] < K) continue;  // already visited
      table[agent_id][u->id] = d;
      OPEN[agent_id].push(u);
      if (u->id == vertex_id) return d;
    }
  }

  return table[agent_id][vertex_id];
}

int DistTable::get(int agent_id, Vertex* v)
{
  if (v == nullptr) return INT_MAX;
  return get(agent_id, v->id);
}

void DistTable::recalculate(int agent_id, const HetInstance& ins,
                            const std::unordered_set<int>& blocked_cells)
{
  auto* fleet = ins.get_fleet(agent_id);
  int K = fleet->G.size();
  table[agent_id].assign(K, K);

  // clear BFS queue
  while (!OPEN[agent_id].empty()) OPEN[agent_id].pop();

  if (ins.goals[agent_id] == nullptr) return;
  auto* goal = ins.goals[agent_id];

  table[agent_id][goal->id] = 0;
  OPEN[agent_id].push(goal);

  // full BFS from goal, skipping blocked cells
  while (!OPEN[agent_id].empty()) {
    auto* v = OPEN[agent_id].front();
    OPEN[agent_id].pop();
    int d = table[agent_id][v->id] + 1;
    for (auto* u : v->neighbor) {
      if (table[agent_id][u->id] < K) continue;
      if (blocked_cells.count(u->index)) continue;
      table[agent_id][u->id] = d;
      OPEN[agent_id].push(u);
    }
  }
}
