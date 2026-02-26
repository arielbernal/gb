# HetPIBT Scaling Experiment — All 4 Maps
**Date:** 2025-02-25
**Solver:** hetpibt (no --swap-xy)
**Timeout:** 60s
**Agent counts:** 5, 10, 15, 20, 25
**Seeds:** 00-04 (5 per configuration, 50 runs per map, 200 total)
**Fleet config:** cs=1 v=1, cs=3 v=1, cs=5 v=2, cs=7 v=3

## 4-Map Comparison (avg goal%)

| agents | bottleneck_doors | intersection | corridor_speed | cooperative_clearing |
|--------|-----------------|-------------|----------------|---------------------|
| 5      | **100.0%**      | 76.0%       | 12.0%          | 28.0%               |
| 10     | **100.0%**      | 50.0%       | 12.0%          | 16.0%               |
| 15     | **98.7%**       | 46.7%       | 16.0%          | 14.7%               |
| 20     | 71.0%           | 38.0%       | 18.0%          | 13.0%               |
| 25     | 84.8%           | 33.6%       | 8.8%           | 2.4%                |

## Difficulty Ranking (easiest to hardest)

1. **bottleneck_doors** — Multiple doors provide routing alternatives. 100% at n<=10, still 85% at n=25.
2. **intersection** — Open center but 4-way conflict. Degrades steadily 76%→34%.
3. **corridor_speed** — Head-on traffic in narrow corridors. Flat ~12-18%, collapses at n=25.
4. **cooperative_clearing** — Single narrow passage with bidirectional traffic. Nearly impossible: 28%→2%.

---

## bottleneck_doors_105

| agents | avg_goal% | seeds_100% | avg_SOC | avg_makespan | avg_time_ms |
|--------|-----------|------------|---------|--------------|-------------|
| 5      | 100.0%    | 5/5        | 128     | 36           | 6           |
| 10     | 100.0%    | 5/5        | 327     | 46           | 17          |
| 15     | 98.7%     | 4/5        | 872     | 176          | 34          |
| 20     | 71.0%     | 3/5        | 1088    | 104          | 43          |
| 25     | 84.8%     | 3/5        | 1996    | 132          | 56          |

**Trend:** Perfect up to 10 agents. Drops at 20 when door contention increases, but recovers slightly at 25 (more cs=1 agents that can use the narrow door). The 4-door design gives PIBT enough routing alternatives to avoid deadlock in most cases.

## intersection_105

| agents | avg_goal% | seeds_100% | avg_SOC | avg_makespan | avg_time_ms |
|--------|-----------|------------|---------|--------------|-------------|
| 5      | 76.0%     | 2/5        | 60      | 15           | 40          |
| 10     | 50.0%     | 0/5        | 264     | 41           | 63          |
| 15     | 46.7%     | 0/5        | 386     | 40           | 76          |
| 20     | 38.0%     | 0/5        | 754     | 46           | 64          |
| 25     | 33.6%     | 0/5        | 847     | 45           | 81          |

**Trend:** Steady decline from 76%→34%. The central intersection creates persistent deadlocks as agents from different corridors compete for the shared space. Never achieves 100% at n>=10.

## corridor_speed_105

| agents | avg_goal% | seeds_100% | avg_SOC | avg_makespan | avg_time_ms |
|--------|-----------|------------|---------|--------------|-------------|
| 5      | 12.0%     | 0/5        | 94      | 30           | 70          |
| 10     | 12.0%     | 0/5        | 207     | 27           | 104         |
| 15     | 16.0%     | 0/5        | 420     | 34           | 106         |
| 20     | 18.0%     | 0/5        | 707     | 40           | 99          |
| 25     | 8.8%      | 0/5        | 846     | 39           | 107         |

**Trend:** Consistently terrible — never above 18%, never 100% even at 5 agents. Head-on traffic in narrow corridors is fundamentally incompatible with PIBT's greedy prioritization. Agents block each other and neither can yield.

## cooperative_clearing_105

