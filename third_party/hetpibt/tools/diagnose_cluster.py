#!/usr/bin/env python3
"""Diagnose agent clustering in HetPIBT results.

Reads result file, finds timesteps where many agents are in the same area,
and prints diagnostic info about their goals, positions, and local connectivity.
"""
import sys
import re
from collections import defaultdict, Counter


def load_map(path):
    with open(path) as f:
        lines = f.readlines()
    grid_start = 0
    width = height = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line == "map":
            grid_start = i + 1
            break
        parts = line.split()
        if len(parts) == 2:
            if parts[0] == "width":
                width = int(parts[1])
            elif parts[0] == "height":
                height = int(parts[1])
    grid = []
    for i in range(grid_start, grid_start + height):
        row = lines[i].rstrip("\n")
        grid.append([c == '.' or c == 'G' or c == 'S' for c in row])
    return width, height, grid


def neighbors(x, y, w, h, grid):
    """Return passable neighbors of (x,y)."""
    result = []
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
            result.append((nx, ny))
    return result


def parse_result(path):
    """Parse result file, return (fleets, agent_fleet, solutions, starts, goals)."""
    fleets = {}
    agent_fleet = []
    solutions = {}
    starts = {}
    goals = {}
    in_solution = False

    with open(path) as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("fleets="):
                for fd in line[len("fleets="):].split(";"):
                    parts = fd.split(":")
                    fid = int(parts[0])
                    fleets[fid] = {"cell_size": int(parts[1]), "speed": float(parts[2]),
                                   "width": int(parts[3]), "height": int(parts[4])}
            elif line.startswith("agent_fleet="):
                agent_fleet = [int(x) for x in line[len("agent_fleet="):].split(",")]
            elif line.startswith("starts="):
                for i, m in enumerate(re.finditer(r"\((\d+),(\d+)\)", line)):
                    starts[i] = (int(m.group(1)), int(m.group(2)))
            elif line.startswith("goals="):
                for i, m in enumerate(re.finditer(r"\((\d+),(\d+)\)", line)):
                    goals[i] = (int(m.group(1)), int(m.group(2)))
            elif line == "solution":
                in_solution = True
                solutions = {}
            elif in_solution:
                if line[0].isdigit():
                    fc = line.index(":")
                    sc = line.index(":", fc+1)
                    aid = int(line[:fc])
                    fid = int(line[fc+1:sc])
                    path = []
                    for m in re.finditer(r"\((\d+),(\d+)\)@(\d+)", line[sc+1:]):
                        path.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
                    solutions[aid] = (fid, path)
                else:
                    in_solution = False
    return fleets, agent_fleet, solutions, starts, goals


