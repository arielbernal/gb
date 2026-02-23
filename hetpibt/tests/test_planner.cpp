#include <hetpibt.hpp>

#include "gtest/gtest.h"

TEST(Planner, BasicSolve)
{
  // two agents on a 4x4 grid, same fleet
  // agent 0: (0,0) -> (3,3)
  // agent 1: (3,0) -> (0,3)
  std::vector<int> fleet_ids = {0, 0};
  std::vector<int> cell_sizes = {1, 1};
  std::vector<float> velocities = {1.0f, 1.0f};
  // index = width * y + x
  std::vector<int> starts = {0, 3};   // (0,0) and (3,0)
  std::vector<int> goals = {15, 12};  // (3,3) and (0,3)

  HetInstance ins("../tests/assets/4x4.map", fleet_ids, cell_sizes,
                  velocities, starts, goals);
  ASSERT_TRUE(ins.is_valid());

  auto MT = std::mt19937(42);
  auto deadline = Deadline(5000);
  auto sol = solve(ins, 0, &deadline, &MT, 100);
  ASSERT_EQ(sol.size(), 2u);
}

TEST(Planner, HeterogeneousSolve)
{
  // agent 0: fleet 0 (cell_size=1), (0,0) -> (3,3) on 4x4 grid
  // agent 1: fleet 1 (cell_size=2), (0,0) -> (1,1) on 2x2 grid
  std::vector<int> fleet_ids = {0, 1};
  std::vector<int> cell_sizes = {1, 2};
  std::vector<float> velocities = {1.0f, 2.0f};
  std::vector<int> starts = {0, 0};  // both at top-left of their graphs
  std::vector<int> goals = {15, 3};  // (3,3) on 4x4, (1,1) on 2x2

  HetInstance ins("../tests/assets/4x4.map", fleet_ids, cell_sizes,
                  velocities, starts, goals);
  ASSERT_TRUE(ins.is_valid());

  auto MT = std::mt19937(42);
  auto deadline = Deadline(5000);
  auto sol = solve(ins, 0, &deadline, &MT, 100);
  ASSERT_EQ(sol.size(), 2u);
}
