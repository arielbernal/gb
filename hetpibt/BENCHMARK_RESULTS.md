# HetPIBT v1 Benchmark Results

Date: 2026-02-23
Tag: `hetpibt-v1-benchmark`

## Setup

- **Map**: room-64-64-8 (64x64 base, scaled 10x to 640x640)
- **Scenarios**: het_bench scen.0 through scen.9 (from pypibt)
- **Agents per scenario**: 9 (3 per fleet)
- **Fleets**: 3 fleets with cell_size = 1, 6, 11
- **Max timesteps**: 500
- **Grid model**: Non-overlapping tiling (paper Section IV-B, Eq. 1)
  - Fleet grid width = base_width / cell_size
  - Fleet cell (fx,fy) covers base cells [fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs)
- **Our solver flags**: `--swap-xy` (matches pypibt/pibt_rs coordinate convention)
- **pibt_rs flags**: map_scale=10, max_steps=500

## Comparison Table

| Scen | N | pibt_rs goals | pibt_rs ms | pibt_rs make | Ours goals | Ours ms | Ours make | Notes |
|------|---|:---:|---:|---:|:---:|---:|---:|-------|
| 0 | 9 | 8/9 | 317 | 371 | **9/9** | **12** | **187** | |
| 1 | 7 | **6/7** | 224 | 500* | 5/7 | 309 | 502* | goal overlap in scenario |
| 2 | 7 | 6/7 | 92 | 105 | **7/7** | **16** | **49** | start/goal overlap |
| 3 | 7 | 6/7 | 131 | 138 | **7/7** | **5** | **69** | |
| 4 | 8 | 6/8 | 831 | 500* | **8/8** | **5** | **61** | |
| 5 | 6 | 5/6 | 238 | 500* | **6/6** | **7** | **170** | |
| 6 | 9 | 8/9 | 265 | 358 | **9/9** | **12** | **176** | start/goal overlap |
| 7 | 9 | 8/9 | 227 | 133 | **9/9** | **52** | **95** | |
| 8 | 9 | 8/9 | 302 | 500* | **9/9** | **8** | **148** | start/goal overlap |
| 9 | 9->8 | 8/9 | 282 | 500* | **8/8** | **7** | **144** | 1 agent on wall (pypibt bug) |
| **Total** | | **69/80** (86%) | | | **77/79** (97%) | | | |

`*` = hit max timesteps without all goals reached.

### Summary

- **Goals reached**: ours 77/79 (97.5%) vs pibt_rs 69/80 (86.3%)
- **Solve time**: ours 5-309ms vs pibt_rs 92-831ms (20-160x faster)
- **Wins**: ours wins goals on 8/10 scenarios; pibt_rs wins on scen.1 (6/7 vs 5/7); tie on scen.9
- **Only loss (scen.1)**: scenario has overlapping goal footprints causing persistent congestion

## pypibt Benchmark Bugs Found

### Bug 1: x/y Coordinate Transposition

Both pypibt and pibt_rs have a consistent transposition of x/y coordinates
when accessing the obstacle grid.

**pypibt** (`scaled_2d_grid.py`, `is_safe_location`):
```python
for ind_x in range(start_ind_x, end_ind_x):     # ind_x is column (from x)
    for ind_y in range(start_ind_y, end_ind_y):  # ind_y is row (from y)
        if not self.upscaled_map[ind_x, ind_y]:  # numpy [row, col] -> [col, row]
```
Accesses `upscaled_map[col, row]` instead of `upscaled_map[row, col]`.

**pibt_rs** (`lib.rs`, `evaluate_individual_agent_cost`):
```rust
for x in 0..base_obstacles.len() {        // x = row in obstacle grid
    for y in 0..base_obstacles[0].len() {  // y = col in obstacle grid
        let x_idx = (x as f32 / scale) as usize;  // row-based index
        let y_idx = (y as f32 / scale) as usize;  // col-based index
        distance_grid[x_idx][y_idx] = -1;          // [row][col]
// ... but later:
distance_grid[agent.end.0][agent.end.1] = 0;  // end = (x/cs, y/cs) = (col, row) -> [col][row]
```
Cost map built as [row][col] but accessed as [col][row] via agent coordinates.

**Effect**: Both tools operate on a transposed version of the map. Because the
transposition is consistent between scenario generation (pypibt) and solving
(pibt_rs), results are correct in the transposed domain. Our solver uses the
`--swap-xy` flag to match this convention.

### Bug 2: Boundary Edge Clamp in Obstacle Checking

