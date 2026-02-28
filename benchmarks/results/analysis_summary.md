# Benchmark Analysis: het_rt_lacam vs hetpibt

## 0. Dataset Overview

- **het_rt_lacam**: 190 rows, 5 categories
- **hetpibt**: 190 rows, 5 categories

**het_rt_lacam** category x agent_label counts:
| category             |   n10 |   n15 |   n20 |   n25 |   n5 |   var |
|:---------------------|------:|------:|------:|------:|-----:|------:|
| bottleneck_doors     |     5 |     5 |     5 |    25 |    5 |     0 |
| cooperative_clearing |     5 |     5 |     5 |    25 |    5 |     0 |
| corridor_speed       |     5 |     5 |     5 |    25 |    5 |     0 |
| het_bench            |     0 |     0 |     0 |     0 |    0 |    10 |
| intersection         |     5 |     5 |     5 |    25 |    5 |     0 |

**hetpibt** category x agent_label counts:
| category             |   n10 |   n15 |   n20 |   n25 |   n5 |   var |
|:---------------------|------:|------:|------:|------:|-----:|------:|
| bottleneck_doors     |     5 |     5 |     5 |    25 |    5 |     0 |
| cooperative_clearing |     5 |     5 |     5 |    25 |    5 |     0 |
| corridor_speed       |     5 |     5 |     5 |    25 |    5 |     0 |
| het_bench            |     0 |     0 |     0 |     0 |    0 |    10 |
| intersection         |     5 |     5 |     5 |    25 |    5 |     0 |

## 1. Solve Rate Table

Format: solved/total for each solver. het_rt_lacam timeout=30s, hetpibt timeout=60s (1000 steps).

### intersection

| agents   | het_rt_lacam   | hetpibt   | lacam_rate   | pibt_rate   |
|:---------|:---------------|:----------|:-------------|:------------|
| n5       | 5/5            | 5/5       | 100%         | 100%        |
| n10      | 1/5            | 5/5       | 20%          | 100%        |
| n15      | 0/5            | 1/5       | 0%           | 20%         |
| n20      | 0/5            | 1/5       | 0%           | 20%         |
| n25      | 0/25           | 3/25      | 0%           | 12%         |

### bottleneck_doors

| agents   | het_rt_lacam   | hetpibt   | lacam_rate   | pibt_rate   |
|:---------|:---------------|:----------|:-------------|:------------|
| n5       | 5/5            | 5/5       | 100%         | 100%        |
| n10      | 5/5            | 5/5       | 100%         | 100%        |
| n15      | 3/5            | 4/5       | 60%          | 80%         |
| n20      | 1/5            | 2/5       | 20%          | 40%         |
| n25      | 20/25          | 8/25      | 80%          | 32%         |

### corridor_speed

| agents   | het_rt_lacam   | hetpibt   | lacam_rate   | pibt_rate   |
|:---------|:---------------|:----------|:-------------|:------------|
| n5       | 5/5            | 5/5       | 100%         | 100%        |
| n10      | 4/5            | 5/5       | 80%          | 100%        |
| n15      | 1/5            | 4/5       | 20%          | 80%         |
| n20      | 1/5            | 4/5       | 20%          | 80%         |
| n25      | 12/25          | 16/25     | 48%          | 64%         |

### cooperative_clearing

| agents   | het_rt_lacam   | hetpibt   | lacam_rate   | pibt_rate   |
|:---------|:---------------|:----------|:-------------|:------------|
| n5       | 5/5            | 5/5       | 100%         | 100%        |
| n10      | 5/5            | 5/5       | 100%         | 100%        |
| n15      | 4/5            | 5/5       | 80%          | 100%        |
| n20      | 1/5            | 4/5       | 20%          | 80%         |
| n25      | 2/25           | 19/25     | 8%           | 76%         |

### het_bench

| agents   | het_rt_lacam   | hetpibt   | lacam_rate   | pibt_rate   |
|:---------|:---------------|:----------|:-------------|:------------|
| var      | 8/10           | 9/10      | 80%          | 90%         |

### Overall Solve Rates

| Solver | Solved | Total | Rate |
|--------|--------|-------|------|
| het_rt_lacam | 88 | 190 | 46.3% |
| hetpibt | 120 | 190 | 63.2% |

## 2. Failure Analysis

### het_rt_lacam failures (by category x agent_label)

| category             | agent_label   |   count | scen_ids                                                         |
|:---------------------|:--------------|--------:|:-----------------------------------------------------------------|
| bottleneck_doors     | n15           |       2 | 0,1                                                              |
| bottleneck_doors     | n20           |       4 | 0,2,3,4                                                          |
| bottleneck_doors     | n25           |       5 | 2,4,5,6,15                                                       |
| cooperative_clearing | n15           |       1 | 1                                                                |
| cooperative_clearing | n20           |       4 | 0,2,3,4                                                          |
| cooperative_clearing | n25           |      23 | 0,1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23       |
| corridor_speed       | n10           |       1 | 4                                                                |
| corridor_speed       | n15           |       4 | 0,1,2,4                                                          |
| corridor_speed       | n20           |       4 | 0,1,2,3                                                          |
| corridor_speed       | n25           |      13 | 0,1,4,10,11,13,16,18,19,20,21,23,24                              |
| het_bench            | var           |       2 | 1,9                                                              |
| intersection         | n10           |       4 | 1,2,3,4                                                          |
| intersection         | n15           |       5 | 0,1,2,3,4                                                        |
| intersection         | n20           |       5 | 0,1,2,3,4                                                        |
| intersection         | n25           |      25 | 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24 |

### hetpibt failures (by category x agent_label)

