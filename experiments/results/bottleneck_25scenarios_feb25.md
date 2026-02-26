# het_lacam 25-Scenario Benchmark Results — Feb 25, 2026

Solver: het_lacam (LaCAM* with HetPIBT config generator), `--no-star` mode
Agents: first 10 per scenario (cs=11:4, cs=7:4, cs=3:2; no cs=1)
Timeout: 60s per scenario

## Summary

| Map Type | Map Size | Solved/Total | Success Rate |
|----------|----------|--------------|--------------|
| corridor_speed | 77x77 | **25/25** | **100.0%** |
| intersection | 77x77 | **24/25** | **96.0%** |
| cooperative_clearing | 77x77 | **16/25** | **64.0%** |

---

## Corridor Speed (25/25 = 100.0%)

Map: corridor_speed_77.map (77x77), 10 agents, 60s timeout

| # | Scenario | Solved | SOC | Makespan | Time(ms) |
|---|----------|--------|-----|----------|----------|
| 00 | corridor_speed_77_00 | YES | 661 | 113 | 16 |
| 01 | corridor_speed_77_01 | YES | 956 | 194 | 30 |
| 02 | corridor_speed_77_02 | YES | 864 | 140 | 17 |
| 03 | corridor_speed_77_03 | YES | 657 | 121 | 14 |
| 04 | corridor_speed_77_04 | YES | 1773 | 351 | 59 |
| 05 | corridor_speed_77_05 | YES | 463 | 70 | 10 |
| 06 | corridor_speed_77_06 | YES | 383 | 73 | 10 |
| 07 | corridor_speed_77_07 | YES | 1208 | 199 | 31 |
| 08 | corridor_speed_77_08 | YES | 555 | 105 | 9 |
| 09 | corridor_speed_77_09 | YES | 475 | 79 | 9 |
| 10 | corridor_speed_77_10 | YES | 2860 | 488 | 2000 |
| 11 | corridor_speed_77_11 | YES | 410 | 66 | 9 |
| 12 | corridor_speed_77_12 | YES | 521 | 102 | 18 |
| 13 | corridor_speed_77_13 | YES | 693 | 133 | 23 |
| 14 | corridor_speed_77_14 | YES | 1310 | 214 | 21 |
| 15 | corridor_speed_77_15 | YES | 988 | 165 | 28 |
| 16 | corridor_speed_77_16 | YES | 779 | 156 | 17 |
| 17 | corridor_speed_77_17 | YES | 576 | 98 | 12 |
| 18 | corridor_speed_77_18 | YES | 704 | 121 | 14 |
| 19 | corridor_speed_77_19 | YES | 666 | 88 | 12 |
| 20 | corridor_speed_77_20 | YES | 474 | 109 | 15 |
| 21 | corridor_speed_77_21 | YES | 650 | 140 | 17 |
| 22 | corridor_speed_77_22 | YES | 746 | 127 | 14 |
| 23 | corridor_speed_77_23 | YES | 1347 | 237 | 112 |
| 24 | corridor_speed_77_24 | YES | 1042 | 166 | 34 |

**Stats**: Avg SOC=835, Avg Makespan=155, Avg Time=25ms (median 17ms)

---

## Intersection (24/25 = 96.0%)

Map: intersection_77.map (77x77), 10 agents, 60s timeout

| # | Scenario | Solved | SOC | Makespan | Time(ms) |
|---|----------|--------|-----|----------|----------|
| 00 | intersection_77_00 | YES | 1500 | 214 | 49 |
| 01 | intersection_77_01 | YES | 1770 | 348 | 619 |
| 02 | intersection_77_02 | YES | 903 | 157 | 17 |
| 03 | intersection_77_03 | YES | 700 | 114 | 12 |
| 04 | intersection_77_04 | YES | 801 | 121 | 15 |
| 05 | intersection_77_05 | YES | 1757 | 243 | 48 |
| 06 | intersection_77_06 | YES | 1342 | 215 | 32 |
| 07 | intersection_77_07 | YES | 1159 | 200 | 20 |
| 08 | intersection_77_08 | YES | 1524 | 331 | 93 |
| 09 | intersection_77_09 | YES | 3375 | 381 | 112 |
| 10 | intersection_77_10 | YES | 2129 | 267 | 51 |
| 11 | intersection_77_11 | YES | 1327 | 215 | 211 |
| 12 | intersection_77_12 | YES | 856 | 130 | 15 |
| 13 | intersection_77_13 | YES | 857 | 110 | 11 |
| 14 | intersection_77_14 | YES | 3085 | 452 | 3280 |
| 15 | intersection_77_15 | YES | 1134 | 180 | 38 |
| 16 | intersection_77_16 | YES | 1594 | 212 | 25 |
| 17 | intersection_77_17 | YES | 687 | 116 | 14 |
| 18 | intersection_77_18 | YES | 1894 | 259 | 74 |
| 19 | intersection_77_19 | YES | 1378 | 203 | 51 |
| 20 | intersection_77_20 | **NO** | — | — | 61229 |
| 21 | intersection_77_21 | YES | 1469 | 247 | 28 |
| 22 | intersection_77_22 | YES | 1731 | 229 | 43 |
| 23 | intersection_77_23 | YES | 1694 | 242 | 52 |
| 24 | intersection_77_24 | YES | 2674 | 347 | 51 |

