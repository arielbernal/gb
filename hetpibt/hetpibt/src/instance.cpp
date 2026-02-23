#include "../include/instance.hpp"

HetInstance::~HetInstance()
{
  for (auto* a : agents) delete a;
  agents.clear();
  for (auto* f : fleets) delete f;
  fleets.clear();
}

Fleet* HetInstance::get_fleet(int agent_id) const
{
  return fleets[agents[agent_id]->fleet_id];
}

// het_bench format:
// agent_id fleet_id footprint velocity sx sy gx gy grid_w grid_h
HetInstance::HetInstance(const std::string& scen_filename,
                         const std::string& map_filename)
    : base_grid(map_filename), N(0)
{
  std::ifstream file(scen_filename);
  if (!file) {
    info(0, 0, scen_filename, " is not found");
    return;
  }

  // first pass: discover fleets and agents
  struct RawAgent {
    int agent_id;
    int fleet_id;
    int cell_size;
    float velocity;
    int sx, sy, gx, gy;
    int grid_w, grid_h;
  };
  std::vector<RawAgent> raw_agents;
  std::unordered_map<int, std::pair<int, float>> fleet_defs;  // id->(cs, vel)

  std::string line;
  while (getline(file, line)) {
    if (!line.empty() && *(line.end() - 1) == 0x0d) line.pop_back();
    if (line.empty()) continue;

    std::istringstream iss(line);
    RawAgent ra;
    iss >> ra.agent_id >> ra.fleet_id >> ra.cell_size >> ra.velocity >> ra.sx
        >> ra.sy >> ra.gx >> ra.gy >> ra.grid_w >> ra.grid_h;
    if (iss.fail()) continue;

    raw_agents.push_back(ra);
    if (fleet_defs.find(ra.fleet_id) == fleet_defs.end()) {
      fleet_defs[ra.fleet_id] = {ra.cell_size, ra.velocity};
    }
  }
  file.close();

  // create fleets sorted by ID
  int max_fleet_id = 0;
  for (auto& [fid, def] : fleet_defs) {
    max_fleet_id = std::max(max_fleet_id, fid);
  }
  fleets.resize(max_fleet_id + 1, nullptr);
  for (auto& [fid, def] : fleet_defs) {
    fleets[fid] = new Fleet(fid, def.first, def.second);
    fleets[fid]->G.build_from_base(base_grid, def.first);
  }

  // initialize collision checker
  cc = CollisionChecker(fleets, base_grid.width, base_grid.height);

  // create agents with start/goal positions
  // het_bench coordinates are absolute free-space; convert to fleet grid
  N = raw_agents.size();
  agents.reserve(N);
  starts.reserve(N);
  goals.reserve(N);

  for (size_t i = 0; i < raw_agents.size(); ++i) {
    auto& ra = raw_agents[i];
    auto* agent = new Agent(static_cast<int>(i), ra.fleet_id);
    agents.push_back(agent);

    auto* fleet = fleets[ra.fleet_id];
    int cs = fleet->cell_size;
    int fw = fleet->G.width;

    // convert absolute free-space coordinates to fleet grid cell
    // het_bench stores cell centers; divide by cell_size to get grid coords
    int fx_s = ra.sx / cs;
    int fy_s = ra.sy / cs;
    int fx_g = ra.gx / cs;
    int fy_g = ra.gy / cs;

    // clamp to fleet grid bounds
    fx_s = std::min(fx_s, fw - 1);
    fy_s = std::min(fy_s, fleet->G.height - 1);
    fx_g = std::min(fx_g, fw - 1);
    fy_g = std::min(fy_g, fleet->G.height - 1);

    auto* sv = fleet->G.U[fw * fy_s + fx_s];
    auto* gv = fleet->G.U[fw * fy_g + fx_g];
    starts.push_back(sv);
    goals.push_back(gv);
  }
}

