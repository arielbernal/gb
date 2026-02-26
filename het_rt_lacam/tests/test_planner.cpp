#include <gtest/gtest.h>

#include "lacam.hpp"

// ---------------------------------------------------------------------------
// 3-agent heterogeneous (1×cs=1 + 2×cs=2): solve and validate.
// ---------------------------------------------------------------------------
TEST(PlannerTest, Solve_Het3Agent)
{
  Instance ins("../assets/test_het_3agent.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 3u);

  auto deadline = Deadline(5000);
  Planner::FLG_STAR = false;
  auto solution = solve(ins, 0, &deadline, 0);

  ASSERT_FALSE(solution.empty()) << "solver returned empty solution";
  ASSERT_TRUE(is_feasible_solution(ins, solution))
      << "solution has collision violations";

  // Solution should start at starts and end at goals
  for (uint i = 0; i < ins.N; ++i) {
    ASSERT_EQ(solution.front()[i], ins.starts[i])
        << "agent " << i << " wrong start in solution";
    ASSERT_EQ(solution.back()[i], ins.goals[i])
        << "agent " << i << " didn't reach goal";
  }
}

// ---------------------------------------------------------------------------
// 4-agent heterogeneous (2×cs=1 + 2×cs=2): solve and validate.
// ---------------------------------------------------------------------------
TEST(PlannerTest, Solve_Het4AgentValid)
{
  Instance ins("../assets/test_het_valid.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 4u);

  auto deadline = Deadline(5000);
  Planner::FLG_STAR = false;
  auto solution = solve(ins, 0, &deadline, 0);

  ASSERT_FALSE(solution.empty()) << "solver returned empty solution";
  ASSERT_TRUE(is_feasible_solution(ins, solution))
      << "solution has collision violations";

  for (uint i = 0; i < ins.N; ++i) {
    ASSERT_EQ(solution.front()[i], ins.starts[i]);
    ASSERT_EQ(solution.back()[i], ins.goals[i]);
  }
}

// ---------------------------------------------------------------------------
// 2-agent same-fleet (both cs=2): swap scenario where agents must
// coordinate to exchange positions.
// ---------------------------------------------------------------------------
TEST(PlannerTest, Solve_HetCs2Swap)
{
  Instance ins("../assets/test_het_cs2only.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 2u);

  auto deadline = Deadline(5000);
  Planner::FLG_STAR = false;
  auto solution = solve(ins, 0, &deadline, 0);

  ASSERT_FALSE(solution.empty()) << "solver returned empty solution";
  ASSERT_TRUE(is_feasible_solution(ins, solution))
      << "solution has collision violations";

  for (uint i = 0; i < ins.N; ++i) {
    ASSERT_EQ(solution.back()[i], ins.goals[i])
        << "agent " << i << " didn't reach goal";
  }
}

// ---------------------------------------------------------------------------
// Homogeneous 10-agent on random-32-32-10: exercises the adapter with
// all cs=1 agents (no fleet heterogeneity).
// ---------------------------------------------------------------------------
TEST(PlannerTest, Solve_Homogeneous10)
{
  Instance ins("../assets/random-32-32-10-random-1.scen",
               "../assets/random-32-32-10.map", 10);
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 10u);

  auto deadline = Deadline(5000);
  Planner::FLG_STAR = false;
  auto solution = solve(ins, 0, &deadline, 0);

  ASSERT_FALSE(solution.empty()) << "solver returned empty solution";
  ASSERT_TRUE(is_feasible_solution(ins, solution))
      << "solution has collision violations";
}
