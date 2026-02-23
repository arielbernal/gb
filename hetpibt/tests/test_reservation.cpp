#include <hetpibt.hpp>

#include "gtest/gtest.h"

class ReservationTest : public ::testing::Test {
 protected:
  Graph base;
  Fleet* f0;
  Fleet* f1;
  Fleets fleets;
  CollisionChecker cc;

  void SetUp() override
  {
    base = Graph("../tests/assets/4x4.map");
    f0 = new Fleet(0, 1, 1.0f);
    f0->G.build_from_base(base, 1);
    f1 = new Fleet(1, 2, 2.0f);
    f1->G.build_from_base(base, 2);
    fleets = {f0, f1};
    cc = CollisionChecker(fleets, base.width, base.height);
  }

  void TearDown() override
  {
    delete f0;
    delete f1;
  }
};

TEST_F(ReservationTest, BasicReserve)
{
  ReservationTable P(&cc, &fleets);
  Trajectory t;
  t.agent_id = 0;
  t.fleet_id = 0;
  t.start_time = 0;
  t.positions = {0, 1, 2};  // move right along row 0

  P.reserve(t);
  ASSERT_TRUE(P.is_occupied(0, 0, 0));   // cell 0 at t=0
  ASSERT_TRUE(P.is_occupied(0, 1, 1));   // cell 1 at t=1
  ASSERT_TRUE(P.is_occupied(0, 2, 2));   // cell 2 at t=2
  ASSERT_FALSE(P.is_occupied(0, 3, 0));  // cell 3 not occupied at t=0
}

TEST_F(ReservationTest, CrossFleetCollision)
{
  ReservationTable P(&cc, &fleets);

  // agent 0 on fleet 1 (cell_size=2) at cell 0 (covers base 0,1,4,5)
  Trajectory t0;
  t0.agent_id = 0;
  t0.fleet_id = 1;
  t0.start_time = 0;
  t0.positions = {0};

  P.reserve(t0);

  // fleet 0 cell 0 (base cell 0) should be occupied
  ASSERT_TRUE(P.is_occupied(0, 0, 0));
  // fleet 0 cell 1 (base cell 1) should be occupied (cross-fleet)
  ASSERT_TRUE(P.is_occupied(0, 1, 0));
}

TEST_F(ReservationTest, TryReserveCollision)
{
  ReservationTable P(&cc, &fleets);

  Trajectory t0;
  t0.agent_id = 0;
  t0.fleet_id = 0;
  t0.start_time = 0;
  t0.positions = {0};
  P.reserve(t0);

  // try to reserve same cell at same time for different agent
  Trajectory t1;
  t1.agent_id = 1;
  t1.fleet_id = 0;
  t1.start_time = 0;
  t1.positions = {0};
  ASSERT_FALSE(P.try_reserve(t1));
}

TEST_F(ReservationTest, GapFilling)
{
  ReservationTable P(&cc, &fleets);

  // agent at cell 0, time 0
  Trajectory t0;
  t0.agent_id = 0;
  t0.fleet_id = 0;
  t0.start_time = 0;
  t0.positions = {0};
  P.reserve(t0);

  // agent jumps to cell 1 at time 3 (gap: t=1, t=2 should hold at cell 0)
  Trajectory t1;
  t1.agent_id = 0;
  t1.fleet_id = 0;
  t1.start_time = 3;
  t1.positions = {1};
  P.reserve(t1);

  // cell 0 should be occupied at t=1 and t=2 (gap-filled)
  ASSERT_TRUE(P.is_occupied(0, 0, 1));
  ASSERT_TRUE(P.is_occupied(0, 0, 2));
}
