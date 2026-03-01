# Benchmark Summary — Het-RT-LaCAM Project

Last updated: 2026-02-28

---

## 1. SOLVER INVENTORY

| Solver | Binary | Scenario format | Het support | Notes |
|--------|--------|-----------------|-------------|-------|
| **het_rt_lacam** | `het_rt_lacam/build/Release/main.exe` | het_bench (`.scen`), MAPF benchmark | Full: size-het + speed-het + combined | Our solver. See flags below. |
| **hetpibt** | `third_party/hetpibt/build/Release/main.exe` | het_bench (`.scen`) | Full: size-het + speed-het + combined | Reference: sequential per-agent PIBT. |
| **lacam3** | `third_party/lacam3/build/Release/main.exe` | MAPF benchmark (MovingAI `.scen`) | Homogeneous only | LaCAM3 base; anytime-optimal on small instances. |
| **CBSH2-RTC** | `agents/backup/center/temp/CBSH2-RTC/build/Release/cbs.exe` | MAPF benchmark (MovingAI `.scen`) | Homogeneous only | CBS optimal with WDG+GR+GC+T+BP heuristics. |
| **pibt_rs** | `third_party/pibt_rs/target/release/examples/benchmark.exe` | het_bench (`.scen`) | Full (reference impl) | Rust reference; not used in benchmarks. |

### het_rt_lacam key flags
```
-m <map>   -i <scen>   -N <num_agents>   -t <sec>   -s <seed>   -v <verbosity>
--swap-xy          # required for het_bench scenarios (pibt_rs coordinate convention)
--goal-lock        # lock agents permanently at goals (biggest quality improvement)
--no-star          # disable LaCAM* anytime improvement (use with refiner)
--no-refiner       # disable SIPP-based iterative refinement (single-fleet only)
--rt               # enable RT-LaCAM incremental mode
--rt-budget <N>    # node expansion budget per RT step (default 100)
--pibt-num <N>     # Monte-Carlo PIBT instances per iteration (default 1)
--no-st-bfs        # use spatial-only BFS instead of space-time BFS
```

### Coverage matrix

| Solver | Homogeneous | Size-only het | Speed-only het | Combined het |
|--------|:-----------:|:-------------:|:--------------:|:------------:|
| CBSH2-RTC | ✅ optimal | ✗ | ✗ | ✗ |
| lacam3 | ✅ near-optimal | ✗ | ✗ | ✗ |
| het_rt_lacam | ✅ | ✅ | ✅ | ✅ |
| hetpibt | ✅ | ✅ | ✅ | ✅ |
| pibt_rs | ✅ | ✅ | ✅ | ✅ (ref only) |

---

## 2. CBS BREAKPOINT COMPARISON

**Setup**: room-64-64-8 map, random scen file, MovingAI benchmark format.
**CBS timeout per solve**: 60 seconds.
**CBS breaking point**: N=54 solves (50.6s); N=55 times out.

### Binary search trace (CBS only)

| N | CBS result | Runtime |
|---|-----------|---------|
| 5 | Optimal | <1ms |
| 30 | Optimal | 173ms |
| 50 | Optimal | 22.2s |
| 52 | Optimal | 16.6s |
| **54** | **Optimal** | **50.6s** |
| **55** | **Timeout** | >60s |
| 60 | Timeout | >60s |

CBS exhibits a sharp cliff: k=52→50.6s is a ~3× blowup in just 2 agents — characteristic of near-optimal CBS heuristics hitting their limit.

### All solver configurations at N=54

| Solver / Mode | Solved | SOC | vs CBS opt | Makespan | Runtime |
|---------------|:------:|----:|:----------:|:--------:|--------:|
| CBSH2-RTC (optimal) | ✅ | **3021** | 1.00× | — | 50,564ms |
| lacam3 Release (anytime) | ✅ | **3021** | 1.00× | 132 | 60,137ms |
| **het_rt_lacam `--no-star --goal-lock -t 60`** (refiner) | ✅ | **3057** | **1.01×** | 135 | 60,091ms |
| het_rt_lacam `--goal-lock -t 60` (LaCAM*, no refiner time) | ✅ | 3626 | 1.20× | 188 | 60,186ms |
| het_rt_lacam RT `--rt-budget 1000 --goal-lock -t 60` | ✅ | 3670 | 1.21× | — | 11,798ms |
| het_rt_lacam RT `--rt-budget 100 --goal-lock -t 60` | ✅ | **3730** | **1.24×** | 226 | **1,145ms** |

