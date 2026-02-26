# Bottleneck Scaling Results — Feb 25, 2026

## 1. Room-64 Scaling (HetPIBT only)

Map: room-64-64-8 (640x640 scaled, MAP_SCALE=10)
Fleet mix: cs=1 (50%), cs=6 (30%), cs=11 (20%)
Agent counts: 15, 50, 100, 150, 200 (10 seeds each)
Max timesteps: 500, Goal lock: enabled

### Summary Table

| Agents | Placed | Goal% | cs1% | cs6% | cs11% | Avg SOC | Avg Makespan | Avg Wait% | Avg ms | Stuck | NoMove |
|--------|--------|-------|------|------|-------|---------|--------------|-----------|--------|-------|--------|
|     15 |    15 | 98.7% | 100% |  95% | 100% |    5115 |         1017 |      5.5% |    403 |   0.2 |    0.0 |
|     50 |    50 | 93.8% |  97% |  87% |  97% |   15590 |         1937 |      8.4% |  19116 |   3.1 |    0.0 |
|    100 |    98 | 71.9% |  69% |  75% |  77% |   21346 |         1275 |     10.1% |  84275 |  27.3 |    0.2 |
|    150 |   138 | 35.2% |  28% |  41% |  53% |    8336 |          391 |     21.2% | 108460 |  75.4 |    0.5 |
|    200 |   178 | 22.5% |  17% |  22% |  53% |    5476 |          267 |     25.9% |  96353 | 102.3 |    0.2 |

### Breaking Points

- Below 90% success: first at N=100 (71.9%)
- Below 50% success: first at N=150 (35.2%)

### Per-Fleet Stuck Agents

| Agents | Stuck cs=1 | Stuck cs=6 | Stuck cs=11 |
|--------|------------|------------|-------------|
|     15 |        0.0 |        0.2 |         0.0 |
|     50 |        0.8 |        2.0 |         0.3 |
|    100 |       15.7 |        7.4 |         4.2 |
|    150 |       46.6 |       22.2 |         6.6 |
|    200 |       62.9 |       34.5 |         4.9 |

Observation: Small agents (cs=1) fail first under congestion; large agents (cs=11) remain most resilient even at N=200 (52.8% success).

---

## 2. Corridor Speed (HetPIBT, 154x154 map, 25 scenarios, 25 agents each)

Fleet distribution: cs=1:12, cs=3:5, cs=7:4, cs=11:4
Max timesteps: 500, Goal lock: enabled

### Aggregate

| Metric | Value |
|--------|-------|
| Total goals | 551/625 (88.2%) |
| Per-fleet cs=1 | 257/300 (85.7%) |
| Per-fleet cs=3 | 121/125 (96.8%) |
| Per-fleet cs=7 | 90/100 (90.0%) |
| Per-fleet cs=11 | 83/100 (83.0%) |
| Avg SOC | 1078 |
| Avg Makespan | 127 |
| Avg Time(ms) | 2977 |

### Per-Scenario

| Scenario | Goals | SOC | Makespan | Time(ms) |
|----------|-------|-----|----------|----------|
| corridor_speed_154_00 | 21/25 | 1058 | 103 | 1436 |
| corridor_speed_154_01 | 22/25 | 1268 | 133 | 3891 |
| corridor_speed_154_02 | 24/25 | 1346 | 154 | 108 |
| corridor_speed_154_03 | 21/25 | 865 | 110 | 75 |
| corridor_speed_154_04 | 20/25 | 1236 | 132 | 60134 |
| corridor_speed_154_05 | 21/25 | 1003 | 133 | 1455 |
| corridor_speed_154_06 | 24/25 | 1331 | 133 | 278 |
| corridor_speed_154_07 | 22/25 | 975 | 124 | 258 |
| corridor_speed_154_08 | 24/25 | 1163 | 134 | 35 |
| corridor_speed_154_09 | 23/25 | 1116 | 117 | 195 |
| corridor_speed_154_10 | 23/25 | 1021 | 125 | 34 |
| corridor_speed_154_11 | 20/25 | 985 | 146 | 1660 |
| corridor_speed_154_12 | 21/25 | 1066 | 110 | 1533 |
| corridor_speed_154_13 | 22/25 | 1116 | 130 | 895 |
| corridor_speed_154_14 | 23/25 | 1223 | 111 | 177 |
| corridor_speed_154_15 | 22/25 | 870 | 99 | 571 |
| corridor_speed_154_16 | 21/25 | 1106 | 121 | 540 |
| corridor_speed_154_17 | 21/25 | 987 | 136 | 50 |
| corridor_speed_154_18 | 23/25 | 1279 | 177 | 306 |
| corridor_speed_154_19 | 23/25 | 1042 | 138 | 94 |
| corridor_speed_154_20 | 21/25 | 695 | 91 | 263 |
| corridor_speed_154_21 | 23/25 | 1148 | 124 | 227 |
| corridor_speed_154_22 | 24/25 | 1045 | 140 | 55 |
| corridor_speed_154_23 | 22/25 | 1225 | 144 | 89 |
| corridor_speed_154_24 | 20/25 | 777 | 114 | 69 |

---

## 3. Intersection (HetPIBT, 77x77 map, 25 scenarios, 25 agents each)

Fleet distribution: cs=1:12, cs=3:5, cs=7:4, cs=11:4

### Aggregate

| Metric | Value |
|--------|-------|
| Total goals | 339/625 (54.2%) |
| Per-fleet cs=1 | 215/300 (71.7%) |
| Per-fleet cs=3 | 89/125 (71.2%) |
| Per-fleet cs=7 | 28/100 (28.0%) |
| Per-fleet cs=11 | 7/100 (7.0%) |
| Avg SOC | 657 |
| Avg Makespan | 96 |
| Avg Time(ms) | 37082 |

