#include "../include/hnode.hpp"

#include <random>

int HNode::COUNT = 0;

HNode::HNode(HetConfig _C, const DistTable *D, const Instance *ins,
             HNode *_parent, int _g, int _h)
    : C(std::move(_C)),
      parent(_parent),
      neighbor(),
      g(_g),
      h(_h),
      f(g + h),
      priorities(C.size(), 0),
      order(C.size(), 0),
      search_tree(std::queue<LNode *>())
{
  ++COUNT;

  search_tree.push(new LNode());
  const auto N = C.size();

  // update neighbor graph (for LaCAM* rewriting)
  if (parent != nullptr) {
    neighbor.insert(parent);
    parent->neighbor.insert(this);
  }

  // set priorities
  if (parent == nullptr) {
    for (size_t i = 0; i < N; ++i) {
      int d = D->get((int)i, C.positions[i]);
      int sp = ins->speed_period((int)i);
      // Weighted by speed_period so slow agents get fair priority
      priorities[i] = (float)(d * sp + C.kappa[i]) / 10000.0f;
    }
  } else {
    // dynamic priorities, akin to PIBT
    for (size_t i = 0; i < N; ++i) {
      if (D->get((int)i, C.positions[i]) != 0 || C.kappa[i] != 0) {
        priorities[i] = parent->priorities[i] + 1;
      } else {
        priorities[i] = parent->priorities[i] - (int)parent->priorities[i];
      }
    }
  }

  // set order: highest priority first
  std::iota(order.begin(), order.end(), 0);
  std::sort(order.begin(), order.end(),
            [&](int i, int j) { return priorities[i] > priorities[j]; });
}

HNode::~HNode()
{
  while (!search_tree.empty()) {
    delete search_tree.front();
    search_tree.pop();
  }
}

LNode *HNode::get_next_lowlevel_node(std::mt19937 &MT, const Instance *ins)
{
  if (search_tree.empty()) return nullptr;

  auto L = search_tree.front();
  search_tree.pop();
  if (L->depth < (int)C.size()) {
    auto i = order[L->depth];

    // Build set of occupied base cells from:
    //  (a) explicitly constrained agents in this LNode
    //  (b) unconstrained speed-gated agents (kappa > 0, must stay in place)
    // This prunes geometrically infeasible constraints early, avoiding
    // wasted PIBT calls (the dominant source of s2 failures).
    std::unordered_set<int> occupied;
    std::unordered_set<int> constrained_set;

    for (int d = 0; d < L->depth; ++d) {
      int j = L->who[d];
      constrained_set.insert(j);
      int fid_j = ins->agents[j].fleet_id;
      int cs_j = ins->fleet_cell_sizes[fid_j];
      auto cells = to_base_cells(L->where[d]->index,
                                 ins->fleet_graphs[fid_j].width,
                                 cs_j, ins->base_width);
      for (int bc : cells) occupied.insert(bc);
    }

    // Speed-gated unconstrained agents are guaranteed to stay at their
    // current position. Include their footprints so no agent is
    // constrained to a cell that will inevitably collide (s25 failures).
    for (uint a = 0; a < ins->N; ++a) {
      if ((int)a == i) continue;
      if (constrained_set.count(a)) continue;
      if (C.kappa[a] == 0) continue;
      int fid_a = ins->agents[a].fleet_id;
      int cs_a = ins->fleet_cell_sizes[fid_a];
      auto cells = to_base_cells(C.positions[a]->index,
                                 ins->fleet_graphs[fid_a].width,
                                 cs_a, ins->base_width);
      for (int bc : cells) occupied.insert(bc);
    }

    int fid_i = ins->agents[i].fleet_id;
    int cs_i = ins->fleet_cell_sizes[fid_i];
    int fw_i = ins->fleet_graphs[fid_i].width;

    if (C.kappa[i] != 0) {
      // Speed gating: must stay. Only push if stay doesn't collide.
      auto *stay = C.positions[i];
      auto stay_cells = to_base_cells(stay->index, fw_i, cs_i,
                                      ins->base_width);
      bool collides = false;
      for (int bc : stay_cells) {
        if (occupied.count(bc)) { collides = true; break; }
      }
      if (!collides) {
        search_tree.push(new LNode(L, i, stay));
      }
    } else {
      // kappa == 0: enumerate neighbors + stay, prune by footprint
      auto cands = C.positions[i]->neighbor;
      cands.push_back(C.positions[i]);
      std::shuffle(cands.begin(), cands.end(), MT);

      for (auto u : cands) {
        auto u_cells = to_base_cells(u->index, fw_i, cs_i, ins->base_width);
        bool collides = false;
        for (int bc : u_cells) {
          if (occupied.count(bc)) { collides = true; break; }
        }
        if (!collides) {
          search_tree.push(new LNode(L, i, u));
        }
      }
    }
  }
  return L;
}

std::ostream &operator<<(std::ostream &os, const HNode *H)
{
  os << "f=" << std::setw(6) << H->f << "\tg=" << std::setw(6) << H->g
     << "\th=" << std::setw(6) << H->h << "\tQ=" << H->C;
  return os;
}

bool CompareHNodePointers::operator()(const HNode *l, const HNode *r) const
{
  const auto N = l->C.size();
  for (size_t i = 0; i < N; ++i) {
    if (l->C.positions[i] != r->C.positions[i])
      return l->C.positions[i]->id < r->C.positions[i]->id;
    if (l->C.kappa[i] != r->C.kappa[i])
      return l->C.kappa[i] < r->C.kappa[i];
  }
  return false;
}