**Key takeaways:**
- het_rt_lacam **RT mode** is **44× faster** than CBS at only 24% SOC overhead.
- het_rt_lacam **refiner mode** (`--no-star`) achieves **1.01× CBS optimal** in 60 seconds.
- LaCAM* anytime search consumes the full time budget; the refiner only fires when LaCAM* exits early (small instances) or when `--no-star` is used.
- Refiner runs SIPP-based LNS until deadline, iteratively replanning agent subsets. On N=54: 3737→3057 in ~500 iterations over 60s.

### CBS configuration
```
cbs.exe -m room-64-64-8.map -a scen-random-1.scen -k 54 -t 60
  solver: CBS with WDG+GR+GC+T+BP heuristics, A* low-level
```

---

## 3. RT+ST-BFS FULL BENCHMARK (190 scenarios)

**Settings**: `--rt --rt-budget 100 --goal-lock -t 60` (+ `--swap-xy` for het_bench)
**Date**: 2026-02-28
**Maps**: 105-series (4 categories × 25 scenarios × 5 agent counts) + het_bench (10 scenarios)
**Source**: `benchmarks/results/rt_stbfs/analysis.md`

### Overall solve rates

| Category | RT+ST-BFS | RT+spatial | hetpibt |
|----------|:---------:|:----------:|:-------:|
| bottleneck_doors | 33/45 (73%) | 35/45 (77%) | 24/45 (53%) |
| corridor_speed | 28/45 (62%) | 24/45 (53%) | 34/45 (75%) |
| intersection | 6/45 (13%) | 8/45 (17%) | 15/45 (33%) |
| cooperative_clearing | 22/45 (48%) | 22/45 (48%) | 38/45 (84%) |
| het_bench | 9/10 (90%) | 9/10 (90%) | 9/10 (90%) |
| **TOTAL** | **98/190 (52%)** | **98/190 (52%)** | **120/190 (63%)** |

### Solve rates by agent count — bottleneck_doors

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|:---------:|:----------:|:-------:|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 4/5 | 5/5 |
| n15 | 4/5 | 3/5 | 4/5 |
| n20 | 1/5 | 4/5 | 2/5 |
| n25 | 18/25 | 19/25 | 8/25 |

### Solve rates by agent count — corridor_speed

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|:---------:|:----------:|:-------:|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 4/5 | 5/5 |
| n15 | 4/5 | 2/5 | 4/5 |
| n20 | 4/5 | 0/5 | 4/5 |
| n25 | 10/25 | 13/25 | 16/25 |

### SOC quality — headline result

**RT+ST-BFS vs RT+spatial** (78 mutual solves):
- Mean SOC ratio: **0.570** (43% lower SOC with space-time BFS)
- Median SOC ratio: **0.536**
- 77/78 mutual solves: ST-BFS strictly better; 1 worse

| Category | Mutual | Mean ratio | Median | ST-BFS better |
|----------|:------:|:----------:|:------:|:-------------:|
| bottleneck_doors | 30 | 0.570 | 0.509 | 30/30 |
| corridor_speed | 16 | **0.439** | 0.433 | 16/16 |
| intersection | 6 | 0.720 | 0.724 | 6/6 |
| cooperative_clearing | 17 | 0.561 | 0.342 | 16/17 |
| het_bench | 9 | 0.722 | 0.677 | 9/9 |

**RT+ST-BFS vs hetpibt** (76 mutual solves):
- Mean SOC ratio: **6.19×**, Median: **4.13×**
- Down from 15.6× with spatial BFS — a 60% improvement in SOC quality ratio.

### Scenario turnover vs RT+spatial

- **20 new solves** (ST-BFS solved, spatial did not): 12 in corridor_speed, 6 in cooperative_clearing, 2 in bottleneck_doors
- **20 regressions** (spatial solved, ST-BFS did not): 8 in corridor_speed n25, 5 in bottleneck_doors, 5 in cooperative_clearing, 2 in intersection n10
- **Net: 0 change** in solve count (98/190 both)
- All regressions were borderline solves with high SOC and long runtimes in spatial mode

### Runtime comparison