HetInstance::HetInstance(const std::string& map_filename,
                         const std::vector<int>& fleet_ids,
                         const std::vector<int>& cell_sizes,
                         const std::vector<float>& velocities,
                         const std::vector<int>& start_indexes,
                         const std::vector<int>& goal_indexes)
    : base_grid(map_filename), N(start_indexes.size())
{
  // discover unique fleets
  std::unordered_map<int, int> fleet_idx;  // fleet_id -> index in params
  for (size_t i = 0; i < fleet_ids.size(); ++i) {
    if (fleet_idx.find(fleet_ids[i]) == fleet_idx.end()) {
      fleet_idx[fleet_ids[i]] = static_cast<int>(i);
    }
  }

  int max_fid = 0;
  for (auto& [fid, idx] : fleet_idx) max_fid = std::max(max_fid, fid);
  fleets.resize(max_fid + 1, nullptr);
  for (auto& [fid, idx] : fleet_idx) {
    fleets[fid] = new Fleet(fid, cell_sizes[idx], velocities[idx]);
    fleets[fid]->G.build_from_base(base_grid, cell_sizes[idx]);
  }

  cc = CollisionChecker(fleets, base_grid.width, base_grid.height);

  agents.reserve(N);
  starts.reserve(N);
  goals.reserve(N);
  for (uint i = 0; i < N; ++i) {
    auto* agent = new Agent(static_cast<int>(i), fleet_ids[i]);
    agents.push_back(agent);
    auto* fleet = fleets[fleet_ids[i]];
    starts.push_back(fleet->G.U[start_indexes[i]]);
    goals.push_back(fleet->G.U[goal_indexes[i]]);
  }
}

bool HetInstance::is_valid(const int verbose) const
{
  if (N != starts.size() || N != goals.size() || N != agents.size()) {
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
  return true;
}

bool HetInstance::validate_scenario(const int verbose) const
{
  bool ok = true;
  int bw = base_grid.width;

  // helper: get base-grid cells for agent i's fleet cell
  auto base_cells_for = [&](uint i, Vertex* v) -> std::vector<int> {
    auto* fleet = get_fleet(i);
    return cc.to_base_cells(fleet->id, v->index, fleet->G.width);
  };

  // 1. check start footprint overlaps on base grid
  std::unordered_map<int, int> start_owner;  // base cell -> agent_id
  for (uint i = 0; i < N; ++i) {
    auto cells = base_cells_for(i, starts[i]);
    for (int bc : cells) {
      auto it = start_owner.find(bc);
      if (it != start_owner.end()) {
        int bx = bc % bw, by = bc / bw;
        info(0, verbose, "VALIDATE: start overlap at base (", bx, ",", by,
             ") between agent ", i, " and agent ", it->second);
        ok = false;
      } else {
        start_owner[bc] = static_cast<int>(i);
      }
    }
  }

  // 2. check goal footprint overlaps on base grid
  std::unordered_map<int, int> goal_owner;  // base cell -> agent_id
  for (uint i = 0; i < N; ++i) {
    auto cells = base_cells_for(i, goals[i]);
    for (int bc : cells) {
      auto it = goal_owner.find(bc);
      if (it != goal_owner.end()) {
        int bx = bc % bw, by = bc / bw;
        info(0, verbose, "VALIDATE: goal overlap at base (", bx, ",", by,
             ") between agent ", i, " and agent ", it->second);
        ok = false;
      } else {
        goal_owner[bc] = static_cast<int>(i);
      }
    }
  }

  // 3. check start/goal cross-overlap on base grid
  for (auto& [bc, sid] : start_owner) {
    auto it = goal_owner.find(bc);
    if (it != goal_owner.end()) {
      int bx = bc % bw, by = bc / bw;
      info(0, verbose, "VALIDATE: start/goal overlap at base (", bx, ",", by,
           ") — agent ", sid, " start vs agent ", it->second, " goal");
      ok = false;
    }
  }

  // 4. BFS reachability: every agent must reach its goal on its fleet graph
  for (uint i = 0; i < N; ++i) {
    auto* start_v = starts[i];
    auto* goal_v = goals[i];
    if (start_v == goal_v) continue;

    // BFS on fleet graph from start to goal
    std::unordered_set<int> visited;
    std::queue<Vertex*> q;
    visited.insert(start_v->id);
    q.push(start_v);
    bool found = false;
    while (!q.empty()) {
      auto* v = q.front();
      q.pop();
      for (auto* u : v->neighbor) {
        if (u == goal_v) {
          found = true;
          break;
        }
        if (visited.insert(u->id).second) {
          q.push(u);
        }
      }
      if (found) break;
    }
    if (!found) {
      auto* fleet = get_fleet(i);
      int fw = fleet->G.width;
      info(0, verbose, "VALIDATE: agent ", i, " (fleet ", fleet->id,
           " cs=", fleet->cell_size, ") cannot reach goal (",
           goal_v->index % fw, ",", goal_v->index / fw, ") from start (",
           start_v->index % fw, ",", start_v->index / fw, ")");
      ok = false;
    }
  }

  if (ok) {
    info(0, verbose, "scenario validation passed");
  }
  return ok;
}