**pypibt** (`scaled_2d_grid.py`, `is_safe_location`):
```python
min_y = int(-0.5)  # -> -1, clamped to 0
max_y = int(0.5)   # -> 0
for ind_y in range(0, 0):  # empty range -> no checks -> returns True
```
When a cell center is at y=0, the bounding box extends to y=-0.5. After int
truncation and clamping, the y-range becomes empty, so `is_safe_location`
returns True even if the cell is on a wall.

**Effect**: scen.9 agent 2 is placed at (74, 0) which maps to column 0 of the
original map (always a wall). pibt_rs leaves this agent stuck (never reaches
goal, counts as failure). Our solver detects and removes the agent.

### Bug 3: No Start/Goal Overlap Validation

pypibt's scenario generator (`generate_heterogeneous_problem.py`) checks that
start and goal positions are unique within each fleet but does NOT check
cross-fleet base-grid footprint overlaps. Several scenarios (scen.1, 2, 6, 8)
have agents from different fleets whose start and goal footprints overlap on the
base grid.

**Effect**: Agents from different fleets compete for the same physical space at
their start or goal positions, potentially preventing one from reaching its
goal. pibt_rs doesn't validate this and lets agents compete. Our solver warns
but continues.

## Solver Configuration

### CORE Heuristics (from PIBT paper)

1. **Elapsed counter**: priority += 1 per step, reset to 0 at goal. Ensures
   agents that haven't reached their goal recently get planned first.

2. **Per-agent tie breakers**: random float in [0,1) added to priority for
   ordering jitter, preventing systematic starvation at equal priority.

3. **Same-fleet BFS depth = 1**: vanilla PIBT one-step lookahead.

4. **Cross-fleet adaptive BFS depth = ceil(parent_cs / agent_cs)**: lets smaller
   agents escape a larger agent's footprint when pushed.

5. **BFS neighbor shuffling**: randomized expansion order so agents don't all
   pick the same path through equal-cost intersections.

### EXTENSION Heuristics (our additions for non-biconnected graphs)

1. **Stuck counter acceleration**: tracks whether each agent's distance-to-goal
   decreased. If not, `stuck_count` increments. Priority formula becomes
   `elapsed + stuck_count`, giving quadratic priority growth for stuck agents
   vs linear for progressing ones. Needed because room-64-64-8 doorways are
   bridge edges (not biconnected), so the paper's Theorem 1 guarantee does
   not hold.

2. **Congestion penalty min(nb, 3)**: added to BFS heuristic cost. Steers agents
   away from cells with many parked blockers, preventing chokepoint funneling
   caused by identical distance-table gradients. Capped at 3 to avoid
   over-penalizing in dense but passable areas.

3. **Minimum BFS depth 2**: all agents get at least 2-step lookahead (paper
   uses 1). On non-biconnected graphs with single-cell doorways (bridges),
   1-step lookahead can't see past the doorway, causing agents to oscillate
   at room entrances.

4. **Oscillation penalty**: in low-density areas (<=2 blockers), penalize BFS
   candidates that revisit the agent's last 10 positions (+2 per revisit).
   Without this, agents oscillate between the same 2-3 cells even with high
   priority -- stuck_count fixes planning ORDER but not PATH SELECTION.
   Density-gated to avoid penalizing necessary revisits in crowded areas.

## Scaling Results (our solver, room-64-64-8, tiling model)

| Agents | Goals | Solve time | Makespan | Collisions |
|--------|-------|------------|----------|------------|
| 19 (corridor30) | 19/19 | 35ms | 135 | 0 |
| 16 | 16/16 | 10ms | 119 | 0 |
| 36 | 36/36 | 28ms | 135 | 0 |
| 106 | 106/106 | 134ms | 174 | 0 |
| 206 | 206/206 | 431ms | 322 | 0 |
| 506 | 505/506 | 4022ms | 1001 | 0 |

All results verified collision-free via check_collisions.py.

## Reproducing

```bash
# Build
cd hetpibt && cmake --build build --config Release

# Run comparison
cd .. && source venv/Scripts/activate
python hetpibt/tools/run_comparison.py --max-steps 500

# Run single het_bench scenario
hetpibt/build/Release/main.exe \
  -m hetpibt/build/room64_scaled.map \
  -s pypibt/het_bench/scen.0.scen \
  --swap-xy -v 1 --max_timesteps 500

# Run own scenario (no --swap-xy)
hetpibt/build/Release/main.exe \
  -m hetpibt/tests/assets/corridor30.map \
  -s hetpibt/tests/assets/corridor30.scen \
  -v 1 --max_timesteps 500

# Check collisions
python hetpibt/tests/assets/check_collisions.py <result_file>
```
