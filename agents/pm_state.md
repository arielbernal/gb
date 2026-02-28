# PM State — Het-RT-LaCAM
Last updated: Feb 27, 2026 (full 190-scenario analysis complete)

## What's Done

### het_rt_lacam solver
- Forked from lacam3, fully rewritten for heterogeneous agents
- HetConfig (positions + kappa speed-phase), per-fleet tiling graphs
- Cross-fleet footprint collision detection on base grid
- Push-based HetPIBT with depth-limited recursion, cascade rollback, cycle detection
- Stuck-counter acceleration (quadratic priority growth for stuck agents)
- Goal locking (permanent goal occupation)
- Constraint pruning for speed-gated and goal-locked agents
- **BFS multi-step lookahead** (ported from hetpibt, Feb 27 2026): replaces 1-step neighbor enumeration with depth-adaptive BFS on fleet graph. Includes congestion penalty (cap 3) and oscillation penalty (recent_cells deque of 10). Depth = max(2, cell_size).
- Null-agent skip (skip_invalid_agents): skips agents with null start/goal
- 14 unit tests passing

### hetpibt solver
- C++ port of pypibt's heterogeneous PIBT
- 6 extensions: stuck counter, BFS lookahead, recursive backtracking, congestion/oscillation penalties, speed throttling, goal locking
- 12 unit tests passing

### Benchmark infrastructure
- 4 map categories: intersection, bottleneck_doors, corridor_speed, cooperative_clearing
- All on 105-series maps, 25 scenarios each, agent counts n5/n10/n15/n20/n25
- run_all_experiments.py: discovers and runs all scenarios, outputs CSV
- Scenario generators, format converters, validators in benchmarks/generators/
- Visualizers for both solvers (pygame-based)

### het_bench comparison (room-64-64-8, 120x120)
- scen.0-9 (excluding infeasible 1,9)
- Both solvers: 100% goals on all 8 valid scenarios
- hetpibt 1000x faster (5-12ms vs 10s), comparable makespan, lower SOC

### Other
- lacam3 integration analysis — complete (890-line report)
- CBSH2-RTC reference solutions — complete
- Scaling experiments + deadlock analysis — complete

## Current Solver Performance

### het_rt_lacam — Full post-BFS benchmark (190 scenarios, Feb 27, 2026)
Full analysis: `benchmarks/results/post_bfs_port/full_analysis.md`
Combined CSV: `benchmarks/results/post_bfs_port/het_rt_lacam_full.csv` (190 rows)

**Overall: 94/190 solved (49%)** — up from 85/190 pre-BFS (45%)

| Category | lacam solved | hetpibt solved | lacam % | pibt % |
|----------|-------------|---------------|---------|--------|
| bottleneck_doors | 35/45 | 24/45 | 78% | 53% |
| corridor_speed | 23/45 | 34/45 | 51% | 76% |
| intersection | 8/45 | 15/45 | 18% | 33% |
| cooperative_clearing | 20/45 | 38/45 | 44% | 84% |
| het_bench | 8/10 | 9/10 | 80% | 90% |
| **TOTAL** | **94/190** | **120/190** | **49%** | **63%** |

**Key findings:**
- BFS lookahead: +23 new solves, 14 regressions, net +9
- het_rt_lacam dominates bottleneck_doors (78% vs 53%), especially at n20/n25
- hetpibt dominates corridor_speed (76% vs 51%) and cooperative_clearing (84% vs 44%)
- het_rt_lacam exclusively solves 26 scenarios hetpibt cannot (mostly bottleneck n20-n25)
- hetpibt exclusively solves 52 scenarios het_rt_lacam cannot
- SOC gap on 67 mutually-solved: mean 12.9x, median 5.2x (het_rt_lacam higher)
- BFS caused SOC regression on mutually-solved scenarios (post/pre ratio ~1.4x) — BFS explores more but finds longer paths

### Root cause of het_rt_lacam timeouts
PIBT config generator fails 85-90% on hard maps → LaCAM falls back to brute-force constraint tree search → exponential blowup. BFS lookahead reduces failure rate to 99%+ success on most maps.

### BFS regressions (14 scenarios)
BFS lookahead is non-deterministic (random seed + BFS evaluation order). Some previously-solvable scenarios now time out. Key regressions: bottleneck_doors n10/scen.01, n25/{01,03,19,21}; corridor_speed n20/scen.04, n25/{06,08,09,15,22}; cooperative_clearing n15/{03,04}. Full list in `full_analysis.md` section E.

