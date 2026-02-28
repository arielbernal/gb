#include <argparse/argparse.hpp>
#include <iostream>
#include <memory>
#include <lacam.hpp>

int main(int argc, char *argv[])
{
  argparse::ArgumentParser program("het_rt_lacam", "0.1.0");
  program.add_argument("-m", "--map").help("map file").required();
  program.add_argument("-i", "--scen")
      .help("scenario file (het_bench or MAPF benchmark)")
      .default_value(std::string(""));
  program.add_argument("-N", "--num")
      .help("number of agents (for MAPF benchmark mode)")
      .default_value(std::string("0"));
  program.add_argument("-s", "--seed")
      .help("seed")
      .default_value(std::string("0"));
  program.add_argument("-v", "--verbose")
      .help("verbose")
      .default_value(std::string("0"));
  program.add_argument("-t", "--time_limit_sec")
      .help("time limit sec")
      .default_value(std::string("10"));
  program.add_argument("-o", "--output")
      .help("output file")
      .default_value(std::string("./build/result.txt"));
  program.add_argument("-l", "--log_short")
      .default_value(false)
      .implicit_value(true);
  program.add_argument("--swap-xy")
      .help("swap x/y in het_bench scenario coordinates")
      .default_value(false)
      .implicit_value(true);

  // solver parameters
  program.add_argument("--goal-lock")
      .help("permanently lock agents at their goals")
      .default_value(false)
      .implicit_value(true);
  program.add_argument("--no-star")
      .help("turn off anytime improvement")
      .default_value(false)
      .implicit_value(true);
  program.add_argument("--pibt-num")
      .help("Monte-Carlo PIBT instances")
      .default_value(std::string("1"));
  program.add_argument("--multi-thread")
      .help("enable multi-threaded PIBT")
      .default_value(false)
      .implicit_value(true);
  program.add_argument("--random-insert-prob1")
      .help("probability of inserting the start node")
      .default_value(std::string("0"));
  program.add_argument("--random-insert-prob2")
      .help("probability of inserting a random node")
      .default_value(std::string("0"));
  program.add_argument("--checkpoints-duration")
      .help("for recording (seconds)")
      .default_value(std::string("5"));
  program.add_argument("--rt")
      .help("enable real-time incremental execution (RT-LaCAM)")
      .default_value(false)
      .implicit_value(true);
  program.add_argument("--rt-budget")
      .help("node expansion budget per RT step")
      .default_value(std::string("100"));
  try {
    program.parse_known_args(argc, argv);
  } catch (const std::runtime_error &err) {
    std::cerr << err.what() << std::endl;
    std::cerr << program;
    std::exit(1);
  }

  const auto verbose = std::stoi(program.get<std::string>("verbose"));
  const auto time_limit_sec =
      std::stoi(program.get<std::string>("time_limit_sec"));
  const auto scen_name = program.get<std::string>("scen");
  const auto seed = std::stoi(program.get<std::string>("seed"));
  const auto map_name = program.get<std::string>("map");
  const auto output_name = program.get<std::string>("output");
  const auto log_short = program.get<bool>("log_short");
  const auto N = std::stoi(program.get<std::string>("num"));
  const auto swap_xy = program.get<bool>("swap-xy");

  // Create instance: het_bench mode (N=0) vs MAPF benchmark mode (N>0)
  // Can't use ternary because Instance contains non-copyable Graph members.
  // Use a unique_ptr for deferred construction.
  std::unique_ptr<Instance> ins_ptr;
  if (N > 0) {
    ins_ptr = std::make_unique<Instance>(scen_name, map_name, N);
  } else {
    ins_ptr = std::make_unique<Instance>(scen_name, map_name, swap_xy);
  }
  auto &ins = *ins_ptr;
  ins.skip_invalid_agents(verbose);
  if (!ins.is_valid(verbose)) return 1;

  info(1, verbose, "agents: ", ins.N, ", fleets: ", ins.num_fleets,
       ", base grid: ", ins.base_width, "x", ins.base_height);
  for (int f = 0; f < ins.num_fleets; ++f) {
    info(1, verbose, "  fleet ", f, ": cs=", ins.fleet_cell_sizes[f],
         " grid=", ins.fleet_graphs[f].width, "x", ins.fleet_graphs[f].height,
         " vertices=", ins.fleet_graphs[f].size());
  }

  // solver parameters
  Planner::FLG_GOAL_LOCK = program.get<bool>("goal-lock");
  Planner::FLG_STAR = !program.get<bool>("no-star");
  Planner::PIBT_NUM = std::stoi(program.get<std::string>("pibt-num"));
  Planner::FLG_MULTI_THREAD = program.get<bool>("multi-thread");
  Planner::RANDOM_INSERT_PROB1 =
      std::stof(program.get<std::string>("random-insert-prob1"));
  Planner::RANDOM_INSERT_PROB2 =
      std::stof(program.get<std::string>("random-insert-prob2"));
  Planner::CHECKPOINTS_DURATION =
      std::stof(program.get<std::string>("checkpoints-duration")) * 1000;

  const auto rt_mode = program.get<bool>("rt");
  const auto rt_budget = std::stoi(program.get<std::string>("rt-budget"));

  const auto deadline = Deadline(time_limit_sec * 1000);

  if (rt_mode) {
    // RT-LaCAM: incremental execution — search for rt_budget nodes, execute
    // one step, repeat. OPEN and EXPLORED persist across steps.
    info(1, verbose, "RT-LaCAM mode, budget=", rt_budget, " per step");
    auto planner = Planner(&ins, verbose - 1, &deadline, seed);

    std::vector<HetConfig> executed;
    executed.push_back(ins.make_start_config());

    bool goal_reached = false;
    const int max_steps = 100000;  // guard against infinite loops

    while (!is_expired(&deadline) && (int)executed.size() <= max_steps) {
      auto next = planner.solve_one_step(rt_budget);
      executed.push_back(next);
      if (ins.is_goal(next)) {
        goal_reached = true;
        break;
      }
    }

    const auto comp_time_ms = deadline.elapsed_ms();
    const int steps_executed = (int)executed.size() - 1;

    if (goal_reached) {
      info(1, verbose, &deadline, "RT: goal reached in ", steps_executed,
           " steps");
    } else {
      info(1, verbose, &deadline, "RT: timeout after ", steps_executed,
           " steps");
    }

    // Convert executed HetConfig path to Solution (vector<Config>)
    Solution solution;
    for (auto &hc : executed) solution.push_back(hc.positions);

    // Validate only if complete
    if (goal_reached && !is_feasible_solution(ins, solution, verbose)) {
      info(0, verbose, &deadline, "RT: invalid solution");
      return 1;
    }

    print_stats(verbose, &deadline, ins, solution, comp_time_ms);
    make_log(ins, solution, output_name, comp_time_ms, map_name, seed,
             log_short);
  } else {
    // Standard (full-horizon) solve
    const auto solution = solve(ins, verbose - 1, &deadline, seed);
    const auto comp_time_ms = deadline.elapsed_ms();

    if (solution.empty()) info(1, verbose, &deadline, "failed to solve");

    // check feasibility
    if (!is_feasible_solution(ins, solution, verbose)) {
      info(0, verbose, &deadline, "invalid solution");
      return 1;
    }

    // post processing
    print_stats(verbose, &deadline, ins, solution, comp_time_ms);
    make_log(ins, solution, output_name, comp_time_ms, map_name, seed,
             log_short);
  }
  return 0;
}