| Solver | Median | p95 | Max |
|--------|-------:|----:|----:|
| RT+ST-BFS | 2,572ms | 16,720ms | 53,595ms |
| RT+spatial | 1,335ms | 20,757ms | 52,318ms |
| hetpibt | 68ms | 144ms | 1,505ms |

ST-BFS is ~2× slower than spatial BFS due to space-time collision table overhead. hetpibt is ~20× faster than RT+ST-BFS.

### Stay fix benchmark (neutral)

Separately tested "don't advance when no progress" fix (latest_generated_ guard in solve_one_step):
- **0 new solves, 0 regressions** — strictly neutral on solve rate
- SOC ratio (stay/old): mean=1.004, median=1.000 — negligible change
- Stay step rate: 13% overall (7% on solved, 14% on failed scenarios)
- **Conclusion**: fix is safe to keep but does not close any gap.

---

## 4. HETPIBT vs HET_RT_LACAM HEAD-TO-HEAD

**Benchmark**: 190 scenarios (105-series × 4 categories + het_bench)
**het_rt_lacam settings**: `--rt --rt-budget 100 --goal-lock --swap-xy -t 60`
**hetpibt settings**: `--goal-lock --swap-xy -t 60`

### Overall

| | het_rt_lacam | hetpibt |
|--|:------------:|:-------:|
| Solved | 98/190 (52%) | 120/190 (63%) |
| Exclusive solves | **26** | **48** |
| Mutually solved | 72 | 72 |

### Exclusive solves breakdown

**het_rt_lacam solves that hetpibt cannot (26)**:
- Concentrated in **bottleneck_doors n25** (large agent counts, narrow corridors)
- Structural reason: LaCAM's anytime search explores more configurations than greedy PIBT

**hetpibt solves that het_rt_lacam cannot (48)**:
- **cooperative_clearing** dominates (most hetpibt-exclusive solves)
- **corridor_speed n20+** and **intersection n10+**
- Structural reason: hetpibt processes agents sequentially with full reservation table, giving better per-agent path quality in open spaces

### Per-category winner

| Category | Winner | Margin |
|----------|--------|--------|
| bottleneck_doors | **het_rt_lacam** | 33 vs 24 (38% more solves) |
| corridor_speed | **hetpibt** | 34 vs 28 (21% more solves) |
| intersection | **hetpibt** | 15 vs 6 (150% more solves) |
| cooperative_clearing | **hetpibt** | 38 vs 22 (73% more solves) |
| het_bench | Tied | 9/10 each |

### SOC quality (mutual solves, 76 shared)

- RT+ST-BFS / hetpibt: mean **6.19×**, median **4.13×** (het_rt_lacam much higher SOC)
- het_rt_lacam SOC is higher because LaCAM generates full N-agent configs in single PIBT call; hetpibt plans each agent sequentially with full reservation awareness

### Root cause analysis

| Failure mode | het_rt_lacam | hetpibt |
|---|---|---|
| PIBT config generator failure | High (85-90% on hard maps; BFS reduced to ~1%) | Rare |
| Corridor/bridge deadlock | High (cs=7 in narrow maps) | Moderate |
| Large-agent deadlock (cs≥7) | Moderate | High (cs=11 in congested maps) |
| SOC quality gap vs CBS optimal | Large (4-15×) | Moderate (1-3×) |

---

## 5. KNOWN LIMITATIONS

### Corridor deadlock (architectural)
- PIBT's safety guarantee (no deadlock) requires biconnected graphs. Corridor maps violate this.
- het_rt_lacam and hetpibt both deadlock on narrow passage scenarios (cs=7 in bottleneck maps, corridor_speed at n20+).
- **Root cause**: het_rt_lacam processes all N agents in one PIBT call; if a large agent blocks a corridor, smaller agents behind it cannot resolve the deadlock in one step.
- **hetpibt**: sequential planning gives partial immunity but still deadlocks with multiple large agents.
- No fix implemented. Would require multi-step look-ahead or explicit deadlock detection.

### Refiner only works for single-fleet instances
- The refiner (SIPP-based LNS, ported from lacam3) uses a flat vertex ID space and a single CollisionTable indexed by `fleet_graphs[0]`.
- Guard in `Planner::solve()`: `if (FLG_REFINER && ins->num_fleets == 1 && ...)`.
- Multi-fleet refinement would require either: (a) a base-grid collision table with footprint projection, or (b) per-fleet collision tables with cross-fleet edge checks.
- **Impact**: het_rt_lacam has no quality improvement mechanism for het-fleet scenarios (standard mode or RT mode with LaCAM* time-exhausted).

