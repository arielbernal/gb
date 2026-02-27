#include "../include/instance.hpp"

Instance::~Instance() {}

// ---------------------------------------------------------------------------
// het_bench scenario loader
// Supports two formats:
//   Simple:    cs sx sy gx gy                (benchmark .scen)
//   Full:      agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h
// Auto-detects by counting fields on the first data line.
// ---------------------------------------------------------------------------
Instance::Instance(const std::string &scen_filename,
                   const std::string &map_filename, bool swap_xy)
    : base_graph(map_filename), N(0), num_fleets(0)
{
  base_width = base_graph.width;
  base_height = base_graph.height;

  struct RawAgent {
    int cell_size;
    int velocity;  // speed period: agent moves every 'velocity' steps
    int sx, sy, gx, gy;
  };
  std::vector<RawAgent> raw;
  std::map<int, int> fleet_cs;  // cell_size -> fleet_id (auto-assigned)
  std::map<int, int> fleet_vel; // cell_size -> velocity (speed period)

  std::ifstream file(scen_filename);
  if (!file) {
    info(0, 0, scen_filename, " is not found");
    return;
  }

  // Detect format by counting fields on first data line
  bool full_format = false;
  std::string line;
  std::streampos start_pos = file.tellg();
  while (std::getline(file, line)) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    if (line.empty() || line[0] == '#') continue;
    std::istringstream iss(line);
    int count = 0;
    std::string token;
    while (iss >> token) ++count;
    full_format = (count >= 10);
    break;
  }
  file.clear();
  file.seekg(start_pos);

  while (std::getline(file, line)) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    if (line.empty() || line[0] == '#') continue;
    std::istringstream iss(line);
    RawAgent ra;
    if (full_format) {
      int agent_id, fleet_id;
      float velocity_f;
      int grid_w, grid_h;
      iss >> agent_id >> fleet_id >> ra.cell_size >> velocity_f
          >> ra.sx >> ra.sy >> ra.gx >> ra.gy >> grid_w >> grid_h;
      ra.velocity = std::max(1, (int)std::round(velocity_f));
    } else {
      // Simple format: cs sx sy gx gy — default velocity = cell_size
      iss >> ra.cell_size >> ra.sx >> ra.sy >> ra.gx >> ra.gy;
      ra.velocity = ra.cell_size;
    }
    if (iss.fail()) continue;
    raw.push_back(ra);
    fleet_cs[ra.cell_size] = 0;  // placeholder, assign fleet_id below
    fleet_vel[ra.cell_size] = ra.velocity;
  }

  // Assign fleet IDs by cell_size (sorted)
  int fid = 0;
  for (auto &[cs, id] : fleet_cs) {
    id = fid++;
  }
  num_fleets = fid;

  // Build fleet graphs
  fleet_graphs.resize(num_fleets);
  fleet_cell_sizes.resize(num_fleets, 1);
  fleet_speed_periods.resize(num_fleets, 1);
  for (auto &[cs, id] : fleet_cs) {
    fleet_cell_sizes[id] = cs;
    fleet_speed_periods[id] = fleet_vel[cs];
    fleet_graphs[id].build_from_base(base_graph, cs);
  }

  // Create agents
  N = (uint)raw.size();
  agents.resize(N);
  starts.resize(N, nullptr);
  goals.resize(N, nullptr);

  for (size_t i = 0; i < raw.size(); ++i) {
    auto &ra = raw[i];
    int fid = fleet_cs[ra.cell_size];
    agents[i] = {fid, ra.cell_size};
    auto &fg = fleet_graphs[fid];
    int cs = ra.cell_size;
    int fw = fg.width;

    int fx_s, fy_s, fx_g, fy_g;
    if (swap_xy) {
      fx_s = ra.sy / cs;  fy_s = ra.sx / cs;
      fx_g = ra.gy / cs;  fy_g = ra.gx / cs;
    } else {
      fx_s = ra.sx / cs;  fy_s = ra.sy / cs;
      fx_g = ra.gx / cs;  fy_g = ra.gy / cs;
    }

    if (fx_s >= 0 && fx_s < fw && fy_s >= 0 && fy_s < fg.height)
      starts[i] = fg.U[fw * fy_s + fx_s];
    if (fx_g >= 0 && fx_g < fw && fy_g >= 0 && fy_g < fg.height)
      goals[i] = fg.U[fw * fy_g + fx_g];
  }
}

