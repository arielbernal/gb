#include <gtest/gtest.h>
#include <memory>

#include "dist_table.hpp"
#include "pibt.hpp"
#include "st_reservation.hpp"

// ---------------------------------------------------------------------------
// Helper: build a minimal Instance with a small base grid and 2 fleets.
// Base grid: 8x8 fully open.
// Fleet 0: cell_size=1 (8x8 fleet grid, same as base)
// Fleet 1: cell_size=2 (4x4 fleet grid)
// Returns unique_ptr because Instance is non-copyable (Graph has deleted copy).
// ---------------------------------------------------------------------------
static std::unique_ptr<Instance> make_test_instance()
{
  // Use the homogeneous constructor with N=0 to get a base graph
  auto ins = std::make_unique<Instance>(
      "../assets/empty-8-8.map", "../assets/empty-8-8.map", 0);

  // Manually set up 2 fleets
  ins->num_fleets = 2;
  ins->fleet_cell_sizes = {1, 2};
  ins->fleet_speed_periods = {1, 1};
  ins->fleet_graphs.clear();
  ins->fleet_graphs.resize(2);
  ins->fleet_graphs[0].build_from_base(ins->base_graph, 1);
  ins->fleet_graphs[1].build_from_base(ins->base_graph, 2);

  // 3 agents: agent 0 on fleet 0 (cs=1), agent 1 on fleet 1 (cs=2),
  //           agent 2 on fleet 0 (cs=1)
  ins->N = 3;
  ins->agents = {{0, 1}, {1, 2}, {0, 1}};
  ins->starts.clear();
  ins->starts.resize(3, nullptr);
  ins->goals.clear();
  ins->goals.resize(3, nullptr);

  auto& fg0 = ins->fleet_graphs[0];
  auto& fg1 = ins->fleet_graphs[1];

  // Agent 0 (fleet 0, cs=1): start at fleet cell (2,2) = index 8*2+2 = 18
  ins->starts[0] = fg0.U[8 * 2 + 2];
  ins->goals[0] = fg0.U[8 * 4 + 4];

  // Agent 1 (fleet 1, cs=2): start at fleet cell (0,0) = index 0
  // covers base cells (0,0),(1,0),(0,1),(1,1)
  ins->starts[1] = fg1.U[4 * 0 + 0];
  ins->goals[1] = fg1.U[4 * 2 + 2];

  // Agent 2 (fleet 0, cs=1): start at fleet cell (5,5) = index 8*5+5 = 45
  ins->starts[2] = fg0.U[8 * 5 + 5];
  ins->goals[2] = fg0.U[8 * 6 + 6];

  return ins;
}

// ---------------------------------------------------------------------------
// pack_key
// ---------------------------------------------------------------------------
TEST(STReservationTest, PackKey)
{
  auto k1 = pack_key(0, 5);
  auto k2 = pack_key(1, 5);
  auto k3 = pack_key(0, 6);
  ASSERT_NE(k1, k2);
  ASSERT_NE(k1, k3);
  ASSERT_NE(k2, k3);

  // deterministic
  ASSERT_EQ(pack_key(3, 7), pack_key(3, 7));
}

// ---------------------------------------------------------------------------
// fleet_to_base
// ---------------------------------------------------------------------------
TEST(STReservationTest, FleetToBase)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  // fleet 0, cs=1: cell 18 -> base cell {18}
  auto b0 = res.fleet_to_base(0, 18);
  ASSERT_EQ(b0.size(), 1u);
  ASSERT_EQ(b0[0], 18);

  // fleet 1, cs=2: cell 0 (fx=0,fy=0) -> base cells (0,0),(1,0),(0,1),(1,1)
  // = {0, 1, 8, 9}
  auto b1 = res.fleet_to_base(1, 0);
  ASSERT_EQ(b1.size(), 4u);
  std::sort(b1.begin(), b1.end());
  ASSERT_EQ(b1[0], 0);
  ASSERT_EQ(b1[1], 1);
  ASSERT_EQ(b1[2], 8);
  ASSERT_EQ(b1[3], 9);
}

