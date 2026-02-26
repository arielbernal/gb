#!/usr/bin/env python3
"""Convert het_lacam result format to hetpibt result format for visualization.

het_lacam format:
  starts=(x,y),(x,y),...     # base-grid coords
  goals=(x,y),(x,y),...
  solution=
  0:(x0,y0),(x1,y1),...      # timestep: fleet-grid coords per agent

hetpibt format:
  fleets=0:cs:vel:gw:gh;1:cs:vel:gw:gh;...
  agent_fleet=fid0,fid1,...
  starts=(fx,fy),(fx,fy),...  # fleet-grid coords
  goals=(fx,fy),(fx,fy),...
  solution
  aid:fid:(fx,fy)@t,(fx,fy)@t,...
"""
import argparse
import re
import os


def load_scen(scen_path):
    """Load het_bench scenario to get fleet assignments and info."""
    agents = []
    fleets = {}
    with open(scen_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 10:
                continue
            aid = int(parts[0])
            fid = int(parts[1])
            cs = int(parts[2])
            vel = float(parts[3])
            sx, sy = int(parts[4]), int(parts[5])
            gx, gy = int(parts[6]), int(parts[7])
            gw, gh = int(parts[8]), int(parts[9])
            agents.append({
                "id": aid, "fleet_id": fid, "cs": cs, "vel": vel,
                "sx": sx, "sy": sy, "gx": gx, "gy": gy,
                "gw": gw, "gh": gh,
            })
            if fid not in fleets:
                fleets[fid] = {"cs": cs, "vel": vel, "gw": gw, "gh": gh}
    return agents, fleets


def convert(lacam_result, scen_path, output_path):
    agents, fleets = load_scen(scen_path)
    N = len(agents)

    # Parse het_lacam result
    meta = {}
    solution_lines = []
    in_solution = False

    with open(lacam_result) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if in_solution:
                solution_lines.append(line)
                continue
            if line.startswith("solution="):
                in_solution = True
                # Check if there's content after "solution="
                rest = line[len("solution="):]
                if rest:
                    solution_lines.append(rest)
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                meta[key] = val

    # Parse timestep-oriented solution into agent trajectories
    # Format: t:(x0,y0),(x1,y1),...
    trajectories = {i: [] for i in range(N)}

    for line in solution_lines:
        m = re.match(r"^(\d+):(.*)", line)
        if not m:
            continue
        t = int(m.group(1))
        coords = re.findall(r"\((-?\d+),(-?\d+)\)", m.group(2))
        for i, (x, y) in enumerate(coords):
            if i < N:
                trajectories[i].append((t, int(x), int(y)))

    # Build hetpibt format
    # Fleet line
    fleet_parts = []
    for fid in sorted(fleets):
        f = fleets[fid]
        fleet_parts.append(f"{fid}:{f['cs']}:{f['vel']}:{f['gw']}:{f['gh']}")
    fleet_line = ";".join(fleet_parts)

    # Agent fleet assignments
    agent_fleet_ids = [a["fleet_id"] for a in agents]

    # Starts/goals in fleet-grid coords
    starts_fg = []
    goals_fg = []
    for a in agents:
        cs = a["cs"]
        starts_fg.append((a["sx"] // cs, a["sy"] // cs))
        goals_fg.append((a["gx"] // cs, a["gy"] // cs))

    with open(output_path, 'w') as f:
        f.write(f"agents={N}\n")
        f.write(f"map_name={meta.get('map_file', 'unknown')}\n")
        f.write(f"seed={meta.get('seed', '0')}\n")
        f.write(f"solver=het_lacam\n")
        f.write(f"comp_time(ms)={meta.get('comp_time', '0')}\n")
        f.write(f"makespan={meta.get('makespan', '0')}\n")
        f.write(f"sum_of_costs={meta.get('soc', '0')}\n")
        f.write(f"fleets={fleet_line}\n")
        f.write(f"agent_fleet={','.join(str(x) for x in agent_fleet_ids)}\n")

        # starts in fleet-grid
        f.write("starts=" + ",".join(f"({x},{y})" for x, y in starts_fg) + "\n")
        f.write("goals=" + ",".join(f"({x},{y})" for x, y in goals_fg) + "\n")

        f.write("solution\n")
        for aid in range(N):
            fid = agent_fleet_ids[aid]
            traj = trajectories.get(aid, [])
            # het_lacam solution coords are fleet-grid coords (v->x, v->y)
            # Write as (fx,fy)@t
            entries = ",".join(f"({fx},{fy})@{t}" for t, fx, fy in traj)
            f.write(f"{aid}:{fid}:{entries}\n")

    print(f"Converted {N} agents, {len(solution_lines)} timesteps -> {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lacam", required=True, help="het_lacam result file")
    parser.add_argument("--scen", required=True, help="het_bench scenario file")
    parser.add_argument("--output", required=True, help="output in hetpibt format")
    args = parser.parse_args()
    convert(args.lacam, args.scen, args.output)


if __name__ == "__main__":
    main()