**Stats** (solved only): Avg SOC=1573, Avg Makespan=228, Avg Time=206ms (median 48ms)
**Failed**: scenario 20 (timeout at 60s)

---

## Cooperative Clearing (16/25 = 64.0%)

Map: cooperative_clearing_77.map (77x77), 10 agents, 60s timeout

| # | Scenario | Solved | SOC | Makespan | Time(ms) |
|---|----------|--------|-----|----------|----------|
| 00 | cooperative_clearing_77_00 | YES | 1483 | 242 | 24 |
| 01 | cooperative_clearing_77_01 | **NO** | — | — | 61270 |
| 02 | cooperative_clearing_77_02 | YES | 1264 | 204 | 737 |
| 03 | cooperative_clearing_77_03 | YES | 2803 | 437 | 24335 |
| 04 | cooperative_clearing_77_04 | YES | 2279 | 350 | 43 |
| 05 | cooperative_clearing_77_05 | YES | 1853 | 272 | 39027 |
| 06 | cooperative_clearing_77_06 | **NO** | — | — | 60703 |
| 07 | cooperative_clearing_77_07 | **NO** | — | — | 60801 |
| 08 | cooperative_clearing_77_08 | YES | 1112 | 160 | 17 |
| 09 | cooperative_clearing_77_09 | YES | 1845 | 374 | 120 |
| 10 | cooperative_clearing_77_10 | **NO** | — | — | 61384 |
| 11 | cooperative_clearing_77_11 | **NO** | — | — | 61318 |
| 12 | cooperative_clearing_77_12 | **NO** | — | — | 61275 |
| 13 | cooperative_clearing_77_13 | YES | 1831 | 281 | 34 |
| 14 | cooperative_clearing_77_14 | YES | 1139 | 170 | 28 |
| 15 | cooperative_clearing_77_15 | YES | 2003 | 354 | 417 |
| 16 | cooperative_clearing_77_16 | **NO** | — | — | 60849 |
| 17 | cooperative_clearing_77_17 | YES | 1728 | 287 | 44 |
| 18 | cooperative_clearing_77_18 | YES | 2328 | 362 | 319 |
| 19 | cooperative_clearing_77_19 | YES | 2732 | 327 | 57 |
| 20 | cooperative_clearing_77_20 | **NO** | — | — | 60717 |
| 21 | cooperative_clearing_77_21 | YES | 2408 | 377 | 5192 |
| 22 | cooperative_clearing_77_22 | YES | 2684 | 443 | 312 |
| 23 | cooperative_clearing_77_23 | **NO** | — | — | 60426 |
| 24 | cooperative_clearing_77_24 | YES | 3554 | 609 | 19351 |

**Stats** (solved only): Avg SOC=2005, Avg Makespan=318, Avg Time=5630ms (median 319ms)
**Failed**: scenarios 01, 06, 07, 10, 11, 12, 16, 20, 23 (9 timeouts at 60s)

---

## Notes

- **Agent composition**: First 10 lines of each scenario = 4 cs=11 + 4 cs=7 + 2 cs=3 (no cs=1 agents)
- **het_lacam mode**: `--no-star` (returns first feasible solution, no anytime refinement)
- **Completeness**: LaCAM* guarantees completeness for homogeneous MAPF, but the heterogeneous extension may not find solutions when the DFS search space is too large
- **Cooperative clearing bottleneck**: The single-passage topology (width=11) creates severe congestion for 4 large (cs=11) agents trying to pass through simultaneously, explaining the 36% failure rate