| agents | avg_goal% | seeds_100% | avg_SOC | avg_makespan | avg_time_ms |
|--------|-----------|------------|---------|--------------|-------------|
| 5      | 28.0%     | 1/5        | 83      | 21           | 54          |
| 10     | 16.0%     | 0/5        | 232     | 30           | 75          |
| 15     | 14.7%     | 0/5        | 427     | 36           | 90          |
| 20     | 13.0%     | 0/5        | 634     | 39           | 103         |
| 25     | 2.4%      | 0/5        | 565     | 25           | 106         |

**Trend:** Already poor at 5 agents (28%), nearly zero at 25 (2.4%). The single narrow passage (7 cells wide, 21 long) is an extreme bottleneck. Bidirectional traffic deadlocks PIBT completely.

---

## Per-Run Data

### bottleneck_doors_105
| seed | n=5 | n=10 | n=15 | n=20 | n=25 |
|------|-----|------|------|------|------|
| 00 | 5/5 (100%) | 10/10 (100%) | 15/15 (100%) | 1/20 (5%) | 20/25 (80%) |
| 01 | 5/5 (100%) | 10/10 (100%) | 15/15 (100%) | 10/20 (50%) | 25/25 (100%) |
| 02 | 5/5 (100%) | 10/10 (100%) | 15/15 (100%) | 20/20 (100%) | 25/25 (100%) |
| 03 | 5/5 (100%) | 10/10 (100%) | 14/15 (93%) | 20/20 (100%) | 25/25 (100%) |
| 04 | 5/5 (100%) | 10/10 (100%) | 15/15 (100%) | 20/20 (100%) | 11/25 (44%) |

### intersection_105
| seed | n=5 | n=10 | n=15 | n=20 | n=25 |
|------|-----|------|------|------|------|
| 00 | 3/5 (60%) | 6/10 (60%) | 13/15 (87%) | 3/20 (15%) | 5/25 (20%) |
| 01 | 3/5 (60%) | 3/10 (30%) | 4/15 (27%) | 5/20 (25%) | 10/25 (40%) |
| 02 | 5/5 (100%) | 8/10 (80%) | 3/15 (20%) | 11/20 (55%) | 17/25 (68%) |
| 03 | 5/5 (100%) | 2/10 (20%) | 5/15 (33%) | 5/20 (25%) | 7/25 (28%) |
| 04 | 3/5 (60%) | 6/10 (60%) | 10/15 (67%) | 14/20 (70%) | 3/25 (12%) |

### corridor_speed_105
| seed | n=5 | n=10 | n=15 | n=20 | n=25 |
|------|-----|------|------|------|------|
| 00 | 0/5 (0%) | 2/10 (20%) | 2/15 (13%) | 8/20 (40%) | 8/25 (32%) |
| 01 | 2/5 (40%) | 1/10 (10%) | 1/15 (7%) | 2/20 (10%) | 1/25 (4%) |
| 02 | 1/5 (20%) | 2/10 (20%) | 8/15 (53%) | 8/20 (40%) | 1/25 (4%) |
| 03 | 0/5 (0%) | 1/10 (10%) | 1/15 (7%) | 0/20 (0%) | 0/25 (0%) |
| 04 | 0/5 (0%) | 0/10 (0%) | 0/15 (0%) | 0/20 (0%) | 1/25 (4%) |

### cooperative_clearing_105
| seed | n=5 | n=10 | n=15 | n=20 | n=25 |
|------|-----|------|------|------|------|
| 00 | 0/5 (0%) | 0/10 (0%) | 0/15 (0%) | 0/20 (0%) | 0/25 (0%) |
| 01 | 1/5 (20%) | 0/10 (0%) | 0/15 (0%) | 0/20 (0%) | 0/25 (0%) |
| 02 | 5/5 (100%) | 0/10 (0%) | 11/15 (73%) | 12/20 (60%) | 2/25 (8%) |
| 03 | 1/5 (20%) | 7/10 (70%) | 0/15 (0%) | 0/20 (0%) | 0/25 (0%) |
| 04 | 0/5 (0%) | 1/10 (10%) | 0/15 (0%) | 1/20 (5%) | 1/25 (4%) |