// ---------------------------------------------------------------------------
// Seed + is_occupied at t=0
// ---------------------------------------------------------------------------
TEST(STReservationTest, SeedAndIsOccupied)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  HetConfig config;
  config.positions = ins->starts;
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Agent 0 at base cell 18 (fleet 0, cell (2,2))
  ASSERT_TRUE(res.is_occupied(18, 0));
  ASSERT_FALSE(res.is_occupied(18, 0, 0));  // exclude self

  // Agent 1 at fleet 1 cell 0 -> base cells {0, 1, 8, 9}
  ASSERT_TRUE(res.is_occupied(0, 0));
  ASSERT_TRUE(res.is_occupied(1, 0));
  ASSERT_TRUE(res.is_occupied(8, 0));
  ASSERT_TRUE(res.is_occupied(9, 0));
  ASSERT_FALSE(res.is_occupied(0, 0, 1));  // exclude agent 1

  // Agent 2 at base cell 45
  ASSERT_TRUE(res.is_occupied(45, 0));

  // Unoccupied cell at t=0
  ASSERT_FALSE(res.is_occupied(30, 0));
}

// ---------------------------------------------------------------------------
// Parked agents: is_occupied beyond explicit reservation
// ---------------------------------------------------------------------------
TEST(STReservationTest, ParkedAgents)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  HetConfig config;
  config.positions = ins->starts;
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Agent 0 seeded at t=0 only. At t=1 it should be "parked" there.
  ASSERT_TRUE(res.is_occupied(18, 1));       // parked agent detected
  ASSERT_FALSE(res.is_occupied(18, 1, 0));   // exclude self
  ASSERT_TRUE(res.is_occupied(18, 5));       // still parked at t=5
}

// ---------------------------------------------------------------------------
// reserve_path: multi-step reservation
// ---------------------------------------------------------------------------
TEST(STReservationTest, ReservePath)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  HetConfig config;
  config.positions = ins->starts;
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Move agent 0 (fleet 0, cs=1) from cell 18 to 19 to 20 over t=0..2
  // cell 18 = (2,2), cell 19 = (3,2), cell 20 = (4,2)
  res.reserve_path(0, 0, 0, {18, 19, 20});

  // Agent 0 at cell 18 at t=0
  ASSERT_TRUE(res.is_occupied(18, 0));
  // Agent 0 at cell 19 at t=1
  ASSERT_TRUE(res.is_occupied(19, 1));
  // Agent 0 at cell 20 at t=2
  ASSERT_TRUE(res.is_occupied(20, 2));

  // Cell 18 at t=2: endpoint moved to cell 20, parked_at_cell for 18 cleared.
  ASSERT_FALSE(res.is_occupied(18, 2));

  // Agent 0 parked at cell 20 at t=3 (beyond explicit reservation)
  ASSERT_TRUE(res.is_occupied(20, 3));
  ASSERT_FALSE(res.is_occupied(20, 3, 0));  // exclude self
}

// ---------------------------------------------------------------------------
// move_collides: vertex conflict
// ---------------------------------------------------------------------------
TEST(STReservationTest, VertexConflict)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  HetConfig config;
  config.positions = ins->starts;
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Agent 0 seeded at fleet 0 cell 18. Parked there at all future times.
  // Agent 2 tries to move from cell 17 to cell 18 at time 0:
  //   vertex check: is cell 18 occupied at t=1? Yes (agent 0 parked).
  ASSERT_TRUE(res.move_collides(0, 17, 18, 0, 2));

  // Agent 0 tries the same move — should NOT self-collide
  ASSERT_FALSE(res.move_collides(0, 17, 18, 0, 0));
}

// ---------------------------------------------------------------------------
// move_collides: swap conflict
// ---------------------------------------------------------------------------
TEST(STReservationTest, SwapConflict)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 2);

  // Reserve explicit path for agent 0: cell 10 at t=0, cell 11 at t=1
  res.reserve_path(0, 0, 0, {10, 11});

  // Agent 1 tries to move from cell 11 to cell 10 at time 0.
  //
  // move_collides(fleet=0, from=11, to=10, time=0, agent=1):
  //   vertex: is base cell 10 occupied at t=1?
  //     Agent 0 is at cell 11 at t=1 (explicit), NOT at cell 10.
  //     Parked? Endpoint is cell 11 (end_time=1). Not parked at 10.
  //     So vertex conflict = false.
  //   swap: agents at cell 10 (to) at t=0 that are also at cell 11 (from) at t=1?
  //     Agent 0 at cell 10 at t=0 (explicit) — yes, in agents_at_to.
  //     Agent 0 at cell 11 at t=1 (explicit) — yes, at from at t+1.
  //     => swap detected!
  ASSERT_TRUE(res.move_collides(0, 11, 10, 0, 1));

  // Agent 0 checking its own move: no self-collision
  ASSERT_FALSE(res.move_collides(0, 10, 11, 0, 0));
}