### LaCAM* / Refiner time conflict
- With `FLG_STAR=true` (default), the anytime LaCAM* search consumes the full time budget.
- The refiner only fires when: (a) OPEN is exhausted (tiny problems), or (b) `--no-star` is used.
- On large homogeneous problems (N≥20 or so), `--no-star --goal-lock` is needed to get refiner benefit.
- Using `--no-star` gives up anytime improvement on the high-level search.

### Stay fix is neutral
- The "don't advance when no progress" fix (latest_generated_ guard) produces measurable stay events (13% of steps) but has **0 net impact** on solve rate or SOC.
- Tested across full 190-scenario benchmark: 0 new solves, 0 regressions, SOC ratio 1.004.

### Budget sweep showed no improvement
- RT budget tested at 100, 1000, 10000 on N=54 room-64-64-8:
  - Budget=100: SOC=3730, 1.1s ← best trade-off
  - Budget=1000: SOC=3670, 11.8s
  - Budget=10000: partial (did not complete in 60s — incomplete solution)
- Larger budget does not monotonically improve quality; high budgets can thrash the search space.

---

## 6. FACTORIAL COMPARISON STATUS

The G-MAPF paper (G-MAPF.pdf) defines a 3-factor experimental design:
- **Size heterogeneity**: agents differ in cell_size (footprint)
- **Speed heterogeneity**: agents differ in velocity / speed_period
- **Combined**: both size and speed differ

### What we have

| Dimension | CBSH2-RTC | lacam3 | hetpibt | het_rt_lacam |
|-----------|:---------:|:------:|:-------:|:------------:|
| Homogeneous | ✅ optimal | ✅ near-opt | ✅ | ✅ |
| Size-only het | ✗ | ✗ | ✅ | ✅ |
| Speed-only het | ✗ | ✗ | ✅ | ✅ |
| Combined het | ✗ | ✗ | ✅ | ✅ |

### What we still need

| Gap | Status | Notes |
|-----|--------|-------|
| **K-CBS** (optimal for size-het) | Not started | Need to build / locate K-CBS binary; extends CBS to k-robust MAPF for large agents |
| **CCBS** (optimal for continuous-time / speed-het) | Not started | Continuous-time CBS; handles variable speeds |
| Size-only het scenarios | Not built | Need scenarios with cs={1,3,5} but same speed |
| Speed-only het scenarios | Not built | Need scenarios with cs=1 but v={1,2,3} |
| Homogeneous quality comparison table | ✅ Done | CBS=lacam3=optimal, het_rt_lacam~1.01× (refiner), hetpibt~comparable |
| het_bench full-het baseline | ✅ Done | hetpibt 9/10, het_rt_lacam 9/10 |

### Current priorities

1. **K-CBS build**: find K-CBS source, build on Windows, validate on size-het scenario
2. **Factorial scenarios**: generate size-only and speed-only scenario sets from existing maps
3. **CCBS**: locate implementation (Andreychuk et al.), build and test
4. **het_rt_lacam multi-fleet refiner**: extend refiner to het-fleet with base-grid collision table

---

## Appendix: Benchmark File Locations

| Dataset | Path |
|---------|------|
| RT+ST-BFS full (190 rows) | `benchmarks/results/rt_stbfs/het_rt_lacam_rt_stbfs_full.csv` |
| RT+ST-BFS analysis | `benchmarks/results/rt_stbfs/analysis.md` |
| RT+ST-BFS+stay (190 rows) | `benchmarks/results/rt_stbfs_stay/het_rt_lacam_rt_stbfs_stay_full.csv` |
| RT+ST-BFS+stay analysis | `benchmarks/results/rt_stbfs_stay/analysis.md` |
| RT+spatial full (190 rows) | `benchmarks/results/rt_lacam/het_rt_lacam_rt_full.csv` |
| RT+spatial analysis | `benchmarks/results/rt_lacam/analysis.md` |
| CBS reference solutions | `third_party/cbsh2rtc/reference_solutions/` |
| Homogeneous baseline CSV | `agents/debug/homogeneous_baseline.csv` |
| CBS breakpoint analysis | `agents/debug/cbs_breakpoint.md` |
| het_bench replays | `experiments/replays/` |
