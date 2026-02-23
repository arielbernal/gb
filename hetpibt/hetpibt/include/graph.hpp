/*
 * graph definition — supports multi-resolution grids
 *
 * A single Graph can represent either the base occupancy grid G'
 * or a fleet-specific navigation graph G^g with a larger cell_size.
 */
#pragma once
#include "utils.hpp"

struct Vertex {
  const int id;     // index for V in Graph
  const int index;  // index for U (width * y + x) in Graph
  std::vector<Vertex*> neighbor;

  Vertex(int _id, int _index);
};
using Vertices = std::vector<Vertex*>;

struct Graph {
  Vertices V;  // without nullptr
  Vertices U;  // with nullptr, i.e., |U| = width * height
  int width;   // grid width (in this graph's cells)
  int height;  // grid height (in this graph's cells)

  Graph();
  ~Graph();

  // move semantics (Graph owns vertex memory)
  Graph(Graph&& other) noexcept;
  Graph& operator=(Graph&& other) noexcept;

  // disable copy (would cause double-free)
  Graph(const Graph&) = delete;
  Graph& operator=(const Graph&) = delete;

  // load from .map file at native (cell_size=1) resolution
  Graph(const std::string& filename);

  // build a coarser fleet graph from a base grid and cell_size
  // a fleet cell is passable only if ALL underlying base cells are passable
  void build_from_base(const Graph& base, int cell_size);

  int size() const;  // the number of vertices, |V|
};

std::ostream& operator<<(std::ostream& os, const Vertex* v);
