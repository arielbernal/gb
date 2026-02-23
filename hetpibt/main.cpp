#include <argparse/argparse.hpp>
#include <hetpibt.hpp>

int main(int argc, char* argv[])
{
  argparse::ArgumentParser program("hetpibt", "0.1.0");

  program.add_argument("-m", "--map")
      .help("map filename")
      .required();
  program.add_argument("-s", "--scen")
      .help("het_bench scenario filename")
      .required();
  program.add_argument("-o", "--output")
      .help("output filename")
      .default_value(std::string("result.txt"));
  program.add_argument("-v", "--verbose")
      .help("verbosity level (0-2)")
      .default_value(0)
      .scan<'i', int>();
  program.add_argument("-t", "--time_limit")
      .help("time limit in milliseconds")
      .default_value(60000.0)
      .scan<'g', double>();
  program.add_argument("--max_timesteps")
      .help("maximum simulation timesteps")
      .default_value(1000)
      .scan<'i', int>();
  program.add_argument("--seed")
      .help("random seed")
      .default_value(0)
      .scan<'i', int>();

  try {
    program.parse_args(argc, argv);
  } catch (const std::runtime_error& err) {
    std::cerr << err.what() << std::endl;
    std::cerr << program;
    return 1;
  }

  auto map_file = program.get<std::string>("--map");
  auto scen_file = program.get<std::string>("--scen");
  auto output_file = program.get<std::string>("--output");
  auto verbose = program.get<int>("--verbose");
  auto time_limit = program.get<double>("--time_limit");
  auto max_timesteps = program.get<int>("--max_timesteps");
  auto seed = program.get<int>("--seed");

  // create instance
  auto ins = HetInstance(scen_file, map_file);
  if (!ins.is_valid(verbose)) {
    std::cerr << "invalid instance" << std::endl;
    return 1;
  }
  if (!ins.validate_scenario(verbose)) {
    std::cerr << "scenario validation failed" << std::endl;
    return 1;
  }
  info(0, verbose, "instance loaded: N=", ins.N, " fleets=",
       ins.fleets.size());

  // solve
  auto MT = std::mt19937(seed);
  auto deadline = Deadline(time_limit);
  auto planner = Planner(&ins, &deadline, &MT, verbose);
  auto sol = planner.solve(max_timesteps);

  // stats and log
  print_stats(verbose, ins, planner.P, deadline.elapsed_ms());
  make_log(ins, planner.P, output_file, deadline.elapsed_ms(), map_file, seed);

  return 0;
}
