#include "../include/post_processing.hpp"

#include "../include/planner.hpp"

bool is_feasible_solution(const Instance &ins, const Solution &solution,
                          const int verbose)
{
  if (solution.empty()) return true;

  // check start locations
  if (!is_same_config(solution.front(), ins.starts)) {
    info(1, verbose, "invalid starts");
    return false;
  }

  // check goal locations
  if (!is_same_config(solution.back(), ins.goals)) {
    info(1, verbose, "invalid goals");
    return false;
  }

  const int bw = ins.base_width;

  for (size_t t = 1; t < solution.size(); ++t) {
    for (size_t i = 0; i < ins.N; ++i) {
      auto v_i_from = solution[t - 1][i];
      auto v_i_to = solution[t][i];

      // check connectivity on fleet graph
      if (v_i_from != v_i_to &&
          std::find(v_i_to->neighbor.begin(), v_i_to->neighbor.end(),
                    v_i_from) == v_i_to->neighbor.end()) {
        info(1, verbose, "invalid move for agent ", i, " at timestep ", t);
        return false;
      }

      // footprint-based conflict check
      int fid_i = ins.agents[i].fleet_id;
      int cs_i = ins.fleet_cell_sizes[fid_i];
      auto &fg_i = ins.fleet_graphs[fid_i];
      auto cells_i = to_base_cells(v_i_to->index, fg_i.width, cs_i, bw);
      std::unordered_set<int> cells_i_set(cells_i.begin(), cells_i.end());

      for (size_t j = i + 1; j < ins.N; ++j) {
        auto v_j_from = solution[t - 1][j];
        auto v_j_to = solution[t][j];

        int fid_j = ins.agents[j].fleet_id;
        int cs_j = ins.fleet_cell_sizes[fid_j];
        auto &fg_j = ins.fleet_graphs[fid_j];

        // vertex conflict: footprint overlap at time t
        auto cells_j = to_base_cells(v_j_to->index, fg_j.width, cs_j, bw);
        for (int bc : cells_j) {
          if (cells_i_set.count(bc)) {
            info(1, verbose, "footprint conflict between agent-", i,
                 " and agent-", j, " at base cell ", bc, " at timestep ", t);
            return false;
          }
        }

        // swap conflict: agent i's next footprint overlaps agent j's current,
        // AND agent j's next footprint overlaps agent i's current
        auto cells_j_from =
            to_base_cells(v_j_from->index, fg_j.width, cs_j, bw);
        auto cells_i_from =
            to_base_cells(v_i_from->index, fg_i.width, cs_i, bw);
        std::unordered_set<int> cells_i_from_set(cells_i_from.begin(),
                                                  cells_i_from.end());
        bool i_to_overlaps_j_from = false;
        for (int bc : cells_j_from) {
          if (cells_i_set.count(bc)) {
            i_to_overlaps_j_from = true;
            break;
          }
        }
        if (i_to_overlaps_j_from) {
          // Check reverse: j's next overlaps i's current
          bool j_to_overlaps_i_from = false;
          for (int bc : cells_j) {
            if (cells_i_from_set.count(bc)) {
              j_to_overlaps_i_from = true;
              break;
            }
          }
          if (j_to_overlaps_i_from) {
            info(1, verbose, "swap conflict between agent-", i,
                 " and agent-", j, " at timestep ", t);
            return false;
          }
        }
      }
    }
  }

  return true;
}

void print_stats(const int verbose, const Deadline *deadline,
                 const Instance &ins, const Solution &solution,
                 const double comp_time_ms)
{
  auto ceil_fn = [](float x) { return std::ceil(x * 100) / 100; };
  auto D = DistTable(&ins);
  const auto makespan = get_makespan(solution);
  const auto makespan_lb = get_makespan_lower_bound(ins, D);
  const auto sum_of_costs = get_sum_of_costs(solution);
  const auto sum_of_costs_lb = get_sum_of_costs_lower_bound(ins, D);
  const auto sum_of_loss = get_sum_of_loss(solution);
  info(1, verbose, deadline, "solved", "\tmakespan: ", makespan,
       " (lb=", makespan_lb,
       ", ub=", ceil_fn((float)makespan / std::max(1, makespan_lb)), ")",
       "\tsum_of_costs: ", sum_of_costs, " (lb=", sum_of_costs_lb,
       ", ub=",
       ceil_fn((float)sum_of_costs / std::max(1, sum_of_costs_lb)), ")",
       "\tsum_of_loss: ", sum_of_loss);
}

static const std::regex r_map_name = std::regex(R"(.+/(.+))");

void make_log(const Instance &ins, const Solution &solution,
              const std::string &output_name, const double comp_time_ms,
              const std::string &map_name, const int seed, const bool log_short)
{
  std::smatch results;
  const auto map_recorded_name =
      (std::regex_match(map_name, results, r_map_name)) ? results[1].str()
                                                        : map_name;

  auto D = DistTable(&ins);
  std::ofstream log;
  log.open(output_name, std::ios::out);
  log << "agents=" << ins.N << "\n";
  log << "map_file=" << map_recorded_name << "\n";
  log << "solver=het_rt_lacam\n";
  log << "solved=" << !solution.empty() << "\n";
  log << "soc=" << get_sum_of_costs(solution) << "\n";
  log << "soc_lb=" << get_sum_of_costs_lower_bound(ins, D) << "\n";
  log << "makespan=" << get_makespan(solution) << "\n";
  log << "makespan_lb=" << get_makespan_lower_bound(ins, D) << "\n";
  log << "sum_of_loss=" << get_sum_of_loss(solution) << "\n";
  log << "comp_time=" << comp_time_ms << "\n";
  log << "seed=" << seed << "\n";
  log << Planner::MSG << "\n";
  if (log_short) return;

  // Fleet definitions: fid:cs:speed_period:grid_w:grid_h;...
  log << "fleets=";
  for (int f = 0; f < ins.num_fleets; ++f) {
    if (f > 0) log << ";";
    int cs = ins.fleet_cell_sizes[f];
    int sp = ins.fleet_speed_periods[f];
    int fw = ins.fleet_graphs[f].width;
    int fh = ins.fleet_graphs[f].height;
    log << f << ":" << cs << ":" << sp << ":" << fw << ":" << fh;
  }
  log << "\n";

  // Per-agent fleet assignment
  log << "agent_fleet=";
  for (size_t i = 0; i < ins.N; ++i) {
    if (i > 0) log << ",";
    log << ins.agents[i].fleet_id;
  }
  log << "\n";

  // Starts/goals: use fleet-graph coords (v->x, v->y)
  log << "starts=";
  for (size_t i = 0; i < ins.N; ++i) {
    log << "(" << ins.starts[i]->x << "," << ins.starts[i]->y << "),";
  }
  log << "\ngoals=";
  for (size_t i = 0; i < ins.N; ++i) {
    log << "(" << ins.goals[i]->x << "," << ins.goals[i]->y << "),";
  }
  log << "\nsolution=\n";
  for (size_t t = 0; t < solution.size(); ++t) {
    log << t << ":";
    auto C = solution[t];
    for (auto v : C) {
      log << "(" << v->x << "," << v->y << "),";
    }
    log << "\n";
  }
  log.close();
}
