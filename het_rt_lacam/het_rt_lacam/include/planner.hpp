/*
 * Het-LaCAM planner — Phase 1 (no refiner, no scatter, no SUO)
 *
 * Core LaCAM* DFS with:
 * - HetConfig (positions + kappa)
 * - HetPIBT configuration generator
 * - Footprint-aware collision checking
 * - Speed-gated constraint enumeration
 */
#pragma once

#include "dist_table.hpp"
#include "graph.hpp"
#include "heuristic.hpp"
#include "hnode.hpp"
#include "instance.hpp"
#include "pibt.hpp"
#include "utils.hpp"

struct Planner {
  const Instance *ins;
  const Deadline *deadline;
  const int seed;
  std::mt19937 MT;
  const int verbose;

  // solver utils
  const int N;
  DistTable *D;

  // heuristic
  Heuristic *heuristic;

  // configuration generator
  std::vector<HetPIBT *> pibts;

  // search state
  std::deque<HNode *> OPEN;
  std::unordered_map<HetConfig, HNode *, HetConfigHasher> EXPLORED;
  HNode *H_init;
  HNode *H_goal;

  // RT-LaCAM incremental state
  HNode *current_root_;       // config agents are currently at (for RT mode)
  bool search_initialized_;   // whether H_init has been created
  HNode *latest_generated_;   // most recently generated node (for extract_next_step)

  // RT search status
  enum class SearchStatus { SEARCHING, GOAL_FOUND, NO_SOLUTION };

  // parameters
  static bool FLG_STAR;
  static bool FLG_GOAL_LOCK;
  static int PIBT_NUM;
  static bool FLG_MULTI_THREAD;
  static float RANDOM_INSERT_PROB1;
  static float RANDOM_INSERT_PROB2;

  // logging
  static std::string MSG;
  static int CHECKPOINTS_DURATION;
  int search_iter;
  int time_initial_solution;
  int cost_initial_solution;
  std::vector<int> checkpoints;

  Planner(const Instance *_ins, int _verbose = 0,
          const Deadline *_deadline = nullptr, int _seed = 0);
  ~Planner();

  // Standard (full-horizon) solve
  Solution solve();

  // RT-LaCAM incremental methods
  SearchStatus search(int node_budget);
  HetConfig extract_next_step() const;
  void advance(const HetConfig &next);
  HetConfig solve_one_step(int node_budget);
  void reset();

  bool set_new_config(HNode *S, LNode *M, HetConfig &Q_to);
  HNode *create_highlevel_node(const HetConfig &Q, HNode *parent);
  void rewrite(HNode *H_from, HNode *H_to);
  int get_edge_cost(const HetConfig &C1, const HetConfig &C2);
  Solution backtrack(HNode *H);
  void update_checkpoints();
  void logging();
};
