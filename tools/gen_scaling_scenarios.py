#!/usr/bin/env python3
"""Generate het_bench scaling scenarios with cs=1,6,11 fleets on a given map.

Usage:
    python gen_scaling_scenarios.py --map ../assets/room120.map --total 15 --out ../assets/scaling_15.scen
"""
import argparse
import random
import sys
import os

# Reuse gen_scenario.py functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'hetpibt', 'tools'))
from gen_scenario import (load_map, build_fleet_grid, flood_fill,
                          place_agents, verify_placements)

# het_bench fleet definitions
FLEET_DEFS = [
    (1, 1.0),    # fleet 0: cs=1
    (6, 0.17),   # fleet 1: cs=6  (velocity ~ 1/6)
    (11, 0.09),  # fleet 2: cs=11 (velocity ~ 1/11)
]


def split_agents(total):
    """Split total agents across 3 fleets. Heavier on cs=1."""
    # Rough split: 55% cs=1, 30% cs=6, 15% cs=11
    n11 = max(1, round(total * 0.15))
    n6 = max(1, round(total * 0.30))
    n1 = total - n6 - n11
    return [n1, n6, n11]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--total", type=int, required=True, help="Total agent count")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    agent_counts = split_agents(args.total)
    print(f"Agents per fleet: cs=1:{agent_counts[0]}, cs=6:{agent_counts[1]}, cs=11:{agent_counts[2]}")

    width, height, base_grid = load_map(args.map)
    print(f"Map: {width}x{height}")

    fleet_grids = []
    for i, (cs, vel) in enumerate(FLEET_DEFS):
        fw, fh, free = build_fleet_grid(base_grid, width, height, cs)
        comps = flood_fill(free)
        largest = max(len(c) for c in comps) if comps else 0
        print(f"Fleet {i} (cs={cs}): {fw}x{fh}, {len(free)} free, largest_comp={largest}")
        fleet_grids.append((fw, fh, free, comps, cs, vel))

    occupied_starts = set()
    occupied_goals = set()
    all_agents = []
    agent_id = 0

    # Place largest first
    for fi in [2, 1, 0]:
        fw, fh, free, comps, cs, vel = fleet_grids[fi]
        n = agent_counts[fi]
        print(f"\nPlacing {n} agents for fleet {fi} (cs={cs})...")
        placements = place_agents(comps, free, cs, n,
                                  occupied_starts, occupied_goals, rng)
        for start, goal in placements:
            all_agents.append((agent_id, fi, cs, vel, start[0], start[1],
                               goal[0], goal[1], fw, fh))
            agent_id += 1

    verify_placements(all_agents, fleet_grids)
    all_agents.sort(key=lambda a: a[0])

    with open(args.out, "w") as f:
        for a in all_agents:
            aid, fid, cs, vel, sx, sy, gx, gy, fw, fh = a
            f.write(f"{aid} {fid} {cs} {vel} {sx*cs} {sy*cs} {gx*cs} {gy*cs} {fw} {fh}\n")

    print(f"\nWrote {len(all_agents)} agents to {args.out}")


if __name__ == "__main__":
    main()