| category             | agent_label   |   count | scen_ids                                                 | partial                                                                                                                             |
|:---------------------|:--------------|--------:|:---------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------|
| bottleneck_doors     | n15           |       1 | 0                                                        | 14/15                                                                                                                               |
| bottleneck_doors     | n20           |       3 | 0,1,4                                                    | 17/19/18/19/18/19                                                                                                                   |
| bottleneck_doors     | n25           |      17 | 0,1,4,7,8,10,12,13,14,15,16,17,18,20,21,23,24            | 21/24/23/24/23/24/21/22/21/24/24/25/21/23/22/25/22/23/24/25/20/22/22/23/23/25/22/23/18/25/23/24/22/23                               |
| cooperative_clearing | n20           |       1 | 0                                                        | 11/13                                                                                                                               |
| cooperative_clearing | n25           |       6 | 2,5,14,17,22,23                                          | 17/19/15/16/13/15/16/18/12/14/16/18                                                                                                 |
| corridor_speed       | n15           |       1 | 1                                                        | 5/6                                                                                                                                 |
| corridor_speed       | n20           |       1 | 1                                                        | 8/9                                                                                                                                 |
| corridor_speed       | n25           |       9 | 1,5,11,12,16,17,18,20,24                                 | 10/12/12/13/7/11/6/9/8/9/7/9/11/12/9/10/8/12                                                                                        |
| het_bench            | var           |       1 | 1                                                        | 6/7                                                                                                                                 |
| intersection         | n15           |       4 | 0,1,2,3                                                  | 12/13/13/14/13/14/10/12                                                                                                             |
| intersection         | n20           |       4 | 0,1,2,3                                                  | 16/18/17/19/12/17/14/17                                                                                                             |
| intersection         | n25           |      22 | 0,1,2,3,5,6,7,8,9,10,11,13,14,15,16,17,18,20,21,22,23,24 | 20/21/19/23/18/21/18/22/18/21/20/21/15/22/17/19/18/19/18/19/16/19/20/21/17/20/16/20/21/22/20/21/18/21/17/18/17/19/19/21/20/21/19/20 |

### Scenarios where BOTH solvers fail

| category             | agent_label   |   count | scen_ids                                                 |
|:---------------------|:--------------|--------:|:---------------------------------------------------------|
| bottleneck_doors     | n15           |       1 | 0                                                        |
| bottleneck_doors     | n20           |       2 | 0,4                                                      |
| bottleneck_doors     | n25           |       2 | 4,15                                                     |
| cooperative_clearing | n20           |       1 | 0                                                        |
| cooperative_clearing | n25           |       6 | 2,5,14,17,22,23                                          |
| corridor_speed       | n15           |       1 | 1                                                        |
| corridor_speed       | n20           |       1 | 1                                                        |
| corridor_speed       | n25           |       6 | 1,11,16,18,20,24                                         |
| het_bench            | var           |       1 | 1                                                        |
| intersection         | n15           |       4 | 0,1,2,3                                                  |
| intersection         | n20           |       4 | 0,1,2,3                                                  |
| intersection         | n25           |      22 | 0,1,2,3,5,6,7,8,9,10,11,13,14,15,16,17,18,20,21,22,23,24 |

### het_rt_lacam solves but hetpibt fails

| category         | agent_label   |   scen_id |   soc_lacam |   goals_reached_pibt |   goals_total_pibt |
|:-----------------|:--------------|----------:|------------:|---------------------:|-------------------:|
| bottleneck_doors | n20           |         1 |        1656 |                   18 |                 19 |
| bottleneck_doors | n25           |         0 |        2582 |                   21 |                 24 |
| bottleneck_doors | n25           |         1 |        2183 |                   23 |                 24 |
| bottleneck_doors | n25           |         7 |        3299 |                   21 |                 22 |
| bottleneck_doors | n25           |         8 |        2829 |                   21 |                 24 |
| bottleneck_doors | n25           |        10 |        1871 |                   24 |                 25 |
| bottleneck_doors | n25           |        12 |        4041 |                   21 |                 23 |
| bottleneck_doors | n25           |        13 |        2743 |                   22 |                 25 |
| bottleneck_doors | n25           |        14 |        2667 |                   22 |                 23 |
| bottleneck_doors | n25           |        16 |        2353 |                   20 |                 22 |
| bottleneck_doors | n25           |        17 |        2964 |                   22 |                 23 |
| bottleneck_doors | n25           |        18 |        2631 |                   23 |                 25 |
| bottleneck_doors | n25           |        20 |        3391 |                   22 |                 23 |
| bottleneck_doors | n25           |        21 |        3177 |                   18 |                 25 |
| bottleneck_doors | n25           |        23 |        2883 |                   23 |                 24 |
| bottleneck_doors | n25           |        24 |        2528 |                   22 |                 23 |
| corridor_speed   | n25           |         5 |       10863 |                   12 |                 13 |
| corridor_speed   | n25           |        12 |       12867 |                    6 |                  9 |
| corridor_speed   | n25           |        17 |        5207 |                    7 |                  9 |

### hetpibt solves but het_rt_lacam fails

