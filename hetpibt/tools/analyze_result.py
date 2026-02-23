#!/usr/bin/env python3
"""
Analyze a hetpibt result file.

Parses the result file header (fleet info, starts, goals) and trajectory lines,
then prints per-agent statistics and identifies agents that barely moved vs
those that reached their goals.

Result file format:
  agents=N
  map_name=...
  seed=...
  solver=...
  comp_time(ms)=...
  makespan=T
  sum_of_costs=...
  fleets=fleet_id:cell_size:velocity:grid_w:grid_h;...
  agent_fleet=f0,f1,...
  starts=(x0,y0),(x1,y1),...
  goals=(x0,y0),(x1,y1),...
  solution
  agent_id:fleet_id:(x,y)@t,(x,y)@t,...

Scenario file format (for reference):
  agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h
"""

import re
import sys
import math
from pathlib import Path


def parse_coord_list(s):
    """Parse a string like '(11,4),(11,3),(12,3)' into list of (x,y) tuples."""
    return [(int(x), int(y)) for x, y in re.findall(r'\((\d+),(\d+)\)', s)]


def parse_fleets(s):
    """Parse fleet string like '0:1:1:64:64;1:2:0.5:32:32;2:3:0.3:21:21'.
    Returns dict: fleet_id -> {cell_size, velocity, grid_w, grid_h}
    """
    fleets = {}
    for part in s.split(';'):
        tokens = part.split(':')
        fleet_id = int(tokens[0])
        cell_size = int(tokens[1])
        velocity = float(tokens[2])
        grid_w = int(tokens[3])
        grid_h = int(tokens[4])
        fleets[fleet_id] = {
            'cell_size': cell_size,
            'velocity': velocity,
            'grid_w': grid_w,
            'grid_h': grid_h,
        }
    return fleets


def parse_trajectory(traj_str):
    """Parse a trajectory string like '(11,4)@0,(11,4)@0,(11,4)@1,...'
    Returns list of ((x, y), t) tuples.
    """
    waypoints = []
    for m in re.finditer(r'\((\d+),(\d+)\)@(\d+)', traj_str):
        x, y, t = int(m.group(1)), int(m.group(2)), int(m.group(3))
        waypoints = waypoints  # no-op, just for clarity
        waypoints.append(((x, y), t))
    return waypoints