def main():
    if len(sys.argv) < 3:
        print("Usage: python diagnose_cluster.py <map_file> <result_file> [timestep]")
        sys.exit(1)

    map_file = sys.argv[1]
    result_file = sys.argv[2]
    target_t = int(sys.argv[3]) if len(sys.argv) > 3 else None

    w, h, grid = load_map(map_file)
    fleets, agent_fleet, solutions, starts, goals = parse_result(result_file)

    # Find last position of each agent
    agent_last_pos = {}
    max_t = 0
    for aid, (fid, path) in solutions.items():
        if path:
            last = path[-1]
            agent_last_pos[aid] = (last[0], last[1], last[2])
            max_t = max(max_t, last[2])

    # Determine which agents did NOT reach their goal
    unreached = []
    for aid in sorted(solutions.keys()):
        fid = agent_fleet[aid]
        cs = fleets[fid]["cell_size"]
        if aid not in goals:
            continue
        gx, gy = goals[aid]
        lx, ly, lt = agent_last_pos.get(aid, (0, 0, 0))
        if (lx, ly) != (gx, gy):
            unreached.append(aid)

    print(f"Total agents: {len(solutions)}")
    print(f"Unreached goals: {len(unreached)}")
    print(f"Max timestep: {max_t}")
    print()

    # For unreached agents, look at their final positions
    if target_t is None:
        target_t = max_t

    # Get positions at target_t
    pos_at_t = {}
    for aid, (fid, path) in solutions.items():
        # Find position at target_t
        pos = None
        for x, y, t in path:
            if t <= target_t:
                pos = (x, y)
            else:
                break
        if pos:
            pos_at_t[aid] = pos

    # Find clusters: group agents by 8x8 grid region
    region_agents = defaultdict(list)
    for aid, (x, y) in pos_at_t.items():
        rx, ry = x // 8, y // 8
        region_agents[(rx, ry)].append(aid)

    # Sort by density
    dense_regions = sorted(region_agents.items(), key=lambda kv: -len(kv[1]))

    print(f"=== Top 5 densest 8x8 regions at t={target_t} ===")
    for (rx, ry), agents in dense_regions[:5]:
        cs1_agents = [a for a in agents if fleets[agent_fleet[a]]["cell_size"] == 1]
        cs2_agents = [a for a in agents if fleets[agent_fleet[a]]["cell_size"] == 2]
        cs3_agents = [a for a in agents if fleets[agent_fleet[a]]["cell_size"] == 3]
        unreached_here = [a for a in agents if a in unreached]
        print(f"\nRegion ({rx*8}-{rx*8+7}, {ry*8}-{ry*8+7}): {len(agents)} agents "
              f"(cs1={len(cs1_agents)}, cs2={len(cs2_agents)}, cs3={len(cs3_agents)}), "
              f"{len(unreached_here)} unreached")

        # Print exact cell occupancy
        cell_count = Counter()
        for aid in agents:
            cell_count[pos_at_t[aid]] += 1

        # connectivity of this region
        region_cells = set()
        for y in range(ry*8, min(ry*8+8, h)):
            for x in range(rx*8, min(rx*8+8, w)):
                if grid[y][x]:
                    region_cells.add((x, y))

        # Count corridor cells (<=2 neighbors) vs open (>=3)
        corridor_cells = sum(1 for (cx,cy) in region_cells
                             if len(neighbors(cx, cy, w, h, grid)) <= 2)
        open_cells = len(region_cells) - corridor_cells

        # Entry/exit points (cells in region with neighbors outside region)
        entry_points = set()
        for (cx, cy) in region_cells:
            for nx, ny in neighbors(cx, cy, w, h, grid):
                if (nx, ny) not in region_cells:
                    entry_points.add((cx, cy))

        print(f"  Passable cells: {len(region_cells)} (corridor={corridor_cells}, open={open_cells})")
        print(f"  Entry/exit points: {len(entry_points)}")

        # Goals of agents in this cluster
        goal_regions = Counter()
        for aid in cs1_agents[:20]:  # sample
            if aid in goals:
                gx, gy = goals[aid]
                goal_regions[(gx//8, gy//8)] += 1
        if goal_regions:
            print(f"  Goal distribution (sampled cs=1 agents):")
            for (grx, gry), cnt in goal_regions.most_common(5):
                print(f"    Region ({grx*8}-{grx*8+7}, {gry*8}-{gry*8+7}): {cnt} agents")

        # Show unreached agents detail
        for aid in unreached_here[:5]:
            x, y = pos_at_t[aid]
            gx, gy = goals[aid]
            fid = agent_fleet[aid]
            cs = fleets[fid]["cell_size"]
            n_nbrs = len(neighbors(x, y, w, h, grid))
            print(f"  Agent {aid}: cs={cs} at ({x},{y}) [{n_nbrs} nbrs] -> goal ({gx},{gy}) "
                  f"[dist ~{abs(gx-x)+abs(gy-y)}]")

    # Overall statistics for unreached agents
    print(f"\n=== Unreached agent analysis ({len(unreached)} agents) ===")
    cs_counts = Counter(fleets[agent_fleet[a]]["cell_size"] for a in unreached)
    print(f"By fleet: {dict(cs_counts)}")

    # How spread out are unreached agents?
    unreached_regions = Counter()
    for aid in unreached:
        if aid in pos_at_t:
            x, y = pos_at_t[aid]
            unreached_regions[(x//8, y//8)] += 1
    print(f"\nUnreached agents by region (top 10):")
    for (rx, ry), cnt in unreached_regions.most_common(10):
        print(f"  Region ({rx*8}-{rx*8+7}, {ry*8}-{ry*8+7}): {cnt} unreached")

    # Check if unreached agents are oscillating
    print(f"\n=== Oscillation analysis (unreached cs=1 agents) ===")
    cs1_unreached = [a for a in unreached if fleets[agent_fleet[a]]["cell_size"] == 1]
    for aid in cs1_unreached[:10]:
        fid, path = solutions[aid]
        if len(path) < 10:
            continue
        # Look at last 20 positions
        last20 = path[-20:]
        positions = [(x,y) for x,y,t in last20]
        unique = len(set(positions))
        visits = Counter(positions)
        most_common = visits.most_common(3)
        gx, gy = goals[aid]
        print(f"  Agent {aid}: last 20 moves visit {unique} unique cells, "
              f"goal=({gx},{gy}), top cells: {most_common}")


if __name__ == "__main__":
    sys.exit(main() or 0)