## Open Questions
- ~~Are the failing n10 intersection scenarios actually solvable?~~ **ANSWERED**: Yes. See "Solvability Check Results" below.
- ~~Which of hetpibt's 6 extensions are missing from het_rt_lacam's PIBT?~~ **ANSWERED**: See "PIBT Extension Comparison" below.
- ~~Is the SOC gap purely multi-step BFS vs 1-step PIBT?~~ **PARTIALLY ANSWERED**: BFS lookahead dramatically improved SOC but gap to hetpibt remains (hetpibt uses full space-time BFS with reservation table; our BFS is spatial-only for candidate evaluation).
- Intersection n10 scen 02 still times out with BFS — very hard config. Needs investigation.

## Needs Doing (Priority Order)
1. ~~Full benchmark run~~ ✅ Done — benchmarks/results/het_rt_lacam.csv + hetpibt.csv (190 scenarios each)
2. ~~PIBT investigation~~ ✅ Done — 3/6 extensions present, BFS lookahead was dominant gap
3. ~~Solvability check~~ ✅ Done — both scen 01/02 solvable, null-agent fix applied
4. ~~Port BFS lookahead~~ ✅ Done — BFS multi-step candidate generation with congestion/oscillation penalties
5. ~~Re-run full benchmarks~~ ✅ Done — 94/190 solved (49%), full analysis in `benchmarks/results/post_bfs_port/full_analysis.md`
6. **Large-agent deadlock**: Both solvers struggle with cs=7/cs=11 in congested maps
7. **Anytime improvement**: LaCAM* (FLG_STAR) currently off, evaluate enabling it
8. Phase 2: Real-time extension (not started)
9. Completeness proof formalization (not started)
10. Paper write-up

## Key Findings

### Solvability Check Results (Feb 27, 2026)
Both failing intersection n10 scenarios (01, 02) are **solvable**. het_rt_lacam's failures are NOT due to infeasible scenarios — they are a **missing null-agent skip** in het_rt_lacam.

**intersection_105_01_n10_hb (scen 01)**:
- hetpibt: SOLVED — 9/9 goals, 6ms, SOC=88, makespan=24 (skipped agent 2: null goal)
- het_rt_lacam: CRASH — "agent 2 has null goal" (exit code 1)
- Replay: `E:/gb/experiments/replays/hetpibt_intersection_01_n10.txt`

**intersection_105_02_n10_hb (scen 02)**:
- hetpibt: SOLVED — 9/9 goals, 7ms, SOC=122, makespan=39 (skipped agent 5: null start)
- het_rt_lacam: CRASH — "agent 5 has null start" (exit code 1)
- Replay: `E:/gb/experiments/replays/hetpibt_intersection_02_n10.txt`

**Root cause**: Some agents in these scenarios have start/goal coordinates that land on wall cells for their fleet grid. hetpibt detects this and skips the agent ("removing agent N (null start/goal)"). het_rt_lacam previously treated null start/goal as a fatal error and aborted.

