"""Generate scaling scenarios for het_bench with cs=1,6,11 on room120.map."""
import sys
sys.path.insert(0, "E:/gb/third_party/hetpibt/tools")
import gen_scenario as gen
import random

MAP = "E:/gb/het_rt_lacam/assets/room120.map"
FLEET_DEFS = [(1, 1.0), (6, 0.17), (11, 0.09)]

# Agent distributions: (cs1, cs6, cs11) for each total
CONFIGS = {
    20: (12, 5, 3),
    30: (16, 9, 5),
    60: (34, 17, 9),
}

def generate(total, counts, seed=42):
    rng = random.Random(seed)
    width, height, base_grid = gen.load_map(MAP)
    print(f"Map: {width}x{height}")

    fleet_grids = []
    for i, (cs, vel) in enumerate(FLEET_DEFS):
        fw, fh, free = gen.build_fleet_grid(base_grid, width, height, cs)
        comps = gen.flood_fill(free)
        largest = max(len(c) for c in comps) if comps else 0
        print(f"Fleet {i} (cs={cs}, v={vel}): {fw}x{fh} grid, "
              f"{len(free)} free, largest={largest}")
        fleet_grids.append((fw, fh, free, comps, cs, vel))

    occupied_starts = set()
    occupied_goals = set()
    all_agents = []

    # Place largest first
    placement_order = sorted(range(len(FLEET_DEFS)), key=lambda i: -FLEET_DEFS[i][0])
    agent_id = 0

    for fi in placement_order:
        fw, fh, free, comps, cs, vel = fleet_grids[fi]
        n = counts[fi]
        print(f"\nPlacing {n} agents for fleet {fi} (cs={cs})...")
        placements = gen.place_agents(comps, free, cs, n,
                                       occupied_starts, occupied_goals, rng)
        for start, goal in placements:
            all_agents.append((agent_id, fi, cs, vel, start[0], start[1],
                              goal[0], goal[1], fw, fh))
            agent_id += 1
            print(f"  Agent {agent_id-1}: fleet={fi} cs={cs} "
                  f"start=({start[0]},{start[1]}) goal=({goal[0]},{goal[1]})")

    gen.verify_placements(all_agents, fleet_grids)
    all_agents.sort(key=lambda a: a[0])

    out = f"E:/gb/het_rt_lacam/assets/scaling_{total}.scen"
    with open(out, "w") as f:
        for a in all_agents:
            aid, fid, cs, vel, sx, sy, gx, gy, fw, fh = a
            f.write(f"{aid} {fid} {cs} {vel} {sx*cs} {sy*cs} {gx*cs} {gy*cs} {fw} {fh}\n")
    print(f"\nWrote {len(all_agents)} agents to {out}")

for total, counts in CONFIGS.items():
    print(f"\n{'='*60}")
    print(f"Generating {total}-agent scenario")
    print(f"{'='*60}")
    generate(total, counts)
