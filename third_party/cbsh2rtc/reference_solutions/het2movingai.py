#!/usr/bin/env python3
"""Convert het_bench scenario files to MovingAI .scen format (cs=1 agents only).

het_bench format (per line):
  agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h

With --swap-xy convention (used in our regression):
  sx = row index, sy = column index

MovingAI .scen format:
  version 1
  bucket  map_name  width  height  start_col  start_row  goal_col  goal_row  optimal_length
"""
import sys
import os

def convert(scen_path, map_name, output_path, map_width=120, map_height=120):
    agents = []
    with open(scen_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 10:
                continue
            agent_id = int(parts[0])
            fleet_id = int(parts[1])
            cell_size = int(parts[2])
            velocity = float(parts[3])
            sx, sy, gx, gy = int(parts[4]), int(parts[5]), int(parts[6]), int(parts[7])

            # Only cs=1 agents (homogeneous for CBS)
            if cell_size != 1:
                continue

            # With --swap-xy convention: sx=row, sy=col
            start_row, start_col = sx, sy
            goal_row, goal_col = gx, gy

            agents.append((start_col, start_row, goal_col, goal_row))

    with open(output_path, 'w') as f:
        f.write("version 1\n")
        for i, (sc, sr, gc, gr) in enumerate(agents):
            # bucket  map  width  height  start_col  start_row  goal_col  goal_row  optimal
            f.write(f"0\t{map_name}\t{map_width}\t{map_height}\t{sc}\t{sr}\t{gc}\t{gr}\t0\n")

    print(f"{scen_path} -> {output_path}: {len(agents)} cs=1 agents")
    return len(agents)

if __name__ == "__main__":
    scen_dir = "E:/gb/benchmarks/scenarios/het_bench"
    out_dir = "E:/gb/agents/center/temp/movingai_scens"
    os.makedirs(out_dir, exist_ok=True)

    map_name = "room120.map"
    total = 0
    for i in range(10):
        scen_path = os.path.join(scen_dir, f"scen.{i}")
        out_path = os.path.join(out_dir, f"scen.{i}.scen")
        n = convert(scen_path, map_name, out_path)
        total += n
    print(f"\nTotal: {total} cs=1 agents across 10 scenarios")