| category             | agent_label   |   scen_id |   soc_pibt |   runtime_ms_pibt |
|:---------------------|:--------------|----------:|-----------:|------------------:|
| intersection         | n10           |         1 |         88 |                33 |
| intersection         | n10           |         2 |        122 |                39 |
| intersection         | n10           |         3 |         61 |                34 |
| intersection         | n10           |         4 |         66 |                38 |
| intersection         | n15           |         4 |        158 |                30 |
| intersection         | n20           |         4 |        302 |                38 |
| intersection         | n25           |         4 |        450 |                39 |
| intersection         | n25           |        12 |        466 |                56 |
| intersection         | n25           |        19 |        427 |                41 |
| bottleneck_doors     | n15           |         1 |        472 |                63 |
| bottleneck_doors     | n20           |         2 |       1005 |                82 |
| bottleneck_doors     | n20           |         3 |        918 |                73 |
| bottleneck_doors     | n25           |         2 |       1486 |                75 |
| bottleneck_doors     | n25           |         5 |       1187 |                74 |
| bottleneck_doors     | n25           |         6 |       1251 |                68 |
| corridor_speed       | n10           |         4 |         61 |                41 |
| corridor_speed       | n15           |         0 |        218 |                38 |
| corridor_speed       | n15           |         2 |        402 |                56 |
| corridor_speed       | n15           |         4 |        274 |               764 |
| corridor_speed       | n20           |         0 |        475 |                58 |
| corridor_speed       | n20           |         2 |        536 |               992 |
| corridor_speed       | n20           |         3 |        213 |                45 |
| corridor_speed       | n25           |         0 |        695 |                50 |
| corridor_speed       | n25           |         4 |        684 |                55 |
| corridor_speed       | n25           |        10 |        553 |                54 |
| corridor_speed       | n25           |        13 |        520 |                43 |
| corridor_speed       | n25           |        19 |        677 |                54 |
| corridor_speed       | n25           |        21 |        946 |                58 |
| corridor_speed       | n25           |        23 |       1033 |                77 |
| cooperative_clearing | n15           |         1 |        141 |                45 |
| cooperative_clearing | n20           |         2 |        809 |                61 |
| cooperative_clearing | n20           |         3 |        634 |                60 |
| cooperative_clearing | n20           |         4 |        537 |                51 |
| cooperative_clearing | n25           |         0 |       1248 |               114 |
| cooperative_clearing | n25           |         1 |       1009 |                64 |
| cooperative_clearing | n25           |         3 |        716 |                68 |
| cooperative_clearing | n25           |         4 |        981 |                74 |
| cooperative_clearing | n25           |         6 |        746 |                52 |
| cooperative_clearing | n25           |         7 |       1179 |               257 |
| cooperative_clearing | n25           |         8 |       1169 |               616 |
| cooperative_clearing | n25           |         9 |       1191 |                68 |
| cooperative_clearing | n25           |        10 |       1780 |              1460 |
| cooperative_clearing | n25           |        11 |       1153 |                58 |
| cooperative_clearing | n25           |        13 |       1002 |                92 |
| cooperative_clearing | n25           |        15 |       1528 |               118 |
| cooperative_clearing | n25           |        16 |       1007 |                65 |
| cooperative_clearing | n25           |        18 |        911 |                60 |
| cooperative_clearing | n25           |        19 |       1513 |               148 |
| cooperative_clearing | n25           |        20 |        922 |                59 |
| cooperative_clearing | n25           |        21 |        669 |                52 |
| het_bench            | var           |         9 |        279 |                43 |

## 3. Head-to-Head: Scenarios Both Solve

### Per-category averages (het_rt_lacam / hetpibt ratio)

> Ratio > 1 means het_rt_lacam is WORSE (higher SOC/makespan/runtime).
> Ratio < 1 means het_rt_lacam is BETTER.

| category             |   n_scenarios |   avg_soc_ratio |   med_soc_ratio |   avg_makespan_ratio |   avg_runtime_ratio |
|:---------------------|--------------:|----------------:|----------------:|---------------------:|--------------------:|
| bottleneck_doors     |            18 |            2.31 |            2.36 |                 1.79 |              449.89 |
| cooperative_clearing |            17 |           20.14 |           12.02 |                 6.41 |              693.08 |
| corridor_speed       |            20 |           18.84 |           17.41 |                 6.08 |              742.64 |
| het_bench            |             8 |            1.86 |            1.66 |                 1.35 |              624.49 |
| intersection         |             6 |            4.63 |            3.27 |                 3.04 |              373.6  |

### Overall head-to-head (all categories)

| Metric | Mean Ratio | Median Ratio |
|--------|-----------|-------------|
| SOC | 11.54 | 5.87 |
| Makespan | 4.20 | 3.00 |
| Runtime | 608.3 | 639.4 |

### Detailed head-to-head (every scenario both solve)

