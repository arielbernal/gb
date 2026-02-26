#!/usr/bin/env python3
"""Generate an intersection benchmark map.

Central open area (28x28+) with 4 corridors radiating N/S/E/W.
N,S: width 7 (all fleets). E: width 5 (cs<=5). W: width 3 (cs<=3).
Agents start in corridors, goals in opposite corridors.

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


def parse_corridor_widths(s):
    result = {}
    for pair in s.split(","):
        direction, width = pair.split(":")
        result[direction.strip()] = int(width)
    return result


def generate(map_size, center_size, corridor_widths, agents_per_fleet,
             num_scenarios, output_dir_maps, output_dir_scens, seed_start=0):
    grid = [['@' for _ in range(map_size)] for _ in range(map_size)]

    # Center area: aligned to 7 (largest fleet size)
    center_start = ((map_size // 2 - center_size // 2) // 7) * 7
    center_end = center_start + center_size
    # Snap center_end to multiple of 7
    center_end = ((center_end + 6) // 7) * 7
    center_size = center_end - center_start

    for r in range(center_start, center_end):
        for c in range(center_start, center_end):
            if r < map_size and c < map_size:
                grid[r][c] = '.'

    # Corridor widths
    nw = corridor_widths.get('N', 7)
    sw = corridor_widths.get('S', 7)
    ew = corridor_widths.get('E', 5)
    ww = corridor_widths.get('W', 3)

    corr_info = {}

    # N corridor: vertical, cols centered in center, rows 0..center_start
    n_col_start = ((center_start + center_size // 2 - nw // 2) // nw) * nw
    n_col_end = n_col_start + nw
    for r in range(0, center_start):
        for c in range(n_col_start, n_col_end):
            grid[r][c] = '.'
    corr_info['N'] = (0, center_start, n_col_start, n_col_end, nw)

    # S corridor
    s_col_start = ((center_start + center_size // 2 - sw // 2) // sw) * sw
    s_col_end = s_col_start + sw
    for r in range(center_end, map_size):
        for c in range(s_col_start, s_col_end):
            grid[r][c] = '.'
    corr_info['S'] = (center_end, map_size, s_col_start, s_col_end, sw)

    # E corridor: horizontal, rows centered in center, cols center_end..map_size
    e_row_start = ((center_start + center_size // 2 - ew // 2) // ew) * ew
    e_row_end = e_row_start + ew
    for r in range(e_row_start, e_row_end):
        for c in range(center_end, map_size):
            grid[r][c] = '.'
    corr_info['E'] = (e_row_start, e_row_end, center_end, map_size, ew)

    # W corridor
    w_row_start = ((center_start + center_size // 2 - ww // 2) // ww) * ww
    w_row_end = w_row_start + ww
    for r in range(w_row_start, w_row_end):
        for c in range(0, center_start):
            grid[r][c] = '.'
    corr_info['W'] = (w_row_start, w_row_end, 0, center_start, ww)

    # Write .map file
    map_name = f"intersection_{map_size}.map"
    map_path = os.path.join(output_dir_maps, map_name)
    with open(map_path, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {map_size}\n")
        f.write(f"width {map_size}\n")
        f.write("map\n")
        for row in grid:
            f.write(''.join(row) + '\n')

    print(f"Map: {map_size}x{map_size}")
    print(f"Center: [{center_start},{center_end}) = {center_size}x{center_size}")
    for d, (r0, r1, c0, c1, w) in corr_info.items():
        fits = [cs for cs in FLEET_SIZES if cs <= w]
        print(f"  {d}: rows [{r0},{r1}), cols [{c0},{c1}), width={w}, fits: {fits}")

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

    # ---- Find endpoint cells per corridor per fleet ----
    def get_corridor_endpoints(cs, free_cells):
        center_mid_r = (center_start + center_end) // 2
        center_mid_c = (center_start + center_end) // 2
        endpoints = {}

        for d, (r0, r1, c0, c1, w) in corr_info.items():
            if w < cs:
                continue

            cells = []
            for (fx, fy) in free_cells:
                bx = fx * cs
                by = fy * cs

                # In the corridor itself (not in center)
                in_corr = False
                if d == 'N' and by + cs <= center_start and bx >= c0 and bx + cs <= c1:
                    in_corr = True
                elif d == 'S' and by >= center_end and bx >= c0 and bx + cs <= c1:
                    in_corr = True
                elif d == 'E' and bx >= center_end and by >= r0 and by + cs <= r1:
                    in_corr = True
                elif d == 'W' and bx + cs <= center_start and by >= r0 and by + cs <= r1:
                    in_corr = True

                # In center area near this corridor's side
                in_center_near = False
                if (bx >= center_start and bx + cs <= center_end and
                        by >= center_start and by + cs <= center_end):
                    if d == 'N' and by + cs <= center_mid_r:
                        in_center_near = True
                    elif d == 'S' and by >= center_mid_r:
                        in_center_near = True
                    elif d == 'E' and bx >= center_mid_c:
                        in_center_near = True
                    elif d == 'W' and bx + cs <= center_mid_c:
                        in_center_near = True

                if in_corr or in_center_near:
                    cells.append((fx, fy))

            if cells:
                endpoints[d] = cells
        return endpoints

    # ---- Validate placement ----
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
        occupied_starts = set()
        occupied_goals = set()

        for cs in sorted(agents_per_fleet.keys(), reverse=True):
            count = agents_per_fleet[cs]
            free_cells, fw, fh = fleet_cells_free(cs)
            endpoints = get_corridor_endpoints(cs, free_cells)

            usable_dirs = list(endpoints.keys())
            if len(usable_dirs) < 2:
                if seed_offset == 0:
                    print(f"  Fleet cs={cs}: only {len(usable_dirs)} usable dirs")
                continue

            placed = 0
            attempts = 0
            max_attempts = 3000

            while placed < count and attempts < max_attempts:
                attempts += 1

                start_dir = random.choice(usable_dirs)
                goal_dir = random.choice([d for d in usable_dirs if d != start_dir])

                start = random.choice(endpoints[start_dir])
                goal = random.choice(endpoints[goal_dir])

                if not validate_placement(cs, start[0], start[1]):
                    continue
                if not validate_placement(cs, goal[0], goal[1]):
                    continue

                s_base = set()
                g_base = set()
                for dy in range(cs):
                    for dx in range(cs):
                        s_base.add((start[0] * cs + dx, start[1] * cs + dy))
                        g_base.add((goal[0] * cs + dx, goal[1] * cs + dy))

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

        scen_name = f"intersection_{map_size}_{seed_offset:02d}.scen"
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
    parser = argparse.ArgumentParser(description="Intersection benchmark")
    parser.add_argument("--map_size", type=int, default=105)
    parser.add_argument("--center_size", type=int, default=35,
                        help="central open area size (will snap to multiple of 7)")
    parser.add_argument("--corridor_widths", type=str, default="N:7,S:7,E:5,W:3")
    parser.add_argument("--agents_per_fleet", type=str, default="1:12,3:5,5:4,7:4")
    parser.add_argument("--num_scenarios", type=int, default=25)
    parser.add_argument("--seed_start", type=int, default=0)
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()

    corridor_widths = parse_corridor_widths(args.corridor_widths)
    agents_per_fleet = parse_agents_per_fleet(args.agents_per_fleet)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = args.output_dir or os.path.dirname(script_dir)
    maps_dir = os.path.join(base_dir, "maps")
    scens_dir = os.path.join(base_dir, "scenarios")
    os.makedirs(maps_dir, exist_ok=True)
    os.makedirs(scens_dir, exist_ok=True)

    generate(args.map_size, args.center_size, corridor_widths, agents_per_fleet,
             args.num_scenarios, maps_dir, scens_dir, args.seed_start)


if __name__ == "__main__":
    main()
