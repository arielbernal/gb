#include <hetpibt.hpp>

#include "gtest/gtest.h"

TEST(Fleet, Creation)
{
  Fleet f(0, 2, 1.5f);
  ASSERT_EQ(f.id, 0);
  ASSERT_EQ(f.cell_size, 2);
  ASSERT_FLOAT_EQ(f.velocity, 1.5f);
}

TEST(CollisionChecker, ToBaseCells)
{
  // setup: 4x4 base grid, fleet 0 cs=1 (4x4), fleet 1 cs=2 (2x2)
  Graph base("../tests/assets/4x4.map");
  auto* f0 = new Fleet(0, 1, 1.0f);
  f0->G.build_from_base(base, 1);
  auto* f1 = new Fleet(1, 2, 2.0f);
  f1->G.build_from_base(base, 2);
  Fleets fleets = {f0, f1};

  CollisionChecker cc(fleets, base.width, base.height);

  // fleet 1 cell (0,0) with cell_size=2 maps to base cells
  // (0,0), (1,0), (0,1), (1,1)
  auto cells = cc.to_base_cells(1, 0, f1->G.width);
  ASSERT_EQ(cells.size(), 4u);

  // fleet 0 cell (0,0) with cell_size=1 maps to just base cell (0,0)
  auto cells0 = cc.to_base_cells(0, 0, f0->G.width);
  ASSERT_EQ(cells0.size(), 1u);

  delete f0;
  delete f1;
}

TEST(CollisionChecker, GetBlockedNodes)
{
  Graph base("../tests/assets/4x4.map");
  auto* f0 = new Fleet(0, 1, 1.0f);
  f0->G.build_from_base(base, 1);
  auto* f1 = new Fleet(1, 2, 2.0f);
  f1->G.build_from_base(base, 2);
  Fleets fleets = {f0, f1};

  CollisionChecker cc(fleets, base.width, base.height);

  // fleet 1 cell (0,0) covers real-world [0,2)x[0,2)
  // on fleet 0 (cell_size=1) this overlaps cells (0,0),(1,0),(0,1),(1,1)
  auto blocked = cc.get_blocked_nodes(1, 0, 0, fleets);
  ASSERT_EQ(blocked.size(), 4u);
  for (auto& [fid, cidx] : blocked) {
    ASSERT_EQ(fid, 0);
  }

  delete f0;
  delete f1;
}