| category             | agent_label   |   scen_id |   soc_lacam |   soc_pibt |   soc_ratio |   makespan_lacam |   makespan_pibt |   makespan_ratio |   runtime_ms_lacam |   runtime_ms_pibt |
|:---------------------|:--------------|----------:|------------:|-----------:|------------:|-----------------:|----------------:|-----------------:|-------------------:|------------------:|
| intersection         | n5            |         0 |          83 |         21 |        3.95 |               37 |               8 |             4.62 |              11445 |                25 |
| intersection         | n5            |         1 |          70 |         27 |        2.59 |               26 |               9 |             2.89 |               9671 |                34 |
| intersection         | n5            |         2 |          71 |         64 |        1.11 |               21 |              24 |             0.88 |               1049 |                34 |
| intersection         | n5            |         3 |         101 |         15 |        6.73 |               35 |               8 |             4.38 |               1909 |                31 |
| intersection         | n5            |         4 |          68 |          6 |       11.33 |               21 |               6 |             3.5  |              12062 |                19 |
| intersection         | n10           |         0 |         210 |        102 |        2.06 |               43 |              22 |             1.95 |              30111 |                39 |
| bottleneck_doors     | n5            |         0 |         232 |         89 |        2.61 |               60 |              32 |             1.88 |              21618 |                47 |
| bottleneck_doors     | n5            |         1 |         196 |         74 |        2.65 |               54 |              28 |             1.93 |              11256 |                33 |
| bottleneck_doors     | n5            |         2 |         245 |         74 |        3.31 |               62 |              30 |             2.07 |               4173 |                45 |
| bottleneck_doors     | n5            |         3 |         223 |         78 |        2.86 |               61 |              32 |             1.91 |              27588 |                40 |
| bottleneck_doors     | n5            |         4 |         196 |         70 |        2.8  |               56 |              23 |             2.43 |               2358 |                40 |
| bottleneck_doors     | n10           |         0 |         695 |        214 |        3.25 |              102 |              34 |             3    |              30139 |                61 |
| bottleneck_doors     | n10           |         1 |         431 |        164 |        2.63 |               88 |              34 |             2.59 |              30169 |                46 |
| bottleneck_doors     | n10           |         2 |         507 |        206 |        2.46 |               73 |              34 |             2.15 |              30139 |                38 |
| bottleneck_doors     | n10           |         3 |         442 |        199 |        2.22 |               74 |              46 |             1.61 |              30102 |                37 |
| bottleneck_doors     | n10           |         4 |         516 |        200 |        2.58 |               93 |              50 |             1.86 |              30149 |                52 |
| bottleneck_doors     | n15           |         2 |         873 |        508 |        1.72 |              107 |             104 |             1.03 |              30197 |                61 |
| bottleneck_doors     | n15           |         3 |         726 |        507 |        1.43 |               92 |             160 |             0.57 |              30123 |                56 |
| bottleneck_doors     | n15           |         4 |        1089 |        482 |        2.26 |              157 |             113 |             1.39 |              30157 |                62 |
| bottleneck_doors     | n25           |         3 |        2451 |       1216 |        2.02 |              238 |             140 |             1.7  |              30349 |                84 |
| bottleneck_doors     | n25           |         9 |        1941 |       1301 |        1.49 |              175 |             146 |             1.2  |              30228 |                84 |
| bottleneck_doors     | n25           |        11 |        2589 |       1266 |        2.05 |              252 |             123 |             2.05 |              31108 |               104 |
| bottleneck_doors     | n25           |        19 |        2400 |       1255 |        1.91 |              241 |             124 |             1.94 |              30275 |                76 |
| bottleneck_doors     | n25           |        22 |        2091 |       1576 |        1.33 |              193 |             191 |             1.01 |              30258 |               167 |
| corridor_speed       | n5            |         0 |         437 |         49 |        8.92 |              126 |              35 |             3.6  |              30579 |                39 |
| corridor_speed       | n5            |         1 |         311 |         49 |        6.35 |               95 |              32 |             2.97 |              30871 |                39 |
| corridor_speed       | n5            |         2 |         532 |         82 |        6.49 |              141 |              25 |             5.64 |              30634 |                37 |
| corridor_speed       | n5            |         3 |         473 |          0 |      nan    |              135 |               0 |           nan    |              30731 |                34 |
| corridor_speed       | n5            |         4 |         355 |         24 |       14.79 |              104 |              24 |             4.33 |              30748 |                34 |
| corridor_speed       | n10           |         0 |        1306 |         75 |       17.41 |              238 |              35 |             6.8  |              30187 |                32 |
| corridor_speed       | n10           |         1 |        1656 |         99 |       16.73 |              280 |              32 |             8.75 |              30208 |                47 |
| corridor_speed       | n10           |         2 |        1844 |        156 |       11.82 |              297 |              47 |             6.32 |              30205 |                30 |
| corridor_speed       | n10           |         3 |        1250 |         71 |       17.61 |              197 |              48 |             4.1  |              30193 |                40 |
| corridor_speed       | n15           |         3 |        4108 |         71 |       57.86 |              490 |              48 |            10.21 |              30539 |                29 |
| corridor_speed       | n20           |         4 |        5021 |        512 |        9.81 |              484 |             138 |             3.51 |              30402 |                50 |
| corridor_speed       | n25           |         2 |       11752 |        658 |       17.86 |             1049 |             137 |             7.66 |              31008 |                48 |
| corridor_speed       | n25           |         3 |       15018 |        768 |       19.55 |             1069 |             160 |             6.68 |              31166 |                54 |
| corridor_speed       | n25           |         6 |        7815 |        384 |       20.35 |              765 |             128 |             5.98 |              31006 |                38 |
| corridor_speed       | n25           |         7 |       13047 |        360 |       36.24 |             1100 |             169 |             6.51 |              31294 |                52 |
| corridor_speed       | n25           |         8 |       14031 |        962 |       14.59 |             1054 |             165 |             6.39 |              31332 |                65 |
| corridor_speed       | n25           |         9 |       10463 |        530 |       19.74 |              873 |             136 |             6.42 |              30944 |                69 |
| corridor_speed       | n25           |        14 |        9828 |        367 |       26.78 |              921 |             145 |             6.35 |              30911 |                42 |
| corridor_speed       | n25           |        15 |        9818 |        934 |       10.51 |              856 |             135 |             6.34 |              31096 |                59 |
| corridor_speed       | n25           |        22 |       13831 |        564 |       24.52 |              941 |             134 |             7.02 |              31110 |                39 |
| cooperative_clearing | n5            |         0 |         316 |         86 |        3.67 |               81 |              40 |             2.02 |              30706 |                44 |
| cooperative_clearing | n5            |         1 |         268 |         49 |        5.47 |               71 |              25 |             2.84 |              30579 |                27 |
| cooperative_clearing | n5            |         2 |         458 |         59 |        7.76 |              113 |              30 |             3.77 |              30740 |                41 |
| cooperative_clearing | n5            |         3 |         265 |         71 |        3.73 |               71 |              16 |             4.44 |              30641 |                40 |
| cooperative_clearing | n5            |         4 |         258 |         34 |        7.59 |               66 |              22 |             3    |              30470 |                40 |
| cooperative_clearing | n10           |         0 |        1909 |        146 |       13.08 |              236 |              42 |             5.62 |              30196 |                46 |
| cooperative_clearing | n10           |         1 |        2289 |         67 |       34.16 |              305 |              25 |            12.2  |              30207 |                32 |
| cooperative_clearing | n10           |         2 |         879 |        208 |        4.23 |              127 |              53 |             2.4  |              30177 |                44 |
| cooperative_clearing | n10           |         3 |        2019 |        168 |       12.02 |              269 |              31 |             8.68 |              30214 |                44 |
| cooperative_clearing | n10           |         4 |        1916 |         72 |       26.61 |              220 |              26 |             8.46 |              30167 |                33 |
| cooperative_clearing | n15           |         0 |       10316 |        397 |       25.98 |              784 |             133 |             5.89 |              30449 |               105 |
| cooperative_clearing | n15           |         2 |        2395 |        382 |        6.27 |              193 |              87 |             2.22 |              30149 |                58 |
| cooperative_clearing | n15           |         3 |        8493 |        293 |       28.99 |              733 |              82 |             8.94 |              30502 |                54 |
| cooperative_clearing | n15           |         4 |       17461 |        317 |       55.08 |             1310 |             127 |            10.31 |              30693 |                48 |
| cooperative_clearing | n20           |         1 |       54829 |        635 |       86.34 |             3017 |             155 |            19.46 |              32225 |                45 |
| cooperative_clearing | n25           |        12 |       12300 |        980 |       12.55 |              624 |             146 |             4.27 |              30681 |                56 |
| cooperative_clearing | n25           |        24 |        8133 |        918 |        8.86 |              510 |             117 |             4.36 |              30556 |                60 |
| het_bench            | var           |         0 |         601 |        404 |        1.49 |              186 |             187 |             0.99 |              30152 |                51 |
| het_bench            | var           |         2 |         488 |        130 |        3.75 |              131 |              49 |             2.67 |              30255 |                46 |
| het_bench            | var           |         3 |         310 |        154 |        2.01 |               78 |              69 |             1.13 |              30159 |                53 |
| het_bench            | var           |         4 |         340 |        179 |        1.9  |              125 |              61 |             2.05 |              30128 |                43 |
| het_bench            | var           |         5 |         389 |        346 |        1.12 |              175 |             176 |             0.99 |              30631 |                55 |
| het_bench            | var           |         6 |         604 |        460 |        1.31 |              173 |             176 |             0.98 |              30136 |                47 |
| het_bench            | var           |         7 |         303 |        184 |        1.65 |               77 |              80 |             0.96 |              30093 |                43 |
| het_bench            | var           |         8 |         517 |        308 |        1.68 |              147 |             148 |             0.99 |              30125 |                52 |

