#include <gtest/gtest.h>

#include "dist_table.hpp"
#include "instance.hpp"
#include "pibt.hpp"

// Helper: check no footprint overlap in a config on the base grid.
// Returns the index of the first colliding agent pair, or (-1,-1) if clean.
static std::pair<int, int> find_footprint_collision(const Instance &ins,
                                                    const HetConfig &Q)
{
  int bsize = ins.base_width * ins.base_height;
  std::vector<int> grid(bsize, -1);
  for (uint i = 0; i < ins.N; ++i) {
    if (Q.positions[i] == nullptr) continue;
    int fid = ins.agents[i].fleet_id;
    int cs = ins.fleet_cell_sizes[fid];
    auto &fg = ins.fleet_graphs[fid];
    auto cells =
        to_base_cells(Q.positions[i]->index, fg.width, cs, ins.base_width);
    for (int bc : cells) {
      if (grid[bc] != -1) return {grid[bc], (int)i};
      grid[bc] = (int)i;
    }
  }
  return {-1, -1};
}

// ---------------------------------------------------------------------------
// Basic: call set_new_config on a 2-agent het scenario, verify success
// and collision-free output.
// ---------------------------------------------------------------------------
TEST(PIBTTest, SetNewConfig_Het2Agent)
{
  Instance ins("../assets/test_het_2agent.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 2u);

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto Q_from = ins.make_start_config();

  HetConfig Q_to;
  Q_to.positions.assign(ins.N, nullptr);
  Q_to.kappa.assign(ins.N, 0);

  std::vector<int> order = {0, 1};
  bool res = pibt.set_new_config(Q_from, Q_to, order);
  ASSERT_TRUE(res);

  // All agents assigned
  for (uint i = 0; i < ins.N; ++i) {
    ASSERT_NE(Q_to.positions[i], nullptr) << "agent " << i << " unassigned";
  }

  // No footprint overlap
  auto [a, b] = find_footprint_collision(ins, Q_to);
  ASSERT_EQ(a, -1) << "footprint collision between agents " << a << " and "
                    << b;
}

// ---------------------------------------------------------------------------
// Hard constraint: pre-fill agent 0's next position and verify the solver
// respects it in the output.
// ---------------------------------------------------------------------------
TEST(PIBTTest, SetNewConfig_HardConstraint)
{
  Instance ins("../assets/test_het_2agent.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto Q_from = ins.make_start_config();

  // Pick a valid neighbor of agent 0's start as the hard constraint
  auto *forced = Q_from.positions[0]->neighbor[0];

  HetConfig Q_to;
  Q_to.positions.assign(ins.N, nullptr);
  Q_to.kappa.assign(ins.N, 0);
  Q_to.positions[0] = forced;  // hard constraint

  std::vector<int> order = {0, 1};
  bool res = pibt.set_new_config(Q_from, Q_to, order);
  ASSERT_TRUE(res);

  // Constraint respected
  ASSERT_EQ(Q_to.positions[0], forced)
      << "hard constraint on agent 0 was overwritten";

  // All agents assigned, no collisions
  for (uint i = 0; i < ins.N; ++i) {
    ASSERT_NE(Q_to.positions[i], nullptr) << "agent " << i << " unassigned";
  }
  auto [a, b] = find_footprint_collision(ins, Q_to);
  ASSERT_EQ(a, -1) << "footprint collision between agents " << a << " and "
                    << b;
}

// ---------------------------------------------------------------------------
// Speed gating: set kappa > 0 for agent 1 (cs=2), verify it stays in place.
// ---------------------------------------------------------------------------
TEST(PIBTTest, SetNewConfig_SpeedGating)
{
  Instance ins("../assets/test_het_2agent.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto Q_from = ins.make_start_config();

  // Agent 1 has cs=2. Set kappa=1 to simulate mid-phase.
  Q_from.kappa[1] = 1;

  HetConfig Q_to;
  Q_to.positions.assign(ins.N, nullptr);
  Q_to.kappa.assign(ins.N, 0);

  std::vector<int> order = {0, 1};
  bool res = pibt.set_new_config(Q_from, Q_to, order);
  ASSERT_TRUE(res);

  // Speed-gated agent must stay in place
  ASSERT_EQ(Q_to.positions[1], Q_from.positions[1])
      << "speed-gated agent 1 (kappa=1) should stay in place";

  // Kappa should advance: (1 + 1) % 2 = 0
  ASSERT_EQ(Q_to.kappa[1], 0)
      << "kappa should advance from 1 to 0 for cs=2 agent";

  auto [a, b] = find_footprint_collision(ins, Q_to);
  ASSERT_EQ(a, -1) << "footprint collision between agents " << a << " and "
                    << b;
}

// ---------------------------------------------------------------------------
// 4-agent mixed fleet scenario: exercises recursive push (cs=2 agents
// may need to push cs=1 agents out of their footprint).
// ---------------------------------------------------------------------------
TEST(PIBTTest, SetNewConfig_Het4Agent)
{
  Instance ins("../assets/test_het_valid.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 4u);

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto Q_from = ins.make_start_config();

  HetConfig Q_to;
  Q_to.positions.assign(ins.N, nullptr);
  Q_to.kappa.assign(ins.N, 0);

  std::vector<int> order = {0, 1, 2, 3};
  bool res = pibt.set_new_config(Q_from, Q_to, order);
  ASSERT_TRUE(res);

  for (uint i = 0; i < ins.N; ++i) {
    ASSERT_NE(Q_to.positions[i], nullptr) << "agent " << i << " unassigned";
  }

  auto [a, b] = find_footprint_collision(ins, Q_to);
  ASSERT_EQ(a, -1) << "footprint collision between agents " << a << " and "
                    << b;
}

// ---------------------------------------------------------------------------
// Multiple consecutive set_new_config calls (simulates the search loop
// calling the generator repeatedly). Verifies state is cleaned up properly
// between calls.
// ---------------------------------------------------------------------------
TEST(PIBTTest, SetNewConfig_MultipleCallsNoLeak)
{
  Instance ins("../assets/test_het_valid.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto Q_from = ins.make_start_config();
  std::vector<int> order = {0, 1, 2, 3};

  // Call set_new_config 10 times, feeding each output back as input
  for (int iter = 0; iter < 10; ++iter) {
    HetConfig Q_to;
    Q_to.positions.assign(ins.N, nullptr);
    Q_to.kappa.assign(ins.N, 0);

    bool res = pibt.set_new_config(Q_from, Q_to, order);
    ASSERT_TRUE(res) << "failed at iteration " << iter;

    for (uint i = 0; i < ins.N; ++i) {
      ASSERT_NE(Q_to.positions[i], nullptr)
          << "agent " << i << " unassigned at iteration " << iter;
    }

    auto [a, b] = find_footprint_collision(ins, Q_to);
    ASSERT_EQ(a, -1) << "footprint collision at iteration " << iter
                      << " between agents " << a << " and " << b;

    Q_from = Q_to;
  }
}
