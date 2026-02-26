# Heterogeneous Fleet Benchmarks

Benchmark maps and scenarios for heterogeneous multi-agent pathfinding (HetMAPF). Each scenario involves agents of different fleet sizes navigating shared spaces.

## Fleet Model

Fleet sizes: **1, 3, 7, 11** (cell sizes in base grid units).

Each agent occupies a `cs x cs` footprint using **non-overlapping tiling**:
- Fleet cell `(fx, fy)` covers base cells `[fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs)`
- A fleet cell is free only if ALL base cells in the footprint are free
- Agents are placed at fleet-grid-aligned positions (`sx % cs == 0, sy % cs == 0`)

Default map size: **77x77** (77 = 7 x 11, giving clean fleet grids for all sizes).

Default agent distribution: `1:12, 3:5, 7:4, 11:4` (25 agents total).

## File Formats

### `.map` (octile)
```
type octile
height 77
width 77
map
@@@@@...
```
- `@` = wall/obstacle, `.` = free space

### `.scen` (scenario)
One agent per line: `cs sx sy gx gy`
- `cs`: cell size (fleet footprint)
- `sx, sy`: start position (base grid, fleet-aligned)
- `gx, gy`: goal position (base grid, fleet-aligned)

### `.hetbench` (HetPIBT solver format)
One agent per line: `agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h`

Convert with: `python generators/convert_to_hetbench.py --scen <scen> --map <map> --output <out>`

## Generators

All generators are in `generators/` and produce 1 map + 25 scenarios (seeds 0-24).

### bottleneck_doors.py

Two rooms separated by a wall with doors of varying widths.

```
 Left Room    | Right Room
              |
  agents -->  D  --> goals
              |
  agents -->  D  --> goals
              |
```

Tests: passage through bottleneck doors of different sizes. Larger fleets can only use wider doors.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--map_size` | 77 | Map dimensions |
| `--door_widths` | "3,7,11" | Comma-separated door widths |
| `--agents_per_fleet` | 3 | Agents per fleet |
| `--seed` | 42 | Random seed |

```bash
python generators/bottleneck_doors.py
```

### corridor_speed.py

Parallel horizontal corridors of varying widths, stacked vertically.

```
 @@@@@@@@@@@@@@@@@@@@@@@@@@@
 @  corridor width=11       @   <-- cs=1,3,7,11
 @@@@@@@@@@@@@@@@@@@@@@@@@@@
 @  corridor width=7        @   <-- cs=1,3,7
 @@@@@@@@@@@@@@@@@@@@@@@@@@@
 @  corridor width=3        @   <-- cs=1,3
 @@@@@@@@@@@@@@@@@@@@@@@@@@@
```

Tests: head-on traffic in corridors. 50% of agents go left-to-right, 50% right-to-left.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--map_size` | 77 | Map dimensions |
| `--corridor_widths` | "11,7,7,11,3" | Corridor widths, top to bottom |
| `--agents_per_fleet` | "1:12,3:5,7:4,11:4" | Fleet distribution |
| `--head_on_ratio` | 0.5 | Fraction going right-to-left |
| `--num_scenarios` | 25 | Number of scenarios |

```bash
python generators/corridor_speed.py
```

### intersection.py

Central open area with 4 corridors (N/S/E/W) of different widths.

```
          |  N (w=22)  |
          |            |
 ---------+            +----------
  W (w=3) |   Center   |  E (w=14)
 ---------+   33x33    +----------
          |            |
          |  S (w=22)  |
```

Tests: multi-directional crossing through center. cs=11 can only use N/S; cs=7 uses N/S/E; cs=3/1 use all corridors.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--map_size` | 77 | Map dimensions |
| `--center_size` | 33 | Central area size |
| `--corridor_widths` | "N:22,S:22,E:14,W:3" | Per-direction widths |
| `--agents_per_fleet` | "1:12,3:5,7:4,11:4" | Fleet distribution |
| `--num_scenarios` | 25 | Number of scenarios |

```bash
python generators/intersection.py
```

### cooperative_clearing.py

Two asymmetric rooms connected by a single passage.

```
 +----- Large Room ------+--+---- Small Room ----+
 |                       |  |                     |
 |                       |  |                     |
 |                       ====                     |
 |                       |  |                     |
 |                       |  |                     |
 +-----------------------+--+---------------------+
              wall_col=44  passage (w=11)
```

Tests: passage congestion. All agents cross through the single passage. Large agents block it while traversing.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--map_size` | 77 | Map dimensions |
| `--wall_col` | 44 | Dividing wall column |
| `--passage_width` | 11 | Passage width |
| `--agents_per_fleet` | "1:12,3:5,7:4,11:4" | Fleet distribution |
| `--lr_ratio` | 0.6 | Fraction left-to-right |
| `--num_scenarios` | 25 | Number of scenarios |

```bash
python generators/cooperative_clearing.py
```

## Validation

Validate any map+scenario pair with 5 checks:

1. All start footprints valid (in bounds, all free)
2. All goal footprints valid
3. No start footprint overlaps (across all agents)
4. No goal footprint overlaps
5. BFS reachability (NxN block, 4-directional)

```bash
python generators/validate.py --map maps/corridor_speed_77.map --scen scenarios/corridor_speed_77_00.scen
```

## Visualization

View a map with agent start/goal positions:

```bash
python generators/show_map.py --map maps/intersection_77.map --scen scenarios/intersection_77_00.scen
```

## Quick Start

Generate all benchmarks:

```bash
cd benchmarks/generators

# Bottleneck doors (1 map, 1 scenario)
python bottleneck_doors.py

# Corridor speed (1 map, 25 scenarios)
python corridor_speed.py

# Intersection (1 map, 25 scenarios)
python intersection.py

# Cooperative clearing (1 map, 25 scenarios)
python cooperative_clearing.py
```

Convert to HetPIBT solver format:

```bash
python convert_to_hetbench.py --map ../maps/corridor_speed_77.map \
    --scen ../scenarios/corridor_speed_77_00.scen \
    --output ../scenarios/corridor_speed_77_00_hetbench.scen
```