## 4. Runtime Comparison (ms)

### het_rt_lacam avg runtime per category x agent_label

| category             | agent_label   |   avg_runtime_ms |   min_runtime |   max_runtime |   n |
|:---------------------|:--------------|-----------------:|--------------:|--------------:|----:|
| bottleneck_doors     | n10           |            30140 |         30102 |         30169 |   5 |
| bottleneck_doors     | n15           |            30211 |         30123 |         30335 |   5 |
| bottleneck_doors     | n20           |            30245 |         30195 |         30311 |   5 |
| bottleneck_doors     | n25           |            30406 |         30141 |         31108 |  25 |
| bottleneck_doors     | n5            |            13399 |          2358 |         27588 |   5 |
| cooperative_clearing | n10           |            30192 |         30167 |         30214 |   5 |
| cooperative_clearing | n15           |            30440 |         30149 |         30693 |   5 |
| cooperative_clearing | n20           |            30710 |         30302 |         32225 |   5 |
| cooperative_clearing | n25           |            30411 |         30191 |         31868 |  25 |
| cooperative_clearing | n5            |            30627 |         30470 |         30740 |   5 |
| corridor_speed       | n10           |            30202 |         30187 |         30217 |   5 |
| corridor_speed       | n15           |            30266 |         30148 |         30539 |   5 |
| corridor_speed       | n20           |            30638 |         30107 |         31121 |   5 |
| corridor_speed       | n25           |            30691 |         30136 |         31332 |  25 |
| corridor_speed       | n5            |            30713 |         30579 |         30871 |   5 |
| het_bench            | var           |            24177 |            39 |         30631 |  10 |
| intersection         | n10           |            30270 |         30111 |         30582 |   5 |
| intersection         | n15           |            30226 |         30065 |         30392 |   5 |
| intersection         | n20           |            30237 |         30083 |         30493 |   5 |
| intersection         | n25           |            30309 |         30044 |         30630 |  25 |
| intersection         | n5            |             7227 |          1049 |         12062 |   5 |

### hetpibt avg runtime per category x agent_label

