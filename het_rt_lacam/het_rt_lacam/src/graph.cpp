#include "../include/graph.hpp"

Vertex::Vertex(int _id, int _index, int _x, int _y)
    : id(_id), index(_index), x(_x), y(_y), neighbor()
{
}

Graph::Graph() : V(Vertices()), width(0), height(0) {}

Graph::~Graph()
{
  for (auto &v : V)
    if (v != nullptr) delete v;
  V.clear();
}

Graph::Graph(Graph &&other) noexcept
    : V(std::move(other.V)),
      U(std::move(other.U)),
      width(other.width),
      height(other.height)
{
  other.width = 0;
  other.height = 0;
}

Graph &Graph::operator=(Graph &&other) noexcept
{
  if (this != &other) {
    for (auto &v : V)
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

// to load graph
static const std::regex r_height = std::regex(R"(height\s(\d+))");
static const std::regex r_width = std::regex(R"(width\s(\d+))");
static const std::regex r_map = std::regex(R"(map)");

Graph::Graph(const std::string &filename) : V(Vertices()), width(0), height(0)
{
  std::ifstream file(filename);
  if (!file) {
    std::cout << "file " << filename << " is not found." << std::endl;
    return;
  }
  std::string line;
  std::smatch results;

  while (getline(file, line)) {
    if (!line.empty() && *(line.end() - 1) == 0x0d) line.pop_back();
    if (std::regex_match(line, results, r_height))
      height = std::stoi(results[1].str());
    if (std::regex_match(line, results, r_width))
      width = std::stoi(results[1].str());
    if (std::regex_match(line, results, r_map)) break;
  }

  U = Vertices(width * height, nullptr);

  int y = 0;
  while (getline(file, line)) {
    if (!line.empty() && *(line.end() - 1) == 0x0d) line.pop_back();
    for (int x = 0; x < width; ++x) {
      char s = line[x];
      if (s == 'T' || s == '@') continue;
      auto index = width * y + x;
      auto v = new Vertex(V.size(), index, x, y);
      V.push_back(v);
      U[index] = v;
    }
    ++y;
  }
  file.close();

  // create 4-connected edges
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      auto v = U[width * y + x];
      if (v == nullptr) continue;
      if (x > 0) {
        auto u = U[width * y + (x - 1)];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (x < width - 1) {
        auto u = U[width * y + (x + 1)];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (y < height - 1) {
        auto u = U[width * (y + 1) + x];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (y > 0) {
        auto u = U[width * (y - 1) + x];
        if (u != nullptr) v->neighbor.push_back(u);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Fleet graph construction via non-overlapping tiling
// ---------------------------------------------------------------------------
void Graph::build_from_base(const Graph &base, int cell_size)
{
  // clean up any existing data
  for (auto &v : V)
    if (v != nullptr) delete v;
  V.clear();
  U.clear();

  width = base.width / cell_size;
  height = base.height / cell_size;
  U = Vertices(width * height, nullptr);

  // A fleet cell is passable only if ALL underlying base cells are passable
  for (int fy = 0; fy < height; ++fy) {
    for (int fx = 0; fx < width; ++fx) {
      bool passable = true;
      for (int dy = 0; dy < cell_size && passable; ++dy) {
        for (int dx = 0; dx < cell_size && passable; ++dx) {
          int bx = fx * cell_size + dx;
          int by = fy * cell_size + dy;
          if (bx >= base.width || by >= base.height ||
              base.U[base.width * by + bx] == nullptr) {
            passable = false;
          }
        }
      }
      if (passable) {
        auto index = width * fy + fx;
        auto v = new Vertex(V.size(), index, fx, fy);
        V.push_back(v);
        U[index] = v;
      }
    }
  }

  // create 4-connected edges on fleet graph
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
      if (fy < height - 1) {
        auto u = U[width * (fy + 1) + fx];
        if (u != nullptr) v->neighbor.push_back(u);
      }
      if (fy > 0) {
        auto u = U[width * (fy - 1) + fx];
        if (u != nullptr) v->neighbor.push_back(u);
      }
    }
  }
}

int Graph::size() const { return V.size(); }

// ---------------------------------------------------------------------------
// Footprint projection
// ---------------------------------------------------------------------------
std::vector<int> to_base_cells_xy(int fx, int fy, int cell_size, int base_width)
{
  std::vector<int> cells;
  cells.reserve(cell_size * cell_size);
  for (int dy = 0; dy < cell_size; ++dy) {
    for (int dx = 0; dx < cell_size; ++dx) {
      int bx = fx * cell_size + dx;
      int by = fy * cell_size + dy;
      cells.push_back(base_width * by + bx);
    }
  }
  return cells;
}

// ---------------------------------------------------------------------------
// HetConfig utilities
// ---------------------------------------------------------------------------
bool is_same_het_config(const HetConfig &C1, const HetConfig &C2)
{
  const auto N = C1.size();
  if (N != C2.size()) return false;
  for (size_t i = 0; i < N; ++i) {
    if (C1.positions[i]->id != C2.positions[i]->id) return false;
    if (C1.kappa[i] != C2.kappa[i]) return false;
  }
  return true;
}

uint HetConfigHasher::operator()(const HetConfig &C) const
{
  uint hash = C.size();
  for (size_t i = 0; i < C.size(); ++i) {
    hash ^= C.positions[i]->id + 0x9e3779b9 + (hash << 6) + (hash >> 2);
    hash ^= C.kappa[i] + 0x9e3779b9 + (hash << 6) + (hash >> 2);
  }
  return hash;
}

// ---------------------------------------------------------------------------
// Original lacam3 utilities
// ---------------------------------------------------------------------------
bool is_same_config(const Config &C1, const Config &C2)
{
  const auto N = C1.size();
  for (size_t i = 0; i < N; ++i) {
    if (C1[i]->id != C2[i]->id) return false;
  }
  return true;
}

uint ConfigHasher::operator()(const Config &C) const
{
  uint hash = C.size();
  for (auto &v : C) {
    hash ^= v->id + 0x9e3779b9 + (hash << 6) + (hash >> 2);
  }
  return hash;
}

std::ostream &operator<<(std::ostream &os, const Vertex *v)
{
  os << v->index;
  return os;
}

std::ostream &operator<<(std::ostream &os, const Config &Q)
{
  for (auto v : Q) os << v << ",";
  return os;
}

std::ostream &operator<<(std::ostream &os, const HetConfig &Q)
{
  for (size_t i = 0; i < Q.size(); ++i) {
    os << "(" << Q.positions[i] << ",k=" << Q.kappa[i] << ")";
    if (i + 1 < Q.size()) os << ",";
  }
  return os;
}