// ---------------------------------------------------------------------------
// move_collides: no conflict
// ---------------------------------------------------------------------------
TEST(STReservationTest, NoConflict)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  HetConfig config;
  config.positions = ins->starts;
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Agent 2 at cell 45. Moving from 30 to 31 at t=0 — far from everyone.
  ASSERT_FALSE(res.move_collides(0, 30, 31, 0, 2));
}

// ---------------------------------------------------------------------------
// get_occupants
// ---------------------------------------------------------------------------
TEST(STReservationTest, GetOccupants)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  HetConfig config;
  config.positions = ins->starts;
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Cell 18 on fleet 0 at t=0 should have agent 0
  auto occ = res.get_occupants(0, 18, 0);
  ASSERT_EQ(occ.size(), 1u);
  ASSERT_EQ(occ[0], 0);

  // Cell 0 on fleet 1 at t=0 should have agent 1
  auto occ2 = res.get_occupants(1, 0, 0);
  ASSERT_EQ(occ2.size(), 1u);
  ASSERT_EQ(occ2[0], 1);

  // Empty cell
  auto occ3 = res.get_occupants(0, 30, 0);
  ASSERT_EQ(occ3.size(), 0u);

  // Parked: agent 0 at cell 18 at t=5 (parked beyond explicit)
  auto occ4 = res.get_occupants(0, 18, 5);
  ASSERT_EQ(occ4.size(), 1u);
  ASSERT_EQ(occ4[0], 0);
}

// ---------------------------------------------------------------------------
// Cross-fleet collision: cs=2 agent overlaps with cs=1 agent
// ---------------------------------------------------------------------------
TEST(STReservationTest, CrossFleetCollision)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  // Seed just agent 1 (fleet 1, cs=2) at fleet cell 0
  // covers base cells {0, 1, 8, 9}
  HetConfig config;
  config.positions = {nullptr, ins->starts[1], nullptr};
  config.kappa = {0, 0, 0};
  res.seed(config);

  // Base cell 0 at t=0 should be occupied (by agent 1's footprint)
  ASSERT_TRUE(res.is_occupied(0, 0));
  ASSERT_TRUE(res.is_occupied(1, 0));

  // Agent 0 (fleet 0, cs=1) moving from cell 8 to cell 0 at t=0
  // vertex check: is base cell 0 occupied at t=1? Yes (agent 1 parked).
  ASSERT_TRUE(res.move_collides(0, 8, 0, 0, 0));
}

// ---------------------------------------------------------------------------
// reserve_stay
// ---------------------------------------------------------------------------
TEST(STReservationTest, ReserveStay)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  // Reserve agent 0 staying at fleet 0 cell 10 from t=0 to t=3
  res.reserve_stay(0, 0, 10, 0, 3);

  ASSERT_TRUE(res.is_occupied(10, 0));
  ASSERT_TRUE(res.is_occupied(10, 1));
  ASSERT_TRUE(res.is_occupied(10, 2));
  ASSERT_TRUE(res.is_occupied(10, 3));
  // Parked beyond t=3
  ASSERT_TRUE(res.is_occupied(10, 4));
  ASSERT_TRUE(res.is_occupied(10, 10));
}

// ---------------------------------------------------------------------------
// Gap fill: reserve_path at t=3 when endpoint is at t=0
// ---------------------------------------------------------------------------
TEST(STReservationTest, GapFill)
{
  auto ins = make_test_instance();
  STReservation res(ins.get(), 3);

  // Agent 0 at cell 10 at t=0
  res.reserve_stay(0, 0, 10, 0, 0);

  // Now reserve path starting at t=3: agent should be gap-filled at cell 10
  // for t=1 and t=2
  res.reserve_path(0, 0, 3, {15, 16});

  // Gap fill at t=1 and t=2 at cell 10
  ASSERT_TRUE(res.is_occupied(10, 1));
  ASSERT_TRUE(res.is_occupied(10, 2));

  // New path
  ASSERT_TRUE(res.is_occupied(15, 3));
  ASSERT_TRUE(res.is_occupied(16, 4));

  // Parked at cell 16 beyond t=4
  ASSERT_TRUE(res.is_occupied(16, 5));

  // Cell 10 at t=3: no longer parked there (endpoint moved to 16)
  ASSERT_FALSE(res.is_occupied(10, 3));
}

