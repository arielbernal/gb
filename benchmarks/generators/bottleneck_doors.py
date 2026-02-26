#!/usr/bin/env python3
"""Generate a bottleneck doors benchmark map.

Two large rooms separated by a single-column wall with 4 doors of different
heights.  Each door admits only fleets whose cell_size <= door height.

Map size 105x105 (LCM of fleet cell sizes 1, 3, 5, 7).

Layout (vertical cross-section at wall column):
  @  wall
  .  door h=1  (cs=1 only)
  @  gap
  ...  door h=3  (cs<=3)
  @  gap
  .....  door h=5  (cs<=5)
  @  gap
  .......  door h=7  (all fleets)
  @  wall

Agents start in Room A (left), goals in Room B (right).
Scenario format: cs sx sy gx gy  (base-grid coordinates).
"""
import argparse
import os
import random


FLEET_SIZES = [1, 3, 5, 7]


def parse_agents_per_fleet(s):
    """Parse '1:12,3:5,5:4,7:4' into {1: 12, 3: 5, 5: 4, 7: 4}."""
    result = {}
    for pair in s.split(","):
        cs_str, count_str = pair.split(":")
        result[int(cs_str)] = int(count_str)
    return result


def fleet_cells_free(grid, map_size, cs):
    """Return (free_set, fw, fh) for fleet with given cell_size."""
    fw = map_size // cs
    fh = map_size // cs
    free = set()
    for fy in range(fh):
        for fx in range(fw):
            ok = True
            for dy in range(cs):
                for dx in range(cs):
                    if grid[fy * cs + dy][fx * cs + dx] != '.':
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                free.add((fx, fy))
    return free, fw, fh


def base_footprint(fx, fy, cs):
    """Base-grid cells covered by fleet cell (fx, fy)."""
    cells = set()
    for dy in range(cs):
        for dx in range(cs):
            cells.add((fx * cs + dx, fy * cs + dy))
    return cells


