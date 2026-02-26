#include <hetpibt.hpp>

#include "gtest/gtest.h"

TEST(Graph, LoadMap)
{
  Graph g("../tests/assets/4x4.map");
  ASSERT_EQ(g.width, 4);
  ASSERT_EQ(g.height, 4);
  ASSERT_EQ(g.size(), 16);  // all cells passable
}

TEST(Graph, BuildFromBase)
{
  // 4x4 base with cell_size=2 -> tiling: (4/2)x(4/2) = 2x2
  Graph base("../tests/assets/4x4.map");
  Graph fleet;
  fleet.build_from_base(base, 2);
  ASSERT_EQ(fleet.width, 2);
  ASSERT_EQ(fleet.height, 2);
  ASSERT_EQ(fleet.size(), 4);

  // each fleet cell should have neighbors
  for (auto* v : fleet.V) {
    ASSERT_FALSE(v->neighbor.empty());
  }
}

TEST(Graph, BuildFromBaseOddSize)
{
  // 4x4 base with cell_size=3 -> tiling: (4/3) = 1x1
  Graph base("../tests/assets/4x4.map");
  Graph fleet;
  fleet.build_from_base(base, 3);
  ASSERT_EQ(fleet.width, 1);
  ASSERT_EQ(fleet.height, 1);
  ASSERT_EQ(fleet.size(), 1);
}