// ---------------------------------------------------------------------------
// Homogeneous MAPF benchmark (all cell_size=1, single fleet 0)
// ---------------------------------------------------------------------------
static const std::regex r_instance =
    std::regex(R"(\d+\t.+\.map\t\d+\t\d+\t(\d+)\t(\d+)\t(\d+)\t(\d+)\t.+)");

Instance::Instance(const std::string &scen_filename,
                   const std::string &map_filename, const int _N)
    : base_graph(map_filename), N(_N), num_fleets(1)
{
  base_width = base_graph.width;
  base_height = base_graph.height;

  // Single fleet with cell_size=1 (same as base graph)
  fleet_graphs.resize(1);
  fleet_cell_sizes = {1};
  fleet_speed_periods = {1};
  fleet_graphs[0].build_from_base(base_graph, 1);

  std::ifstream file(scen_filename);
  if (!file) {
    info(0, 0, scen_filename, " is not found");
    return;
  }
  std::string line;
  std::smatch results;
  while (getline(file, line)) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    if (std::regex_match(line, results, r_instance)) {
      auto x_s = std::stoi(results[1].str());
      auto y_s = std::stoi(results[2].str());
      auto x_g = std::stoi(results[3].str());
      auto y_g = std::stoi(results[4].str());
      auto &G = fleet_graphs[0];
      if (x_s < 0 || G.width <= x_s || x_g < 0 || G.width <= x_g) continue;
      if (y_s < 0 || G.height <= y_s || y_g < 0 || G.height <= y_g) continue;
      auto s = G.U[G.width * y_s + x_s];
      auto g = G.U[G.width * y_g + x_g];
      if (s == nullptr || g == nullptr) continue;
      starts.push_back(s);
      goals.push_back(g);
      agents.push_back({0, 1});
    }
    if (starts.size() == N) break;
  }
  N = (uint)starts.size();
}

const Graph *Instance::fleet_graph(int agent_id) const
{
  return &fleet_graphs[agents[agent_id].fleet_id];
}

int Instance::speed_period(int agent_id) const
{
  return fleet_speed_periods[agents[agent_id].fleet_id];
}

bool Instance::is_valid(const int verbose) const
{
  if (N != starts.size() || N != goals.size()) {
    info(1, verbose, "invalid N, check instance");
    return false;
  }
  for (uint i = 0; i < N; ++i) {
    if (starts[i] == nullptr) {
      info(1, verbose, "agent ", i, " has null start");
      return false;
    }
    if (goals[i] == nullptr) {
      info(1, verbose, "agent ", i, " has null goal");
      return false;
    }
  }

  // Check start config for footprint overlaps on base grid
  int bsize = base_width * base_height;
  std::vector<int> grid(bsize, -1);
  for (uint i = 0; i < N; ++i) {
    int fid = agents[i].fleet_id;
    int cs = fleet_cell_sizes[fid];
    auto &fg = fleet_graphs[fid];
    auto cells = to_base_cells(starts[i]->index, fg.width, cs, base_width);
    for (int bc : cells) {
      if (grid[bc] != -1) {
        info(1, verbose, "start footprint overlap: agent ", i,
             " (cs=", cs, ") and agent ", grid[bc],
             " (cs=", agents[grid[bc]].cell_size, ") at base cell ", bc);
        return false;
      }
      grid[bc] = i;
    }
  }

  // Check goal config for footprint overlaps
  std::fill(grid.begin(), grid.end(), -1);
  for (uint i = 0; i < N; ++i) {
    int fid = agents[i].fleet_id;
    int cs = fleet_cell_sizes[fid];
    auto &fg = fleet_graphs[fid];
    auto cells = to_base_cells(goals[i]->index, fg.width, cs, base_width);
    for (int bc : cells) {
      if (grid[bc] != -1) {
        info(1, verbose, "goal footprint overlap: agent ", i,
             " (cs=", cs, ") and agent ", grid[bc],
             " (cs=", agents[grid[bc]].cell_size, ") at base cell ", bc);
        return false;
      }
      grid[bc] = i;
    }
  }

  return true;
}

HetConfig Instance::make_start_config() const
{
  HetConfig C;
  C.positions = starts;
  C.kappa.assign(N, 0);
  return C;
}

bool Instance::is_goal(const HetConfig &C) const
{
  for (uint i = 0; i < N; ++i) {
    if (C.positions[i]->id != goals[i]->id) return false;
    if (C.kappa[i] != 0) return false;  // must be at phase 0 to be "arrived"
  }
  return true;
}
