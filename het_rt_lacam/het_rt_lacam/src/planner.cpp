#include "../include/planner.hpp"

#include <algorithm>
#include <iostream>

bool Planner::FLG_STAR = false;  // Phase 1: no anytime by default
bool Planner::FLG_GOAL_LOCK = false;
int Planner::PIBT_NUM = 1;      // Phase 1: single PIBT
bool Planner::FLG_MULTI_THREAD = false;
bool Planner::FLG_ST_BFS = true;  // space-time BFS by default
float Planner::RANDOM_INSERT_PROB1 = 0.0;
float Planner::RANDOM_INSERT_PROB2 = 0.0;

std::string Planner::MSG;
int Planner::CHECKPOINTS_DURATION = 5000;
constexpr int CHECKPOINTS_NIL = -1;

Planner::Planner(const Instance *_ins, int _verbose, const Deadline *_deadline,
                 int _seed)
    : ins(_ins),
      deadline(_deadline),
      seed(_seed),
      MT(std::mt19937(seed)),
      verbose(_verbose),
      N(ins->N),
      D(new DistTable(ins)),
      heuristic(new Heuristic(ins, D)),
      OPEN(),
      EXPLORED(),
      H_init(nullptr),
      H_goal(nullptr),
      current_root_(nullptr),
      search_initialized_(false),
      latest_generated_(nullptr),
      search_iter(0),
      time_initial_solution(-1),
      cost_initial_solution(-1),
      checkpoints()
{
  // Create PIBT instances
  for (int k = 0; k < PIBT_NUM; ++k) {
    pibts.push_back(new HetPIBT(ins, D, k + seed, FLG_GOAL_LOCK, FLG_ST_BFS));
  }
}

Planner::~Planner()
{
  for (auto &p : EXPLORED) delete p.second;
  delete heuristic;
  for (auto &p : pibts) delete p;
  delete D;
}

Solution Planner::solve()
{
  info(1, verbose, deadline, "start search (Het-LaCAM)");
  update_checkpoints();

  // insert initial node
  auto start_config = ins->make_start_config();
  H_init = create_highlevel_node(start_config, nullptr);
  OPEN.push_front(H_init);

  // search loop
  while (!OPEN.empty() && !is_expired(deadline)) {
    search_iter += 1;
    update_checkpoints();

    auto H = OPEN.front();

    // random diversification after initial solution
    if (H_goal != nullptr && RANDOM_INSERT_PROB2 > 0 &&
        get_random_float(MT) < RANDOM_INSERT_PROB2) {
      H = OPEN[get_random_int(MT, 0, (int)OPEN.size() - 1)];
    }

    // pruning: skip if f >= best known goal f
    if (H_goal != nullptr && H->f >= H_goal->f) {
      OPEN.pop_front();
      continue;
    }

    // goal check
    if (H_goal == nullptr && ins->is_goal(H->C)) {
      time_initial_solution = (int)elapsed_ms(deadline);
      cost_initial_solution = H->g;
      H_goal = H;
      info(1, verbose, deadline, "found initial solution, cost: ", H_goal->g);
      if (!FLG_STAR) break;
      continue;
    }

    // low-level search
    auto L = H->get_next_lowlevel_node(MT, ins, FLG_GOAL_LOCK);
    if (L == nullptr) {
      OPEN.pop_front();
      continue;
    }

    // generate successor configuration
    HetConfig Q_to;
    Q_to.positions.assign(N, nullptr);
    Q_to.kappa.assign(N, 0);

    auto res = set_new_config(H, L, Q_to);
    delete L;
    if (!res) continue;

    // check explored list
    auto iter = EXPLORED.find(Q_to);
    if (iter != EXPLORED.end()) {
      rewrite(H, iter->second);
      if (RANDOM_INSERT_PROB1 > 0 &&
          get_random_float(MT) < RANDOM_INSERT_PROB1) {
        OPEN.push_front(H_init);
      } else {
        OPEN.push_front(iter->second);
      }
    } else {
      auto H_new = create_highlevel_node(Q_to, H);
      OPEN.push_front(H_new);
    }
  }

  // end processing
  update_checkpoints();
  logging();
  auto solution = backtrack(H_goal);
  for (auto &p : EXPLORED) delete p.second;
  EXPLORED.clear();  // prevent double-free in destructor
  return solution;
}

HNode *Planner::create_highlevel_node(const HetConfig &Q, HNode *parent)
{
  auto g_val =
      (parent == nullptr) ? 0 : parent->g + get_edge_cost(parent->C, Q);
  auto h_val = heuristic->get(Q);
  auto H_new = new HNode(Q, D, ins, parent, g_val, h_val);
  EXPLORED[Q] = H_new;
  return H_new;
}