def generate(map_size, door_heights, agents_per_fleet, num_scenarios,
             output_dir_maps, output_dir_scens, seed_start=0):
    max_cs = max(FLEET_SIZES)  # 7
    wall_col = map_size // 2   # 52

    # ---- Build map ----
    grid = [['.' for _ in range(map_size)] for _ in range(map_size)]

    # Outer walls
    for r in range(map_size):
        grid[r][0] = '@'
        grid[r][map_size - 1] = '@'
    for c in range(map_size):
        grid[0][c] = '@'
        grid[map_size - 1][c] = '@'

    # Dividing wall at wall_col
    for r in range(map_size):
        grid[r][wall_col] = '@'

    # Cut doors in the wall, stacked vertically with gaps.
    # Each door's start row is aligned to the door height so fleet grids
    # line up cleanly.
    door_positions = []  # (start_row, end_row_exclusive, height)
    gap = max_cs         # 7 rows gap between doors

    current_row = max_cs  # start well past the outer wall
    for dh in sorted(door_heights):
        # Align start to dh boundary
        aligned_start = ((current_row + dh - 1) // dh) * dh
        end_row = aligned_start + dh
        if end_row >= map_size - 1:
            print(f"WARNING: not enough space for door height {dh}, skipping")
            continue
        for r in range(aligned_start, end_row):
            grid[r][wall_col] = '.'
        door_positions.append((aligned_start, end_row, dh))
        current_row = end_row + gap

    # Write .map file
    map_name = f"bottleneck_doors_{map_size}.map"
    map_path = os.path.join(output_dir_maps, map_name)
    with open(map_path, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {map_size}\n")
        f.write(f"width {map_size}\n")
        f.write("map\n")
        for row in grid:
            f.write(''.join(row) + '\n')

    room_a_cols = wall_col - 1
    room_b_cols = map_size - wall_col - 2
    print(f"Map: {map_size}x{map_size}  ->  {map_path}")
    print(f"Wall at col {wall_col}")
    print(f"Room A: cols 1..{wall_col-1} ({room_a_cols} cols)")
    print(f"Room B: cols {wall_col+1}..{map_size-2} ({room_b_cols} cols)")
    print(f"Doors:")
    for sr, er, dh in door_positions:
        fits = [cs for cs in FLEET_SIZES if cs <= dh]
        print(f"  rows [{sr},{er}), height={dh}, fits fleets: {fits}")

    for cs in FLEET_SIZES:
        free, fw, fh = fleet_cells_free(grid, map_size, cs)
        left = sum(1 for fx, fy in free if fx * cs < wall_col)
        right = sum(1 for fx, fy in free if fx * cs > wall_col)
        print(f"  Fleet cs={cs}: {fw}x{fh} grid, {len(free)} free "
              f"(left={left}, right={right})")

    # ---- Generate scenarios ----
    for seed_offset in range(num_scenarios):
        seed = seed_start + seed_offset
        random.seed(seed)

        agents = []
        occupied_starts = set()  # base cells
        occupied_goals = set()   # base cells

        for cs in sorted(agents_per_fleet.keys(), reverse=True):
            count = agents_per_fleet[cs]
            free_cells, fw, fh = fleet_cells_free(grid, map_size, cs)

            # Room A = left of wall, Room B = right of wall
            left_cells = sorted([c for c in free_cells if c[0] * cs < wall_col])
            right_cells = sorted([c for c in free_cells if c[0] * cs > wall_col])

            if not left_cells or not right_cells:
                if seed_offset == 0:
                    print(f"  Fleet cs={cs}: no left/right cells, skipping")
                continue

            placed = 0
            attempts = 0
            while placed < count and attempts < 3000:
                attempts += 1

                start = random.choice(left_cells)
                goal = random.choice(right_cells)

                s_base = base_footprint(start[0], start[1], cs)
                g_base = base_footprint(goal[0], goal[1], cs)

                if s_base & occupied_starts or g_base & occupied_goals:
                    continue

                sx = start[0] * cs
                sy = start[1] * cs
                gx = goal[0] * cs
                gy = goal[1] * cs
                agents.append((cs, sx, sy, gx, gy))
                occupied_starts |= s_base
                occupied_goals |= g_base
                placed += 1

            if placed < count and seed_offset == 0:
                print(f"  Fleet cs={cs}: placed {placed}/{count}")

        # Write .scen file
        scen_name = f"bottleneck_doors_{map_size}_{seed_offset:02d}.scen"
        scen_path = os.path.join(output_dir_scens, scen_name)
        with open(scen_path, 'w') as f:
            for cs, sx, sy, gx, gy in agents:
                f.write(f"{cs} {sx} {sy} {gx} {gy}\n")

        if seed_offset == 0:
            print(f"\nScenario 00: {len(agents)} agents")
            for cs in sorted(agents_per_fleet.keys()):
                n = sum(1 for a in agents if a[0] == cs)
                print(f"  Fleet cs={cs}: {n} agents")

    print(f"\nGenerated {num_scenarios} scenarios -> {output_dir_scens}")
    return map_path


def main():
    parser = argparse.ArgumentParser(description="Bottleneck doors benchmark")
    parser.add_argument("--map_size", type=int, default=105,
                        help="map dimensions (105 = LCM of 1,3,5,7)")
    parser.add_argument("--door_heights", type=str, default="1,3,5,7",
                        help="comma-separated door heights (vertical openings)")
    parser.add_argument("--agents_per_fleet", type=str, default="1:12,3:5,5:4,7:4",
                        help="fleet_cs:count pairs (25 total)")
    parser.add_argument("--num_scenarios", type=int, default=25)
    parser.add_argument("--seed_start", type=int, default=0)
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    door_heights = [int(x) for x in args.door_heights.split(",")]
    agents_per_fleet = parse_agents_per_fleet(args.agents_per_fleet)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = args.output_dir or os.path.dirname(script_dir)
    maps_dir = os.path.join(base_dir, "maps")
    scens_dir = os.path.join(base_dir, "scenarios")
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(scens_dir, exist_ok=True)

    generate(args.map_size, door_heights, agents_per_fleet, args.num_scenarios,
             maps_dir, scens_dir, args.seed_start)


if __name__ == "__main__":
    main()
