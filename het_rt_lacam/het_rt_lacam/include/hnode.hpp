/*
 * high-level node of Het-LaCAM
 */
#pragma once

#include "dist_table.hpp"
#include "instance.hpp"
#include "lnode.hpp"

struct HNode;
struct CompareHNodePointers {
  bool operator()(const HNode *lhs, const HNode *rhs) const;
};

struct HNode {
  static int COUNT;

  const HetConfig C;
  HNode *parent;
  std::set<HNode *, CompareHNodePointers> neighbor;

  int g;
  int h;
  int f;

  // for low-level search
  std::vector<float> priorities;
  std::vector<int> order;
  std::queue<LNode *> search_tree;

  HNode(HetConfig _C, const DistTable *D, const Instance *ins,
        HNode *_parent = nullptr, int _g = 0, int _h = 0);
  ~HNode();

  // Speed-gated: agents with kappa>0 get only the stay option
  LNode *get_next_lowlevel_node(std::mt19937 &MT, const Instance *ins);
};
