/*
 * heterogeneous MAPF instance definition
 *
 * Supports the het_bench scenario format:
 *   agent_id fleet_id footprint velocity sx sy gx gy grid_w grid_h
 * (space-separated, no header line)
 *
 * Also supports programmatic construction for testing.
 */
#pragma once
#include <random>

#include "fleet.hpp"

struct HetInstance {
  Graph base_grid;       // G': finest resolution occupancy grid
  Fleets fleets;         // all fleet definitions (owned)
  Agents agents;         // all agents across all fleets (owned)
  Vertices starts;       // start[i] on agent[i]'s fleet graph
  Vertices goals;        // goal[i] on agent[i]'s fleet graph
  uint N;                // total number of agents
  CollisionChecker cc;   // cross-fleet collision checker

  // load from het_bench scenario file + .map file
  HetInstance(const std::string& scen_filename,
              const std::string& map_filename);

  // programmatic construction for testing
  HetInstance(const std::string& map_filename,
              const std::vector<int>& fleet_ids,
              const std::vector<int>& cell_sizes,
              const std::vector<float>& velocities,
              const std::vector<int>& start_indexes,
              const std::vector<int>& goal_indexes);

  ~HetInstance();

  // simple feasibility check
  bool is_valid(const int verbose = 0) const;

  // thorough scenario validation:
  //  - no start footprints overlap on base grid (cross-fleet)
  //  - no goal footprints overlap on base grid (cross-fleet)
  //  - no start footprint overlaps any goal footprint
  //  - every agent can BFS-reach its goal on its fleet graph
  // returns true if all checks pass; prints errors to stderr
  bool validate_scenario(const int verbose = 0) const;

  // get the fleet for a given agent
  Fleet* get_fleet(int agent_id) const;
};