### Per-Scenario

| Scenario | Goals | SOC | Makespan | Time(ms) |
|----------|-------|-----|----------|----------|
| intersection_77_00 | 14/25 | 540 | 59 | 60054 |
| intersection_77_01 | 16/25 | 660 | 96 | 6267 |
| intersection_77_02 | 14/25 | 1997 | 301 | 60043 |
| intersection_77_03 | 14/25 | 489 | 83 | 60125 |
| intersection_77_04 | 15/25 | 648 | 87 | 36660 |
| intersection_77_05 | 19/25 | 876 | 73 | 6743 |
| intersection_77_06 | 10/25 | 419 | 76 | 60180 |
| intersection_77_07 | 16/25 | 538 | 77 | 11061 |
| intersection_77_08 | 19/25 | 946 | 93 | 55353 |
| intersection_77_09 | 5/25 | 115 | 35 | 66079 |
| intersection_77_10 | 11/25 | 364 | 52 | 13397 |
| intersection_77_11 | 16/25 | 788 | 137 | 19742 |
| intersection_77_12 | 13/25 | 404 | 59 | 63431 |
| intersection_77_13 | 17/25 | 1078 | 193 | 23693 |
| intersection_77_14 | 12/25 | 448 | 80 | 8110 |
| intersection_77_15 | 11/25 | 471 | 69 | 26675 |
| intersection_77_16 | 14/25 | 609 | 84 | 33018 |
| intersection_77_17 | 6/25 | 197 | 45 | 60733 |
| intersection_77_18 | 13/25 | 770 | 149 | 28722 |
| intersection_77_19 | 17/25 | 845 | 107 | 17964 |
| intersection_77_20 | 13/25 | 570 | 112 | 60273 |
| intersection_77_21 | 15/25 | 927 | 110 | 52969 |
| intersection_77_22 | 12/25 | 425 | 65 | 13621 |
| intersection_77_23 | 9/25 | 402 | 71 | 60045 |
| intersection_77_24 | 18/25 | 890 | 96 | 22090 |

---

## 4. Cooperative Clearing (HetPIBT, 77x77 map, 25 scenarios, 25 agents each)

Fleet distribution: cs=1:12, cs=3:5, cs=7:4, cs=11:4

### Aggregate

| Metric | Value |
|--------|-------|
| Total goals | 335/625 (53.6%) |
| Per-fleet cs=1 | 211/300 (70.3%) |
| Per-fleet cs=3 | 89/125 (71.2%) |
| Per-fleet cs=7 | 30/100 (30.0%) |
| Per-fleet cs=11 | 5/100 (5.0%) |
| Avg SOC | 967 |
| Avg Makespan | 102 |
| Avg Time(ms) | 29215 |

### Per-Scenario

| Scenario | Goals | SOC | Makespan | Time(ms) |
|----------|-------|-----|----------|----------|
| cooperative_clearing_77_00 | 13/25 | 1333 | 129 | 49626 |
| cooperative_clearing_77_01 | 21/25 | 1698 | 183 | 2370 |
| cooperative_clearing_77_02 | 16/25 | 1153 | 106 | 60865 |
| cooperative_clearing_77_03 | 17/25 | 1172 | 105 | 8838 |
| cooperative_clearing_77_04 | 20/25 | 1353 | 120 | 3967 |
| cooperative_clearing_77_05 | 18/25 | 1202 | 90 | 1900 |
| cooperative_clearing_77_06 | 16/25 | 1330 | 118 | 60142 |
| cooperative_clearing_77_07 | 19/25 | 1456 | 139 | 4318 |
| cooperative_clearing_77_08 | 0/25 | 0 | 0 | 62380 |
| cooperative_clearing_77_09 | 19/25 | 1276 | 114 | 9177 |
| cooperative_clearing_77_10 | 15/25 | 864 | 116 | 25065 |
| cooperative_clearing_77_11 | 18/25 | 1291 | 120 | 7042 |
| cooperative_clearing_77_12 | 16/25 | 1234 | 121 | 60145 |
| cooperative_clearing_77_13 | 17/25 | 1225 | 173 | 7022 |
| cooperative_clearing_77_14 | 1/25 | 35 | 35 | 60786 |
| cooperative_clearing_77_15 | 0/25 | 0 | 0 | 60187 |
| cooperative_clearing_77_16 | 12/25 | 774 | 115 | 2147 |
| cooperative_clearing_77_17 | 0/25 | 0 | 0 | 61746 |
| cooperative_clearing_77_18 | 17/25 | 1386 | 137 | 39304 |
| cooperative_clearing_77_19 | 19/25 | 1396 | 138 | 6122 |
| cooperative_clearing_77_20 | 1/25 | 7 | 7 | 12521 |
| cooperative_clearing_77_21 | 21/25 | 1443 | 131 | 1748 |
| cooperative_clearing_77_22 | 4/25 | 210 | 75 | 63283 |
| cooperative_clearing_77_23 | 18/25 | 1226 | 139 | 52459 |
| cooperative_clearing_77_24 | 17/25 | 1114 | 137 | 7216 |

---

## 5. Bottleneck Doors (HetPIBT vs het_lacam, 77x77 map, 1 scenario, 12 agents)

| Solver | Goals | SOC | Makespan | Time(ms) |
|--------|-------|-----|----------|----------|
| hetpibt | 12/12 (100%) | 396 | 48 | 2662 |
| het_lacam | FAILED (invalid instance) | — | — | — |
