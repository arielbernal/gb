# Results Summary

## 1. het_bench Comparison: het_lacam vs hetpibt

Map: room-64-64-8 (120x120 cropped). Fleets: cs=1, cs=6, cs=11. `--swap-xy` enabled.
hetpibt: uncapped time. het_lacam: 10s anytime search.

| Scen | N | hetpibt Goals | hetpibt SOC | hetpibt MK | hetpibt ms | het_lacam Goals | het_lacam SOC | het_lacam MK | het_lacam ms |
|------|---|---------------|-------------|------------|------------|-----------------|---------------|--------------|--------------|
| 0    | 9 | 9/9           | 404         | 187        | 11         | 9/9             | 799           | 186          | 10079        |
| 2    | 7 | 7/7           | 130         | 49         | 7          | 7/7             | 497           | 142          | 10189        |
| 3    | 7 | 7/7           | 152         | 69         | 5          | 7/7             | 316           | 78           | 10098        |
| 4    | 8 | 8/8           | 179         | 61         | 5          | 8/8             | 309           | 108          | 10065        |
| 5    | 6 | 6/6           | 338         | 170        | 8          | 6/6             | 497           | 175          | 10146        |
| 6    | 9 | 9/9           | 452         | 176        | 12         | 9/9             | 1046          | 222          | 10108        |
| 7    | 9 | 9/9           | 184         | 80         | 6          | 9/9             | 303           | 77           | 10082        |
| 8    | 9 | 9/9           | 308         | 148        | 9          | 9/9             | 523           | 147          | 10098        |

Both solvers: 100% goals on all 8 valid scenarios. Skipped: scen.1 (goal overlap), scen.9 (boundary wall).
SOC note: het_lacam SOC includes wait-at-goal padding to makespan.

## 2. Custom Benchmark Results (hetpibt only)

### Bottleneck (77x77, 1 scenario, 12 agents)

| Scenario | Goals | Goal% | SOC | Makespan | Wait% | ms |
|----------|-------|-------|-----|----------|-------|----|
| bottleneck_77 | 12/12 | 100.0 | 396 | 48 | 24.0 | 2662 |

### Corridor Speed (154x154, 25 scenarios, 25 agents each)

| Metric | Value |
|--------|-------|
| Total goals | 549/625 |
| Avg goal% | 87.8 |
| Avg SOC | 1066 |
| Avg makespan | 127 |
| Avg ms | 2911 |
| Per-fleet: cs=1 | 253/300 (84.3%) |
| Per-fleet: cs=3 | 122/125 (97.6%) |
| Per-fleet: cs=7 | 85/100 (85.0%) |
| Per-fleet: cs=11 | 84/100 (84.0%) |

### Intersection (77x77, 25 scenarios, 25 agents each)

| Metric | Value |
|--------|-------|
| Total goals | 333/625 |
| Avg goal% | 53.3 |
| Avg SOC | 614 |
| Avg makespan | 90 |
| Avg ms | 32798 |
| Per-fleet: cs=1 | 207/300 (69.0%) |
| Per-fleet: cs=3 | 86/125 (68.8%) |
| Per-fleet: cs=7 | 25/100 (25.0%) |
| Per-fleet: cs=11 | 7/100 (7.0%) |

### Cooperative Clearing (77x77, 25 scenarios, 25 agents each)

| Metric | Value |
|--------|-------|
| Total goals | 319/625 |
| Avg goal% | 51.0 |
| Avg SOC | 867 |
| Avg makespan | 97 |
| Avg ms | 26835 |
| Per-fleet: cs=1 | 198/300 (66.0%) |
| Per-fleet: cs=3 | 92/125 (73.6%) |
| Per-fleet: cs=7 | 28/100 (28.0%) |
| Per-fleet: cs=11 | 5/100 (5.0%) |

## 3. Constraint Pruning (s2 failure rates)

No before/after data recorded. The `[PIBT diag]` counters (fail_s2, fail_s3, etc.) are printed to stderr at runtime but no saved comparison exists in the repository.
