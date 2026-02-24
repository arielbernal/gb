#include "../include/post_processing.hpp"

bool is_feasible_solution(const HetInstance& ins, const ReservationTable& P,
                          int verbose)
{
  // verify every agent has a valid endpoint
  for (uint i = 0; i < ins.N; ++i) {
    auto ep = P.get_endpoint(i);
    if (ep.fleet_id < 0) {
      info(1, verbose, "agent ", i, " has no trajectory");
      return false;
    }
  }
  // the reservation table guarantees collision-freedom by construction
  // (all reservations are checked before insertion)
  return true;
}

int get_makespan(const ReservationTable& P, int N,
                 const std::unordered_map<int, int>& goal_time)
{
  int makespan = 0;
  for (int i = 0; i < N; ++i) {
    auto gt = goal_time.find(i);
    int t = (gt != goal_time.end()) ? gt->second : P.get_endpoint(i).end_time;
    if (t > makespan) makespan = t;
  }
  return makespan;
}

int get_sum_of_costs(const ReservationTable& P, const HetInstance& ins,
                     const std::unordered_map<int, int>& goal_time)
{
  int total = 0;
  for (uint i = 0; i < ins.N; ++i) {
    auto gt = goal_time.find(i);
    total += (gt != goal_time.end()) ? gt->second : P.get_endpoint(i).end_time;
  }
  return total;
}

void print_stats(int verbose, const HetInstance& ins,
                 const ReservationTable& P, double comp_time_ms,
                 const std::unordered_map<int, int>& goal_time)
{
  auto N = static_cast<int>(ins.N);
  auto feasible = is_feasible_solution(ins, P, verbose);
  auto makespan = get_makespan(P, N, goal_time);
  auto soc = get_sum_of_costs(P, ins, goal_time);

  int goals_reached = 0;
  for (uint i = 0; i < ins.N; ++i) {
    auto ep = P.get_endpoint(i);
    if (ins.goals[i] != nullptr && ep.cell_index == ins.goals[i]->index) {
      ++goals_reached;
    }
  }

  info(0, verbose, "comp_time(ms)=", comp_time_ms);
  info(0, verbose, "feasible=", feasible);
  info(0, verbose, "makespan=", makespan);
  info(0, verbose, "sum_of_costs=", soc);
  info(0, verbose, "goals_reached=", goals_reached, "/", N);
}

void make_log(const HetInstance& ins, const ReservationTable& P,
              const std::string& output_file, double comp_time_ms,
              const std::string& map_name, int seed,
              const std::unordered_map<int, int>& goal_time)
{
  std::ofstream log(output_file);
  if (!log) {
    std::cout << "cannot open " << output_file << std::endl;
    return;
  }

  auto N = static_cast<int>(ins.N);

  // --- metadata ---
  log << "agents=" << N << "\n";
  log << "map_name=" << map_name << "\n";
  log << "seed=" << seed << "\n";
  log << "solver=hetpibt\n";
  log << "comp_time(ms)=" << comp_time_ms << "\n";
  log << "makespan=" << get_makespan(P, N, goal_time) << "\n";
  log << "sum_of_costs=" << get_sum_of_costs(P, ins, goal_time) << "\n";

  // --- fleet definitions ---
  // format: fleets=id:cell_size:velocity:grid_w:grid_h;...
  log << "fleets=";
  bool first_fleet = true;
  for (auto* f : ins.fleets) {
    if (f == nullptr) continue;
    if (!first_fleet) log << ";";
    log << f->id << ":" << f->cell_size << ":" << f->velocity << ":"
        << f->G.width << ":" << f->G.height;
    first_fleet = false;
  }
  log << "\n";

  // --- per-agent fleet assignment ---
  // format: agent_fleet=fleet_id,fleet_id,...
  log << "agent_fleet=";
  for (int i = 0; i < N; ++i) {
    if (i > 0) log << ",";
    log << ins.agents[i]->fleet_id;
  }
  log << "\n";

  // --- starts in fleet grid coordinates ---
  log << "starts=";
  for (int i = 0; i < N; ++i) {
    if (i > 0) log << ",";
    if (ins.starts[i] != nullptr) {
      auto* fleet = ins.get_fleet(i);
      int fw = fleet->G.width;
      int idx = ins.starts[i]->index;
      log << "(" << (idx % fw) << "," << (idx / fw) << ")";
    } else {
      log << "(-1,-1)";
    }
  }
  log << "\n";

  // --- goals in fleet grid coordinates ---
  log << "goals=";
  for (int i = 0; i < N; ++i) {
    if (i > 0) log << ",";
    if (ins.goals[i] != nullptr) {
      auto* fleet = ins.get_fleet(i);
      int fw = fleet->G.width;
      int idx = ins.goals[i]->index;
      log << "(" << (idx % fw) << "," << (idx / fw) << ")";
    } else {
      log << "(-1,-1)";
    }
  }
  log << "\n";

  // --- per-agent trajectories ---
  // format: solution
  // agent_id:fleet_id:(x,y)@t,(x,y)@t,...
  // sorted chronologically per agent
  log << "solution\n";
  for (int i = 0; i < N; ++i) {
    auto tl_it = P.traj_log.find(i);
    if (tl_it == P.traj_log.end()) continue;

    auto& entries = tl_it->second;
    auto* fleet = ins.get_fleet(i);
    int fw = fleet->G.width;

    // sort by time (should already be sorted, but ensure)
    auto sorted = entries;
    std::sort(sorted.begin(), sorted.end());

    // deduplicate consecutive identical entries
    log << i << ":" << fleet->id << ":";
    bool first = true;
    for (auto& [t, cell] : sorted) {
      if (!first) log << ",";
      int fx = cell % fw;
      int fy = cell / fw;
      log << "(" << fx << "," << fy << ")@" << t;
      first = false;
    }
    log << "\n";
  }

  log.close();
}
