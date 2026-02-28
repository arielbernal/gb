/*
 * instance definition — heterogeneous multi-fleet agents
 */
#pragma once
#include <random>

#include "graph.hpp"
#include "utils.hpp"

struct AgentInfo {
  int fleet_id;
  int cell_size;  // footprint in base cells (1 = unit agent)
};

struct Instance {
  Graph base_graph;                    // shared base grid
  std::vector<Graph> fleet_graphs;     // one per fleet, indexed by fleet_id
  std::vector<int> fleet_cell_sizes;   // cell_size per fleet_id
  std::vector<int> fleet_speed_periods; // speed period per fleet (kappa modulus)

  Config starts;                       // fleet-specific start vertices
  Config goals;                        // fleet-specific goal vertices
  std::vector<AgentInfo> agents;       // per-agent metadata
  uint N;                              // number of agents
  int base_width;
  int base_height;
  int num_fleets;

  // het_bench scenario
  Instance(const std::string &scen_filename, const std::string &map_filename,
           bool swap_xy = false);

  // homogeneous (standard MAPF benchmark), all cell_size=1
  Instance(const std::string &scen_filename, const std::string &map_filename,
           int _N);

  ~Instance();

  const Graph *fleet_graph(int agent_id) const;
  int speed_period(int agent_id) const;
  int skip_invalid_agents(const int verbose = 0);
  bool is_valid(const int verbose = 0) const;

  // Build initial HetConfig from starts (all kappa=0)
  HetConfig make_start_config() const;
  bool is_goal(const HetConfig &C) const;
};

using Solution = std::vector<Config>;
