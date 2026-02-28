# Full Post-BFS Benchmark Analysis
Date: Feb 27, 2026
Total scenarios: 190 post-BFS, 190 pre-BFS, 190 hetpibt

## A. Solve Rate: het_rt_lacam (post-BFS) vs hetpibt

### 105-series categories

| Category | Agents | lacam solved | pibt solved | lacam % | pibt % |
|----------|--------|-------------|-------------|---------|--------|
| bottleneck_doors | n5 | 5/5 | 5/5 | 100% | 100% |
| bottleneck_doors | n10 | 4/5 | 5/5 | 80% | 100% |
| bottleneck_doors | n15 | 3/5 | 4/5 | 60% | 80% |
| bottleneck_doors | n20 | 4/5 | 2/5 | 80% | 40% |
| bottleneck_doors | n25 | 19/25 | 8/25 | 76% | 32% |
| corridor_speed | n5 | 5/5 | 5/5 | 100% | 100% |
| corridor_speed | n10 | 4/5 | 5/5 | 80% | 100% |
| corridor_speed | n15 | 2/5 | 4/5 | 40% | 80% |
| corridor_speed | n20 | 0/5 | 4/5 | 0% | 80% |
| corridor_speed | n25 | 12/25 | 16/25 | 48% | 64% |
| intersection | n5 | 5/5 | 5/5 | 100% | 100% |
| intersection | n10 | 3/5 | 5/5 | 60% | 100% |
| intersection | n15 | 0/5 | 1/5 | 0% | 20% |
| intersection | n20 | 0/5 | 1/5 | 0% | 20% |
| intersection | n25 | 0/25 | 3/25 | 0% | 12% |
| cooperative_clearing | n5 | 5/5 | 5/5 | 100% | 100% |
| cooperative_clearing | n10 | 5/5 | 5/5 | 100% | 100% |
| cooperative_clearing | n15 | 3/5 | 5/5 | 60% | 100% |
| cooperative_clearing | n20 | 2/5 | 4/5 | 40% | 80% |
| cooperative_clearing | n25 | 5/25 | 19/25 | 20% | 76% |

### Category totals (105-series)

| Category | lacam solved | pibt solved | lacam % | pibt % |
|----------|-------------|-------------|---------|--------|
| bottleneck_doors | 35/45 | 24/45 | 78% | 53% |
| corridor_speed | 23/45 | 34/45 | 51% | 76% |
| intersection | 8/45 | 15/45 | 18% | 33% |
| cooperative_clearing | 20/45 | 38/45 | 44% | 84% |
| **105-series total** | **86/180** | **111/180** | **48%** | **62%** |

### het_bench (room120)

| Solver | Solved | Total | % |
|--------|--------|-------|---|
| het_rt_lacam | 8 | 10 | 80% |
| hetpibt | 9 | 10 | 90% |

**Grand total: het_rt_lacam 94/190 (49%), hetpibt 120/190 (63%)**

## B. Pre-BFS vs Post-BFS Comparison

| Category | Pre-BFS solved | Post-BFS solved | Delta | Pre % | Post % |
|----------|---------------|----------------|-------|-------|--------|
| bottleneck_doors | 34/45 | 35/45 | +1 | 76% | 78% |
| corridor_speed | 21/45 | 23/45 | +2 | 47% | 51% |
| intersection | 6/45 | 8/45 | +2 | 13% | 18% |
| cooperative_clearing | 16/45 | 20/45 | +4 | 36% | 44% |
| het_bench | 8/10 | 8/10 | +0 | 80% | 80% |
| **TOTAL** | **85/190** | **94/190** | **+9** | **45%** | **49%** |

## C. SOC Comparison on Mutually-Solved Scenarios

### het_rt_lacam (post-BFS) vs hetpibt SOC ratios

| Category | Mutual solves | Mean SOC ratio | Median SOC ratio | Mean lacam SOC | Mean pibt SOC |
|----------|--------------|----------------|-----------------|----------------|---------------|
| bottleneck_doors | 18 | 3.02x | 3.00x | 1695 | 611 |
| corridor_speed | 15 | 24.37x | 20.31x | 6558 | 290 |
| intersection | 8 | 4.85x | 3.01x | 168 | 56 |
| cooperative_clearing | 18 | 21.44x | 16.93x | 8188 | 345 |
| het_bench | 8 | 2.41x | 2.22x | 590 | 271 |
| **Overall** | **67** | **12.89x** | **5.19x** | — | — |

### het_rt_lacam post-BFS vs pre-BFS SOC ratios (both must solve)

| Category | Mutual solves | Mean post/pre ratio | Median | Improved | Regressed | Same |
|----------|--------------|--------------------|---------|---------|-----------| -----|
| bottleneck_doors | 28 | 1.49x | 1.40x | 0 | 28 | 0 |
| corridor_speed | 15 | 1.36x | 1.26x | 2 | 13 | 0 |
| intersection | 6 | 1.15x | 1.06x | 2 | 4 | 0 |
| cooperative_clearing | 14 | 1.55x | 1.39x | 4 | 10 | 0 |
| het_bench | 8 | 1.30x | 1.24x | 0 | 8 | 0 |

