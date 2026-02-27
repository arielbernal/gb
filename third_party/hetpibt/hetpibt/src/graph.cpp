#include "../include/graph.hpp"

Vertex::Vertex(int _id, int _index)
    : id(_id), index(_index), neighbor(Vertices())
{
}

Graph::Graph() : V(Vertices()), width(0), height(0) {}

Graph::~Graph()
{
  for (auto& v : V)
    if (v != nullptr) delete v;
  V.clear();
}

Graph::Graph(Graph&& other) noexcept
    : V(std::move(other.V)),
      U(std::move(other.U)),
      width(other.width),
      height(other.height)
{
  other.width = 0;
  other.height = 0;
}

Graph& Graph::operator=(Graph&& other) noexcept
{
  if (this != &other) {
    // free existing vertices
    for (auto& v : V)
      if (v != nullptr) delete v;
    V = std::move(other.V);
    U = std::move(other.U);
    width = other.width;
    height = other.height;
    other.width = 0;
    other.height = 0;
  }
  return *this;
}

// to load graph from .map file
static const std::regex r_height = std::regex(R"(height\s(\d+))");
static const std::regex r_width = std::regex(R"(width\s(\d+))");
static const std::regex r_map = std::regex(R"(map)");

Graph::Graph(const std::string& filename) : V(Vertices()), width(0), height(0)
{
  std::ifstream file(filename);
  if (!file) {
    std::cout << "file " << filename << " is not found." << std::endl;
    return;
  }
  std::string line;
  std::smatch results;

  // read fundamental graph parameters
  while (getline(file, line)) {
    // for CRLF coding
    if (!line.empty() && *(line.end() - 1) == 0x0d) line.pop_back();

    if (std::regex_match(line, results, r_height)) {
      height = std::stoi(results[1].str());
    }
    if (std::regex_match(line, results, r_width)) {
      width = std::stoi(results[1].str());
    }
    if (std::regex_match(line, results, r_map)) break;
  }

  U = Vertices(width * height, nullptr);

  // create vertices
  int y = 0;
  while (getline(file, line)) {
    // for CRLF coding
    if (!line.empty() && *(line.end() - 1) == 0x0d) line.pop_back();
    for (int x = 0; x < width; ++x) {
      char s = line[x];
      if (s == 'T' or s == '@') continue;  // obstacle
      auto index = width * y + x;
      auto v = new Vertex(V.size(), index);
      V.push_back(v);
      U[index] = v;
    }
    ++y;
  }
  file.close();

  // create edges (4-connected grid)
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      auto v = U[width * y + x];
      if (v == nullptr) continue;
      // left
      if (x > 0) {
        auto u = U[width * y + (x - 1)];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      // right
      if (x < width - 1) {
        auto u = U[width * y + (x + 1)];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      // up
      if (y > 0) {
        auto u = U[width * (y - 1) + x];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      // down
      if (y < height - 1) {
        auto u = U[width * (y + 1) + x];
        if (u != nullptr) v->neighbor.push_back(u);
      }
    }
  }
}

void Graph::build_from_base(const Graph& base, int cell_size)
{
  // clear any existing data
  for (auto& v : V)
    if (v != nullptr) delete v;
  V.clear();
  U.clear();

  // non-overlapping tiling: fleet cell (fx, fy) occupies base cells
  // [fx*cell_size..(fx+1)*cell_size-1] x [fy*cell_size..(fy+1)*cell_size-1]
  // agent moves cell_size base cells per step
  width = base.width / cell_size;
  height = base.height / cell_size;
  if (width <= 0 || height <= 0) {
    width = 0;
    height = 0;
    return;
  }
  U = Vertices(width * height, nullptr);

  // a fleet cell (fx, fy) is passable only if ALL underlying
  // base cells in [fx*cs .. (fx+1)*cs) x [fy*cs .. (fy+1)*cs) are passable
  for (int fy = 0; fy < height; ++fy) {
    for (int fx = 0; fx < width; ++fx) {
      bool passable = true;
      for (int dy = 0; dy < cell_size && passable; ++dy) {
        for (int dx = 0; dx < cell_size && passable; ++dx) {
          int bx = fx * cell_size + dx;
          int by = fy * cell_size + dy;
          if (bx >= base.width || by >= base.height) {
            passable = false;
          } else if (base.U[base.width * by + bx] == nullptr) {
            passable = false;
          }
        }
      }
      if (passable) {
        auto index = width * fy + fx;
        auto v = new Vertex(V.size(), index);
        V.push_back(v);
        U[index] = v;
      }
    }
  }

  // create edges (4-connected)
  for (int fy = 0; fy < height; ++fy) {
    for (int fx = 0; fx < width; ++fx) {
      auto v = U[width * fy + fx];
      if (v == nullptr) continue;
      if (fx > 0) {
        auto u = U[width * fy + (fx - 1)];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (fx < width - 1) {
        auto u = U[width * fy + (fx + 1)];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (fy > 0) {
        auto u = U[width * (fy - 1) + fx];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (fy < height - 1) {
        auto u = U[width * (fy + 1) + fx];
        if (u != nullptr) v->neighbor.push_back(u);
      }
    }
  }
}

int Graph::size() const { return V.size(); }
