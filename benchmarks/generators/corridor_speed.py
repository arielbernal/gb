#!/usr/bin/env python3
"""Generate a corridor speed benchmark map.

Layout: [open_left 28cols] -- [corridor_section ~49cols] -- [open_right 28cols]
All corridors connect to both open areas. Agents start left, goals right.
The challenge: agents must choose which corridor based on their size.

Map size: 105x105 (LCM of 1,3,5,7).
Fleet config: cs={1,3,5,7}.
"""
import argparse
import os
import random

FLEET_SIZES = [1, 3, 5, 7]


def parse_agents_per_fleet(s):
    result = {}
    for pair in s.split(","):
        cs_str, count_str = pair.split(":")
        result[int(cs_str)] = int(count_str)
    return result


def generate(map_size, agents_per_fleet, num_scenarios,
             output_dir_maps, output_dir_scens, seed_start=0):
    # ---- Build map ----
    grid = [['@' for _ in range(map_size)] for _ in range(map_size)]

    # Layout parameters
    open_width = 28  # columns for each open area
    corr_start_col = open_width  # corridor section starts here
    corr_end_col = map_size - open_width  # corridor section ends here

    # Carve left open area (cols 0..open_width-1, rows 0..map_size-1)
    for r in range(map_size):
        for c in range(open_width):
            grid[r][c] = '.'

    # Carve right open area
    for r in range(map_size):
        for c in range(map_size - open_width, map_size):
            grid[r][c] = '.'

    # Define corridors in the middle section, stacked vertically
    # Each corridor: (width, start_row). Walls between them.
    # Align start rows to LCM-friendly positions for fleet grids.
    # Corridor widths: 7, 5, 3, 1, 7, 5, 3, 1 (repeat to fill space)
    corridor_widths = [7, 7, 5, 5, 3, 3, 1, 1]
    wall_gap = 1  # wall rows between corridors

    corridors = []  # (start_row, end_row_exclusive, width)
    current_row = 0  # start from top

    for w in corridor_widths:
        # Align to fleet grid for the corridor width
        aligned = ((current_row + w - 1) // w) * w
        if aligned + w > map_size:
            break
        corridors.append((aligned, aligned + w, w))
        current_row = aligned + w + wall_gap

    # Carve corridors in the middle section, connecting to both open areas
    for sr, er, w in corridors:
        for r in range(sr, er):
            for c in range(corr_start_col, corr_end_col):
                grid[r][c] = '.'

    # Write .map file
    map_name = f"corridor_speed_{map_size}.map"
    map_path = os.path.join(output_dir_maps, map_name)
    with open(map_path, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {map_size}\n")
        f.write(f"width {map_size}\n")
        f.write("map\n")
        for row in grid:
            f.write(''.join(row) + '\n')

    print(f"Map: {map_size}x{map_size}")
    print(f"Open areas: cols [0,{open_width}) and [{map_size-open_width},{map_size})")
    print(f"Corridor section: cols [{corr_start_col},{corr_end_col})")
    print(f"Corridors ({len(corridors)}):")
    for sr, er, w in corridors:
        fits = [cs for cs in FLEET_SIZES if cs <= w]
        print(f"  rows [{sr},{er}), width={w}, fits: {fits}")

    # ---- Precompute free fleet cells ----
    def fleet_cells_free(cs):
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

    # ---- Classify cells into left/right open areas ----
    def get_left_right_cells(cs, free_cells):
        """Return (left_cells, right_cells) in the open areas."""
        left = []
        right = []
        for (fx, fy) in free_cells:
            bx = fx * cs
            # Left open area: base x + cs <= open_width
            if bx + cs <= open_width:
                left.append((fx, fy))
            # Right open area: base x >= map_size - open_width
            elif bx >= map_size - open_width:
                right.append((fx, fy))
        return left, right

    # ---- Validate: check wall overlaps ----
    def validate_placement(cs, fx, fy):
        for dy in range(cs):
            for dx in range(cs):
                bx = fx * cs + dx
                by = fy * cs + dy
                if bx >= map_size or by >= map_size:
                    return False
                if grid[by][bx] != '.':
                    return False
        return True

    # ---- Generate scenarios ----
    for seed_offset in range(num_scenarios):
        seed = seed_start + seed_offset
        random.seed(seed)

        agents = []
        occupied_starts = set()  # base cells
        occupied_goals = set()

        for cs in sorted(agents_per_fleet.keys(), reverse=True):
            count = agents_per_fleet[cs]
            free_cells, fw, fh = fleet_cells_free(cs)
            left, right = get_left_right_cells(cs, free_cells)

            if not left or not right:
                if seed_offset == 0:
                    print(f"  Fleet cs={cs}: no left/right cells")
                continue

            placed = 0
            attempts = 0
            max_attempts = 3000

            while placed < count and attempts < max_attempts:
                attempts += 1

                # Half go left->right, half right->left
                if random.random() < 0.5:
                    start_cell = random.choice(left)
                    goal_cell = random.choice(right)
                else:
                    start_cell = random.choice(right)
                    goal_cell = random.choice(left)

                if not validate_placement(cs, start_cell[0], start_cell[1]):
                    continue
                if not validate_placement(cs, goal_cell[0], goal_cell[1]):
                    continue

                # Build base footprints
                s_base = set()
                g_base = set()
                for dy in range(cs):
                    for dx in range(cs):
                        s_base.add((start_cell[0] * cs + dx, start_cell[1] * cs + dy))
                        g_base.add((goal_cell[0] * cs + dx, goal_cell[1] * cs + dy))

                if s_base & occupied_starts or g_base & occupied_goals:
                    continue

                sx = start_cell[0] * cs
                sy = start_cell[1] * cs
                gx = goal_cell[0] * cs
                gy = goal_cell[1] * cs
                agents.append((cs, sx, sy, gx, gy))
                occupied_starts |= s_base
                occupied_goals |= g_base
                placed += 1

            if placed < count and seed_offset == 0:
                print(f"  Fleet cs={cs}: placed {placed}/{count}")

        scen_name = f"corridor_speed_{map_size}_{seed_offset:02d}.scen"
        scen_path = os.path.join(output_dir_scens, scen_name)
        with open(scen_path, 'w') as f:
            for cs, sx, sy, gx, gy in agents:
                f.write(f"{cs} {sx} {sy} {gx} {gy}\n")

        if seed_offset == 0:
            print(f"\nScenario {scen_name}: {len(agents)} agents")
            for cs in sorted(agents_per_fleet.keys()):
                n = sum(1 for a in agents if a[0] == cs)
                if n > 0:
                    print(f"  Fleet cs={cs}: {n} agents")

    print(f"\nGenerated {num_scenarios} scenarios -> {output_dir_scens}")
    return map_path


def main():
    parser = argparse.ArgumentParser(description="Corridor speed benchmark")
    parser.add_argument("--map_size", type=int, default=105)
    parser.add_argument("--agents_per_fleet", type=str, default="1:12,3:5,5:4,7:4")
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

    generate(args.map_size, agents_per_fleet, args.num_scenarios,
             maps_dir, scens_dir, args.seed_start)


if __name__ == "__main__":
    main()
