#!/usr/bin/env python3
"""
Check for collisions between agents in a HetPIBT result file.

A collision occurs when two agents occupy the same base-grid cell at the same
timestep.  Each agent belongs to a fleet with a given cell_size.  A fleet-graph
position (fx, fy) maps to base-grid top-left corner (fx * cell_size, fy * cell_size),
and the agent occupies the cs x cs block of base cells from there.

Usage:
    python check_collisions.py <result_file>
"""

import sys
import re
from collections import defaultdict


def parse_fleet_line(line):
    """Parse the fleets line and return a dict mapping fleet_id -> dict with
    cell_size, speed, width, height."""
    # Format: fleets=0:1:1:30:30;1:2:0.5:15:15;2:3:0.3:10:10
    fleets = {}
    fleet_defs = line.split(";")
    for fd in fleet_defs:
        parts = fd.split(":")
        fleet_id = int(parts[0])
        cell_size = int(parts[1])
        speed = float(parts[2])
        width = int(parts[3])
        height = int(parts[4])
        fleets[fleet_id] = {
            "cell_size": cell_size,
            "speed": speed,
            "width": width,
            "height": height,
        }
    return fleets


def parse_agent_fleet(line):
    """Parse agent_fleet line into a list where index i gives the fleet_id of
    agent i."""
    return [int(x) for x in line.split(",")]


def parse_solution_line(line):
    """Parse a single solution line.

    Format: agent_id:fleet_id:(x,y)@t,(x,y)@t,...
    Returns (agent_id, fleet_id, list of (x, y, t) tuples).
    """
    # Split into at most 3 parts on ':', but the third part contains ':'
    # Actually the format is agent_id:fleet_id:(x,y)@t,...
    # We need to split carefully.
    first_colon = line.index(":")
    second_colon = line.index(":", first_colon + 1)
    agent_id = int(line[:first_colon])
    fleet_id = int(line[first_colon + 1 : second_colon])
    path_str = line[second_colon + 1 :]

    # Parse path entries: (x,y)@t
    path = []
    for entry in re.findall(r"\((\d+),(\d+)\)@(\d+)", path_str):
        x, y, t = int(entry[0]), int(entry[1]), int(entry[2])
        path.append((x, y, t))

    return agent_id, fleet_id, path


def get_occupied_base_cells(fx, fy, cell_size):
    """Return the set of base-grid cells occupied by an agent at fleet-graph
    position (fx, fy) with the given cell_size.

    Non-overlapping tiling: fleet cell (fx, fy) covers base cells
    [fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs).
    """
    cells = set()
    for dx in range(cell_size):
        for dy in range(cell_size):
            cells.add((fx * cell_size + dx, fy * cell_size + dy))
    return cells