| category             | agent_label   |   avg_runtime_ms |   min_runtime |   max_runtime |   n |
|:---------------------|:--------------|-----------------:|--------------:|--------------:|----:|
| bottleneck_doors     | n10           |               47 |            37 |            61 |   5 |
| bottleneck_doors     | n15           |               84 |            56 |           180 |   5 |
| bottleneck_doors     | n20           |              110 |            73 |           211 |   5 |
| bottleneck_doors     | n25           |              929 |            68 |         19565 |  25 |
| bottleneck_doors     | n5            |               41 |            33 |            47 |   5 |
| cooperative_clearing | n10           |               40 |            32 |            46 |   5 |
| cooperative_clearing | n15           |               62 |            45 |           105 |   5 |
| cooperative_clearing | n20           |              176 |            45 |           664 |   5 |
| cooperative_clearing | n25           |              233 |            52 |          1460 |  25 |
| cooperative_clearing | n5            |               38 |            27 |            44 |   5 |
| corridor_speed       | n10           |               38 |            30 |            47 |   5 |
| corridor_speed       | n15           |              190 |            29 |           764 |   5 |
| corridor_speed       | n20           |              243 |            45 |           992 |   5 |
| corridor_speed       | n25           |              688 |            38 |          7535 |  25 |
| corridor_speed       | n5            |               37 |            34 |            39 |   5 |
| het_bench            | var           |               58 |            43 |           144 |  10 |
| intersection         | n10           |               37 |            33 |            39 |   5 |
| intersection         | n15           |              152 |            30 |           247 |   5 |
| intersection         | n20           |              416 |            38 |          1196 |   5 |
| intersection         | n25           |              583 |            39 |          4563 |  25 |
| intersection         | n5            |               29 |            19 |            34 |   5 |

## 5. Hardest Scenarios

### Top 10 by runtime (het_rt_lacam)

| category             | agent_label   |   scen_id |   agents | solved   |   soc |   runtime_ms |
|:---------------------|:--------------|----------:|---------:|:---------|------:|-------------:|
| cooperative_clearing | n20           |         1 |       20 | True     | 54829 |        32225 |
| cooperative_clearing | n25           |         8 |       25 | False    |     0 |        31868 |
| corridor_speed       | n25           |         8 |       25 | True     | 14031 |        31332 |
| corridor_speed       | n25           |         7 |       25 | True     | 13047 |        31294 |
| corridor_speed       | n25           |         5 |       25 | True     | 10863 |        31237 |
| corridor_speed       | n25           |         3 |       25 | True     | 15018 |        31166 |
| corridor_speed       | n20           |         0 |       20 | False    |     0 |        31121 |
| corridor_speed       | n25           |        22 |       25 | True     | 13831 |        31110 |
| bottleneck_doors     | n25           |        11 |       25 | True     |  2589 |        31108 |
| corridor_speed       | n25           |        15 |       25 | True     |  9818 |        31096 |

### Top 10 by runtime (hetpibt)

| category             | agent_label   |   scen_id |   agents | solved   |   soc |   runtime_ms |
|:---------------------|:--------------|----------:|---------:|:---------|------:|-------------:|
| bottleneck_doors     | n25           |        21 |       25 | False    |  3239 |        19565 |
| corridor_speed       | n25           |        11 |       11 | False    |  1652 |         7535 |
| corridor_speed       | n25           |        24 |       12 | False    |  1572 |         7189 |
| intersection         | n25           |         1 |       23 | False    |  1673 |         4563 |
| intersection         | n25           |        11 |       19 | False    |   404 |         3037 |
| cooperative_clearing | n25           |        10 |       15 | True     |  1780 |         1460 |
| intersection         | n25           |         7 |       22 | False    |  8357 |         1228 |
| intersection         | n20           |         2 |       17 | False    |  5321 |         1196 |
| intersection         | n25           |        21 |       19 | False    |   573 |         1108 |
| intersection         | n25           |        14 |       20 | False    |  1421 |         1075 |

### Top 10 by SOC (het_rt_lacam, solved only)

| category             | agent_label   |   scen_id |   agents |   soc |   soc_lb |   makespan |   runtime_ms |
|:---------------------|:--------------|----------:|---------:|------:|---------:|-----------:|-------------:|
| cooperative_clearing | n20           |         1 |       20 | 54829 |     1190 |       3017 |        32225 |
| cooperative_clearing | n15           |         4 |       15 | 17461 |      542 |       1310 |        30693 |
| corridor_speed       | n25           |         3 |       25 | 15018 |     1919 |       1069 |        31166 |
| corridor_speed       | n25           |         8 |       25 | 14031 |     1944 |       1054 |        31332 |
| corridor_speed       | n25           |        22 |       25 | 13831 |     1619 |        941 |        31110 |
| corridor_speed       | n25           |         7 |       25 | 13047 |     1757 |       1100 |        31294 |
| corridor_speed       | n25           |        12 |       25 | 12867 |     1709 |        963 |        30968 |
| cooperative_clearing | n25           |        12 |       25 | 12300 |     1554 |        624 |        30681 |
| corridor_speed       | n25           |         2 |       25 | 11752 |     1882 |       1049 |        31008 |
| corridor_speed       | n25           |         5 |       25 | 10863 |     1822 |        992 |        31237 |

### Top 10 by SOC (hetpibt, solved only)

| category             | agent_label   |   scen_id |   agents |   soc |   makespan |   runtime_ms |
|:---------------------|:--------------|----------:|---------:|------:|-----------:|-------------:|
| cooperative_clearing | n25           |        10 |       15 |  1780 |        228 |         1460 |
| bottleneck_doors     | n25           |        22 |       24 |  1576 |        191 |          167 |
| cooperative_clearing | n25           |        15 |       21 |  1528 |        223 |          118 |
| cooperative_clearing | n25           |        19 |       16 |  1513 |        156 |          148 |
| bottleneck_doors     | n25           |         2 |       23 |  1486 |        160 |           75 |
| bottleneck_doors     | n25           |         9 |       24 |  1301 |        146 |           84 |
| bottleneck_doors     | n25           |        11 |       21 |  1266 |        123 |          104 |
| bottleneck_doors     | n25           |        19 |       24 |  1255 |        124 |           76 |
| bottleneck_doors     | n25           |         6 |       24 |  1251 |        122 |           68 |
| cooperative_clearing | n25           |         0 |       18 |  1248 |        132 |          114 |

