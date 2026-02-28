# RT+ST-BFS Benchmark Analysis

## A. Overall Solve Rates

| Category | RT+ST-BFS | RT+spatial | hetpibt |
|----------|-----------|------------|---------|
| bottleneck_doors | 33/45 (73%) | 35/45 (77%) | 24/45 (53%) |
| corridor_speed | 28/45 (62%) | 24/45 (53%) | 34/45 (75%) |
| intersection | 6/45 (13%) | 8/45 (17%) | 15/45 (33%) |
| cooperative_clearing | 22/45 (48%) | 22/45 (48%) | 38/45 (84%) |
| het_bench | 9/10 (90%) | 9/10 (90%) | 9/10 (90%) |
| **TOTAL** | **98/190** | **98/190** | **120/190** |

## B. Solve Rate by Category × Agent Count

### bottleneck_doors

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|-----------|------------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 4/5 | 5/5 |
| n15 | 4/5 | 3/5 | 4/5 |
| n20 | 1/5 | 4/5 | 2/5 |
| n25 | 18/25 | 19/25 | 8/25 |

### corridor_speed

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|-----------|------------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 4/5 | 5/5 |
| n15 | 4/5 | 2/5 | 4/5 |
| n20 | 4/5 | 0/5 | 4/5 |
| n25 | 10/25 | 13/25 | 16/25 |

### intersection

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|-----------|------------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 1/5 | 3/5 | 5/5 |
| n15 | 0/5 | 0/5 | 1/5 |
| n20 | 0/5 | 0/5 | 1/5 |
| n25 | 0/25 | 0/25 | 3/25 |

### cooperative_clearing

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|-----------|------------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 5/5 | 5/5 |
| n15 | 4/5 | 4/5 | 5/5 |
| n20 | 3/5 | 2/5 | 4/5 |
| n25 | 5/25 | 6/25 | 19/25 |

### het_bench

| Agents | RT+ST-BFS | RT+spatial | hetpibt |
|--------|-----------|------------|---------|
| var | 9/10 | 9/10 | 9/10 |

## C. New Solves (RT+ST-BFS solved, RT+spatial did not)

**20 new solves:**

| Category | Agents | Scen | SOC | Makespan | Steps | Time |
|----------|--------|------|-----|----------|-------|------|
| bottleneck_doors | n10 | 01 | 430 | 82 | 82 | 818ms |
| bottleneck_doors | n15 | 02 | 834 | 103 | 103 | 1236ms |
| bottleneck_doors | n25 | 21 | 2110 | 187 | 187 | 3976ms |
| cooperative_clearing | n15 | 04 | 1143 | 128 | 128 | 1491ms |
| cooperative_clearing | n20 | 00 | 2269 | 190 | 190 | 2668ms |
| cooperative_clearing | n20 | 02 | 1815 | 153 | 153 | 3011ms |
| cooperative_clearing | n25 | 09 | 2926 | 203 | 203 | 4434ms |
| cooperative_clearing | n25 | 11 | 3098 | 222 | 222 | 3089ms |
| corridor_speed | n10 | 04 | 596 | 137 | 137 | 3022ms |
| corridor_speed | n15 | 02 | 2068 | 322 | 322 | 3436ms |
| corridor_speed | n15 | 04 | 1764 | 314 | 314 | 9681ms |
| corridor_speed | n20 | 01 | 6621 | 2251 | 2251 | 53595ms |
| corridor_speed | n20 | 02 | 3768 | 413 | 413 | 9290ms |
| corridor_speed | n20 | 03 | 3552 | 439 | 439 | 9627ms |
| corridor_speed | n20 | 04 | 3559 | 415 | 415 | 7485ms |
| corridor_speed | n25 | 02 | 5032 | 528 | 528 | 14758ms |
| corridor_speed | n25 | 03 | 6932 | 622 | 622 | 13038ms |
| corridor_speed | n25 | 09 | 5886 | 547 | 547 | 12313ms |
| corridor_speed | n25 | 15 | 4518 | 408 | 408 | 8796ms |
| corridor_speed | n25 | 21 | 7362 | 722 | 722 | 16720ms |

## D. Regressions (RT+spatial solved, RT+ST-BFS did not)

**20 regressions:**

| Category | Agents | Scen | Old SOC | Old Steps | Old Time |
|----------|--------|------|---------|-----------|----------|
| bottleneck_doors | n20 | 01 | 3493 | 346 | 1335ms |
| bottleneck_doors | n20 | 03 | 2676 | 253 | 954ms |
| bottleneck_doors | n20 | 04 | 2010 | 192 | 663ms |
| bottleneck_doors | n25 | 04 | 3370 | 275 | 1106ms |
| bottleneck_doors | n25 | 20 | 4757 | 558 | 2669ms |
| cooperative_clearing | n15 | 03 | 16298 | 1227 | 31400ms |
| cooperative_clearing | n20 | 01 | 45883 | 2890 | 26308ms |
| cooperative_clearing | n25 | 08 | 21233 | 1373 | 7287ms |
| cooperative_clearing | n25 | 12 | 18489 | 981 | 6028ms |
| cooperative_clearing | n25 | 15 | 81131 | 3605 | 52318ms |
| corridor_speed | n25 | 01 | 13691 | 1140 | 6158ms |
| corridor_speed | n25 | 04 | 20134 | 1508 | 16838ms |
| corridor_speed | n25 | 05 | 14201 | 874 | 3651ms |
| corridor_speed | n25 | 10 | 17321 | 1910 | 20757ms |
| corridor_speed | n25 | 11 | 23828 | 2592 | 18377ms |
| corridor_speed | n25 | 17 | 9433 | 830 | 5056ms |
| corridor_speed | n25 | 19 | 8851 | 805 | 3143ms |
| corridor_speed | n25 | 22 | 41435 | 3359 | 36200ms |
| intersection | n10 | 00 | 318 | 53 | 195ms |
| intersection | n10 | 02 | 383 | 74 | 258ms |

## E. SOC Comparison on Mutually Solved Scenarios

### RT+ST-BFS vs RT+spatial (78 mutual solves)

- Mean SOC ratio (ST-BFS / spatial): **0.570**
- Median SOC ratio: **0.536**
- ST-BFS better (ratio < 0.95): 77
- Similar (0.95-1.05): 0
- ST-BFS worse (ratio > 1.05): 1

| Category | Mutual | Mean ratio | Median | Better | Worse |
|----------|--------|------------|--------|--------|-------|
| bottleneck_doors | 30 | 0.570 | 0.509 | 30 | 0 |
| corridor_speed | 16 | 0.439 | 0.433 | 16 | 0 |
| intersection | 6 | 0.720 | 0.724 | 6 | 0 |
| cooperative_clearing | 17 | 0.561 | 0.342 | 16 | 1 |
| het_bench | 9 | 0.722 | 0.677 | 9 | 0 |

### RT+ST-BFS vs hetpibt (76 mutual solves)

- Mean SOC ratio (ST-BFS / hetpibt): **6.190**
- Median SOC ratio: **4.128**

## F. Runtime Comparison

- RT+ST-BFS: median=2572ms, p95=16720ms, max=53595ms (n=98)
- RT+spatial: median=1335ms, p95=20757ms, max=52318ms (n=98)
- hetpibt: median=68ms, p95=144ms, max=1505ms (n=120)