def interpolate_path(path):
    """Given a sparse path [(x, y, t), ...], produce a dict mapping every
    integer timestep to (x, y).

    Between waypoints the agent is assumed to stay at the previous waypoint
    position (wait) or move linearly.  Since HetPIBT outputs every timestep
    the agent acts on, we simply fill gaps by holding position at the last
    known waypoint until the next one."""
    if not path:
        return {}
    pos_at_t = {}
    for i, (x, y, t) in enumerate(path):
        if i == 0:
            pos_at_t[t] = (x, y)
        else:
            prev_x, prev_y, prev_t = path[i - 1]
            # Fill any gap by holding at the previous position
            for fill_t in range(prev_t + 1, t):
                pos_at_t[fill_t] = (prev_x, prev_y)
            pos_at_t[t] = (x, y)
    return pos_at_t


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_collisions.py <result_file>")
        sys.exit(1)

    result_file = sys.argv[1]

    fleets = None
    agent_fleet_list = None
    solutions = {}  # agent_id -> (fleet_id, path)

    in_solution = False

    with open(result_file, "r") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("fleets="):
                fleets = parse_fleet_line(line[len("fleets=") :])
                in_solution = False
            elif line.startswith("agent_fleet="):
                agent_fleet_list = parse_agent_fleet(line[len("agent_fleet=") :])
            elif line == "solution":
                in_solution = True
                solutions = {}  # Reset for this solution block
            elif in_solution:
                # Solution lines start with a digit (agent_id)
                if line[0].isdigit():
                    agent_id, fleet_id, path = parse_solution_line(line)
                    solutions[agent_id] = (fleet_id, path)
                else:
                    in_solution = False

    if fleets is None:
        print("ERROR: No 'fleets=' line found in result file.")
        sys.exit(1)
    if agent_fleet_list is None:
        print("ERROR: No 'agent_fleet=' line found in result file.")
        sys.exit(1)
    if not solutions:
        print("ERROR: No solution lines found in result file.")
        sys.exit(1)

    num_agents = len(solutions)
    print(f"Parsed {num_agents} agent paths")
    print(f"Fleets: {fleets}")
    print()

    # Build per-agent position timeline
    agent_positions = {}  # agent_id -> {t: (fx, fy)}
    max_timestep = 0
    for agent_id, (fleet_id, path) in solutions.items():
        pos_at_t = interpolate_path(path)
        agent_positions[agent_id] = (fleet_id, pos_at_t)
        if pos_at_t:
            max_timestep = max(max_timestep, max(pos_at_t.keys()))

    print(f"Makespan (max timestep): {max_timestep}")
    print(f"Checking for collisions at each timestep...")
    print()

    collisions = []
    agent_ids = sorted(solutions.keys())

    for t in range(max_timestep + 1):
        # Collect occupied base cells for each agent at this timestep
        # Map base_cell -> list of agent_ids occupying it
        cell_to_agents = defaultdict(list)

        for agent_id in agent_ids:
            fleet_id, pos_at_t = agent_positions[agent_id]
            if t not in pos_at_t:
                continue
            fx, fy = pos_at_t[t]
            cs = fleets[fleet_id]["cell_size"]
            occupied = get_occupied_base_cells(fx, fy, cs)
            for cell in occupied:
                cell_to_agents[cell].append(agent_id)

        # Check for collisions (cells with more than one agent)
        for cell, agents in cell_to_agents.items():
            if len(agents) > 1:
                # Record collision between each pair
                for i in range(len(agents)):
                    for j in range(i + 1, len(agents)):
                        collisions.append((t, cell, agents[i], agents[j]))

    # Report results
    if not collisions:
        print("NO COLLISIONS DETECTED. The solution is collision-free.")
    else:
        # Deduplicate: for a given timestep and agent pair, multiple base
        # cells might overlap. Count unique (timestep, agent_i, agent_j) pairs.
        unique_pairs = set()
        for t, cell, a1, a2 in collisions:
            pair = (t, min(a1, a2), max(a1, a2))
            unique_pairs.add(pair)

        print(f"COLLISIONS DETECTED!")
        print(f"  Total overlapping base cells across all timesteps: {len(collisions)}")
        print(f"  Unique (timestep, agent_pair) collisions: {len(unique_pairs)}")
        print()

        # Show details of first 20 collisions (by base-cell overlap)
        show_count = min(20, len(collisions))
        print(f"First {show_count} base-cell collision details:")
        print("-" * 72)
        for idx in range(show_count):
            t, cell, a1, a2 = collisions[idx]
            f1 = agent_fleet_list[a1]
            f2 = agent_fleet_list[a2]
            cs1 = fleets[f1]["cell_size"]
            cs2 = fleets[f2]["cell_size"]
            _, pos1 = agent_positions[a1]
            _, pos2 = agent_positions[a2]
            fx1, fy1 = pos1[t]
            fx2, fy2 = pos2[t]
            print(
                f"  t={t}: base cell {cell} shared by "
                f"agent {a1} (fleet={f1}, cs={cs1}, fleet_pos=({fx1},{fy1})) and "
                f"agent {a2} (fleet={f2}, cs={cs2}, fleet_pos=({fx2},{fy2}))"
            )

        if len(collisions) > show_count:
            print(f"  ... and {len(collisions) - show_count} more base-cell overlaps")

    print()
    print("Done.")
    return 1 if collisions else 0


if __name__ == "__main__":
    sys.exit(main())