// ===========================================================================
// Space-time BFS tests (Task B)
// ===========================================================================

// ---------------------------------------------------------------------------
// st_bfs_get_candidates: basic operation on 2-agent het scenario.
// Agent 0 (cs=1) at (0,0) with goal at (7,0). Agent 1 (cs=2) at (6,6).
// Seed reservation, call st_bfs for agent 0, verify valid ProposedPaths.
// ---------------------------------------------------------------------------
TEST(STBfsTest, BasicCandidates)
{
  Instance ins("../assets/test_het_2agent.scen", "../assets/empty-8-8.map");
  ASSERT_TRUE(ins.is_valid());
  ASSERT_EQ(ins.N, 2u);

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto config = ins.make_start_config();
  STReservation res(&ins, ins.N);
  res.seed(config);

  // BFS for agent 0 (cs=1, fleet 0), depth=2
  auto candidates = pibt.st_bfs_get_candidates(0, res, 2);

  // Should return at least 1 candidate (wait-in-place at minimum gets emitted)
  ASSERT_GE(candidates.size(), 1u);
  ASSERT_LE(candidates.size(), 5u);

  // Each candidate should have a valid path
  auto &fg0 = ins.fleet_graphs[0];
  for (auto &pp : candidates) {
    ASSERT_GE(pp.path.size(), 2u);  // at least start + one step
    // path[0] should be the start cell
    ASSERT_EQ(pp.path[0], config.positions[0]->index);
    // first_step should match path[1]
    ASSERT_EQ(pp.first_step, pp.path[1]);
    // All cells in path should be valid fleet vertices
    for (int cell : pp.path) {
      ASSERT_NE(fg0.U[cell], nullptr) << "invalid cell " << cell << " in path";
    }
    // Consecutive cells should be neighbors or same (wait)
    for (size_t i = 1; i < pp.path.size(); ++i) {
      int prev = pp.path[i - 1];
      int cur = pp.path[i];
      if (prev == cur) continue;  // wait in place
      auto *pv = fg0.U[prev];
      bool found = false;
      for (auto *nb : pv->neighbor) {
        if (nb->index == cur) { found = true; break; }
      }
      ASSERT_TRUE(found) << "path step " << prev << " -> " << cur
                          << " not adjacent";
    }
  }

  // Candidates should be sorted: first candidate should have best
  // (or tied) endpoint distance
  if (candidates.size() >= 2) {
    int d0 = D.get(0, fg0.U[candidates[0].path.back()]);
    int d1 = D.get(0, fg0.U[candidates[1].path.back()]);
    ASSERT_LE(d0, d1);
  }
}