## 6. hetpibt Goal Completion (Partial Solutions)

### Partial completions (goals_reached < goals_total)

| category             | agent_label   |   scen_id |   agents | solved   | completion   |   soc |   runtime_ms |
|:---------------------|:--------------|----------:|---------:|:---------|:-------------|------:|-------------:|
| intersection         | n15           |         0 |       13 | False    | 12/13 (92%)  |  1302 |          226 |
| intersection         | n15           |         1 |       14 | False    | 13/14 (93%)  |  1234 |          201 |
| intersection         | n15           |         2 |       14 | False    | 13/14 (93%)  |  1164 |           58 |
| intersection         | n15           |         3 |       12 | False    | 10/12 (83%)  |  2142 |          247 |
| intersection         | n20           |         0 |       18 | False    | 16/18 (89%)  |  2430 |          327 |
| intersection         | n20           |         1 |       19 | False    | 17/19 (89%)  |  2332 |          257 |
| intersection         | n20           |         2 |       17 | False    | 12/17 (71%)  |  5321 |         1196 |
| intersection         | n20           |         3 |       17 | False    | 14/17 (82%)  |  3241 |          263 |
| intersection         | n25           |         0 |       21 | False    | 20/21 (95%)  |  1763 |          223 |
| intersection         | n25           |         1 |       23 | False    | 19/23 (83%)  |  1673 |         4563 |
| intersection         | n25           |         2 |       21 | False    | 18/21 (86%)  |  3719 |          412 |
| intersection         | n25           |         3 |       22 | False    | 18/22 (82%)  |  4388 |          346 |
| intersection         | n25           |         5 |       21 | False    | 18/21 (86%)  |  3563 |          333 |
| intersection         | n25           |         6 |       21 | False    | 20/21 (95%)  |  1702 |           69 |
| intersection         | n25           |         7 |       22 | False    | 15/22 (68%)  |  8357 |         1228 |
| intersection         | n25           |         8 |       19 | False    | 17/19 (89%)  |  2428 |           99 |
| intersection         | n25           |         9 |       19 | False    | 18/19 (95%)  |  1490 |           76 |
| intersection         | n25           |        10 |       19 | False    | 18/19 (95%)  |  1473 |          124 |
| intersection         | n25           |        11 |       19 | False    | 16/19 (84%)  |   404 |         3037 |
| intersection         | n25           |        13 |       21 | False    | 20/21 (95%)  |  1616 |          172 |
| intersection         | n25           |        14 |       20 | False    | 17/20 (85%)  |  1421 |         1075 |
| intersection         | n25           |        15 |       20 | False    | 16/20 (80%)  |  4460 |          218 |
| intersection         | n25           |        16 |       22 | False    | 21/22 (95%)  |  1610 |           63 |
| intersection         | n25           |        17 |       21 | False    | 20/21 (95%)  |  1571 |          160 |
| intersection         | n25           |        18 |       21 | False    | 18/21 (86%)  |  3526 |          349 |
| intersection         | n25           |        20 |       18 | False    | 17/18 (94%)  |  1456 |           79 |
| intersection         | n25           |        21 |       19 | False    | 17/19 (89%)  |   573 |         1108 |
| intersection         | n25           |        22 |       21 | False    | 19/21 (90%)  |  2483 |          339 |
| intersection         | n25           |        23 |       21 | False    | 20/21 (95%)  |  1603 |          281 |
| intersection         | n25           |        24 |       20 | False    | 19/20 (95%)  |  1455 |           75 |
| bottleneck_doors     | n15           |         0 |       15 | False    | 14/15 (93%)  |  1507 |          180 |
| bottleneck_doors     | n20           |         0 |       19 | False    | 17/19 (89%)  |  2849 |          211 |
| bottleneck_doors     | n20           |         1 |       19 | False    | 18/19 (95%)  |  1897 |           97 |
| bottleneck_doors     | n20           |         4 |       19 | False    | 18/19 (95%)  |  1836 |           87 |
| bottleneck_doors     | n25           |         0 |       24 | False    | 21/24 (88%)  |  4235 |          330 |
| bottleneck_doors     | n25           |         1 |       24 | False    | 23/24 (96%)  |  2472 |          104 |
| bottleneck_doors     | n25           |         4 |       24 | False    | 23/24 (96%)  |  2295 |          105 |
| bottleneck_doors     | n25           |         7 |       22 | False    | 21/22 (95%)  |  2391 |           93 |
| bottleneck_doors     | n25           |         8 |       24 | False    | 21/24 (88%)  |  3936 |          132 |
| bottleneck_doors     | n25           |        10 |       25 | False    | 24/25 (96%)  |  2179 |          926 |
| bottleneck_doors     | n25           |        12 |       23 | False    | 21/23 (91%)  |  3138 |          114 |
| bottleneck_doors     | n25           |        13 |       25 | False    | 22/25 (88%)  |  4355 |          192 |
| bottleneck_doors     | n25           |        14 |       23 | False    | 22/23 (96%)  |  2537 |          114 |
| bottleneck_doors     | n25           |        15 |       25 | False    | 24/25 (96%)  |  2458 |          128 |
| bottleneck_doors     | n25           |        16 |       22 | False    | 20/22 (91%)  |  2951 |          114 |
| bottleneck_doors     | n25           |        17 |       23 | False    | 22/23 (96%)  |  2268 |           87 |
| bottleneck_doors     | n25           |        18 |       25 | False    | 23/25 (92%)  |  3382 |          160 |
| bottleneck_doors     | n25           |        20 |       23 | False    | 22/23 (96%)  |  2393 |          105 |
| bottleneck_doors     | n25           |        21 |       25 | False    | 18/25 (72%)  |  3239 |        19565 |
| bottleneck_doors     | n25           |        23 |       24 | False    | 23/24 (96%)  |  2194 |           96 |
| bottleneck_doors     | n25           |        24 |       23 | False    | 22/23 (96%)  |  2414 |          124 |
| corridor_speed       | n15           |         1 |        6 | False    | 5/6 (83%)    |  1147 |           65 |
| corridor_speed       | n20           |         1 |        9 | False    | 8/9 (89%)    |  1494 |           71 |
| corridor_speed       | n25           |         1 |       12 | False    | 10/12 (83%)  |  2820 |           88 |
| corridor_speed       | n25           |         5 |       13 | False    | 12/13 (92%)  |  1813 |          167 |
| corridor_speed       | n25           |        11 |       11 | False    | 7/11 (64%)   |  1652 |         7535 |
| corridor_speed       | n25           |        12 |        9 | False    | 6/9 (67%)    |  3356 |          860 |
| corridor_speed       | n25           |        16 |        9 | False    | 8/9 (89%)    |  1585 |          127 |
| corridor_speed       | n25           |        17 |        9 | False    | 7/9 (78%)    |  2687 |          107 |
| corridor_speed       | n25           |        18 |       12 | False    | 11/12 (92%)  |  1907 |           85 |
| corridor_speed       | n25           |        20 |       10 | False    | 9/10 (90%)   |  1675 |          187 |
| corridor_speed       | n25           |        24 |       12 | False    | 8/12 (67%)   |  1572 |         7189 |
| cooperative_clearing | n20           |         0 |       13 | False    | 11/13 (85%)  |   872 |          664 |
| cooperative_clearing | n25           |         2 |       19 | False    | 17/19 (89%)  |  3124 |          108 |
| cooperative_clearing | n25           |         5 |       16 | False    | 15/16 (94%)  |  1966 |           86 |
| cooperative_clearing | n25           |        14 |       15 | False    | 13/15 (87%)  |   966 |          563 |
| cooperative_clearing | n25           |        17 |       18 | False    | 16/18 (89%)  |  1197 |          653 |
| cooperative_clearing | n25           |        22 |       14 | False    | 12/14 (86%)  |   707 |          778 |
| cooperative_clearing | n25           |        23 |       18 | False    | 16/18 (89%)  |  2888 |           98 |
| het_bench            | var           |         1 |        7 | False    | 6/7 (86%)    |  1103 |          144 |