## D. Exclusive Solves

### het_rt_lacam solves, hetpibt fails

**26 scenarios:**

- bottleneck_doors/n15/scen.00: lacam SOC=2003, pibt goals=14/15
- bottleneck_doors/n20/scen.01: lacam SOC=3456, pibt goals=18/19
- bottleneck_doors/n20/scen.04: lacam SOC=1986, pibt goals=18/19
- bottleneck_doors/n25/scen.00: lacam SOC=5484, pibt goals=21/24
- bottleneck_doors/n25/scen.04: lacam SOC=3316, pibt goals=23/24
- bottleneck_doors/n25/scen.07: lacam SOC=4061, pibt goals=21/22
- bottleneck_doors/n25/scen.08: lacam SOC=5128, pibt goals=21/24
- bottleneck_doors/n25/scen.10: lacam SOC=3581, pibt goals=24/25
- bottleneck_doors/n25/scen.12: lacam SOC=5416, pibt goals=21/23
- bottleneck_doors/n25/scen.13: lacam SOC=3894, pibt goals=22/25
- bottleneck_doors/n25/scen.14: lacam SOC=4776, pibt goals=22/23
- bottleneck_doors/n25/scen.16: lacam SOC=4643, pibt goals=20/22
- bottleneck_doors/n25/scen.17: lacam SOC=4884, pibt goals=22/23
- bottleneck_doors/n25/scen.18: lacam SOC=3423, pibt goals=23/25
- bottleneck_doors/n25/scen.20: lacam SOC=4724, pibt goals=22/23
- bottleneck_doors/n25/scen.23: lacam SOC=3314, pibt goals=23/24
- bottleneck_doors/n25/scen.24: lacam SOC=4798, pibt goals=22/23
- cooperative_clearing/n25/scen.02: lacam SOC=11306, pibt goals=17/19
- cooperative_clearing/n25/scen.22: lacam SOC=19090, pibt goals=12/14
- corridor_speed/n15/scen.01: lacam SOC=7049, pibt goals=5/6
- corridor_speed/n25/scen.01: lacam SOC=13635, pibt goals=10/12
- corridor_speed/n25/scen.05: lacam SOC=14180, pibt goals=12/13
- corridor_speed/n25/scen.11: lacam SOC=22105, pibt goals=7/11
- corridor_speed/n25/scen.12: lacam SOC=16198, pibt goals=6/9
- corridor_speed/n25/scen.17: lacam SOC=9431, pibt goals=7/9
- corridor_speed/n25/scen.24: lacam SOC=15444, pibt goals=8/12

### hetpibt solves, het_rt_lacam fails

**52 scenarios:**

- bottleneck_doors/n10/scen.01: pibt SOC=164
- bottleneck_doors/n15/scen.01: pibt SOC=472
- bottleneck_doors/n15/scen.02: pibt SOC=508
- bottleneck_doors/n25/scen.03: pibt SOC=1216
- bottleneck_doors/n25/scen.05: pibt SOC=1187
- bottleneck_doors/n25/scen.19: pibt SOC=1255
- cooperative_clearing/n15/scen.03: pibt SOC=293
- cooperative_clearing/n15/scen.04: pibt SOC=317
- cooperative_clearing/n20/scen.02: pibt SOC=809
- cooperative_clearing/n20/scen.04: pibt SOC=537
- cooperative_clearing/n25/scen.00: pibt SOC=1248
- cooperative_clearing/n25/scen.01: pibt SOC=1009
- cooperative_clearing/n25/scen.03: pibt SOC=716
- cooperative_clearing/n25/scen.04: pibt SOC=981
- cooperative_clearing/n25/scen.06: pibt SOC=746
- cooperative_clearing/n25/scen.07: pibt SOC=1179
- cooperative_clearing/n25/scen.09: pibt SOC=1191
- cooperative_clearing/n25/scen.10: pibt SOC=1780
- cooperative_clearing/n25/scen.11: pibt SOC=1153
- cooperative_clearing/n25/scen.13: pibt SOC=1002
- cooperative_clearing/n25/scen.15: pibt SOC=1528
- cooperative_clearing/n25/scen.16: pibt SOC=1007
- cooperative_clearing/n25/scen.18: pibt SOC=911
- cooperative_clearing/n25/scen.19: pibt SOC=1513
- cooperative_clearing/n25/scen.20: pibt SOC=922
- cooperative_clearing/n25/scen.21: pibt SOC=669
- corridor_speed/n10/scen.04: pibt SOC=61
- corridor_speed/n15/scen.00: pibt SOC=218
- corridor_speed/n15/scen.02: pibt SOC=402
- corridor_speed/n15/scen.04: pibt SOC=274
- corridor_speed/n20/scen.00: pibt SOC=475
- corridor_speed/n20/scen.02: pibt SOC=536
- corridor_speed/n20/scen.03: pibt SOC=213
- corridor_speed/n20/scen.04: pibt SOC=512
- corridor_speed/n25/scen.00: pibt SOC=695
- corridor_speed/n25/scen.02: pibt SOC=658
- corridor_speed/n25/scen.03: pibt SOC=768
- corridor_speed/n25/scen.06: pibt SOC=384
- corridor_speed/n25/scen.08: pibt SOC=962
- corridor_speed/n25/scen.09: pibt SOC=530
- corridor_speed/n25/scen.13: pibt SOC=520
- corridor_speed/n25/scen.15: pibt SOC=934
- corridor_speed/n25/scen.21: pibt SOC=946
- corridor_speed/n25/scen.22: pibt SOC=564
- het_bench/var/scen.9: pibt SOC=279
- intersection/n10/scen.03: pibt SOC=61
- intersection/n10/scen.04: pibt SOC=66
- intersection/n15/scen.04: pibt SOC=158
- intersection/n20/scen.04: pibt SOC=302
- intersection/n25/scen.04: pibt SOC=450
- intersection/n25/scen.12: pibt SOC=466
- intersection/n25/scen.19: pibt SOC=427

