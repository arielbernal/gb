# HetPIBT Benchmark Results

Generated: 2026-02-24 17:00
Solver: HetPIBT, max_steps=500, goal_lock=True

## Overview

| Map Type | Scenarios | Goals | Goal% | Avg SOC | Avg Makespan | Avg Wait% | Avg Time(ms) | Perfect |
|----------|-----------|-------|-------|---------|--------------|-----------|--------------|----------|
| bottleneck_doors | 1 | 12/12 | 100.0% | 396 | 48 | 24.0% | 2662 | 1/1 |
| corridor_speed | 25 | 551/625 | 88.2% | 1078 | 127 | 10.5% | 2977 | 0/25 |
| intersection | 25 | 339/625 | 54.2% | 657 | 96 | 23.3% | 37082 | 0/25 |
| cooperative_clearing | 25 | 335/625 | 53.6% | 967 | 102 | 12.1% | 29215 | 0/25 |

## Per-Fleet Goal Breakdown


### bottleneck_doors

| Fleet | Reached | Total | % |
|-------|---------|-------|---|
| cs=1 | 3 | 3 | 100.0% |
| cs=3 | 3 | 3 | 100.0% |
| cs=7 | 3 | 3 | 100.0% |
| cs=11 | 3 | 3 | 100.0% |

### corridor_speed

| Fleet | Reached | Total | % |
|-------|---------|-------|---|
| cs=1 | 257 | 300 | 85.7% |
| cs=3 | 121 | 125 | 96.8% |
| cs=7 | 90 | 100 | 90.0% |
| cs=11 | 83 | 100 | 83.0% |

### intersection

| Fleet | Reached | Total | % |
|-------|---------|-------|---|
| cs=1 | 215 | 300 | 71.7% |
| cs=3 | 89 | 125 | 71.2% |
| cs=7 | 28 | 100 | 28.0% |
| cs=11 | 7 | 100 | 7.0% |

### cooperative_clearing

| Fleet | Reached | Total | % |
|-------|---------|-------|---|
| cs=1 | 211 | 300 | 70.3% |
| cs=3 | 89 | 125 | 71.2% |
| cs=7 | 30 | 100 | 30.0% |
| cs=11 | 5 | 100 | 5.0% |

## Failure Analysis


### corridor_speed

Failed scenarios: 25/25

- **corridor_speed_154_00.scen**: deadlock [cs=1(11/12),cs=7(2/4),cs=11(3/4)]
- **corridor_speed_154_01.scen**: deadlock [cs=3(4/5),cs=7(3/4),cs=11(3/4)]
- **corridor_speed_154_02.scen**: deadlock [cs=1(11/12)]
- **corridor_speed_154_03.scen**: deadlock [cs=1(8/12)]
- **corridor_speed_154_04.scen**: deadlock [cs=1(11/12),cs=3(4/5),cs=7(1/4)]
- **corridor_speed_154_05.scen**: deadlock [cs=1(10/12),cs=7(3/4),cs=11(3/4)]
- **corridor_speed_154_06.scen**: deadlock [cs=11(3/4)]
- **corridor_speed_154_07.scen**: deadlock [cs=1(10/12),cs=11(3/4)]
- **corridor_speed_154_08.scen**: deadlock [cs=1(11/12)]
- **corridor_speed_154_09.scen**: deadlock [cs=1(11/12),cs=11(3/4)]
- **corridor_speed_154_10.scen**: deadlock [cs=1(10/12)]
- **corridor_speed_154_11.scen**: deadlock [cs=1(9/12),cs=11(2/4)]
- **corridor_speed_154_12.scen**: deadlock [cs=1(11/12),cs=7(3/4),cs=11(2/4)]
- **corridor_speed_154_13.scen**: deadlock [cs=11(1/4)]
- **corridor_speed_154_14.scen**: deadlock [cs=1(10/12)]
- **corridor_speed_154_15.scen**: deadlock [cs=1(9/12)]
- **corridor_speed_154_16.scen**: deadlock [cs=1(11/12),cs=7(3/4),cs=11(2/4)]
- **corridor_speed_154_17.scen**: deadlock [cs=1(8/12)]
- **corridor_speed_154_18.scen**: deadlock [cs=1(11/12),cs=11(3/4)]
- **corridor_speed_154_19.scen**: deadlock [cs=1(10/12)]
- **corridor_speed_154_20.scen**: deadlock [cs=1(10/12),cs=3(3/5)]
- **corridor_speed_154_21.scen**: deadlock [cs=1(11/12),cs=11(3/4)]
- **corridor_speed_154_22.scen**: deadlock [cs=1(11/12)]
- **corridor_speed_154_23.scen**: deadlock [cs=1(10/12),cs=7(3/4)]
- **corridor_speed_154_24.scen**: deadlock [cs=1(7/12)]

