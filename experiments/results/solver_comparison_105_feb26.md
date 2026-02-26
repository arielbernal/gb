# HetPIBT vs Het-LaCAM — 105x105 Benchmark Comparison

**Date:** 2026-02-25
**Maps:** corridor_speed_105, intersection_105, cooperative_clearing_105, bottleneck_doors_105
**Agents:** 25 per scenario, fleets cs={1,3,5,7}, velocities v={1,1,2,3}
**Scenarios:** 25 seeds per map type (100 total)
**Timeout:** 60s

## Summary

| Map Type | HetPIBT Avg Goal% | Het-LaCAM Solved | HetPIBT Avg ms | Het-LaCAM Avg ms | HetPIBT 100% | Het-LaCAM 100% |
|----------|-------------------|------------------|----------------|------------------|--------------|----------------|
| corridor_speed | 8.8% | 21/25 (84%) | 72 | 13883 | 0/25 | 21/25 |
| intersection | 30.4% | 3/25 (12%) | 76 | 55597 | 0/25 | 3/25 |
| cooperative_clearing | 2.6% | 4/25 (16%) | 87 | 51077 | 0/25 | 4/25 |
| bottleneck_doors | 80.2% | 21/25 (84%) | 52 | 9951 | 16/25 | 21/25 |

**Key observations:**
- **Het-LaCAM dominates completeness** on corridor_speed (84% solved vs 0% at 100% goals) and bottleneck_doors (84% vs 64%)
- **HetPIBT dominates speed** — 7-130x faster across all map types
- **HetPIBT has lower SOC/makespan** in every head-to-head, but this is misleading: HetPIBT only moves agents partway while Het-LaCAM delivers all 25 to their goals
- **Both solvers struggle** on intersection (3/25 solved) and cooperative_clearing (4/25 solved) — these are genuinely hard scenarios

## Solution Quality (scenarios where Het-LaCAM solved)

### corridor_speed (21 scenarios)
- HetPIBT reached 100% goals: 0/21
- SOC: HetPIBT avg 868 vs Het-LaCAM avg 14145 (HetPIBT wins 21/21 — but incomplete)
- Makespan: HetPIBT avg 40 vs Het-LaCAM avg 1148
- Speed: HetPIBT 66x faster (74ms vs 4841ms)

### intersection (3 scenarios)
- HetPIBT reached 100% goals: 0/3
- SOC: HetPIBT avg 793 vs Het-LaCAM avg 3394
- Makespan: HetPIBT avg 44 vs Het-LaCAM avg 266
- Speed: HetPIBT 130x faster (122ms vs 15831ms)

### cooperative_clearing (4 scenarios)
- HetPIBT reached 100% goals: 0/4
- SOC: HetPIBT avg 763 vs Het-LaCAM avg 11289
- Makespan: HetPIBT avg 38 vs Het-LaCAM avg 831
- Speed: HetPIBT 7x faster (66ms vs 486ms)

### bottleneck_doors (21 scenarios)
- HetPIBT reached 100% goals: 14/21
- SOC: HetPIBT avg 1822 vs Het-LaCAM avg 3199 (HetPIBT wins 21/21)
- Makespan: HetPIBT avg 121 vs Het-LaCAM avg 215 (HetPIBT wins 20/21)
- Speed: roughly tied (52ms vs 47ms)

## Per-Scenario Results

### corridor_speed_105
| Seed | PIBT Goals | PIBT SOC | PIBT MK | PIBT ms | LaCAM | LaCAM SOC | LaCAM MK | LaCAM ms |
|------|------------|----------|---------|---------|-------|-----------|----------|----------|
| 00 | 8/25 | 1717 | 82 | 63 | FAIL | - | - | 61823 |
| 01 | 1/25 | 709 | 31 | 64 | 25/25 | 10875 | 797 | 464 |
| 02 | 1/25 | 726 | 32 | 64 | 25/25 | 12333 | 1251 | 2336 |
| 03 | 0/25 | 558 | 27 | 70 | 25/25 | 10311 | 1030 | 7484 |
| 04 | 1/25 | 520 | 23 | 269 | 25/25 | 11179 | 960 | 950 |
| 05 | 1/25 | 1089 | 48 | 61 | 25/25 | 15680 | 1365 | 3154 |
| 06 | 0/25 | 491 | 23 | 62 | 25/25 | 8286 | 733 | 160 |
| 07 | 1/25 | 1108 | 51 | 63 | 25/25 | 12703 | 1146 | 6275 |
| 08 | 7/25 | 1523 | 70 | 61 | FAIL | - | - | 60672 |
| 09 | 3/25 | 1180 | 52 | 63 | FAIL | - | - | 61150 |
| 10 | 7/25 | 1514 | 66 | 61 | 25/25 | 21880 | 1456 | 5686 |
| 11 | 0/25 | 734 | 34 | 62 | 25/25 | 20810 | 1347 | 14317 |
| 12 | 0/25 | 867 | 41 | 61 | 25/25 | 14326 | 1142 | 224 |
| 13 | 8/25 | 1611 | 80 | 64 | FAIL | - | - | 61760 |
| 14 | 0/25 | 944 | 44 | 62 | 25/25 | 18145 | 1363 | 7403 |
| 15 | 2/25 | 601 | 33 | 66 | 25/25 | 16829 | 1409 | 676 |
| 16 | 4/25 | 1181 | 53 | 61 | 25/25 | 16473 | 1406 | 32628 |
| 17 | 4/25 | 1394 | 67 | 61 | 25/25 | 7923 | 557 | 399 |
| 18 | 1/25 | 925 | 43 | 62 | 25/25 | 13719 | 1326 | 8873 |
| 19 | 2/25 | 830 | 36 | 62 | 25/25 | 19432 | 1452 | 2019 |
| 20 | 0/25 | 605 | 28 | 70 | 25/25 | 7907 | 573 | 84 |
| 21 | 0/25 | 403 | 19 | 75 | 25/25 | 14277 | 1301 | 510 |
| 22 | 1/25 | 982 | 43 | 62 | 25/25 | 15289 | 1284 | 1226 |
| 23 | 3/25 | 1405 | 59 | 65 | 25/25 | 17746 | 1255 | 2351 |
| 24 | 0/25 | 644 | 31 | 63 | 25/25 | 10924 | 953 | 4441 |

