#!/usr/bin/env python3
"""Generate scenario files in pibt_rs format from our HetPIBT .scen files.

pibt_rs format (one agent per line):
  agent_id fleet_id footprint_size velocity start_x start_y goal_x goal_y grid_width grid_height

Where start_x/start_y/goal_x/goal_y are real-world (float) coordinates.
For pibt_rs, fleet grid = base_grid / footprint_size (non-overlapping cells).
Our solver uses sliding window: fleet grid = base_grid - footprint_size + 1.

This tool converts our (fleet-graph) coordinates to real-world coordinates
that both solvers can interpret correctly for their own grid models.
"""
import sys
import re


def parse_our_scen(path):
    """Parse our scenario format. Returns fleet_defs and agents."""
    fleet_defs = {}  # fid -> (cell_size, speed)
    agents = []  # list of (agent_id, fleet_id, start_x, start_y, goal_x, goal_y)

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('fleets='):
                for fd in line[7:].split(';'):
                    parts = fd.split(':')
                    fid = int(parts[0])
                    cs = int(parts[1])
                    speed = float(parts[2])
                    fleet_defs[fid] = (cs, speed)
            elif line.startswith('agents='):
                for agent_def in line[7:].split(';'):
                    parts = agent_def.split(':')
                    aid = int(parts[0])
                    fid = int(parts[1])
                    sm = re.match(r'\((\d+),(\d+)\)', parts[2])
                    gm = re.match(r'\((\d+),(\d+)\)', parts[3])
                    sx, sy = int(sm.group(1)), int(sm.group(2))
                    gx, gy = int(gm.group(1)), int(gm.group(2))
                    agents.append((aid, fid, sx, sy, gx, gy))
    return fleet_defs, agents


def main():
    if len(sys.argv) < 4:
        print("Usage: python gen_pibt_rs_scenario.py <our_scen_file> <map_width> <map_height> [output_file]")
        print("  Generates pibt_rs format scenario from our scenario format.")
        sys.exit(1)

    our_scen = sys.argv[1]
    base_w = int(sys.argv[2])
    base_h = int(sys.argv[3])
    out_file = sys.argv[4] if len(sys.argv) > 4 else None

    fleet_defs, agents = parse_our_scen(our_scen)

    lines = []
    for aid, fid, sx, sy, gx, gy in agents:
        cs, speed = fleet_defs[fid]
        # Our fleet coords are in the sliding-window space.
        # The top-left base-grid cell of fleet position (fx, fy) is at (fx, fy).
        # For pibt_rs, we need real-world coordinates.
        # pibt_rs uses: fleet_coord = floor(real_world / scale)
        # So real_world = fleet_coord * scale + offset
        # Our sliding window: fleet_coord IS the base-grid top-left.
        # For cs=1: real_world coords = fleet coords (trivial)
        # For cs>1: the agent center is at (fx + cs/2, fy + cs/2) in base grid,
        #   but pibt_rs uses top-left convention too.
        # Simplest: use the base-grid top-left as real-world coordinate.
        # pibt_rs will compute: fleet_coord = floor(real_world / scale)
        # For cs=1: fleet_coord = floor(fx / 1) = fx  ✓
        # For cs=2: fleet_coord = floor(fx / 2) — but our fx can be any value,
        #   not just multiples of 2. This is the fundamental incompatibility.

        # For a fair comparison, we need to ensure both solvers get the same
        # logical start/goal. Since the grid models differ, we pass real-world
        # coordinates that are valid in BOTH models:
        # - Our solver: fleet_coord = real_world (for sliding window, the coord IS the base pos)
        # - pibt_rs: fleet_coord = floor(real_world / scale)

        # For cs=1 agents, the grids are identical.
        # For cs>1 agents, we multiply our fleet coords by cs to get the real-world
        # position that pibt_rs expects (since pibt_rs divides by cs).
        real_sx = float(sx * cs)
        real_sy = float(sy * cs)
        real_gx = float(gx * cs)
        real_gy = float(gy * cs)

        # pibt_rs grid dimensions = base_grid / scale (integer division)
        grid_w = base_w // cs
        grid_h = base_h // cs

        line = f"{aid} {fid} {float(cs)} {speed} {real_sx} {real_sy} {real_gx} {real_gy} {grid_w} {grid_h}"
        lines.append(line)

    output = '\n'.join(lines) + '\n'

    if out_file:
        with open(out_file, 'w') as f:
            f.write(output)
        print(f"Wrote {len(lines)} agents to {out_file}")
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
