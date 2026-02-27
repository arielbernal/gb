/*
 * graph definition — extended for heterogeneous agents
 *
 * Additions over lacam3:
 * - HetConfig: positions + kappa (speed phase counters)
 * - Fleet graph construction via non-overlapping tiling
 * - Base-grid footprint projection (to_base_cells)
 */
#pragma once
#include "utils.hpp"

struct Vertex {
  const int id;     // index for V in Graph
  const int index;  // index for U (width * y + x) in Graph
  const int x;
  const int y;
  std::vector<Vertex *> neighbor;

  Vertex(int _id, int _index, int _x, int _y);
};
using Vertices = std::vector<Vertex *>;
using Config = std::vector<Vertex *>;  // locations for all agents

// ---------------------------------------------------------------------------
// HetConfig: configuration augmented with speed-phase counters
// ---------------------------------------------------------------------------
struct HetConfig {
  Config positions;         // fleet-specific vertex per agent
  std::vector<int> kappa;   // speed phase counter per agent, 0..cell_size-1

  size_t size() const { return positions.size(); }

  bool operator==(const HetConfig &other) const
  {
    if (positions.size() != other.positions.size()) return false;
    for (size_t i = 0; i < positions.size(); ++i) {
      if (positions[i]->id != other.positions[i]->id) return false;
      if (kappa[i] != other.kappa[i]) return false;
    }
    return true;
  }
};

struct HetConfigHasher {
  uint operator()(const HetConfig &C) const;
};

// ---------------------------------------------------------------------------
// Graph
// ---------------------------------------------------------------------------
struct Graph {
  Vertices V;  // without nullptr
  Vertices U;  // with nullptr, i.e., |U| = width * height
  int width;   // grid width
  int height;  // grid height
  Graph();
  Graph(const std::string &filename);  // taking map filename
  ~Graph();

  // move semantics (Graph owns Vertex memory)
  Graph(Graph &&other) noexcept;
  Graph &operator=(Graph &&other) noexcept;
  Graph(const Graph &) = delete;
  Graph &operator=(const Graph &) = delete;

  // Build coarser fleet graph from base grid using non-overlapping tiling.
  // Fleet cell (fx, fy) covers base cells [fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs).
  // A fleet cell is passable only if ALL underlying base cells are passable.
  void build_from_base(const Graph &base, int cell_size);

  int size() const;
};

// ---------------------------------------------------------------------------
// Footprint projection: fleet cell -> base grid cells
// ---------------------------------------------------------------------------

// Given fleet-grid coordinates (fx, fy) and cell_size, return base-grid
// cell indices covered by the footprint.
std::vector<int> to_base_cells_xy(int fx, int fy, int cell_size,
                                  int base_width);

// Convenience: given a fleet-cell linear index and fleet_width.
inline std::vector<int> to_base_cells(int cell_index, int fleet_width,
                                      int cell_size, int base_width)
{
  return to_base_cells_xy(cell_index % fleet_width, cell_index / fleet_width,
                          cell_size, base_width);
}

bool is_same_config(const Config &C1, const Config &C2);
