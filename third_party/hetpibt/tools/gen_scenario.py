"""
Generate a heterogeneous MAPF scenario file for a given .map file.

Produces the het_bench format used by HetPIBT:
  agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h

Coordinates (sx,sy,gx,gy) are in base-grid space.
The solver divides by cell_size to get fleet-grid coords.

Usage:
  python gen_scenario.py --map assets/room-64-64-8.map --out assets/room-64-64-8.scen
  python gen_scenario.py --map tests/assets/corridor30.map --out tests/assets/corridor30.scen --agents 10,6,3
"""
import argparse
import random
from collections import deque


def load_map(path):
    """Load a .map file. Returns (width, height, grid) where grid[y][x] is True if free."""
    with open(path) as f:
        lines = f.readlines()
    header = {}
    grid_start = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line == "map":
            grid_start = i + 1
            break
        parts = line.split()
        if len(parts) == 2:
            header[parts[0]] = parts[1]
    width = int(header["width"])
    height = int(header["height"])
    grid = []
    for i in range(grid_start, grid_start + height):
        row = lines[i].rstrip("\n\r")
        grid.append([c == "." for c in row])
    return width, height, grid


def build_fleet_grid(base_grid, width, height, cell_size):
    """Build a non-overlapping tiling fleet grid.

    Fleet cell (fx,fy) covers base cells [fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs).
    Agent moves cell_size base cells per step.
    A fleet cell is free if ALL cs*cs base cells are free.
    """
    fw = width // cell_size
    fh = height // cell_size
    if fw <= 0 or fh <= 0:
        return 0, 0, set()
    free = set()
    for fy in range(fh):
        for fx in range(fw):
            ok = True
            for dy in range(cell_size):
                for dx in range(cell_size):
                    bx = fx * cell_size + dx
                    by = fy * cell_size + dy
                    if bx >= width or by >= height or not base_grid[by][bx]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                free.add((fx, fy))
    return fw, fh, free


def get_neighbors(fx, fy, free_cells):
    """Get 4-connected neighbors of (fx,fy) that are in free_cells."""
    result = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        n = (fx + dx, fy + dy)
        if n in free_cells:
            result.append(n)
    return result


def flood_fill(free_cells):
    """Find connected components using 4-connectivity on the fleet grid."""
    visited = set()
    components = []
    for cell in free_cells:
        if cell in visited:
            continue
        comp = []
        queue = deque([cell])
        visited.add(cell)
        while queue:
            cx, cy = queue.popleft()
            comp.append((cx, cy))
            for n in get_neighbors(cx, cy, free_cells):
                if n not in visited:
                    visited.add(n)
                    queue.append(n)
        components.append(comp)
    return components


def bfs_reachable(start, goal, free_cells):
    """BFS from start to goal on the fleet grid. Returns True if reachable."""
    if start == goal:
        return True
    visited = {start}
    queue = deque([start])
    while queue:
        cx, cy = queue.popleft()
        for n in get_neighbors(cx, cy, free_cells):
            if n == goal:
                return True
            if n not in visited:
                visited.add(n)
                queue.append(n)
    return False


def get_base_footprint(fx, fy, cell_size):
    """Get the set of base-grid cells occupied by fleet cell (fx,fy).

    Non-overlapping tiling: fleet cell (fx,fy) covers base
    [fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs).
    """
    cells = set()
    for dy in range(cell_size):
        for dx in range(cell_size):
            cells.add((fx * cell_size + dx, fy * cell_size + dy))
    return cells


def place_agents(components, free_cells, cell_size, n_agents,
                 occupied_starts, occupied_goals, rng):
    """Place n_agents with non-overlapping starts and goals on the base grid.

    All positions are checked for base-grid footprint overlap:
    - Starts must not overlap any other agent's start footprint (cross-fleet)
    - Starts must not overlap any other agent's goal footprint (cross-fleet)
    - Goals must not overlap any other agent's goal footprint (cross-fleet)
    - Goals must not overlap any other agent's start footprint (cross-fleet)
    - Each agent's goal must be BFS-reachable from its start on the fleet graph

    Returns list of (start_fleet, goal_fleet) tuples.
    """
    # use largest component
    comp = max(components, key=len)
    placements = []

    for _ in range(n_agents):
        candidates = list(comp)
        rng.shuffle(candidates)

        # find valid start: no overlap with any start OR any goal
        start = None
        for s in candidates:
            fp = get_base_footprint(s[0], s[1], cell_size)
            if fp & occupied_starts:
                continue
            if fp & occupied_goals:
                continue
            start = s
            break
        if start is None:
            print(f"  Warning: could not place start (cs={cell_size}), "
                  f"{len(occupied_starts)} start + "
                  f"{len(occupied_goals)} goal base cells occupied")
            break

        # find valid goal: no overlap with any goal, any start, own start,
        # BFS-reachable from start, and avoid narrow corridor bottlenecks
        goal = None
        fallback_goal = None  # corridor cell, used only if no open cell found
        start_fp = get_base_footprint(start[0], start[1], cell_size)
        for g in candidates:
            if g == start:
                continue
            gfp = get_base_footprint(g[0], g[1], cell_size)
            # must not overlap with own start footprint
            if gfp & start_fp:
                continue
            # must not overlap with any other agent's goal footprint
            if gfp & occupied_goals:
                continue
            # must not overlap with any other agent's start footprint
            if gfp & occupied_starts:
                continue
            # must be BFS-reachable from start on the fleet graph
            if not bfs_reachable(start, g, free_cells):
                continue
            # avoid corridor bottlenecks: cells with <=2 neighbors where
            # a parked agent blocks the only path through
            n_neighbors = len(get_neighbors(g[0], g[1], free_cells))
            if n_neighbors <= 2:
                if fallback_goal is None:
                    fallback_goal = g
                continue
            goal = g
            break
        if goal is None:
            goal = fallback_goal  # use corridor cell if no open cell available

        if goal is None:
            print(f"  Warning: could not find valid goal for agent at "
                  f"{start} (cs={cell_size})")
            break

        # reserve footprints
        occupied_starts |= start_fp
        goal_fp = get_base_footprint(goal[0], goal[1], cell_size)
        occupied_goals |= goal_fp
        placements.append((start, goal))

    return placements