bool Planner::set_new_config(HNode *H, LNode *L, HetConfig &Q_to)
{
  auto Q_cands = std::vector<HetConfig>(PIBT_NUM);
  auto f_vals = std::vector<int>(PIBT_NUM, INT_MAX);

  auto worker = [&](int k) {
    Q_cands[k].positions.assign(N, nullptr);
    Q_cands[k].kappa.assign(N, 0);

    // Set hard constraints from LNode
    for (int d = 0; d < L->depth; ++d) {
      Q_cands[k].positions[L->who[d]] = L->where[d];
    }

    auto res =
        pibts[k]->set_new_config(H->C, Q_cands[k], H->order);
    if (res) {
      f_vals[k] =
          get_edge_cost(H->C, Q_cands[k]) + heuristic->get(Q_cands[k]);
    }
  };

  if (FLG_MULTI_THREAD && PIBT_NUM > 1) {
    auto threads = std::vector<std::thread>();
    for (int k = 0; k < PIBT_NUM; ++k) threads.emplace_back(worker, k);
    for (auto &th : threads) th.join();
  } else {
    for (int k = 0; k < PIBT_NUM; ++k) worker(k);
  }

  int min_f = INT_MAX;
  int min_idx = -1;
  for (int k = 0; k < PIBT_NUM; ++k) {
    if (f_vals[k] < min_f) {
      min_f = f_vals[k];
      min_idx = k;
    }
  }

  if (min_f < INT_MAX) {
    Q_to = std::move(Q_cands[min_idx]);
    return true;
  }
  return false;
}

void Planner::rewrite(HNode *H_from, HNode *H_to)
{
  H_from->neighbor.insert(H_to);

  std::queue<HNode *> Q({H_from});
  while (!Q.empty()) {
    auto n_from = Q.front();
    Q.pop();
    for (auto n_to : n_from->neighbor) {
      auto g_val = n_from->g + get_edge_cost(n_from->C, n_to->C);
      if (g_val < n_to->g) {
        if (n_to == H_goal)
          info(2, verbose, deadline, "cost update: ", H_goal->g, " -> ", g_val);
        n_to->g = g_val;
        n_to->f = n_to->g + n_to->h;
        n_to->parent = n_from;
        Q.push(n_to);
        if (H_goal != nullptr && n_to->f < H_goal->f) OPEN.push_front(n_to);
      }
    }
  }
}

int Planner::get_edge_cost(const HetConfig &C1, const HetConfig &C2)
{
  int cost = 0;
  for (int i = 0; i < N; ++i) {
    // Agent contributes cost 1 unless at goal with kappa=0 in both configs
    bool at_goal_c1 =
        (C1.positions[i] == ins->goals[i] && C1.kappa[i] == 0);
    bool at_goal_c2 =
        (C2.positions[i] == ins->goals[i] && C2.kappa[i] == 0);
    if (!at_goal_c1 || !at_goal_c2) cost += 1;
  }
  return cost;
}

Solution Planner::backtrack(HNode *H)
{
  std::vector<Config> plan;
  auto _H = H;
  while (_H != nullptr) {
    plan.push_back(_H->C.positions);
    _H = _H->parent;
  }
  std::reverse(plan.begin(), plan.end());
  return plan;
}

void Planner::update_checkpoints()
{
  const auto time = elapsed_ms(deadline);
  while (time >= checkpoints.size() * CHECKPOINTS_DURATION) {
    checkpoints.push_back(H_goal != nullptr ? H_goal->f : CHECKPOINTS_NIL);
  }
}

void Planner::logging()
{
  MSG = "";
  MSG += "checkpoints=";
  for (auto &k : checkpoints) MSG += std::to_string(k) + ",";
  MSG +=
      "\ncomp_time_initial_solution=" + std::to_string(time_initial_solution);
  MSG += "\ncost_initial_solution=" + std::to_string(cost_initial_solution);
  MSG += "\nsearch_iteration=" + std::to_string(search_iter);
  MSG += "\nnum_high_level_node=" + std::to_string(HNode::COUNT);
  MSG += "\nnum_low_level_node=" + std::to_string(LNode::COUNT);

  if (H_goal != nullptr && OPEN.empty()) {
    info(1, verbose, deadline, "solved optimally, cost:", H_goal->g);
  } else if (H_goal != nullptr) {
    info(1, verbose, deadline, "solved sub-optimally, cost:", H_goal->g);
  } else if (OPEN.empty()) {
    info(1, verbose, deadline, "no solution");
  } else {
    info(1, verbose, deadline, "timeout");
  }
  info(1, verbose, deadline, "search iteration:", search_iter,
       "\texplored:", EXPLORED.size());
}

// ---------------------------------------------------------------------------
// RT-LaCAM incremental methods
// ---------------------------------------------------------------------------

