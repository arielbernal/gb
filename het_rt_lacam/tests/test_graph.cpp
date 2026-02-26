#include <gtest/gtest.h>

#include "graph.hpp"

TEST(GraphTest, LoadMap)
{
  Graph G("../assets/empty-8-8.map");
  ASSERT_EQ(G.width, 8);
  ASSERT_EQ(G.height, 8);
  ASSERT_EQ(G.size(), 64);
}

TEST(GraphTest, FleetGraphTiling)
{
  Graph base("../assets/empty-8-8.map");
  Graph fleet;
  fleet.build_from_base(base, 2);
  ASSERT_EQ(fleet.width, 4);
  ASSERT_EQ(fleet.height, 4);
  ASSERT_EQ(fleet.size(), 16);
  // Each fleet vertex should have up to 4 neighbors
  for (auto* v : fleet.V) {
    ASSERT_LE(v->neighbor.size(), 4u);
  }
}

TEST(GraphTest, HetConfigHash)
{
  Graph G("../assets/empty-8-8.map");
  // Two HetConfigs with same positions but different kappa should differ
  HetConfig c1;
  c1.positions = {G.V[0], G.V[1]};
  c1.kappa = {0, 0};

  HetConfig c2;
  c2.positions = {G.V[0], G.V[1]};
  c2.kappa = {1, 0};

  HetConfigHasher hasher;
  ASSERT_NE(hasher(c1), hasher(c2));
  ASSERT_TRUE(is_same_het_config(c1, c1));
  ASSERT_FALSE(is_same_het_config(c1, c2));
}

TEST(GraphTest, ToBaseCells)
{
  // Fleet cell (1,1) with cell_size=2 on base_width=8
  // Should cover base cells: (2,2), (3,2), (2,3), (3,3)
  // Using to_base_cells_xy(fx=1, fy=1, cell_size=2, base_width=8)
  auto cells = to_base_cells_xy(1, 1, 2, 8);
  ASSERT_EQ(cells.size(), 4u);
  // base index = base_width * by + bx
  // (2,2) = 8*2+2 = 18, (3,2) = 8*2+3 = 19, (2,3) = 8*3+2 = 26, (3,3) = 8*3+3 = 27
  std::sort(cells.begin(), cells.end());
  ASSERT_EQ(cells[0], 18);
  ASSERT_EQ(cells[1], 19);
  ASSERT_EQ(cells[2], 26);
  ASSERT_EQ(cells[3], 27);

  // Also test the linear-index overload: cell_index=5, fleet_width=4
  // fx = 5%4 = 1, fy = 5/4 = 1. Same result.
  auto cells2 = to_base_cells(5, 4, 2, 8);
  ASSERT_EQ(cells2.size(), 4u);
  std::sort(cells2.begin(), cells2.end());
  ASSERT_EQ(cells2[0], 18);
  ASSERT_EQ(cells2[1], 19);
  ASSERT_EQ(cells2[2], 26);
  ASSERT_EQ(cells2[3], 27);
}