### intersection

Failed scenarios: 25/25

- **intersection_77_00.scen**: deadlock [cs=1(9/12),cs=3(4/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_01.scen**: deadlock [cs=1(9/12),cs=3(4/5),cs=7(1/4),cs=11(2/4)]
- **intersection_77_02.scen**: deadlock [cs=1(8/12),cs=3(4/5),cs=7(1/4),cs=11(1/4)]
- **intersection_77_03.scen**: deadlock [cs=1(10/12),cs=3(4/5),cs=7(0/4),cs=11(0/4)]
- **intersection_77_04.scen**: deadlock [cs=3(2/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_05.scen**: deadlock [cs=1(11/12),cs=3(4/5),cs=11(0/4)]
- **intersection_77_06.scen**: deadlock [cs=1(6/12),cs=3(2/5),cs=7(1/4),cs=11(1/4)]
- **intersection_77_07.scen**: deadlock [cs=1(9/12),cs=7(2/4),cs=11(0/4)]
- **intersection_77_08.scen**: deadlock [cs=1(11/12),cs=7(2/4),cs=11(1/4)]
- **intersection_77_09.scen**: deadlock [cs=1(5/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)]
- **intersection_77_10.scen**: deadlock [cs=1(7/12),cs=3(3/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_11.scen**: deadlock [cs=1(11/12),cs=3(4/5),cs=7(0/4),cs=11(1/4)]
- **intersection_77_12.scen**: deadlock [cs=1(10/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)]
- **intersection_77_13.scen**: deadlock [cs=7(0/4),cs=11(0/4)]
- **intersection_77_14.scen**: deadlock [cs=1(6/12),cs=3(3/5),cs=7(2/4),cs=11(1/4)]
- **intersection_77_15.scen**: deadlock [cs=1(5/12),cs=7(1/4),cs=11(0/4)]
- **intersection_77_16.scen**: deadlock [cs=1(8/12),cs=3(2/5),cs=11(0/4)]
- **intersection_77_17.scen**: deadlock [cs=1(2/12),cs=3(3/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_18.scen**: deadlock [cs=1(8/12),cs=3(4/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_19.scen**: deadlock [cs=1(11/12),cs=7(1/4),cs=11(0/4)]
- **intersection_77_20.scen**: deadlock [cs=1(8/12),cs=3(4/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_21.scen**: deadlock [cs=1(11/12),cs=3(3/5),cs=7(1/4),cs=11(0/4)]
- **intersection_77_22.scen**: deadlock [cs=1(9/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)]
- **intersection_77_23.scen**: deadlock [cs=1(6/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)]
- **intersection_77_24.scen**: deadlock [cs=1(11/12),cs=7(2/4),cs=11(0/4)]

### cooperative_clearing

Failed scenarios: 25/25

- **cooperative_clearing_77_00.scen**: deadlock [cs=1(10/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_01.scen**: deadlock [cs=1(10/12),cs=11(2/4)]
- **cooperative_clearing_77_02.scen**: deadlock [cs=1(11/12),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_03.scen**: deadlock [cs=1(11/12),cs=7(1/4),cs=11(0/4)]
- **cooperative_clearing_77_04.scen**: deadlock [cs=1(10/12),cs=11(1/4)]
- **cooperative_clearing_77_05.scen**: deadlock [cs=3(4/5),cs=7(1/4),cs=11(1/4)]
- **cooperative_clearing_77_06.scen**: deadlock [cs=1(10/12),cs=7(1/4),cs=11(0/4)]
- **cooperative_clearing_77_07.scen**: deadlock [cs=1(11/12),cs=7(3/4),cs=11(0/4)]
- **cooperative_clearing_77_08.scen**: deadlock [cs=1(0/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_09.scen**: deadlock [cs=7(1/4),cs=11(1/4)]
- **cooperative_clearing_77_10.scen**: deadlock [cs=1(10/12),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_11.scen**: deadlock [cs=7(1/4),cs=11(0/4)]
- **cooperative_clearing_77_12.scen**: deadlock [cs=1(11/12),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_13.scen**: deadlock [cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_14.scen**: deadlock [cs=1(1/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_15.scen**: deadlock [cs=1(0/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_16.scen**: deadlock [cs=1(10/12),cs=3(0/5),cs=7(2/4),cs=11(0/4)]
- **cooperative_clearing_77_17.scen**: deadlock [cs=1(0/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_18.scen**: deadlock [cs=1(11/12),cs=7(1/4),cs=11(0/4)]
- **cooperative_clearing_77_19.scen**: deadlock [cs=7(2/4),cs=11(0/4)]
- **cooperative_clearing_77_20.scen**: deadlock [cs=1(0/12),cs=3(0/5),cs=7(1/4),cs=11(0/4)]
- **cooperative_clearing_77_21.scen**: deadlock [cs=11(0/4)]
- **cooperative_clearing_77_22.scen**: deadlock [cs=1(2/12),cs=3(2/5),cs=7(0/4),cs=11(0/4)]
- **cooperative_clearing_77_23.scen**: deadlock [cs=1(9/12),cs=11(0/4)]
- **cooperative_clearing_77_24.scen**: deadlock [cs=7(0/4),cs=11(0/4)]

## Detailed Results


### bottleneck_doors

| Scenario | Goals | SOC | Makespan | Wait% | Time(ms) | cs=1 | cs=3 | cs=7 | cs=11 | Failure |
|----------|-------|-----|----------|-------|----------|--------|--------|--------|--------|----------|
| bottleneck_77 | 12/12 | 396 | 48 | 24% | 2662 | 3/3 | 3/3 | 3/3 | 3/3 |  |

### corridor_speed

| Scenario | Goals | SOC | Makespan | Wait% | Time(ms) | cs=1 | cs=3 | cs=7 | cs=11 | Failure |
|----------|-------|-----|----------|-------|----------|--------|--------|--------|--------|----------|
| corridor_speed_154_00 | 21/25 | 1058 | 103 | 8% | 1436 | 11/12 | 5/5 | 2/4 | 3/4 | deadlock [cs=1(11/12),cs=7(2/4),cs=11(3/4)] |
| corridor_speed_154_01 | 22/25 | 1268 | 133 | 7% | 3891 | 12/12 | 4/5 | 3/4 | 3/4 | deadlock [cs=3(4/5),cs=7(3/4),cs=11(3/4)] |
| corridor_speed_154_02 | 24/25 | 1346 | 154 | 18% | 108 | 11/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(11/12)] |
| corridor_speed_154_03 | 21/25 | 865 | 110 | 8% | 75 | 8/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(8/12)] |
| corridor_speed_154_04 | 20/25 | 1236 | 132 | 8% | 60134 | 11/12 | 4/5 | 1/4 | 4/4 | deadlock [cs=1(11/12),cs=3(4/5),cs=7(1/4)] |
| corridor_speed_154_05 | 21/25 | 1003 | 133 | 7% | 1455 | 10/12 | 5/5 | 3/4 | 3/4 | deadlock [cs=1(10/12),cs=7(3/4),cs=11(3/4)] |
| corridor_speed_154_06 | 24/25 | 1331 | 133 | 12% | 278 | 12/12 | 5/5 | 4/4 | 3/4 | deadlock [cs=11(3/4)] |
| corridor_speed_154_07 | 22/25 | 975 | 124 | 9% | 258 | 10/12 | 5/5 | 4/4 | 3/4 | deadlock [cs=1(10/12),cs=11(3/4)] |
| corridor_speed_154_08 | 24/25 | 1163 | 134 | 5% | 35 | 11/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(11/12)] |
| corridor_speed_154_09 | 23/25 | 1116 | 117 | 11% | 195 | 11/12 | 5/5 | 4/4 | 3/4 | deadlock [cs=1(11/12),cs=11(3/4)] |
| corridor_speed_154_10 | 23/25 | 1021 | 125 | 7% | 34 | 10/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(10/12)] |
| corridor_speed_154_11 | 20/25 | 985 | 146 | 13% | 1660 | 9/12 | 5/5 | 4/4 | 2/4 | deadlock [cs=1(9/12),cs=11(2/4)] |
| corridor_speed_154_12 | 21/25 | 1066 | 110 | 7% | 1533 | 11/12 | 5/5 | 3/4 | 2/4 | deadlock [cs=1(11/12),cs=7(3/4),cs=11(2/4)] |
| corridor_speed_154_13 | 22/25 | 1116 | 130 | 8% | 895 | 12/12 | 5/5 | 4/4 | 1/4 | deadlock [cs=11(1/4)] |
| corridor_speed_154_14 | 23/25 | 1223 | 111 | 19% | 177 | 10/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(10/12)] |
| corridor_speed_154_15 | 22/25 | 870 | 99 | 10% | 571 | 9/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(9/12)] |
| corridor_speed_154_16 | 21/25 | 1106 | 121 | 10% | 540 | 11/12 | 5/5 | 3/4 | 2/4 | deadlock [cs=1(11/12),cs=7(3/4),cs=11(2/4)] |
| corridor_speed_154_17 | 21/25 | 987 | 136 | 9% | 50 | 8/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(8/12)] |
| corridor_speed_154_18 | 23/25 | 1279 | 177 | 11% | 306 | 11/12 | 5/5 | 4/4 | 3/4 | deadlock [cs=1(11/12),cs=11(3/4)] |
| corridor_speed_154_19 | 23/25 | 1042 | 138 | 16% | 94 | 10/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(10/12)] |
| corridor_speed_154_20 | 21/25 | 695 | 91 | 14% | 263 | 10/12 | 3/5 | 4/4 | 4/4 | deadlock [cs=1(10/12),cs=3(3/5)] |
| corridor_speed_154_21 | 23/25 | 1148 | 124 | 10% | 227 | 11/12 | 5/5 | 4/4 | 3/4 | deadlock [cs=1(11/12),cs=11(3/4)] |
| corridor_speed_154_22 | 24/25 | 1045 | 140 | 11% | 55 | 11/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(11/12)] |
| corridor_speed_154_23 | 22/25 | 1225 | 144 | 11% | 89 | 10/12 | 5/5 | 3/4 | 4/4 | deadlock [cs=1(10/12),cs=7(3/4)] |
| corridor_speed_154_24 | 20/25 | 777 | 114 | 12% | 69 | 7/12 | 5/5 | 4/4 | 4/4 | deadlock [cs=1(7/12)] |

### intersection

| Scenario | Goals | SOC | Makespan | Wait% | Time(ms) | cs=1 | cs=3 | cs=7 | cs=11 | Failure |
|----------|-------|-----|----------|-------|----------|--------|--------|--------|--------|----------|
| intersection_77_00 | 14/25 | 540 | 59 | 24% | 60054 | 9/12 | 4/5 | 1/4 | 0/4 | deadlock [cs=1(9/12),cs=3(4/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_01 | 16/25 | 660 | 96 | 30% | 6267 | 9/12 | 4/5 | 1/4 | 2/4 | deadlock [cs=1(9/12),cs=3(4/5),cs=7(1/4),cs=11(2/4)] |
| intersection_77_02 | 14/25 | 1997 | 301 | 30% | 60043 | 8/12 | 4/5 | 1/4 | 1/4 | deadlock [cs=1(8/12),cs=3(4/5),cs=7(1/4),cs=11(1/4)] |
| intersection_77_03 | 14/25 | 489 | 83 | 14% | 60125 | 10/12 | 4/5 | 0/4 | 0/4 | deadlock [cs=1(10/12),cs=3(4/5),cs=7(0/4),cs=11(0/4)] |
| intersection_77_04 | 15/25 | 648 | 87 | 18% | 36660 | 12/12 | 2/5 | 1/4 | 0/4 | deadlock [cs=3(2/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_05 | 19/25 | 876 | 73 | 28% | 6743 | 11/12 | 4/5 | 4/4 | 0/4 | deadlock [cs=1(11/12),cs=3(4/5),cs=11(0/4)] |
| intersection_77_06 | 10/25 | 419 | 76 | 23% | 60180 | 6/12 | 2/5 | 1/4 | 1/4 | deadlock [cs=1(6/12),cs=3(2/5),cs=7(1/4),cs=11(1/4)] |
| intersection_77_07 | 16/25 | 538 | 77 | 21% | 11061 | 9/12 | 5/5 | 2/4 | 0/4 | deadlock [cs=1(9/12),cs=7(2/4),cs=11(0/4)] |
| intersection_77_08 | 19/25 | 946 | 93 | 28% | 55353 | 11/12 | 5/5 | 2/4 | 1/4 | deadlock [cs=1(11/12),cs=7(2/4),cs=11(1/4)] |
| intersection_77_09 | 5/25 | 115 | 35 | 5% | 66079 | 5/12 | 0/5 | 0/4 | 0/4 | deadlock [cs=1(5/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)] |
| intersection_77_10 | 11/25 | 364 | 52 | 16% | 13397 | 7/12 | 3/5 | 1/4 | 0/4 | deadlock [cs=1(7/12),cs=3(3/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_11 | 16/25 | 788 | 137 | 22% | 19742 | 11/12 | 4/5 | 0/4 | 1/4 | deadlock [cs=1(11/12),cs=3(4/5),cs=7(0/4),cs=11(1/4)] |
| intersection_77_12 | 13/25 | 404 | 59 | 15% | 63431 | 10/12 | 3/5 | 0/4 | 0/4 | deadlock [cs=1(10/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)] |
| intersection_77_13 | 17/25 | 1078 | 193 | 15% | 23693 | 12/12 | 5/5 | 0/4 | 0/4 | deadlock [cs=7(0/4),cs=11(0/4)] |
| intersection_77_14 | 12/25 | 448 | 80 | 29% | 8110 | 6/12 | 3/5 | 2/4 | 1/4 | deadlock [cs=1(6/12),cs=3(3/5),cs=7(2/4),cs=11(1/4)] |
| intersection_77_15 | 11/25 | 471 | 69 | 26% | 26675 | 5/12 | 5/5 | 1/4 | 0/4 | deadlock [cs=1(5/12),cs=7(1/4),cs=11(0/4)] |
| intersection_77_16 | 14/25 | 609 | 84 | 32% | 33018 | 8/12 | 2/5 | 4/4 | 0/4 | deadlock [cs=1(8/12),cs=3(2/5),cs=11(0/4)] |
| intersection_77_17 | 6/25 | 197 | 45 | 35% | 60733 | 2/12 | 3/5 | 1/4 | 0/4 | deadlock [cs=1(2/12),cs=3(3/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_18 | 13/25 | 770 | 149 | 22% | 28722 | 8/12 | 4/5 | 1/4 | 0/4 | deadlock [cs=1(8/12),cs=3(4/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_19 | 17/25 | 845 | 107 | 24% | 17964 | 11/12 | 5/5 | 1/4 | 0/4 | deadlock [cs=1(11/12),cs=7(1/4),cs=11(0/4)] |
| intersection_77_20 | 13/25 | 570 | 112 | 25% | 60273 | 8/12 | 4/5 | 1/4 | 0/4 | deadlock [cs=1(8/12),cs=3(4/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_21 | 15/25 | 927 | 110 | 32% | 52969 | 11/12 | 3/5 | 1/4 | 0/4 | deadlock [cs=1(11/12),cs=3(3/5),cs=7(1/4),cs=11(0/4)] |
| intersection_77_22 | 12/25 | 425 | 65 | 17% | 13621 | 9/12 | 3/5 | 0/4 | 0/4 | deadlock [cs=1(9/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)] |
| intersection_77_23 | 9/25 | 402 | 71 | 22% | 60045 | 6/12 | 3/5 | 0/4 | 0/4 | deadlock [cs=1(6/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)] |
| intersection_77_24 | 18/25 | 890 | 96 | 30% | 22090 | 11/12 | 5/5 | 2/4 | 0/4 | deadlock [cs=1(11/12),cs=7(2/4),cs=11(0/4)] |

### cooperative_clearing

| Scenario | Goals | SOC | Makespan | Wait% | Time(ms) | cs=1 | cs=3 | cs=7 | cs=11 | Failure |
|----------|-------|-----|----------|-------|----------|--------|--------|--------|--------|----------|
| cooperative_clearing_77_00 | 13/25 | 1333 | 129 | 13% | 49626 | 10/12 | 3/5 | 0/4 | 0/4 | deadlock [cs=1(10/12),cs=3(3/5),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_01 | 21/25 | 1698 | 183 | 21% | 2370 | 10/12 | 5/5 | 4/4 | 2/4 | deadlock [cs=1(10/12),cs=11(2/4)] |
| cooperative_clearing_77_02 | 16/25 | 1153 | 106 | 12% | 60865 | 11/12 | 5/5 | 0/4 | 0/4 | deadlock [cs=1(11/12),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_03 | 17/25 | 1172 | 105 | 16% | 8838 | 11/12 | 5/5 | 1/4 | 0/4 | deadlock [cs=1(11/12),cs=7(1/4),cs=11(0/4)] |
| cooperative_clearing_77_04 | 20/25 | 1353 | 120 | 22% | 3967 | 10/12 | 5/5 | 4/4 | 1/4 | deadlock [cs=1(10/12),cs=11(1/4)] |
| cooperative_clearing_77_05 | 18/25 | 1202 | 90 | 10% | 1900 | 12/12 | 4/5 | 1/4 | 1/4 | deadlock [cs=3(4/5),cs=7(1/4),cs=11(1/4)] |
| cooperative_clearing_77_06 | 16/25 | 1330 | 118 | 27% | 60142 | 10/12 | 5/5 | 1/4 | 0/4 | deadlock [cs=1(10/12),cs=7(1/4),cs=11(0/4)] |
| cooperative_clearing_77_07 | 19/25 | 1456 | 139 | 18% | 4318 | 11/12 | 5/5 | 3/4 | 0/4 | deadlock [cs=1(11/12),cs=7(3/4),cs=11(0/4)] |
| cooperative_clearing_77_08 | 0/25 | 0 | 0 | 0% | 62380 | 0/12 | 0/5 | 0/4 | 0/4 | deadlock [cs=1(0/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_09 | 19/25 | 1276 | 114 | 19% | 9177 | 12/12 | 5/5 | 1/4 | 1/4 | deadlock [cs=7(1/4),cs=11(1/4)] |
| cooperative_clearing_77_10 | 15/25 | 864 | 116 | 5% | 25065 | 10/12 | 5/5 | 0/4 | 0/4 | deadlock [cs=1(10/12),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_11 | 18/25 | 1291 | 120 | 14% | 7042 | 12/12 | 5/5 | 1/4 | 0/4 | deadlock [cs=7(1/4),cs=11(0/4)] |
| cooperative_clearing_77_12 | 16/25 | 1234 | 121 | 16% | 60145 | 11/12 | 5/5 | 0/4 | 0/4 | deadlock [cs=1(11/12),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_13 | 17/25 | 1225 | 173 | 8% | 7022 | 12/12 | 5/5 | 0/4 | 0/4 | deadlock [cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_14 | 1/25 | 35 | 35 | 3% | 60786 | 1/12 | 0/5 | 0/4 | 0/4 | deadlock [cs=1(1/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_15 | 0/25 | 0 | 0 | 0% | 60187 | 0/12 | 0/5 | 0/4 | 0/4 | deadlock [cs=1(0/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_16 | 12/25 | 774 | 115 | 6% | 2147 | 10/12 | 0/5 | 2/4 | 0/4 | deadlock [cs=1(10/12),cs=3(0/5),cs=7(2/4),cs=11(0/4)] |
| cooperative_clearing_77_17 | 0/25 | 0 | 0 | 0% | 61746 | 0/12 | 0/5 | 0/4 | 0/4 | deadlock [cs=1(0/12),cs=3(0/5),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_18 | 17/25 | 1386 | 137 | 12% | 39304 | 11/12 | 5/5 | 1/4 | 0/4 | deadlock [cs=1(11/12),cs=7(1/4),cs=11(0/4)] |
| cooperative_clearing_77_19 | 19/25 | 1396 | 138 | 10% | 6122 | 12/12 | 5/5 | 2/4 | 0/4 | deadlock [cs=7(2/4),cs=11(0/4)] |
| cooperative_clearing_77_20 | 1/25 | 7 | 7 | 14% | 12521 | 0/12 | 0/5 | 1/4 | 0/4 | deadlock [cs=1(0/12),cs=3(0/5),cs=7(1/4),cs=11(0/4)] |
| cooperative_clearing_77_21 | 21/25 | 1443 | 131 | 9% | 1748 | 12/12 | 5/5 | 4/4 | 0/4 | deadlock [cs=11(0/4)] |
| cooperative_clearing_77_22 | 4/25 | 210 | 75 | 5% | 63283 | 2/12 | 2/5 | 0/4 | 0/4 | deadlock [cs=1(2/12),cs=3(2/5),cs=7(0/4),cs=11(0/4)] |
| cooperative_clearing_77_23 | 18/25 | 1226 | 139 | 32% | 52459 | 9/12 | 5/5 | 4/4 | 0/4 | deadlock [cs=1(9/12),cs=11(0/4)] |
| cooperative_clearing_77_24 | 17/25 | 1114 | 137 | 10% | 7216 | 12/12 | 5/5 | 0/4 | 0/4 | deadlock [cs=7(0/4),cs=11(0/4)] |