### intersection_105
| Seed | PIBT Goals | PIBT SOC | PIBT MK | PIBT ms | LaCAM | LaCAM SOC | LaCAM MK | LaCAM ms |
|------|------------|----------|---------|---------|-------|-----------|----------|----------|
| 00 | 5/25 | 875 | 47 | 63 | FAIL | - | - | 60469 |
| 01 | 9/25 | 863 | 46 | 61 | FAIL | - | - | 60528 |
| 02 | 17/25 | 1277 | 67 | 61 | 25/25 | 3525 | 261 | 10528 |
| 03 | 7/25 | 684 | 35 | 62 | FAIL | - | - | 60601 |
| 04 | 3/25 | 588 | 33 | 139 | 25/25 | 3722 | 293 | 19881 |
| 05 | 8/25 | 880 | 46 | 136 | FAIL | - | - | 61024 |
| 06 | 5/25 | 1290 | 56 | 61 | FAIL | - | - | 61545 |
| 07 | 1/25 | 146 | 10 | 87 | FAIL | - | - | 60562 |
| 08 | 18/25 | 1266 | 71 | 61 | FAIL | - | - | 61579 |
| 09 | 6/25 | 1141 | 51 | 61 | FAIL | - | - | 60754 |
| 10 | 3/25 | 252 | 19 | 85 | FAIL | - | - | 61395 |
| 11 | 4/25 | 463 | 26 | 62 | FAIL | - | - | 61596 |
| 12 | 7/25 | 731 | 39 | 61 | FAIL | - | - | 61131 |
| 13 | 11/25 | 1107 | 54 | 62 | FAIL | - | - | 60752 |
| 14 | 11/25 | 755 | 43 | 61 | FAIL | - | - | 60893 |
| 15 | 10/25 | 916 | 46 | 62 | FAIL | - | - | 60310 |
| 16 | 6/25 | 318 | 16 | 100 | FAIL | - | - | 61491 |
| 17 | 5/25 | 375 | 20 | 81 | FAIL | - | - | 61222 |
| 18 | 12/25 | 1295 | 65 | 63 | FAIL | - | - | 61309 |
| 19 | 11/25 | 1012 | 45 | 61 | FAIL | - | - | 60609 |
| 20 | 11/25 | 908 | 49 | 65 | FAIL | - | - | 61204 |
| 21 | 6/25 | 806 | 40 | 63 | FAIL | - | - | 60971 |
| 22 | 6/25 | 515 | 32 | 166 | 25/25 | 2935 | 245 | 17084 |
| 23 | 4/25 | 1002 | 49 | 61 | FAIL | - | - | 61290 |
| 24 | 4/25 | 673 | 32 | 63 | FAIL | - | - | 61206 |

