/*
 * HetPIBT planner
 *
 * Implements:
 *   - Priority traversal search (Algorithm 1 from the paper)
 *   - Per-agent space-time BFS (Algorithm 2)
 *   - Recursive push_agent with cross-fleet adaptive BFS depth
 *   - Windowed reservation with variable depth
 */
#pragma once

#include "dist_table.hpp"
#include "reservation.hpp"

// per-agent trajectories indexed by agent_id
using Solution = std::vector<Trajectory>;

struct Planner {
  const HetInstance* ins;
  const Deadline* deadline;
  std::mt19937* MT;
  const int verbose;

  const int N;       // total agents
  const int V_size;  // base grid vertex count
  DistTable D;
  ReservationTable P;
  std::vector<float> tie_breakers;
  std::unordered_set<int> goal_reached;      // agents permanently at their goals
  std::unordered_map<int, int> goal_time;   // agent_id -> step when goal reached

  // CORE (paper): elapsed counter — steps since last reaching goal, reset to 0
  std::vector<int> elapsed;

  // EXTENSION: stuck counter for non-biconnected graphs
  // Tracks distance-to-goal progress; increments when agent doesn't get closer
  std::vector<int> last_dist;
  std::vector<int> stuck_count;

  // EXTENSION: recent position history for anti-oscillation
  std::vector<std::deque<int>> recent_cells;

  const bool goal_lock;  // permanently lock agents at goals (pibt_rs-style)

  Planner(const HetInstance* _ins, const Deadline* _deadline,
          std::mt19937* _mt, int _verbose = 0, bool _goal_lock = false);
  ~Planner();

  Solution solve(int max_timesteps = 1000);

  // Algorithm 1: attempt to solve for one agent at a given timestep
  // returns true if a trajectory was reserved
  bool attempt_solve_for_agent(int agent_id, int time);

  // Algorithm 2: per-agent space-time BFS
  // returns candidate proposed paths sorted by (distance_to_goal, #blocking)
  std::vector<ProposedPath> get_next_locations(int agent_id, int time,
                                               const std::unordered_set<int>& keep_out,
                                               int depth);

 private:
  // recursive push: try to move agent_id out of the way at time `time`,
  // avoiding base cells in keep_out.  Pushes blockers recursively.
  // min_bfs_depth: minimum BFS lookahead (set by parent's cell_size so
  //   small agents can escape a large agent's footprint)
  bool push_agent(int agent_id, int time,
                  const std::unordered_set<int>& keep_out,
                  std::unordered_set<int>& in_chain, int max_depth,
                  int min_bfs_depth = 1);

  // update priorities for all agents
  void update_priorities(int step);
};

// convenience entry point
Solution solve(const HetInstance& ins, int verbose = 0,
               const Deadline* deadline = nullptr,
               std::mt19937* MT = nullptr, int max_timesteps = 1000,
               bool goal_lock = false);