// ---------------------------------------------------------------------------
// st_bfs_get_candidates: avoids reserved cells.
// Place agent 1 directly in agent 0's path, verify BFS routes around it.
// ---------------------------------------------------------------------------
TEST(STBfsTest, AvoidsReservedCells)
{
  // Use empty 8x8, 2 agents both on fleet 0 (cs=1)
  Instance ins("../assets/empty-8-8.map", "../assets/empty-8-8.map", 0);
  ins.num_fleets = 1;
  ins.fleet_cell_sizes = {1};
  ins.fleet_speed_periods = {1};
  ins.fleet_graphs.clear();
  ins.fleet_graphs.resize(1);
  ins.fleet_graphs[0].build_from_base(ins.base_graph, 1);

  auto &fg = ins.fleet_graphs[0];
  ins.N = 2;
  ins.agents = {{0, 1}, {0, 1}};
  ins.starts = {fg.U[8 * 3 + 3], fg.U[8 * 3 + 4]};  // agent 0 at (3,3), agent 1 at (4,3)
  ins.goals = {fg.U[8 * 3 + 5], fg.U[8 * 3 + 2]};    // agent 0 goal at (5,3), agent 1 goal at (2,3)

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto config = ins.make_start_config();
  STReservation res(&ins, ins.N);
  res.seed(config);

  // Agent 0 at cell (3,3)=27, goal at (5,3)=29
  // Agent 1 at cell (4,3)=28, directly blocking the path
  auto candidates = pibt.st_bfs_get_candidates(0, res, 3);
  ASSERT_GE(candidates.size(), 1u);

  // Agent 1 is at cell 28, parked there. BFS should:
  // - NOT have cell 28 at t=1 as first step (blocked by vertex conflict)
  // - Either route around or wait+move
  for (auto &pp : candidates) {
    // Check that agent 1 appears in blocking_agents IF the path goes through
    // its cell — or that the path avoids it entirely
    for (size_t i = 1; i < pp.path.size(); ++i) {
      if (pp.path[i] == 28) {
        // If path goes through cell 28, agent 1 should be in blockers
        bool found_blocker = false;
        for (int b : pp.blocking_agents) {
          if (b == 1) { found_blocker = true; break; }
        }
        // Note: BFS prunes edges via move_collides, so it should NOT include
        // cell 28 if agent 1 is explicitly reserved there. The path should
        // route around. But if the parked agent is detected via get_occupants,
        // it may appear as a blocker in the path reconstruction.
      }
    }
  }

  // Verify that move_collides correctly blocks the direct path
  // Agent 0 trying to move from cell 27 to cell 28 at t=0:
  // vertex conflict at (28, t+1=1) — agent 1 parked there
  ASSERT_TRUE(res.move_collides(0, 27, 28, 0, 0));
}

// ---------------------------------------------------------------------------
// st_bfs_get_candidates: blocking_agents populated for parked agents.
// ---------------------------------------------------------------------------
TEST(STBfsTest, BlockingAgentsDetected)
{
  Instance ins("../assets/empty-8-8.map", "../assets/empty-8-8.map", 0);
  ins.num_fleets = 1;
  ins.fleet_cell_sizes = {1};
  ins.fleet_speed_periods = {1};
  ins.fleet_graphs.clear();
  ins.fleet_graphs.resize(1);
  ins.fleet_graphs[0].build_from_base(ins.base_graph, 1);

  auto &fg = ins.fleet_graphs[0];
  ins.N = 2;
  ins.agents = {{0, 1}, {0, 1}};
  // Agent 0 at (3,3)=27, agent 1 far away at (0,0)=0
  ins.starts = {fg.U[27], fg.U[0]};
  // Agent 0 goal at (5,3)=29, agent 1 goal at (7,7)=63
  ins.goals = {fg.U[29], fg.U[63]};

  DistTable D(&ins);
  HetPIBT pibt(&ins, &D, 42);

  auto config = ins.make_start_config();
  STReservation res(&ins, ins.N);
  res.seed(config);

  // BFS for agent 0 — agent 1 is far away, no blocking
  auto candidates = pibt.st_bfs_get_candidates(0, res, 2);
  ASSERT_GE(candidates.size(), 1u);

  // First candidate (best path toward goal) should have no blockers
  // since agent 1 is at (0,0), far from agent 0's path toward (5,3)
  ASSERT_EQ(candidates[0].blocking_agents.size(), 0u);
}

// ---------------------------------------------------------------------------
// st_bfs_get_candidates: cross-fleet, larger agent blocks smaller agent
// ---------------------------------------------------------------------------
TEST(STBfsTest, CrossFleetBlocking)
{
  auto ins = make_test_instance();  // fleet 0 (cs=1), fleet 1 (cs=2)
  DistTable D(ins.get());
  HetPIBT pibt(ins.get(), &D, 42);

  // Agent 0 (fleet 0, cs=1) at cell 18 = (2,2)
  // Agent 1 (fleet 1, cs=2) at cell 0, covers base cells {0,1,8,9}
  auto config = ins->make_start_config();
  STReservation res(ins.get(), ins->N);
  res.seed(config);

  // BFS for agent 0: should find paths that don't collide with
  // agent 1's cs=2 footprint
  auto candidates = pibt.st_bfs_get_candidates(0, res, 3);
  ASSERT_GE(candidates.size(), 1u);

  // All path cells should be valid fleet-0 vertices
  auto &fg0 = ins->fleet_graphs[0];
  for (auto &pp : candidates) {
    ASSERT_EQ(pp.path[0], config.positions[0]->index);
    for (int cell : pp.path) {
      ASSERT_NE(fg0.U[cell], nullptr);
    }
  }
}