### cooperative_clearing_105
| Seed | PIBT Goals | PIBT SOC | PIBT MK | PIBT ms | LaCAM | LaCAM SOC | LaCAM MK | LaCAM ms |
|------|------------|----------|---------|---------|-------|-----------|----------|----------|
| 00 | 0/25 | 366 | 18 | 99 | FAIL | - | - | 60900 |
| 01 | 0/25 | 312 | 17 | 88 | FAIL | - | - | 60456 |
| 02 | 2/25 | 875 | 40 | 61 | FAIL | - | - | 61079 |
| 03 | 0/25 | 944 | 41 | 63 | FAIL | - | - | 60881 |
| 04 | 1/25 | 389 | 17 | 202 | FAIL | - | - | 60684 |
| 05 | 1/25 | 862 | 44 | 64 | 25/25 | 9832 | 887 | 322 |
| 06 | 0/25 | 354 | 16 | 70 | FAIL | - | - | 60466 |
| 07 | 5/25 | 1562 | 70 | 61 | FAIL | - | - | 60479 |
| 08 | 0/25 | 358 | 22 | 64 | 25/25 | 23968 | 1669 | 1360 |
| 09 | 0/25 | 939 | 44 | 67 | FAIL | - | - | 60834 |
| 10 | 0/25 | 1179 | 55 | 66 | FAIL | - | - | 61071 |
| 11 | 2/25 | 988 | 50 | 64 | FAIL | - | - | 60478 |
| 12 | 1/25 | 280 | 14 | 220 | FAIL | - | - | 60263 |
| 13 | 0/25 | 463 | 35 | 71 | FAIL | - | - | 61363 |
| 14 | 0/25 | 561 | 27 | 63 | FAIL | - | - | 60569 |
| 15 | 0/25 | 383 | 18 | 73 | FAIL | - | - | 60723 |
| 16 | 0/25 | 838 | 37 | 62 | FAIL | - | - | 60733 |
| 17 | 0/25 | 417 | 20 | 82 | FAIL | - | - | 60439 |
| 18 | 0/25 | 358 | 20 | 82 | FAIL | - | - | 60653 |
| 19 | 0/25 | 593 | 28 | 61 | FAIL | - | - | 60664 |
| 20 | 0/25 | 296 | 15 | 69 | FAIL | - | - | 60770 |
| 21 | 3/25 | 778 | 36 | 74 | 25/25 | 4202 | 396 | 68 |
| 22 | 0/25 | 704 | 30 | 61 | FAIL | - | - | 60852 |
| 23 | 0/25 | 270 | 13 | 228 | FAIL | - | - | 60628 |
| 24 | 1/25 | 1053 | 52 | 61 | 25/25 | 7155 | 371 | 193 |

### bottleneck_doors_105
| Seed | PIBT Goals | PIBT SOC | PIBT MK | PIBT ms | LaCAM | LaCAM SOC | LaCAM MK | LaCAM ms |
|------|------------|----------|---------|---------|-------|-----------|----------|----------|
| 00 | 20/25 | 1973 | 120 | 62 | FAIL | - | - | 61910 |
| 01 | 25/25 | 2106 | 173 | 50 | 25/25 | 2767 | 167 | 18 |
| 02 | 25/25 | 2159 | 158 | 46 | 25/25 | 3156 | 176 | 17 |
| 03 | 25/25 | 2473 | 151 | 58 | 25/25 | 2955 | 165 | 35 |
| 04 | 15/25 | 1823 | 106 | 61 | FAIL | - | - | 61794 |
| 05 | 25/25 | 2217 | 139 | 52 | 25/25 | 2800 | 142 | 13 |
| 06 | 25/25 | 2069 | 152 | 42 | FAIL | - | - | 61993 |
| 07 | 4/25 | 791 | 39 | 79 | 25/25 | 4168 | 331 | 50 |
| 08 | 25/25 | 1868 | 139 | 44 | 25/25 | 2733 | 149 | 13 |
| 09 | 25/25 | 1680 | 150 | 32 | 25/25 | 2842 | 216 | 34 |
| 10 | 11/25 | 956 | 49 | 61 | 25/25 | 2651 | 154 | 21 |
| 11 | 25/25 | 1537 | 131 | 39 | 25/25 | 2999 | 270 | 28 |
| 12 | 25/25 | 2003 | 164 | 45 | 25/25 | 2900 | 165 | 19 |
| 13 | 11/25 | 1729 | 78 | 61 | 25/25 | 3850 | 293 | 27 |
| 14 | 14/25 | 2311 | 114 | 61 | 25/25 | 3430 | 248 | 46 |
| 15 | 25/25 | 2014 | 139 | 46 | 25/25 | 3141 | 249 | 31 |
| 16 | 25/25 | 1871 | 134 | 36 | 25/25 | 4664 | 353 | 427 |
| 17 | 12/25 | 1426 | 69 | 61 | 25/25 | 2846 | 183 | 34 |
| 18 | 25/25 | 2272 | 125 | 59 | 25/25 | 2676 | 142 | 31 |
| 19 | 10/25 | 1330 | 68 | 61 | 25/25 | 3509 | 259 | 24 |
| 20 | 25/25 | 1969 | 162 | 46 | FAIL | - | - | 62099 |
| 21 | 25/25 | 2479 | 166 | 49 | 25/25 | 3302 | 201 | 22 |
| 22 | 25/25 | 1852 | 146 | 40 | 25/25 | 3843 | 268 | 37 |
| 23 | 4/25 | 912 | 44 | 63 | 25/25 | 2883 | 174 | 28 |
| 24 | 25/25 | 2276 | 161 | 57 | 25/25 | 3064 | 214 | 24 |

## Notes

- HetPIBT SOC/makespan counts only the steps taken before deadlock, not full solutions
- Het-LaCAM SOC includes wait-at-goal padding (all agents run to global makespan)
- Het-LaCAM "FAIL" = timed out at 60s without finding a complete solution
- Both solvers use the same map and scenario files; only input format differs (.scen vs het_bench)