void Planner::reset()
{
  for (auto &p : EXPLORED) delete p.second;
  EXPLORED.clear();
  OPEN.clear();
  H_init = nullptr;
  H_goal = nullptr;
  current_root_ = nullptr;
  latest_generated_ = nullptr;
  search_initialized_ = false;
  search_iter = 0;
  time_initial_solution = -1;
  cost_initial_solution = -1;
  checkpoints.clear();
}

Planner::SearchStatus Planner::search(int node_budget)
{
  // Initialize on first call
  if (!search_initialized_) {
    auto start_config = ins->make_start_config();
    H_init = create_highlevel_node(start_config, nullptr);
    OPEN.push_front(H_init);
    current_root_ = H_init;
    latest_generated_ = H_init;
    search_initialized_ = true;
  }

  int iterations = 0;
  while (!OPEN.empty() && !is_expired(deadline) && iterations < node_budget) {
    search_iter += 1;
    iterations += 1;
    update_checkpoints();

    auto H = OPEN.front();

    // random diversification after initial solution
    if (H_goal != nullptr && RANDOM_INSERT_PROB2 > 0 &&
        get_random_float(MT) < RANDOM_INSERT_PROB2) {
      H = OPEN[get_random_int(MT, 0, (int)OPEN.size() - 1)];
    }

    // pruning: skip if f >= best known goal f
    if (H_goal != nullptr && H->f >= H_goal->f) {
      OPEN.pop_front();
      continue;
    }

    // goal check
    if (H_goal == nullptr && ins->is_goal(H->C)) {
      time_initial_solution = (int)elapsed_ms(deadline);
      cost_initial_solution = H->g;
      H_goal = H;
      latest_generated_ = H;
      info(1, verbose, deadline, "RT: found solution, cost: ", H_goal->g);
      if (!FLG_STAR) return SearchStatus::GOAL_FOUND;
      continue;
    }

    // low-level search
    auto L = H->get_next_lowlevel_node(MT, ins, FLG_GOAL_LOCK);
    if (L == nullptr) {
      OPEN.pop_front();
      continue;
    }

    // generate successor configuration
    HetConfig Q_to;
    Q_to.positions.assign(N, nullptr);
    Q_to.kappa.assign(N, 0);

    auto res = set_new_config(H, L, Q_to);
    delete L;
    if (!res) continue;

    // check explored list
    auto iter = EXPLORED.find(Q_to);
    if (iter != EXPLORED.end()) {
      rewrite(H, iter->second);
      latest_generated_ = iter->second;
      if (RANDOM_INSERT_PROB1 > 0 &&
          get_random_float(MT) < RANDOM_INSERT_PROB1) {
        OPEN.push_front(H_init);
      } else {
        OPEN.push_front(iter->second);
      }
    } else {
      auto H_new = create_highlevel_node(Q_to, H);
      latest_generated_ = H_new;
      OPEN.push_front(H_new);
    }
  }

  if (H_goal != nullptr) return SearchStatus::GOAL_FOUND;
  if (OPEN.empty()) return SearchStatus::NO_SOLUTION;
  return SearchStatus::SEARCHING;
}

HetConfig Planner::extract_next_step() const
{
  HNode *target = (H_goal != nullptr) ? H_goal : latest_generated_;

  if (target == nullptr || target == current_root_) {
    return current_root_->C;
  }

  // Strategy 1: parent-chain walk from target back to current_root_.
  // Works when the chain is intact (no rewrite() interference).
  {
    HNode *step = target;
    while (step->parent != nullptr && step->parent != current_root_) {
      step = step->parent;
    }
    if (step->parent == current_root_) {
      return step->C;
    }
  }

  // Strategy 2: rewrite() may have re-parented nodes, breaking the chain.
  // BFS through the neighbor graph from current_root_ to target.
  // The neighbor graph is always connected (bidirectional edges from
  // constructor), so this is guaranteed to find a path if one exists.
  {
    std::unordered_map<HNode *, HNode *> came_from;
    std::queue<HNode *> bfs;
    bfs.push(current_root_);
    came_from[current_root_] = nullptr;

    while (!bfs.empty()) {
      auto node = bfs.front();
      bfs.pop();
      if (node == target) {
        // Backtrack to find first step after current_root_
        HNode *step = node;
        while (came_from[step] != current_root_) step = came_from[step];
        return step->C;
      }
      for (HNode *nb : node->neighbor) {
        if (came_from.find(nb) == came_from.end()) {
          came_from[nb] = node;
          bfs.push(nb);
        }
      }
    }
  }

  // Stay in place — no forward step found yet
  return current_root_->C;
}

void Planner::advance(const HetConfig &next)
{
  auto iter = EXPLORED.find(next);
  if (iter != EXPLORED.end()) {
    current_root_ = iter->second;
  }
  // If next == current_root_->C (stay in place), current_root_ unchanged
}

HetConfig Planner::solve_one_step(int node_budget)
{
  search(node_budget);
  auto next = extract_next_step();
  advance(next);
  return next;
}
