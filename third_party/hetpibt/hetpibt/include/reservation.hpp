/*
 * reservation table and trajectory types for HetPIBT
 *
 * The reservation table P maps agents to their trajectories.
 * Internally it uses a spatial-temporal hash map keyed on
 * pack(time, base_cell_id) for O(1) collision checking.
 *
 * Cross-fleet collision detection uses T_g: when a trajectory is
 * reserved on one fleet's graph, ghost reservations are projected
 * onto all other fleets' overlapping cells via the base grid.
 */
#pragma once
#include "fleet.hpp"

// timed waypoint on a fleet's graph
struct TimedCell {
  int cell_index;  // vertex index on the fleet's graph (width * y + x)
  int time;        // discrete timestep
};

// trajectory: timed series of cells for one agent on its fleet's graph
struct Trajectory {
  int agent_id;
  int fleet_id;
  int start_time;
  std::vector<int> positions;  // cell_index at each timestep from start_time

  int end_time() const;
  int cell_at(int t) const;  // returns cell_index at timestep t
};

// path: untimed sequence of cells (used during planning before timing)
using Path = std::vector<int>;  // sequence of cell_index on a fleet graph

// proposed path from per-agent search (Algorithm 2 output)
struct ProposedPath {
  Path path;                       // untimed cells the agent would traverse
  std::vector<int> blocking_agents;  // agents that must move out
};

// dependency node for backtrack_and_reserve
// stored in an arena (vector); parent index = -1 for root
struct DepNode {
  int agent_id;
  int parent;       // index in the arena, -1 = root
  ProposedPath pp;  // the proposed path for this agent
};

// the reservation table P
//
// primary index: spatial-temporal hash map
//   key = pack(time, base_cell_id) -> set of agent IDs
// This gives O(1) collision checks per (time, cell) pair.
//
// secondary index: agent_cells[agent_id] -> list of (time, base_cell_id)
//   enables O(|trajectory|) removal.
//
// endpoint index: agent_last[agent_id] -> (fleet_id, cell_index, end_time)
//   tracks where each agent is "parked" after its last trajectory.
struct ReservationTable {
  // primary spatial-temporal index
  std::unordered_map<uint64_t, std::vector<int>> st_map;

  // reverse index for trajectory removal
  std::unordered_map<int, std::vector<uint64_t>> agent_cells;

  // agent endpoint tracking
  struct AgentEndpoint {
    int fleet_id;
    int cell_index;
    int end_time;
  };
  std::unordered_map<int, AgentEndpoint> agent_last;

  // spatial index for parked agents: base_cell -> set of agent IDs
  // maintained by update_parked_index(); enables O(1) parked-agent lookups
  std::unordered_map<int, std::vector<int>> parked_at_cell;

  // trajectory log: traj_log[agent_id] = chronological (time, cell_index)
  // populated by reserve(); used by make_log for visualization output
  std::unordered_map<int, std::vector<std::pair<int, int>>> traj_log;

  // cross-fleet collision checker
  const CollisionChecker* cc;
  const Fleets* fleets;

  ReservationTable();
  ReservationTable(const CollisionChecker* _cc, const Fleets* _fleets);

  // reserve a trajectory; also reserves cross-fleet ghost cells
  // fills timing gaps by holding the agent at its last position
  // returns false if the trajectory collides with existing reservations
  bool try_reserve(const Trajectory& traj);

  // force-reserve (used during backtrack; assumes collision-free)
  void reserve(const Trajectory& traj);

  // check if moving from `from` to `to` on fleet `fleet_id` at time `t`
  // collides with any existing reservation (vertex or swap conflict)
  bool move_collides(int fleet_id, int from, int to, int time,
                     int agent_id,
                     bool include_parked = false) const;

  // check if a cell on fleet `fleet_id` is occupied at time `t`
  // by any agent other than `exclude_agent`
  // when include_parked=true, also checks agents "parked" beyond
  // their last explicit reservation (for try_reserve collision safety)
  bool is_occupied(int fleet_id, int cell_index, int time,
                   int exclude_agent = -1,
                   bool include_parked = false) const;

  // get agents occupying a cell (including cross-fleet projections)
  std::vector<int> get_occupants(int fleet_id, int cell_index,
                                 int time) const;

  // remove all reservations for an agent
  void remove_agent(int agent_id);

  // get endpoint for an agent (-1 time if not found)
  AgentEndpoint get_endpoint(int agent_id) const;

  void clear();

 private:
  // project a fleet cell to base cells and insert into st_map
  void insert_cell(int agent_id, int fleet_id, int cell_index, int time);
  // collect all base cells for a fleet cell (including cross-fleet ghosts)
  std::vector<int> get_all_base_cells(int fleet_id, int cell_index) const;
  // update the parked_at_cell index when an agent's endpoint changes
  void update_parked_index(int agent_id, const AgentEndpoint* old_ep,
                           const AgentEndpoint* new_ep);
};