## E. Regressions (solved pre-BFS, fails post-BFS)

**14 regressions:**

- bottleneck_doors/n10/scen.01: pre-BFS SOC=439, post-BFS FAIL
- bottleneck_doors/n15/scen.02: pre-BFS SOC=873, post-BFS FAIL
- bottleneck_doors/n25/scen.01: pre-BFS SOC=2183, post-BFS FAIL
- bottleneck_doors/n25/scen.03: pre-BFS SOC=2451, post-BFS FAIL
- bottleneck_doors/n25/scen.19: pre-BFS SOC=2400, post-BFS FAIL
- bottleneck_doors/n25/scen.21: pre-BFS SOC=3177, post-BFS FAIL
- cooperative_clearing/n15/scen.03: pre-BFS SOC=8493, post-BFS FAIL
- cooperative_clearing/n15/scen.04: pre-BFS SOC=17461, post-BFS FAIL
- corridor_speed/n20/scen.04: pre-BFS SOC=5021, post-BFS FAIL
- corridor_speed/n25/scen.06: pre-BFS SOC=7815, post-BFS FAIL
- corridor_speed/n25/scen.08: pre-BFS SOC=14031, post-BFS FAIL
- corridor_speed/n25/scen.09: pre-BFS SOC=10463, post-BFS FAIL
- corridor_speed/n25/scen.15: pre-BFS SOC=9818, post-BFS FAIL
- corridor_speed/n25/scen.22: pre-BFS SOC=13831, post-BFS FAIL

## F. New Solves (failed pre-BFS, solved post-BFS)

**23 new solves:**

- bottleneck_doors/n15/scen.00: post-BFS SOC=2003
- bottleneck_doors/n20/scen.02: post-BFS SOC=2869
- bottleneck_doors/n20/scen.03: post-BFS SOC=2668
- bottleneck_doors/n20/scen.04: post-BFS SOC=1986
- bottleneck_doors/n25/scen.02: post-BFS SOC=3539
- bottleneck_doors/n25/scen.04: post-BFS SOC=3316
- bottleneck_doors/n25/scen.06: post-BFS SOC=4042
- cooperative_clearing/n15/scen.01: post-BFS SOC=6918
- cooperative_clearing/n20/scen.03: post-BFS SOC=7761
- cooperative_clearing/n25/scen.02: post-BFS SOC=11306
- cooperative_clearing/n25/scen.08: post-BFS SOC=21167
- cooperative_clearing/n25/scen.22: post-BFS SOC=19090
- cooperative_clearing/n5/scen.03: post-BFS SOC=318
- corridor_speed/n15/scen.01: post-BFS SOC=7049
- corridor_speed/n25/scen.01: post-BFS SOC=13635
- corridor_speed/n25/scen.04: post-BFS SOC=18680
- corridor_speed/n25/scen.10: post-BFS SOC=13597
- corridor_speed/n25/scen.11: post-BFS SOC=22105
- corridor_speed/n25/scen.19: post-BFS SOC=8786
- corridor_speed/n25/scen.23: post-BFS SOC=15261
- corridor_speed/n25/scen.24: post-BFS SOC=15444
- intersection/n10/scen.01: post-BFS SOC=267
- intersection/n10/scen.02: post-BFS SOC=352

## G. Overall Summary

- **Pre-BFS**: 85/190 solved (45%)
- **Post-BFS**: 94/190 solved (49%)
- **Net improvement**: +9 scenarios (5% of total)
- **Regressions**: 14
- **New solves**: 23
- **hetpibt reference**: 120/190 solved (63%)

- het_rt_lacam exclusively solves 26 scenarios that hetpibt cannot
- hetpibt exclusively solves 52 scenarios that het_rt_lacam cannot
- On 67 mutually-solved scenarios, het_rt_lacam SOC is 12.89x hetpibt (median 5.19x)