**Fix applied (Feb 27, 2026)**: Added `Instance::skip_invalid_agents()` method to het_rt_lacam (mirrors hetpibt's approach). Skips agents with null start/goal, logs a warning, adjusts agent count. Called in main.cpp before `is_valid()`.

**Post-fix results**:
- intersection_105_01 (scen 01): **SOLVED** — skipped agent 2 (null goal), 9 agents, makespan=35 (lb=23), SOC=189 (lb=75)
- intersection_105_02 (scen 02): **TIMEOUT** — skipped agent 5 (null start), 9 agents, failed to solve in 30s
- All 14 unit tests still pass

**Visualization commands** (het_rt_lacam replays):
```
python E:/gb/het_rt_lacam/visualize.py --result E:/gb/experiments/replays/lacam_intersection_01_n10.txt --map E:/gb/benchmarks/maps/intersection_105.map
```
hetpibt replays:
```
python E:/gb/third_party/hetpibt/visualize.py --result E:/gb/experiments/replays/hetpibt_intersection_01_n10.txt --map E:/gb/benchmarks/maps/intersection_105.map
python E:/gb/third_party/hetpibt/visualize.py --result E:/gb/experiments/replays/hetpibt_intersection_02_n10.txt --map E:/gb/benchmarks/maps/intersection_105.map
```

### BFS Lookahead Port Results (Feb 27, 2026)

Ported multi-step BFS candidate generation from hetpibt into het_rt_lacam's PIBT. Changed only pibt.hpp and pibt.cpp — no changes to LaCAM high-level search, constraint tree, or HetConfig.

**Implementation**: BFS explores fleet graph up to depth D = max(2, cell_size). Cost = steps + h(endpoint) + congestion(cap 3) + oscillation(+2 per recent revisit). Groups by first-step vertex and sorts by best endpoint cost. Oscillation history: deque of 10 recent positions per agent.

**Validation results (intersection n10)**:
| Scenario | Before BFS | After BFS | hetpibt |
|---|---|---|---|
| scen 00 | SOC=? (solved) | SOC=? (solved) | SOC=? |
| scen 01 | SOC=189, 30s | SOC=227, 30s | SOC=88, 6ms |
| scen 02 | TIMEOUT | TIMEOUT | SOC=122, 7ms |
| scen 03 | **TIMEOUT** | **SOC=117, 30s** | SOC=61, 34ms |
| scen 04 | TIMEOUT | **SOC=79, 3.8s** | SOC=? |

**Validation results (cooperative_clearing n10)**:
| Scenario | After BFS | Runtime |
|---|---|---|
| scen 00 | SOC=263, ms=30s | lb=102, ratio=2.58x |
| scen 01 | SOC=154, ms=814 | lb=61, ratio=2.53x |
| scen 02 | SOC=491, ms=30s | lb=175, ratio=2.81x |
| scen 03 | SOC=444, ms=30s | lb=150, ratio=2.96x |
| scen 04 | SOC=124, ms=148 | lb=61, ratio=2.04x |

**Regression check**: het_bench scen 0 — SOC=1120 (unchanged), 14/14 tests pass.

**Key improvements**:
- intersection n10 scen 03: TIMEOUT → SOLVED (SOC=117, 2.34x lb)
- intersection n10 scen 04: TIMEOUT → SOLVED (SOC=79, 1.34x lb — near optimal!)
- cooperative_clearing n10: all 5 solve (2 sub-second), SOC/lb ratios 2.0-3.0x
- PIBT success rate dramatically improved (99%+ on cooperative_clearing n10 vs ~90% before)

**Remaining gap to hetpibt**: Our BFS is spatial-only (evaluates candidates by looking ahead on the fleet graph using current occupancy). hetpibt's BFS is space-time (uses a reservation table for temporal collision checking during BFS). This means our BFS can't plan around agents that will move, only around agents that are currently blocking.

**Replay**: `E:/gb/experiments/replays/lacam_bfs_intersection_03_n10.txt`
```
python E:/gb/het_rt_lacam/visualize.py --result E:/gb/experiments/replays/lacam_bfs_intersection_03_n10.txt --map E:/gb/benchmarks/maps/intersection_105.map
```

### PIBT Extension Comparison (Feb 27, 2026)

| Extension | het_rt_lacam | hetpibt | Status |
|---|---|---|---|
| 1. Stuck counter | YES | YES | Equivalent |
| 2. BFS lookahead | YES (spatial) | YES (space-time) | Ported (spatial variant) |
| 3. Recursive backtracking | YES | YES | Equivalent |
| 4. Congestion/oscillation | YES (in BFS) | YES (in BFS) | Ported |
| 5. Speed throttling | NO | NO | Neither has it |
| 6. Goal locking | YES | YES | Equivalent |

### Other Findings
- Smaller agents (cs=1) fail most on het_rt_lacam, but large agents (cs=7, cs=11) deadlock most on hetpibt — different failure modes
- Deadlocks occur in non-biconnected graph regions (bridges/corridors)
- PIBT reachability guarantee requires biconnected graphs — corridors violate this
- Speed bug found and fixed: velocity was stored but never read
- Goal locking is the single biggest quality improvement for het_rt_lacam
- 100% of failures on bottleneck maps are deadlocks, not timeouts
- Congestion penalty in PIBT sort was tested and reverted (hurt scen.8)

## Fleet Config
- 105-series maps: cs=1/v=1, cs=3/v=1, cs=5/v=2, cs=7/v=3
- het_bench (room120): cs=1, cs=6, cs=11