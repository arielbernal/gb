#!/usr/bin/env python3
"""Convert benchmarks .scen format to het_bench format for the HetPIBT solver.

Input format:  fleet_cs start_x start_y goal_x goal_y
Output format: agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h

Snaps positions to fleet grid boundaries (non-overlapping tiling).
"""
import argparse
import sys


# Fleet definitions: cs -> (fleet_id, velocity)
FLEET_DEFS = {
    1:  (0, 1.0),
    3:  (1, 0.33),
    7:  (2, 0.14),
    11: (3, 0.09),
}


def load_map(map_path):
    """Load .map and return grid as list of strings."""
    grid = []
    reading = False
    width = height = 0
    with open(map_path) as f:
        for line in f:
            line = line.rstrip('\n\r')
            if line == "map":
                reading = True
                continue
            if reading and line:
                grid.append(line)
            elif 'width' in line:
                width = int(line.split()[1])
            elif 'height' in line:
                height = int(line.split()[1])
    return grid, width, height


def is_fleet_cell_free(grid, fx, fy, cs, width, height):
    """Check if fleet cell (fx, fy) with cell_size cs is all free."""
    bx = fx * cs
    by = fy * cs
    if bx + cs > width or by + cs > height:
        return False
    for dy in range(cs):
        for dx in range(cs):
            if grid[by + dy][bx + dx] != '.':
                return False
    return True


def convert(scen_path, map_path, output_path):
    grid, width, height = load_map(map_path)

    agents = []
    with open(scen_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            cs, sx, sy, gx, gy = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
            agents.append((cs, sx, sy, gx, gy))

    with open(output_path, 'w') as f:
        for i, (cs, sx, sy, gx, gy) in enumerate(agents):
            fleet_id, velocity = FLEET_DEFS.get(cs, (0, 1.0))
            # Snap to fleet grid
            fx_s = sx // cs
            fy_s = sy // cs
            fx_g = gx // cs
            fy_g = gy // cs
            # Convert back to real-world coords (fleet-aligned)
            rw_sx = fx_s * cs
            rw_sy = fy_s * cs
            rw_gx = fx_g * cs
            rw_gy = fy_g * cs
            grid_w = width // cs
            grid_h = height // cs

            # Validate fleet cells are free
            if not is_fleet_cell_free(grid, fx_s, fy_s, cs, width, height):
                print(f"WARNING: agent {i} cs={cs} start ({fx_s},{fy_s}) -> base ({rw_sx},{rw_sy}) is blocked")
            if not is_fleet_cell_free(grid, fx_g, fy_g, cs, width, height):
                print(f"WARNING: agent {i} cs={cs} goal ({fx_g},{fy_g}) -> base ({rw_gx},{rw_gy}) is blocked")

            f.write(f"{i} {fleet_id} {cs} {velocity} {rw_sx} {rw_sy} {rw_gx} {rw_gy} {grid_w} {grid_h}\n")

    print(f"Converted {len(agents)} agents -> {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scen", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    convert(args.scen, args.map, args.output)


if __name__ == "__main__":
    main()
