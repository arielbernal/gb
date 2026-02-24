#!/usr/bin/env python3
"""Generate a bottleneck doors benchmark map.

Two rectangular rooms (left and right) separated by a wall with doors
of specified widths stacked vertically. Each fleet's agents are assigned
to pass through doors they physically fit through.

Agents are placed at fleet-grid-aligned positions (non-overlapping tiling).
"""
import argparse
import os
import random


FLEET_SIZES = [1, 3, 7, 11]


def generate(map_size, door_widths, agents_per_fleet, output_dir_maps,
             output_dir_scens, seed=42):
    random.seed(seed)
    wall_col = map_size // 2

    # Initialize grid: all free
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

    # Cut doors in the wall, stacked vertically.
    # Each door's start row is aligned to the door width so that the door
    # spans exactly one fleet row for the largest fleet that fits (cs = dw).
    # This ensures fleet cells at the wall column are fully free for that fleet.
    door_positions = []  # (start_row, end_row_exclusive, width_value)
    current_row = 1  # after outer wall

    for dw in sorted(door_widths):
        # Align start row to dw (= target fleet cs) boundary
        aligned_start = ((current_row + dw - 1) // dw) * dw
        if aligned_start + dw >= map_size - 1:
            print(f"WARNING: not enough space for door width {dw}, skipping")
            continue
        end_row = aligned_start + dw
        for r in range(aligned_start, end_row):
            grid[r][wall_col] = '.'
        door_positions.append((aligned_start, end_row, dw))
        current_row = end_row + 1  # 1 wall row gap between doors

    # Precompute free fleet cells for each cs
    def fleet_cells_free(cs):
        """Return set of (fx, fy) where the fleet cell is entirely free."""
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

    # Write .map file
    map_name = f"bottleneck_{map_size}.map"
    map_path = os.path.join(output_dir_maps, map_name)
    with open(map_path, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {map_size}\n")
        f.write(f"width {map_size}\n")
        f.write("map\n")
        for row in grid:
            f.write(''.join(row) + '\n')

    # Generate scenario
    agents = []  # (cs, sx, sy, gx, gy) in base coords (fleet-aligned)
    occupied_fleet_starts = {}  # cs -> set of (fx, fy) used as starts
    occupied_fleet_goals = {}

    for cs in sorted(FLEET_SIZES, reverse=True):  # largest first for placement priority
        free_cells, fw, fh = fleet_cells_free(cs)
        occupied_fleet_starts[cs] = set()
        occupied_fleet_goals[cs] = set()

        # Find doors this fleet can actually cross on the fleet grid.
        # A door [sr, er) is usable by fleet cs if it contains at least one
        # complete cs-aligned row span: ceil(sr/cs)*cs + cs <= er
        def door_usable(sr, er, cs):
            first_fy = (sr + cs - 1) // cs
            return first_fy * cs + cs <= er

        usable_doors = [(sr, er, dw) for sr, er, dw in door_positions
                        if dw >= cs and door_usable(sr, er, cs)]
        if not usable_doors:
            print(f"  Fleet cs={cs}: no usable doors, skipping")
            continue

        # Separate free cells into left room and right room (in fleet coords)
        wall_fx = wall_col // cs  # fleet column of the wall
        left_cells = sorted([c for c in free_cells if c[0] < wall_fx])
        right_cells = sorted([c for c in free_cells if c[0] > wall_fx])

        # Filter to cells near usable doors (fleet row range)
        def near_door(fy, cs):
            for sr, er, dw in usable_doors:
                # Fleet cell fy covers base rows [fy*cs, (fy+1)*cs)
                # Door covers base rows [sr, er)
                # Fleet cell overlaps door if fy*cs < er and (fy+1)*cs > sr
                if fy * cs < er and (fy + 1) * cs > sr:
                    return True
                # Also allow cells within a few fleet cells of the door
                door_fy_min = sr // cs
                door_fy_max = (er - 1) // cs
                if abs(fy - door_fy_min) <= 3 or abs(fy - door_fy_max) <= 3:
                    return True
            return False

        left_near = [c for c in left_cells if near_door(c[1], cs)]
        right_near = [c for c in right_cells if near_door(c[1], cs)]

        if not left_near or not right_near:
            print(f"  Fleet cs={cs}: no valid start/goal cells near doors")
            continue

        placed = 0
        attempts = 0
        max_attempts = 2000

        # Track base-cell occupancy across all fleets to prevent overlap
        while placed < agents_per_fleet and attempts < max_attempts:
            attempts += 1
            start = random.choice(left_near)
            goal = random.choice(right_near)

            if start in occupied_fleet_starts[cs]:
                continue
            if goal in occupied_fleet_goals[cs]:
                continue

            # Check cross-fleet base-cell overlap
            s_base = set()
            g_base = set()
            for dy in range(cs):
                for dx in range(cs):
                    s_base.add((start[0] * cs + dx, start[1] * cs + dy))
                    g_base.add((goal[0] * cs + dx, goal[1] * cs + dy))

            overlap = False
            for a_cs, a_sx, a_sy, a_gx, a_gy in agents:
                for dy in range(a_cs):
                    for dx in range(a_cs):
                        if (a_sx + dx, a_sy + dy) in s_base:
                            overlap = True
                            break
                        if (a_gx + dx, a_gy + dy) in g_base:
                            overlap = True
                            break
                    if overlap:
                        break
                if overlap:
                    break

            if overlap:
                continue

            sx = start[0] * cs
            sy = start[1] * cs
            gx = goal[0] * cs
            gy = goal[1] * cs
            agents.append((cs, sx, sy, gx, gy))
            occupied_fleet_starts[cs].add(start)
            occupied_fleet_goals[cs].add(goal)
            placed += 1

        if placed < agents_per_fleet:
            print(f"  Fleet cs={cs}: only placed {placed}/{agents_per_fleet}")

    # Write .scen file
    scen_name = f"bottleneck_{map_size}.scen"
    scen_path = os.path.join(output_dir_scens, scen_name)
    with open(scen_path, 'w') as f:
        for cs, sx, sy, gx, gy in agents:
            f.write(f"{cs} {sx} {sy} {gx} {gy}\n")

    # Print summary
    print(f"\nMap: {map_size}x{map_size}")
    print(f"Map file: {map_path}")
    print(f"Scen file: {scen_path}")
    print(f"Dividing wall at column {wall_col}")
    print(f"Doors:")
    for sr, er, dw in door_positions:
        fits = [cs for cs in FLEET_SIZES if cs <= dw]
        print(f"  rows {sr}-{er-1}, width={dw}, fits fleets: {fits}")
    print(f"Agents: {len(agents)} total")
    for cs in FLEET_SIZES:
        n = sum(1 for a in agents if a[0] == cs)
        if n > 0:
            print(f"  Fleet cs={cs}: {n} agents")

    # ASCII preview
    print(f"\nASCII preview (first 40 rows):")
    preview_rows = min(40, map_size)
    for r in range(preview_rows):
        row_chars = list(''.join(grid[r]))
        for cs, sx, sy, gx, gy in agents:
            if sy <= r < sy + cs:
                for dx in range(cs):
                    if sx + dx < len(row_chars):
                        row_chars[sx + dx] = 'S'
            if gy <= r < gy + cs:
                for dx in range(cs):
                    if gx + dx < len(row_chars):
                        row_chars[gx + dx] = 'G'
        line = ''.join(row_chars)
        if len(line) > 80:
            line = line[:80] + "..."
        print(f"  {r:3d} {line}")
    if preview_rows < map_size:
        print(f"  ... ({map_size - preview_rows} more rows)")

    return map_path, scen_path


def main():
    parser = argparse.ArgumentParser(description="Bottleneck doors benchmark")
    parser.add_argument("--map_size", type=int, default=77,
                        help="map dimensions (77 is LCM-friendly for cs=7,11)")
    parser.add_argument("--door_widths", type=str, default="3,7,11",
                        help="comma-separated door widths (should match fleet cs values)")
    parser.add_argument("--agents_per_fleet", type=int, default=3)
    parser.add_argument("--output_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    door_widths = [int(x) for x in args.door_widths.split(",")]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = args.output_dir or os.path.dirname(script_dir)
    maps_dir = os.path.join(base_dir, "maps")
    scens_dir = os.path.join(base_dir, "scenarios")
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(scens_dir, exist_ok=True)

    generate(args.map_size, door_widths, args.agents_per_fleet,
             maps_dir, scens_dir, args.seed)


if __name__ == "__main__":
    main()