### Summary: avg goal completion by category x agent_label (hetpibt)

| category             | agent_label   |   avg_completion_pct |   min_completion_pct |   n_partial |   n_total |
|:---------------------|:--------------|---------------------:|---------------------:|------------:|----------:|
| bottleneck_doors     | n10           |                100   |                100   |           0 |         5 |
| bottleneck_doors     | n15           |                 98.7 |                 93.3 |           1 |         5 |
| bottleneck_doors     | n20           |                 95.8 |                 89.5 |           3 |         5 |
| bottleneck_doors     | n25           |                 94.7 |                 72   |          17 |        25 |
| bottleneck_doors     | n5            |                100   |                100   |           0 |         5 |
| cooperative_clearing | n10           |                100   |                100   |           0 |         5 |
| cooperative_clearing | n15           |                100   |                100   |           0 |         5 |
| cooperative_clearing | n20           |                 96.9 |                 84.6 |           1 |         5 |
| cooperative_clearing | n25           |                 97.3 |                 85.7 |           6 |        25 |
| cooperative_clearing | n5            |                100   |                100   |           0 |         5 |
| corridor_speed       | n10           |                100   |                100   |           0 |         5 |
| corridor_speed       | n15           |                 96.7 |                 83.3 |           1 |         5 |
| corridor_speed       | n20           |                 97.8 |                 88.9 |           1 |         5 |
| corridor_speed       | n25           |                 92.8 |                 63.6 |           9 |        25 |
| corridor_speed       | n5            |                100   |                100   |           0 |         4 |
| het_bench            | var           |                 98.6 |                 85.7 |           1 |        10 |
| intersection         | n10           |                100   |                100   |           0 |         5 |
| intersection         | n15           |                 92.3 |                 83.3 |           4 |         5 |
| intersection         | n20           |                 86.3 |                 70.6 |           4 |         5 |
| intersection         | n25           |                 90.4 |                 68.2 |          22 |        25 |
| intersection         | n5            |                100   |                100   |           0 |         5 |

## 7. Key Findings Summary

1. **Overall solve rates**: het_rt_lacam 88/190 (46.3%), hetpibt 120/190 (63.2%)

2. **SOC quality gap**: On scenarios both solve, het_rt_lacam SOC is 11.54x hetpibt (mean ratio). Makespan ratio: 4.20x.

3. **Scalability**: het_rt_lacam struggles at n15+ on intersection (0/35 solved). hetpibt also struggles but achieves partial solutions.

4. **het_bench**: het_rt_lacam solves 8/10 (fails scen 1,9 known infeasible). hetpibt solves 9/10 (fails scen 1).

5. **Exclusive solves**: het_rt_lacam solves 19 scenarios hetpibt fails. hetpibt solves 51 scenarios het_rt_lacam fails.

6. **Runtime**: het_rt_lacam uses ~30s timeout (most runs ~30000ms). hetpibt is orders of magnitude faster (typically <100ms), but caps at 1000 steps.

