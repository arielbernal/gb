# Scenario Validation Report — 2025-02-25

Validator: `benchmarks/generators/validate.py`
Checks: (1) start positions valid, (2) goal positions valid, (3) no start footprint overlaps, (4) no goal footprint overlaps, (5) BFS reachability for NxN block.

## Summary

**114 scenarios validated. ALL PASSED.**

| Map | Scenarios | Agents/scen | Result |
|-----|-----------|-------------|--------|
| bottleneck_64 | 1 | 9 | PASS |
| bottleneck_77 | 1 | 12 | PASS |
| corridor_speed_77 (seeds 00–24) | 25 | 25 | ALL PASS |
| corridor_speed_154 (seeds 00–24) | 25 | 25 | ALL PASS |
| intersection_77 (seeds 00–24) | 25 | 25 | ALL PASS |
| cooperative_clearing_77 (seeds 00–24) | 25 | 25 | ALL PASS |
| corridor_speed_77_00 scaling (n5,n10,n15,n20) | 4 | 5–20 | ALL PASS |
| intersection_77_00 scaling (n5,n10,n15,n20) | 4 | 5–20 | ALL PASS |
| cooperative_clearing_77_00 scaling (n5,n10,n15,n20) | 4 | 5–20 | ALL PASS |

## Not Validated (different format)

These use het_bench 10-column format (`instance_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h`), which the validator doesn't parse:

- `bottleneck_64_hetbench.scen` (11 agents)
- `bottleneck_77_hetbench.scen` (12 agents)
- `corridor_speed_77_00_hetbench.scen` (25 agents)

## Fleet Grid Divisibility

| Map | cs=1 | cs=3 | cs=7 | cs=11 |
|-----|------|------|------|-------|
| bottleneck_64 (64×64) | 64 OK | 21 WARN (r=1) | 9 WARN (r=1) | 5 WARN (r=9) |
| bottleneck_77 (77×77) | 77 OK | 25 WARN (r=2) | 11 OK | 7 OK |
| corridor_speed_77 (77×77) | 77 OK | 25 WARN (r=2) | 11 OK | 7 OK |
| corridor_speed_154 (154×154) | 154 OK | 51 WARN (r=1) | 22 OK | 14 OK |
| intersection_77 (77×77) | 77 OK | 25 WARN (r=2) | 11 OK | 7 OK |
| cooperative_clearing_77 (77×77) | 77 OK | 25 WARN (r=2) | 11 OK | 7 OK |

Key: fleet_grid = floor(map_size / cell_size). WARN = remainder > 0 (edge strip unused). r = remainder.

### Impact of non-integer division

- **cs=3 on 77-wide maps**: fleet_grid=25, covers 75 of 77 cols/rows. 2 edge cols/rows unused.
- **cs=3 on 154-wide maps**: fleet_grid=51, covers 153 of 154. 1 edge col/row unused.
- **bottleneck_64**: worst case — cs=11 covers only 55 of 64 (9 unused edge cols/rows).
- **All generators use floor-division placement**, so no agent is placed in partial edge tiles.
- **No functional impact**: the solver's tiling model uses floor division, matching the generators.

### Tiling alignment

All 114 scenarios checked: every coordinate (sx, sy, gx, gy) is divisible by its cell_size. Agents are always placed at tiling-aligned positions.

### Max cs=3 coordinates (the non-dividing fleet)

| Map set | Max coord | Max footprint end | Map width | In bounds? |
|---------|-----------|-------------------|-----------|------------|
| corridor_speed_77 | 72 | 75 | 77 | YES |
| corridor_speed_154 | 150 | 153 | 154 | YES |
| intersection_77 | 72 | 75 | 77 | YES |
| cooperative_clearing_77 | 72 | 75 | 77 | YES |
| bottleneck_64 | 54 | 57 | 64 | YES |
| bottleneck_77 | 69 | 72 | 77 | YES |

## Conclusion

All 114 scenarios are valid for paper use:
- No out-of-bounds positions
- No start/goal footprint overlaps
- All goals BFS-reachable
- All coordinates tiling-aligned
- Non-integer fleet grid division is benign (unused edge strip only)

The 3 hetbench-format files should be validated separately if used in the paper.
