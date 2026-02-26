#!/usr/bin/env python3
"""Generate a cooperative clearing benchmark map.

Two large rooms connected by a narrow passage.  Agents start mixed in both
rooms with goals that require swapping sides, forcing cooperative clearing
at the passage.

Map size 105x105 (LCM of fleet cell sizes 1, 3, 5, 7).

Layout (horizontal cross-section):
  [Room A  cols 1..41]  [wall zone cols 42..62]  [Room B  cols 63..103]
                         passage: 7 rows high

Agents are placed at fleet-grid-aligned positions (non-overlapping tiling).
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


def generate(map_size, agents_per_fleet, lr_ratio, num_scenarios,
             output_dir_maps, output_dir_scens, seed_start=0):
    max_cs = max(FLEET_SIZES)  # 7

    # ---- Passage zone dimensions ----
    passage_width = max_cs          # 7 rows high
    passage_length = 3 * max_cs     # 21 cols long
    wall_start = (map_size - passage_length) // 2  # col 42
    wall_end = wall_start + passage_length          # col 63

    # Passage vertical position: centered, aligned to max_cs
    passage_row_center = map_size // 2              # ~52
    passage_row_start = (passage_row_center // max_cs) * max_cs  # 49
    passage_row_end = passage_row_start + passage_width           # 56

    # ---- Build map ----
    grid = [['.' for _ in range(map_size)] for _ in range(map_size)]

    # Outer walls
    for r in range(map_size):
        grid[r][0] = '@'
        grid[r][map_size - 1] = '@'
    for c in range(map_size):
        grid[0][c] = '@'
        grid[map_size - 1][c] = '@'

    # Passage zone: fill with walls
    for r in range(map_size):
        for c in range(wall_start, wall_end):
            grid[r][c] = '@'

    # Cut the passage tunnel
    for r in range(passage_row_start, passage_row_end):
        for c in range(wall_start, wall_end):
            grid[r][c] = '.'

    # Write .map file
    map_name = f"cooperative_clearing_{map_size}.map"
    map_path = os.path.join(output_dir_maps, map_name)
    with open(map_path, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {map_size}\n")
        f.write(f"width {map_size}\n")
        f.write("map\n")
        for row in grid:
            f.write(''.join(row) + '\n')

    # Room dimensions
    room_a_cols = wall_start - 1          # free cols in Room A  (1..wall_start-1)
    room_b_cols = map_size - 1 - wall_end  # free cols in Room B  (wall_end..map_size-2)
    room_rows = map_size - 2               # free rows (1..map_size-2)

    print(f"Map: {map_size}x{map_size}  ->  {map_path}")
    print(f"Room A: {room_a_cols} cols x {room_rows} rows (cols 1..{wall_start-1})")
    print(f"Room B: {room_b_cols} cols x {room_rows} rows (cols {wall_end}..{map_size-2})")
    print(f"Passage: rows [{passage_row_start},{passage_row_end}), "
          f"cols [{wall_start},{wall_end}), width={passage_width}, length={passage_length}")
    for cs in FLEET_SIZES:
        free, fw, fh = fleet_cells_free(grid, map_size, cs)
        left = sum(1 for fx, fy in free if fx * cs < wall_start)
        right = sum(1 for fx, fy in free if fx * cs >= wall_end)
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

            # Split into left room / right room
            left_cells = sorted([c for c in free_cells if c[0] * cs < wall_start])
            right_cells = sorted([c for c in free_cells if c[0] * cs >= wall_end])

            if not left_cells or not right_cells:
                if seed_offset == 0:
                    print(f"  Fleet cs={cs}: no left/right cells, skipping")
                continue

            placed = 0
            attempts = 0
            while placed < count and attempts < 3000:
                attempts += 1

                # Bidirectional: lr_ratio go left->right, rest right->left
                if random.random() < lr_ratio:
                    start_pool, goal_pool = left_cells, right_cells
                else:
                    start_pool, goal_pool = right_cells, left_cells

                start = random.choice(start_pool)
                goal = random.choice(goal_pool)

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
        scen_name = f"cooperative_clearing_{map_size}_{seed_offset:02d}.scen"
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
    parser = argparse.ArgumentParser(description="Cooperative clearing benchmark")
    parser.add_argument("--map_size", type=int, default=105,
                        help="map dimensions (105 = LCM of 1,3,5,7)")
    parser.add_argument("--agents_per_fleet", type=str, default="1:12,3:5,5:4,7:4",
                        help="fleet_cs:count pairs (25 total)")
    parser.add_argument("--lr_ratio", type=float, default=0.6,
                        help="fraction going left->right (rest go right->left)")
    parser.add_argument("--num_scenarios", type=int, default=25)
    parser.add_argument("--seed_start", type=int, default=0)
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    agents_per_fleet = parse_agents_per_fleet(args.agents_per_fleet)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = args.output_dir or os.path.dirname(script_dir)
    maps_dir = os.path.join(base_dir, "maps")
    scens_dir = os.path.join(base_dir, "scenarios")
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(scens_dir, exist_ok=True)

    generate(args.map_size, agents_per_fleet, args.lr_ratio, args.num_scenarios,
             maps_dir, scens_dir, args.seed_start)


if __name__ == "__main__":
    main()
