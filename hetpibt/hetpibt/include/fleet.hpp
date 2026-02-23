/*
 * fleet and agent definitions for heterogeneous MAPF
 *
 * A Fleet groups agents sharing identical footprint, velocity, and graph.
 * The CollisionChecker maps between fleet graphs via the base grid G'.
 */
#pragma once
#include "graph.hpp"

struct Fleet {
  const int id;
  const int cell_size;  // footprint in base-grid cells (e.g., 1, 2, 3)
  const float velocity;  // cells per timestep on this fleet's graph
  Graph G;               // this fleet's navigation graph

  Fleet(int _id, int _cell_size, float _velocity);
  ~Fleet() {}
};
using Fleets = std::vector<Fleet*>;

// agent with heterogeneous properties
struct Agent {
  const int id;        // global agent ID
  const int fleet_id;  // which fleet this agent belongs to
  float priority;      // dynamic priority (higher = more urgent)

  Agent(int _id, int _fleet_id);
};
using Agents = std::vector<Agent*>;

// maps between fleet graphs via the shared base occupancy grid G'
//
// T_g(cell) returns the set of base-grid cell indices that a fleet cell
// covers.  Two cells c1 in G1 and c2 in G2 overlap iff
// T_G1(c1) ∩ T_G2(c2) != {}.
//
// For efficiency, get_blocked_nodes() directly returns the cells on OTHER
// fleet graphs that overlap with a given cell (Rust reference approach).
struct CollisionChecker {
  std::vector<float> grid_sizes;  // grid_sizes[fleet_id] = cell_size
  int base_width;                 // base grid width
  int base_height;                // base grid height

  CollisionChecker();
  CollisionChecker(const Fleets& fleets, int _base_width, int _base_height);

  // T_g: map a fleet cell to base-grid cell indices
  std::vector<int> to_base_cells(int fleet_id, int cell_index,
                                 int fleet_width) const;

  // get cells on ALL OTHER fleet graphs that overlap with (fleet_id, x, y)
  // returns vector of (other_fleet_id, other_cell_index)
  std::vector<std::pair<int, int>> get_blocked_nodes(
      int fleet_id, int x, int y, const Fleets& fleets) const;

  // convert real-world coordinate to grid cell in a specific fleet
  std::pair<int, int> to_grid_space(int fleet_id, float wx, float wy) const;
};