def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean_distance(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


def analyze(result_path):
    with open(result_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    # Parse header
    header = {}
    trajectory_lines = []
    in_solution = False

    for line in lines:
        if line == 'solution':
            in_solution = True
            continue
        if in_solution:
            trajectory_lines.append(line)
        elif '=' in line:
            key, val = line.split('=', 1)
            header[key] = val

    num_agents = int(header['agents'])
    makespan = int(header['makespan'])
    sum_of_costs = int(header['sum_of_costs'])
    comp_time = float(header['comp_time(ms)'])
    solver = header.get('solver', '?')

    # Parse fleets
    fleets = parse_fleets(header['fleets'])

    # Parse agent-fleet assignment
    agent_fleet_ids = [int(x) for x in header['agent_fleet'].split(',')]

    # Parse starts and goals (these are in fleet-grid coordinates)
    starts = parse_coord_list(header['starts'])
    goals = parse_coord_list(header['goals'])

    # Parse trajectories
    agents = {}
    for tline in trajectory_lines:
        # Format: agent_id:fleet_id:(x,y)@t,...
        colon1 = tline.index(':')
        colon2 = tline.index(':', colon1 + 1)
        agent_id = int(tline[:colon1])
        fleet_id = int(tline[colon1+1:colon2])
        traj_str = tline[colon2+1:]
        waypoints = parse_trajectory(traj_str)
        agents[agent_id] = {
            'fleet_id': fleet_id,
            'waypoints': waypoints,
        }

    # Print summary header
    print("=" * 110)
    print(f"RESULT ANALYSIS: {result_path}")
    print(f"  Solver: {solver}  |  Agents: {num_agents}  |  Makespan: {makespan}  |  Sum of costs: {sum_of_costs}  |  Comp time: {comp_time:.1f} ms")
    print("=" * 110)

    # Print fleet info
    print("\nFLEET DEFINITIONS:")
    print(f"  {'Fleet':>5}  {'CellSize':>8}  {'Velocity':>8}  {'GridW':>5}  {'GridH':>5}  {'Agents':>6}")
    print(f"  {'-'*5}  {'-'*8}  {'-'*8}  {'-'*5}  {'-'*5}  {'-'*6}")
    for fid in sorted(fleets.keys()):
        fi = fleets[fid]
        n_agents = sum(1 for af in agent_fleet_ids if af == fid)
        print(f"  {fid:>5}  {fi['cell_size']:>8}  {fi['velocity']:>8.2f}  {fi['grid_w']:>5}  {fi['grid_h']:>5}  {n_agents:>6}")

    # Per-agent analysis
    print("\nPER-AGENT DETAILS:")
    print(f"  {'ID':>3}  {'Fleet':>5}  {'Cell':>4}  {'Start':>10}  {'Goal':>10}  {'Final':>10}  "
          f"{'Moves':>5}  {'Steps':>5}  {'Dist2Goal':>9}  {'Reached?':>8}")
    print(f"  {'-'*3}  {'-'*5}  {'-'*4}  {'-'*10}  {'-'*10}  {'-'*10}  "
          f"{'-'*5}  {'-'*5}  {'-'*9}  {'-'*8}")

    reached_goal = []
    barely_moved = []
    stuck_agents = []

    for aid in range(num_agents):
        fid = agent_fleet_ids[aid]
        fi = fleets[fid]
        cell_size = fi['cell_size']
        start = starts[aid]
        goal = goals[aid]

        if aid not in agents:
            print(f"  {aid:>3}  {fid:>5}  {cell_size:>4}  {str(start):>10}  {str(goal):>10}  {'N/A':>10}  "
                  f"{'N/A':>5}  {'N/A':>5}  {'N/A':>9}  {'N/A':>8}")
            continue

        wp = agents[aid]['waypoints']
        final_pos = wp[-1][0]
        final_t = wp[-1][1]

        # Count non-stay moves: position changes between consecutive waypoints
        move_count = 0
        for i in range(1, len(wp)):
            if wp[i][0] != wp[i-1][0]:
                move_count += 1

        # Total timesteps in this agent's trajectory
        total_steps = final_t  # last timestamp

        # Distance from final position to goal (Manhattan)
        dist_to_goal = manhattan_distance(final_pos, goal)

        at_goal = (final_pos == goal)
        reached_str = "YES" if at_goal else f"no ({dist_to_goal})"

        print(f"  {aid:>3}  {fid:>5}  {cell_size:>4}  {str(start):>10}  {str(goal):>10}  {str(final_pos):>10}  "
              f"{move_count:>5}  {total_steps:>5}  {dist_to_goal:>9}  {reached_str:>8}")

        if at_goal:
            reached_goal.append(aid)

        # "Barely moved" = moved fewer than 3 unique positions total
        unique_positions = set(pos for pos, t in wp)
        initial_dist = manhattan_distance(start, goal)

        if not at_goal and dist_to_goal > 0:
            if move_count <= 3 or (initial_dist > 0 and dist_to_goal >= initial_dist * 0.8):
                barely_moved.append((aid, move_count, dist_to_goal, initial_dist))

        if not at_goal and final_t == makespan:
            stuck_agents.append((aid, dist_to_goal, initial_dist))

    # Summary
    print("\n" + "=" * 110)
    print("SUMMARY")
    print("=" * 110)
    print(f"  Makespan (total timesteps solver ran): {makespan}")
    print(f"  Agents that reached goal: {len(reached_goal)}/{num_agents}  ->  {reached_goal}")
    print(f"  Agents that did NOT reach goal: {num_agents - len(reached_goal)}/{num_agents}")

    if barely_moved:
        print(f"\n  BARELY MOVED (<=3 moves or covered <20% of initial distance):")
        for aid, moves, dist, init_dist in barely_moved:
            pct = ((init_dist - dist) / init_dist * 100) if init_dist > 0 else 0
            print(f"    Agent {aid}: {moves} moves, dist-to-goal={dist}, "
                  f"initial-dist={init_dist}, progress={pct:.1f}%")

    if stuck_agents:
        print(f"\n  STUCK AT MAKESPAN (trajectory ran to t={makespan}, did not reach goal):")
        for aid, dist, init_dist in stuck_agents:
            pct = ((init_dist - dist) / init_dist * 100) if init_dist > 0 else 0
            print(f"    Agent {aid}: dist-to-goal={dist}, initial-dist={init_dist}, "
                  f"progress={pct:.1f}%")

    # Agents that reached goal quickly vs slowly
    if reached_goal:
        print(f"\n  GOAL-REACHED AGENTS (sorted by arrival time):")
        arrivals = []
        for aid in reached_goal:
            wp = agents[aid]['waypoints']
            # Find first time agent is at goal
            goal_pos = goals[aid]
            first_at_goal = None
            for pos, t in wp:
                if pos == goal_pos:
                    first_at_goal = t
                    break
            arrivals.append((aid, first_at_goal))
        arrivals.sort(key=lambda x: x[1])
        for aid, t in arrivals:
            fid = agent_fleet_ids[aid]
            init_dist = manhattan_distance(starts[aid], goals[aid])
            print(f"    Agent {aid} (fleet {fid}): arrived at t={t}, initial manhattan dist={init_dist}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        result_path = sys.argv[1]
    else:
        # Default path
        result_path = str(Path(__file__).resolve().parent.parent / 'build' / 'room64_result.txt')

    analyze(result_path)
