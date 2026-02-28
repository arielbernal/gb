/*
 * Space-time reservation table for het_rt_lacam PIBT
 *
 * Lightweight, ephemeral reservation table created per set_new_config() call.
 * Tracks agent positions across time steps using a spatial-temporal hash map
 * keyed on pack_key(time, base_cell_id) for O(1) collision checking.
 *
 * Cross-fleet collision detection: when a path is reserved on one fleet's
 * graph, base-grid cells covered by the footprint are inserted into st_map,
 * so agents on different fleets correctly detect overlaps.
 *
 * Ported from hetpibt's ReservationTable, simplified for per-call use:
 *   - No agent_cells reverse index (no trajectory removal needed)
 *   - No traj_log (visualization handled separately)
 *   - Uses het_rt_lacam's Instance* and free to_base_cells() from graph.hpp
 */
#pragma once
#include "instance.hpp"

// pack two ints into a uint64_t key for hash maps
inline uint64_t pack_key(int a, int b)
{
  return (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
         static_cast<uint64_t>(static_cast<uint32_t>(b));
}

// proposed path from space-time BFS (Task B output)
struct ProposedPath {
  std::vector<int> path;              // fleet cell indices: path[0]=start, path[1]=first step, ...
  std::vector<int> blocking_agents;   // agents parked at destination that need pushing
  int first_step;                     // fleet cell index to move to at t=1 (= path[1], or path[0] for wait)
  int cost;                           // BFS cost (for sorting)
};

struct STReservation {
  // primary spatial-temporal index: pack_key(time, base_cell) -> agent IDs
  std::unordered_map<uint64_t, std::vector<int>> st_map;

  // agent endpoint tracking: where each agent is "parked" after its last
  // explicit reservation (persists indefinitely beyond end_time)
  struct AgentEndpoint {
    int fleet_id;
    int cell_index;   // fleet cell index
    int end_time;
  };
  std::vector<AgentEndpoint> agent_endpoints;  // indexed by agent_id

  // spatial index for parked agents: base_cell -> agent IDs
  // agents parked beyond their last explicit reservation are tracked here
  std::unordered_map<int, std::vector<int>> parked_at_cell;

  // processed flag: only processed agents (goal-locked, speed-gated, or
  // assigned by funcPIBT) block future timesteps via parked_at_cell.
  // Unprocessed agents are only visible at their seed time (t=0).
  std::vector<bool> processed_;

  const Instance* ins;

  STReservation(const Instance* _ins, int num_agents);

  // seed the table with a configuration at t=0 (agents become parked)
  void seed(const HetConfig& config);

  // seed agents at t=0 WITHOUT parking them at future times.
  // Used by set_new_config: unprocessed agents should be visible at t=0
  // but not block BFS at t=1+. Only explicitly reserved agents (goal-locked,
  // speed-gated, already-processed) persist via reserve_path/reserve_stay.
  void seed_transient(const HetConfig& config);

  // reset an agent's endpoint and parked index to a given position.
  // Used during push cascade undo to fix stale endpoints from failed pushes.
  void reset_agent(int agent_id, int fleet_id, int cell_index);

  // mark an agent as processed — its parked position now blocks future times
  void mark_processed(int agent_id) { processed_[agent_id] = true; }

  // reserve a multi-step path for an agent (force-reserve, no collision check)
  // positions[0] = cell at start_time, positions[1] = cell at start_time+1, ...
  void reserve_path(int agent_id, int fleet_id, int start_time,
                    const std::vector<int>& positions);

  // reserve agent staying in place from start_time through end_time (inclusive)
  void reserve_stay(int agent_id, int fleet_id, int cell_index,
                    int start_time, int end_time);

  // check if a base cell is occupied at time by anyone other than exclude_agent
  bool is_occupied(int base_cell, int time, int exclude_agent = -1) const;

  // check if moving from->to on fleet fleet_id at time collides with
  // existing reservations. Checks:
  //   1. vertex conflict: is any base cell of `to` occupied at time+1?
  //   2. swap conflict: is there an agent at `to` at time that moves to
  //      `from` at time+1?
  bool move_collides(int fleet_id, int from_cell, int to_cell, int time,
                     int agent_id) const;

  // get all agents occupying base cells covered by fleet cell at given time
  // (for blocker identification). includes parked agents.
  std::vector<int> get_occupants(int fleet_id, int cell_index,
                                 int time) const;

  // get base cells covered by a fleet cell (convenience wrapper)
  std::vector<int> fleet_to_base(int fleet_id, int cell_index) const;

 private:
  // insert one fleet cell's base-grid footprint into st_map for agent at time
  void insert_cell(int agent_id, int fleet_id, int cell_index, int time);

  // update parked_at_cell index when an agent's endpoint changes
  void update_parked(int agent_id, int old_fleet, int old_cell,
                     bool had_old, int new_fleet, int new_cell);
};
