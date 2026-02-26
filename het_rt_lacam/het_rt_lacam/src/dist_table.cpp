#include "../include/dist_table.hpp"

DistTable::DistTable(const Instance *_ins) : ins(_ins)
{
  table.resize(ins->N);

  // BFS per agent on its fleet graph (parallel)
  auto bfs = [&](const int i) {
    auto *fg = ins->fleet_graph(i);
    const int K = fg->size();
    table[i].assign(K, K);  // K = unreachable sentinel

    auto g_i = ins->goals[i];
    if (g_i == nullptr) return;
    table[i][g_i->id] = 0;
    auto Q = std::queue<Vertex *>({g_i});
    while (!Q.empty()) {
      auto n = Q.front();
      Q.pop();
      const int d_n = table[i][n->id];
      for (auto &m : n->neighbor) {
        if (d_n + 1 >= table[i][m->id]) continue;
        table[i][m->id] = d_n + 1;
        Q.push(m);
      }
    }
  };

  auto pool = std::vector<std::future<void>>();
  for (uint i = 0; i < ins->N; ++i) {
    pool.emplace_back(std::async(std::launch::async, bfs, (int)i));
  }
  // futures join on destruction
}

int DistTable::get(const int i, const int v_id) const
{
  if (v_id < 0 || v_id >= (int)table[i].size()) return (int)table[i].size();
  return table[i][v_id];
}

int DistTable::get(const int i, const Vertex *v) const
{
  return get(i, v->id);
}
