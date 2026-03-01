# RT+ST-BFS+Stay Benchmark Analysis

## A. Overall Solve Rates

| Category | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |
|----------|----------------|-----------|---------|
| bottleneck_doors | 33/45 (73%) | 33/45 (73%) | 24/45 (53%) |
| corridor_speed | 28/45 (62%) | 28/45 (62%) | 34/45 (75%) |
| intersection | 6/45 (13%) | 6/45 (13%) | 15/45 (33%) |
| cooperative_clearing | 22/45 (48%) | 22/45 (48%) | 38/45 (84%) |
| het_bench | 9/10 (90%) | 9/10 (90%) | 9/10 (90%) |
| **TOTAL** | **98/190** | **98/190** | **120/190** |

## B. Solve Rate by Category x Agent Count

### bottleneck_doors

| Agents | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |
|--------|----------------|-----------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 5/5 | 5/5 |
| n15 | 4/5 | 4/5 | 4/5 |
| n20 | 1/5 | 1/5 | 2/5 |
| n25 | 18/25 | 18/25 | 8/25 |

### corridor_speed

| Agents | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |
|--------|----------------|-----------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 5/5 | 5/5 |
| n15 | 4/5 | 4/5 | 4/5 |
| n20 | 4/5 | 4/5 | 4/5 |
| n25 | 10/25 | 10/25 | 16/25 |

### intersection

| Agents | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |
|--------|----------------|-----------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 1/5 | 1/5 | 5/5 |
| n15 | 0/5 | 0/5 | 1/5 |
| n20 | 0/5 | 0/5 | 1/5 |
| n25 | 0/25 | 0/25 | 3/25 |

### cooperative_clearing

| Agents | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |
|--------|----------------|-----------|---------|
| n5 | 5/5 | 5/5 | 5/5 |
| n10 | 5/5 | 5/5 | 5/5 |
| n15 | 4/5 | 4/5 | 5/5 |
| n20 | 3/5 | 3/5 | 4/5 |
| n25 | 5/25 | 5/25 | 19/25 |

### het_bench

| Agents | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |
|--------|----------------|-----------|---------|
| var | 9/10 | 9/10 | 9/10 |

## C. New Solves (stay solved, old ST-BFS did not)

No new solves.

## D. Regressions (old ST-BFS solved, stay did not)

0 regressions.

## E. SOC Comparison on Mutually Solved Scenarios

### Stay vs old ST-BFS (98 mutual solves)

- Mean SOC ratio (stay / old): **1.004**
- Median SOC ratio: **1.000**
- Stay better (ratio < 0.95): 0
- Similar (0.95-1.05): 97
- Stay worse (ratio > 1.05): 1

| Category | Mutual | Mean ratio | Median | Better | Worse |
|----------|--------|------------|--------|--------|-------|
| bottleneck_doors | 33 | 1.000 | 1.000 | 0 | 0 |
| corridor_speed | 28 | 1.013 | 1.000 | 0 | 1 |
| intersection | 6 | 1.000 | 1.000 | 0 | 0 |
| cooperative_clearing | 22 | 1.000 | 1.000 | 0 | 0 |
| het_bench | 9 | 1.000 | 1.000 | 0 | 0 |

### Stay vs hetpibt (76 mutual solves)

- Mean SOC ratio (stay / hetpibt): **6.239**
- Median SOC ratio: **4.128**

## F. Runtime Comparison

- RT+ST-BFS+stay: median=2451ms, p95=16829ms, max=51966ms (n=98)
- RT+ST-BFS: median=2572ms, p95=16720ms, max=53595ms (n=98)
- hetpibt: median=68ms, p95=144ms, max=1505ms (n=120)

## G. Stay vs Move Steps

**All scenarios**: move=147729, stay=22255, stay%=13%, total_explored=2254359
- Solved: move=22553, stay=1726, stay%=7%
- Failed: move=125176, stay=20529, stay%=14%

| Category | Solved move | Solved stay | Failed move | Failed stay |
|----------|------------|------------|-------------|-------------|
| bottleneck_doors | 4601 | 219 | 15537 | 3202 |
| corridor_speed | 12029 | 752 | 21611 | 1955 |
| intersection | 113 | 69 | 65663 | 14433 |
| cooperative_clearing | 4666 | 547 | 22365 | 939 |
| het_bench | 1144 | 139 | 0 | 0 |
