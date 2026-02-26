# Scenario Validation Report — 105-Map Series (2026-02-25)

Validator: `benchmarks/generators/validate.py` (7-check version)

## Checks Performed

1. Start positions in bounds and on free cells (NxN footprint)
2. Goal positions in bounds and on free cells (NxN footprint)
3. **Wall-overlap check**: explicit per-cell wall character detection (`@`, `O`, `T`, etc.)
4. **Fleet grid alignment**: all coords divisible by cell_size (`sx%cs==0`, etc.)
5. No start footprint overlaps between agents
6. No goal footprint overlaps between agents
7. BFS reachability: NxN block can reach goal from start

## Results

**100/100 scenarios — ALL 7 CHECKS PASSED**

| Map | Size | Scenarios | Agents/scen | Pass | Fail |
|-----|------|-----------|-------------|------|------|
| corridor_speed_105 | 105x105 | 25 (seeds 00–24) | 25 | 25 | 0 |
| intersection_105 | 105x105 | 25 (seeds 00–24) | 25 | 25 | 0 |
| cooperative_clearing_105 | 105x105 | 25 (seeds 00–24) | 25 | 25 | 0 |
| bottleneck_doors_105 | 105x105 | 25 (seeds 00–24) | 25 | 25 | 0 |

### Fleet Grid Divisibility (105x105)

| Cell Size | Fleet Grid | Exact? |
|-----------|------------|--------|
| cs=1 | 105 | 105*1=105 YES |
| cs=3 | 35 | 35*3=105 YES |
| cs=5 | 21 | 21*5=105 YES |
| cs=7 | 15 | 15*7=105 YES |
| cs=15 | 7 | 7*15=105 YES |
| cs=21 | 5 | 5*21=105 YES |

All cell sizes divide 105 evenly — no unused edge strips. This is a major improvement over the 77-map series where cs=3 had remainder=2.

## Visualizations Generated

| File | Size | Map Type |
|------|------|----------|
| `viz_corridor_speed_105_00.png` | 303K | Corridor speed |
| `viz_intersection_105_00.png` | 161K | Intersection |
| `viz_cooperative_clearing_105_00.png` | 306K | Cooperative clearing |
| `viz_bottleneck_doors_105_00.png` | 277K | Bottleneck doors |

## Conclusion

All 100 new 105-map scenarios are valid for paper use:
- Zero wall overlaps
- Zero alignment violations
- Zero footprint collisions
- All goals BFS-reachable
- 105 = 3*5*7 ensures all fleet cell sizes divide evenly