def verify_placements(all_agents, fleet_grids):
    """Post-placement verification: check all starts and goals are unique
    on the base grid, and all goals are reachable."""
    print("\n--- VERIFICATION ---")
    ok = True

    # check start overlaps on base grid
    all_start_cells = {}  # base cell -> agent_id
    all_goal_cells = {}   # base cell -> agent_id
    for aid, fi, cs, vel, sx, sy, gx, gy, fw, fh in all_agents:
        # tiling: sx,sy are fleet coords, base cells at (sx*cs, sy*cs)
        sfp = get_base_footprint(sx, sy, cs)
        for bc in sfp:
            if bc in all_start_cells:
                print(f"  ERROR: Start overlap at base {bc}: "
                      f"agent {aid} and agent {all_start_cells[bc]}")
                ok = False
            all_start_cells[bc] = aid
        gfp = get_base_footprint(gx, gy, cs)
        for bc in gfp:
            if bc in all_goal_cells:
                print(f"  ERROR: Goal overlap at base {bc}: "
                      f"agent {aid} and agent {all_goal_cells[bc]}")
                ok = False
            all_goal_cells[bc] = aid

    # check BFS reachability for each agent
    for aid, fi, cs, vel, sx, sy, gx, gy, fw, fh in all_agents:
        _, _, free, _, _, _ = fleet_grids[fi]
        start_fleet = (sx, sy)
        goal_fleet = (gx, gy)
        if not bfs_reachable(start_fleet, goal_fleet, free):
            print(f"  ERROR: Agent {aid} goal {goal_fleet} unreachable "
                  f"from start {start_fleet} on fleet {fi} (cs={cs})")
            ok = False

    if ok:
        print("  All checks passed.")
    return ok


def main():
    parser = argparse.ArgumentParser(description="Generate heterogeneous MAPF scenario")
    parser.add_argument("--map", required=True, help="Path to .map file")
    parser.add_argument("--out", required=True, help="Output .scen file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--agents", type=str, default="10,5,3",
                        help="Comma-separated agent counts per fleet (cs=1,cs=2,cs=3)")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # fleet definitions: (cell_size, velocity)
    fleet_defs = [
        (1, 1.0),
        (2, 0.5),
        (3, 0.3),
    ]
    agent_counts = [int(x) for x in args.agents.split(",")]
    assert len(agent_counts) == len(fleet_defs), "agent counts must match fleet count"

    # load map
    width, height, base_grid = load_map(args.map)
    print(f"Map: {width}x{height}")

    n_free = sum(1 for y in range(height) for x in range(width) if base_grid[y][x])
    print(f"Free base cells: {n_free}/{width * height}")

    # build fleet grids and find components
    fleet_grids = []
    for i, (cs, vel) in enumerate(fleet_defs):
        fw, fh, free = build_fleet_grid(base_grid, width, height, cs)
        comps = flood_fill(free)
        largest = max(len(c) for c in comps) if comps else 0
        print(f"Fleet {i} (cs={cs}, v={vel}): {fw}x{fh} grid, "
              f"{len(free)} free cells, {len(comps)} components, "
              f"largest={largest}")
        fleet_grids.append((fw, fh, free, comps, cs, vel))

    # place agents: largest cell_size first so large footprints get placed
    # before small agents fill gaps around them
    occupied_starts = set()  # base-grid cells taken by starts
    occupied_goals = set()   # base-grid cells taken by goals
    all_agents = []

    placement_order = sorted(range(len(fleet_defs)), key=lambda i: -fleet_defs[i][0])
    agent_id = 0

    for fi in placement_order:
        fw, fh, free, comps, cs, vel = fleet_grids[fi]
        n = agent_counts[fi]
        print(f"\nPlacing {n} agents for fleet {fi} (cs={cs})...")
        placements = place_agents(comps, free, cs, n,
                                   occupied_starts, occupied_goals, rng)
        for start, goal in placements:
            # tiling: fleet coords; base top-left at (fx*cs, fy*cs)
            sx = start[0]
            sy = start[1]
            gx = goal[0]
            gy = goal[1]
            all_agents.append((agent_id, fi, cs, vel, sx, sy, gx, gy, fw, fh))
            agent_id += 1
            print(f"  Agent {agent_id-1}: fleet={fi} cs={cs} "
                  f"start=({sx},{sy}) goal=({gx},{gy})")

    # verify all placements
    verify_placements(all_agents, fleet_grids)

    # sort by agent_id for output
    all_agents.sort(key=lambda a: a[0])

    # write .scen file
    with open(args.out, "w") as f:
        for a in all_agents:
            aid, fid, cs, vel, sx, sy, gx, gy, fw, fh = a
            # write real-world coords (fleet_coord * cell_size) so the
            # het_bench parser can recover fleet coords via division
            f.write(f"{aid} {fid} {cs} {vel} {sx*cs} {sy*cs} {gx*cs} {gy*cs} {fw} {fh}\n")

    print(f"\nWrote {len(all_agents)} agents to {args.out}")


if __name__ == "__main__":
    main()
