#!/usr/bin/env python3
"""Scale HetPIBT to failure: run increasing agent counts until the solver breaks.

Generates randomized scenarios on room-64-64-8 (640x640 scaled) with 3 fleet types
(cs=1, cs=6, cs=11), runs the solver, and records per-scenario metrics.

Fleet composition: ~50% small (cs=1), ~30% medium (cs=6), ~20% large (cs=11)

Usage:
    python run_scaling.py [--counts 15,30,50,75,100,150,200] [--seeds 10]
                          [--max-steps 500] [--time-limit 120000]
"""
import argparse
import csv
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from collections import deque
from pathlib import Path

# === Paths ===
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PYPIBT_DIR = ROOT_DIR.parent / "pypibt"
SOLVER = ROOT_DIR / "build" / "Release" / "main.exe"
BASE_MAP = PYPIBT_DIR / "assets" / "room-64-64-8.map"
SCALED_MAP = ROOT_DIR / "build" / "room64_scaled.map"
RESULTS_DIR = ROOT_DIR / "scaling_results"

MAP_SCALE = 10

# Fleet definitions: (cell_size, speed_counter)
# speed_counter = how many timesteps per fleet-cell move
# Effective base-grid speed = cell_size / speed_counter
#   cs=1, speed=1 → 1 base/step
#   cs=6, speed=2 → 3 base/step
#   cs=11, speed=3 → 3.7 base/step
FLEET_DEFS = [
    (1, 1.0),
    (6, 2.0),
    (11, 3.0),
]

# Composition ratios (must sum to 1.0)
FLEET_RATIOS = [0.50, 0.30, 0.20]  # cs=1, cs=6, cs=11


# ============================================================
# Scenario generation (adapted from gen_scenario.py)
# ============================================================

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


def create_scaled_map(base_map, scale, output_map):
    """Create a scaled-up version of a .map file."""
    width, height, grid = load_map(str(base_map))
    new_w = width * scale
    new_h = height * scale
    with open(output_map, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {new_h}\n")
        f.write(f"width {new_w}\n")
        f.write("map\n")
        for row in grid:
            scaled_row = ''.join(('.' if c else '@') * scale for c in row)
            for _ in range(scale):
                f.write(scaled_row + '\n')
    return new_w, new_h


def build_fleet_grid(base_grid, width, height, cell_size):
    """Build non-overlapping tiling fleet grid. Returns (fw, fh, free_cells_set)."""
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
    result = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        n = (fx + dx, fy + dy)
        if n in free_cells:
            result.append(n)
    return result


def flood_fill(free_cells):
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


def bfs_distance(start, goal, free_cells):
    """BFS shortest path distance between two cells on a fleet grid."""
    if start == goal:
        return 0
    visited = {start}
    queue = deque([(start, 0)])
    while queue:
        (cx, cy), d = queue.popleft()
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            n = (cx + dx, cy + dy)
            if n == goal:
                return d + 1
            if n in free_cells and n not in visited:
                visited.add(n)
                queue.append((n, d + 1))
    return -1  # unreachable


def get_base_footprint(fx, fy, cell_size):
    cells = set()
    for dy in range(cell_size):
        for dx in range(cell_size):
            cells.add((fx * cell_size + dx, fy * cell_size + dy))
    return cells


def place_agents(components, free_cells, cell_size, n_agents,
                 occupied_starts, occupied_goals, rng):
    """Place n_agents with non-overlapping starts and goals on the base grid.

    Optimized: skip BFS reachability (both start & goal are from the same
    connected component, so always reachable). Sample random candidates
    instead of shuffling the full list.
    """
    comp = max(components, key=len)
    comp_list = list(comp)
    n_comp = len(comp_list)
    MAX_TRIES = min(2000, n_comp)
    placements = []

    for _ in range(n_agents):
        sample = rng.sample(comp_list, MAX_TRIES)

        start = None
        for s in sample:
            fp = get_base_footprint(s[0], s[1], cell_size)
            if fp & occupied_starts:
                continue
            if fp & occupied_goals:
                continue
            start = s
            break
        if start is None:
            break

        goal = None
        fallback_goal = None
        start_fp = get_base_footprint(start[0], start[1], cell_size)
        goal_sample = rng.sample(comp_list, MAX_TRIES)
        for g in goal_sample:
            if g == start:
                continue
            gfp = get_base_footprint(g[0], g[1], cell_size)
            if gfp & start_fp:
                continue
            if gfp & occupied_goals:
                continue
            if gfp & occupied_starts:
                continue
            # Skip BFS — both cells are in same connected component
            n_neighbors = len(get_neighbors(g[0], g[1], free_cells))
            if n_neighbors <= 2:
                if fallback_goal is None:
                    fallback_goal = g
                continue
            goal = g
            break
        if goal is None:
            goal = fallback_goal

        if goal is None:
            break

        occupied_starts |= start_fp
        goal_fp = get_base_footprint(goal[0], goal[1], cell_size)
        occupied_goals |= goal_fp
        placements.append((start, goal))

    return placements


def generate_scenario(map_grid, map_w, map_h, agent_counts, fleet_defs, seed,
                      prebuilt_fleet_grids=None):
    """Generate a scenario. Returns (agents, placed, requested, all_placed, fleet_grids)."""
    rng = random.Random(seed)

    if prebuilt_fleet_grids is not None:
        fleet_grids = prebuilt_fleet_grids
    else:
        fleet_grids = []
        for i, (cs, vel) in enumerate(fleet_defs):
            fw, fh, free = build_fleet_grid(map_grid, map_w, map_h, cs)
            comps = flood_fill(free)
            fleet_grids.append((fw, fh, free, comps, cs, vel))

    occupied_starts = set()
    occupied_goals = set()
    all_agents = []

    # Place largest first
    placement_order = sorted(range(len(fleet_defs)), key=lambda i: -fleet_defs[i][0])
    agent_id = 0

    requested = {}
    placed = {}

    for fi in placement_order:
        fw, fh, free, comps, cs, vel = fleet_grids[fi]
        n = agent_counts[fi]
        requested[fi] = n
        if not comps:
            placed[fi] = 0
            continue
        placements = place_agents(comps, free, cs, n,
                                   occupied_starts, occupied_goals, rng)
        placed[fi] = len(placements)
        for start, goal in placements:
            sx, sy = start
            gx, gy = goal
            all_agents.append((agent_id, fi, cs, vel, sx, sy, gx, gy, fw, fh))
            agent_id += 1

    all_agents.sort(key=lambda a: a[0])
    all_placed = all(placed.get(fi, 0) == requested[fi] for fi in range(len(fleet_defs)))

    return all_agents, placed, requested, all_placed, fleet_grids


def write_scenario(agents, path):
    """Write scenario file in het_bench format."""
    with open(path, "w") as f:
        for a in agents:
            aid, fid, cs, vel, sx, sy, gx, gy, fw, fh = a
            # Output real-world coords: fleet_coord * cell_size
            f.write(f"{aid} {fid} {cs} {vel} {sx*cs} {sy*cs} {gx*cs} {gy*cs} {fw} {fh}\n")


def compute_horizon(agents, fleet_grids, min_horizon=1500):
    """Compute simulation horizon accounting for speed counters.

    Each agent needs bfs_distance * speed_counter timesteps to reach its goal
    (since it only moves every speed_counter steps). Horizon is set to
    max(2 * max_steps_needed, min_horizon).

    To keep scenario generation fast, only BFS the top 10 agents by
    Manhattan distance (they dominate the max BFS distance).
    """
    # Compute Manhattan distances and sort descending
    agent_manhattan = []
    for aid, fi, cs, vel, sx, sy, gx, gy, fw, fh in agents:
        md = abs(sx - gx) + abs(sy - gy)
        agent_manhattan.append((md, aid, fi, vel, sx, sy, gx, gy))
    agent_manhattan.sort(reverse=True)

    # BFS only the top 10 (or all if fewer)
    max_bfs = 0
    max_steps_needed = 0
    for md, aid, fi, vel, sx, sy, gx, gy in agent_manhattan[:10]:
        _, _, free, _, _, _ = fleet_grids[fi]
        d = bfs_distance((sx, sy), (gx, gy), free)
        speed = max(1, int(vel))
        steps = d * speed  # agent needs d moves × speed timesteps per move
        if d > max_bfs:
            max_bfs = d
        if steps > max_steps_needed:
            max_steps_needed = steps

    horizon = max(2 * max_steps_needed, min_horizon)
    return horizon, max_bfs


# ============================================================
# Solver execution & result parsing
# ============================================================

def run_solver(scen_file, result_file, max_steps, time_limit):
    """Run our solver and parse output. No --swap-xy needed for gen_scenario.py output."""
    cmd = [str(SOLVER), "-m", str(SCALED_MAP), "-s", str(scen_file), "-v", "1",
           "--max_timesteps", str(max_steps), "--goal-lock",
           "--time_limit", str(time_limit),
           "-o", str(result_file)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=time_limit/1000 + 30)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "goals_reached": "0/0", "comp_time_ms": str(time_limit)}
    except FileNotFoundError:
        return {"status": "NOT_BUILT"}

    parsed = {"status": "OK", "_raw": output}
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("goals_reached="):
            parsed["goals_reached"] = line.split("=", 1)[1]
        elif line.startswith("makespan="):
            parsed["makespan"] = line.split("=", 1)[1]
        elif line.startswith("comp_time(ms)="):
            parsed["comp_time_ms"] = line.split("=", 1)[1]
        elif line.startswith("sum_of_costs="):
            parsed["sum_of_costs"] = line.split("=", 1)[1]
        elif line.startswith("feasible="):
            parsed["feasible"] = line.split("=", 1)[1]

    return parsed


def parse_result_file(result_path):
    """Parse result file for per-agent trajectory analysis."""
    agent_fleets = []
    fleet_defs = {}
    starts = []
    goals = []
    trajectories = {}
    in_solution = False

    try:
        with open(result_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if in_solution:
                    m = re.match(r"^(\d+):(\d+):(.*)", line)
                    if not m:
                        continue
                    aid = int(m.group(1))
                    entries = re.findall(r"\((-?\d+),(-?\d+)\)@(\d+)", m.group(3))
                    traj = [(int(t), int(x), int(y)) for x, y, t in entries]
                    traj.sort()
                    deduped = {}
                    for t_val, fx, fy in traj:
                        deduped[t_val] = (t_val, fx, fy)
                    trajectories[aid] = sorted(deduped.values())
                    continue

                if line == "solution":
                    in_solution = True
                    continue
                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                if key == "fleets":
                    for part in value.split(";"):
                        fields = part.split(":")
                        if len(fields) >= 5:
                            fid = int(fields[0])
                            fleet_defs[fid] = int(fields[1])
                elif key == "agent_fleet":
                    agent_fleets = [int(x) for x in value.split(",")]
                elif key == "starts":
                    pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
                    starts = [(int(x), int(y)) for x, y in pairs]
                elif key == "goals":
                    pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
                    goals = [(int(x), int(y)) for x, y in pairs]
    except (FileNotFoundError, ValueError):
        return {}

    n_agents = len(agent_fleets)
    if n_agents == 0:
        return {}

    # Per-agent analysis
    per_fleet_reached = {}
    per_fleet_total = {}
    per_fleet_stuck = {}      # agents at makespan, didn't reach goal
    per_fleet_no_move = {}    # agents that never moved

    makespan_val = 0
    soc = 0
    total_wait_ratio = 0.0
    goal_reached_count = 0

    for aid in range(n_agents):
        fid = agent_fleets[aid]
        cs = fleet_defs.get(fid, 1)
        per_fleet_total[cs] = per_fleet_total.get(cs, 0) + 1

        if aid not in trajectories or aid >= len(goals):
            per_fleet_stuck[cs] = per_fleet_stuck.get(cs, 0) + 1
            continue

        traj = trajectories[aid]
        gx, gy = goals[aid]

        # Find first timestep at goal
        goal_time = None
        for t_val, fx, fy in traj:
            if fx == gx and fy == gy:
                goal_time = t_val
                break

        if goal_time is not None:
            per_fleet_reached[cs] = per_fleet_reached.get(cs, 0) + 1
            soc += goal_time
            if goal_time > makespan_val:
                makespan_val = goal_time
            if goal_time > 0:
                waits = 0
                prev = None
                for t_val, fx, fy in traj:
                    if t_val > goal_time:
                        break
                    if prev is not None and fx == prev[0] and fy == prev[1]:
                        waits += 1
                    prev = (fx, fy)
                total_wait_ratio += waits / goal_time
            goal_reached_count += 1
        else:
            per_fleet_stuck[cs] = per_fleet_stuck.get(cs, 0) + 1
            # Check if agent never moved
            if aid in trajectories and aid < len(starts):
                traj_data = trajectories[aid]
                unique_pos = set((fx, fy) for _, fx, fy in traj_data)
                if len(unique_pos) <= 1:
                    per_fleet_no_move[cs] = per_fleet_no_move.get(cs, 0) + 1

    avg_wait = total_wait_ratio / goal_reached_count if goal_reached_count > 0 else 0.0

    result = {
        "soc_computed": soc,
        "makespan_computed": makespan_val,
        "avg_wait_ratio": avg_wait,
        "per_fleet_reached": per_fleet_reached,
        "per_fleet_total": per_fleet_total,
        "per_fleet_stuck": per_fleet_stuck,
        "per_fleet_no_move": per_fleet_no_move,
        "total_reached": goal_reached_count,
        "total_agents": n_agents,
    }
    return result


# ============================================================
# Main experiment
# ============================================================

def compute_agent_counts(total, ratios, fleet_defs):
    """Compute per-fleet agent counts given total and ratios.
    Ensures at least 1 agent per fleet and sum == total."""
    counts = [max(1, int(total * r)) for r in ratios]
    # Adjust to hit exact total
    diff = total - sum(counts)
    # Add/remove from fleet 0 (cs=1, most flexible)
    counts[0] += diff
    if counts[0] < 1:
        counts[0] = 1
    return counts


def safe_float(s, default=0.0):
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def safe_int(s, default=0):
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def main():
    parser = argparse.ArgumentParser(description="Scale HetPIBT to failure")
    parser.add_argument("--counts", type=str, default="15,50,100,150,200",
                        help="Comma-separated agent counts to test")
    parser.add_argument("--seeds", type=int, default=10,
                        help="Number of random seeds per agent count")
    parser.add_argument("--max-steps", type=int, default=0,
                        help="Fixed max timesteps (0 = auto-compute per scenario)")
    parser.add_argument("--min-horizon", type=int, default=1500,
                        help="Minimum horizon when auto-computing")
    parser.add_argument("--time-limit", type=int, default=120000,
                        help="Time limit per run in ms")
    args = parser.parse_args()

    agent_counts_list = [int(x) for x in args.counts.split(",")]
    n_seeds = args.seeds
    fixed_max_steps = args.max_steps  # 0 = auto
    min_horizon = args.min_horizon
    time_limit = args.time_limit

    # Check prerequisites
    if not SOLVER.exists():
        print(f"ERROR: solver not found at {SOLVER}")
        sys.exit(1)
    if not BASE_MAP.exists():
        print(f"ERROR: base map not found at {BASE_MAP}")
        sys.exit(1)

    # Ensure scaled map exists
    if not SCALED_MAP.exists():
        print(f"Creating {MAP_SCALE}x scaled map...")
        create_scaled_map(BASE_MAP, MAP_SCALE, str(SCALED_MAP))

    # Load scaled map for scenario generation
    print("Loading scaled map...", flush=True)
    map_w, map_h, map_grid = load_map(str(SCALED_MAP))
    print(f"  Scaled map: {map_w}x{map_h}", flush=True)

    # Pre-compute fleet grids (reused across all scenarios)
    cached_fleet_grids = []
    for i, (cs, vel) in enumerate(FLEET_DEFS):
        print(f"  Building fleet {i} (cs={cs})...", end="", flush=True)
        fw, fh, free = build_fleet_grid(map_grid, map_w, map_h, cs)
        comps = flood_fill(free)
        largest = max(len(c) for c in comps) if comps else 0
        print(f" {fw}x{fh} grid, {len(free)} free cells, "
              f"largest component={largest}", flush=True)
        cached_fleet_grids.append((fw, fh, free, comps, cs, vel))

    # Setup output
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / "scaling_data.csv"
    tmp_dir = tempfile.mkdtemp(prefix="hetpibt_scaling_")

    csv_fields = [
        "agent_count", "seed", "n_placed", "placement_ok",
        "n_cs1", "n_cs6", "n_cs11",
        "max_steps", "max_bfs_dist",
        "goals_reached", "goal_pct",
        "goals_cs1", "total_cs1", "pct_cs1",
        "goals_cs6", "total_cs6", "pct_cs6",
        "goals_cs11", "total_cs11", "pct_cs11",
        "soc", "makespan", "wait_pct", "comp_time_ms",
        "stuck_cs1", "stuck_cs6", "stuck_cs11",
        "no_move_cs1", "no_move_cs6", "no_move_cs11",
        "feasible", "status",
    ]

    all_rows = []
    total_runs = len(agent_counts_list) * n_seeds

    print(f"\n{'='*100}", flush=True)
    print(f"SCALING EXPERIMENT: room-64-64-8 (640x640), fleets cs={{1,6,11}}", flush=True)
    print(f"Agent counts: {agent_counts_list}", flush=True)
    horizon_desc = f"auto: max(2*max_bfs, {min_horizon})" if fixed_max_steps == 0 else f"fixed: {fixed_max_steps}"
    print(f"Seeds per count: {n_seeds} | Horizon: {horizon_desc} | Time limit: {time_limit}ms", flush=True)
    print(f"Composition: {int(FLEET_RATIOS[0]*100)}% cs=1, "
          f"{int(FLEET_RATIOS[1]*100)}% cs=6, {int(FLEET_RATIOS[2]*100)}% cs=11", flush=True)
    print(f"{'='*100}\n", flush=True)

    run_idx = 0
    for n_agents in agent_counts_list:
        counts = compute_agent_counts(n_agents, FLEET_RATIOS, FLEET_DEFS)
        print(f"\n--- N={n_agents} (cs1={counts[0]}, cs6={counts[1]}, cs11={counts[2]}) ---")
        print(f"{'Seed':>4}  {'Placed':>6}  {'Horiz':>5}  {'Goals':>10}  {'Pct':>5}  "
              f"{'cs1':>8}  {'cs6':>8}  {'cs11':>8}  "
              f"{'SOC':>6}  {'Make':>5}  {'Wait%':>5}  {'ms':>8}  {'Status'}")
        print("-" * 110)

        for seed in range(n_seeds):
            run_idx += 1

            # Generate scenario (reuse cached fleet grids)
            agents, placed, requested, all_placed, fgrids = generate_scenario(
                map_grid, map_w, map_h, counts, FLEET_DEFS, seed=seed*1000 + n_agents,
                prebuilt_fleet_grids=cached_fleet_grids)

            n_placed = len(agents)

            # Compute per-scenario horizon
            if fixed_max_steps > 0:
                max_steps = fixed_max_steps
                max_bfs = 0
            else:
                max_steps, max_bfs = compute_horizon(agents, fgrids, min_horizon)

            scen_path = os.path.join(tmp_dir, f"scen_n{n_agents}_s{seed}.scen")
            result_path = os.path.join(tmp_dir, f"result_n{n_agents}_s{seed}.txt")
            write_scenario(agents, scen_path)

            # Run solver
            solver_out = run_solver(scen_path, result_path, max_steps, time_limit)

            # Parse results
            detailed = parse_result_file(result_path) if solver_out["status"] == "OK" else {}

            goals_str = solver_out.get("goals_reached", "0/0")
            if '/' in goals_str:
                gr, gt = goals_str.split('/')
                goals_reached = int(gr)
                goals_total = int(gt)
            else:
                goals_reached = 0
                goals_total = n_placed

            goal_pct = (goals_reached / goals_total * 100) if goals_total > 0 else 0.0
            comp_time = safe_float(solver_out.get("comp_time_ms", "0"))
            makespan = safe_int(solver_out.get("makespan", "0"))
            soc = detailed.get("soc_computed", safe_int(solver_out.get("sum_of_costs", "0")))
            wait_pct = detailed.get("avg_wait_ratio", 0.0) * 100
            feasible = solver_out.get("feasible", "?")

            # Per-fleet breakdown
            pf_reached = detailed.get("per_fleet_reached", {})
            pf_total = detailed.get("per_fleet_total", {})
            pf_stuck = detailed.get("per_fleet_stuck", {})
            pf_no_move = detailed.get("per_fleet_no_move", {})

            def fleet_str(cs):
                r = pf_reached.get(cs, 0)
                t = pf_total.get(cs, 0)
                return f"{r}/{t}" if t > 0 else "-"

            row = {
                "agent_count": n_agents,
                "seed": seed,
                "n_placed": n_placed,
                "placement_ok": "yes" if all_placed else "no",
                "n_cs1": placed.get(0, 0),
                "n_cs6": placed.get(1, 0),
                "n_cs11": placed.get(2, 0),
                "max_steps": max_steps,
                "max_bfs_dist": max_bfs,
                "goals_reached": goals_reached,
                "goal_pct": round(goal_pct, 1),
                "goals_cs1": pf_reached.get(1, 0),
                "total_cs1": pf_total.get(1, 0),
                "pct_cs1": round(pf_reached.get(1, 0) / pf_total.get(1, 1) * 100, 1) if pf_total.get(1, 0) > 0 else 0,
                "goals_cs6": pf_reached.get(6, 0),
                "total_cs6": pf_total.get(6, 0),
                "pct_cs6": round(pf_reached.get(6, 0) / pf_total.get(6, 1) * 100, 1) if pf_total.get(6, 0) > 0 else 0,
                "goals_cs11": pf_reached.get(11, 0),
                "total_cs11": pf_total.get(11, 0),
                "pct_cs11": round(pf_reached.get(11, 0) / pf_total.get(11, 1) * 100, 1) if pf_total.get(11, 0) > 0 else 0,
                "soc": soc,
                "makespan": makespan,
                "wait_pct": round(wait_pct, 1),
                "comp_time_ms": round(comp_time, 2),
                "stuck_cs1": pf_stuck.get(1, 0),
                "stuck_cs6": pf_stuck.get(6, 0),
                "stuck_cs11": pf_stuck.get(11, 0),
                "no_move_cs1": pf_no_move.get(1, 0),
                "no_move_cs6": pf_no_move.get(6, 0),
                "no_move_cs11": pf_no_move.get(11, 0),
                "feasible": feasible,
                "status": solver_out["status"],
            }
            all_rows.append(row)

            print(f"{seed:>4}  {n_placed:>6}  {max_steps:>5}  {goals_str:>10}  {goal_pct:>4.0f}%  "
                  f"{fleet_str(1):>8}  {fleet_str(6):>8}  {fleet_str(11):>8}  "
                  f"{soc:>6}  {makespan:>5}  {wait_pct:>4.0f}%  {comp_time:>8.1f}  "
                  f"{solver_out['status']}")

    # Write CSV
    print(f"\n\nWriting CSV to {csv_path}...")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(all_rows)

    # Generate markdown summary
    md_path = RESULTS_DIR / "scaling_summary.md"
    print(f"Generating summary at {md_path}...")
    generate_markdown_summary(all_rows, md_path, agent_counts_list, n_seeds)

    # Cleanup temp files
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\nDone! Results in {RESULTS_DIR}/")


def generate_markdown_summary(all_rows, md_path, agent_counts, n_seeds):
    """Generate a markdown summary with key findings and failure analysis."""
    lines = []
    lines.append("# HetPIBT Scaling Results")
    lines.append("")
    lines.append("## Experiment Setup")
    lines.append("")
    lines.append(f"- **Map**: room-64-64-8 (640x640 scaled, MAP_SCALE=10)")
    lines.append(f"- **Fleet types**: cs=1 (50%), cs=6 (30%), cs=11 (20%)")
    lines.append(f"- **Agent counts**: {agent_counts}")
    lines.append(f"- **Seeds per count**: {n_seeds}")
    lines.append(f"- **Max timesteps**: 500 | **Goal lock**: enabled")
    lines.append("")

    # Aggregate stats per agent count
    lines.append("## Summary Table")
    lines.append("")
    lines.append("| Agents | Placed | Goal% | cs1% | cs6% | cs11% | "
                 "Avg SOC | Avg Make | Avg Wait% | Avg ms | Stuck | NoMove |")
    lines.append("|--------|--------|-------|------|------|-------|"
                 "---------|----------|-----------|--------|-------|--------|")

    summary_data = {}
    for n in agent_counts:
        rows = [r for r in all_rows if r["agent_count"] == n]
        if not rows:
            continue

        avg_placed = sum(r["n_placed"] for r in rows) / len(rows)
        avg_goal_pct = sum(r["goal_pct"] for r in rows) / len(rows)
        avg_cs1 = sum(r["pct_cs1"] for r in rows) / len(rows)
        avg_cs6 = sum(r["pct_cs6"] for r in rows) / len(rows)
        avg_cs11 = sum(r["pct_cs11"] for r in rows) / len(rows)
        avg_soc = sum(r["soc"] for r in rows) / len(rows)
        avg_make = sum(r["makespan"] for r in rows) / len(rows)
        avg_wait = sum(r["wait_pct"] for r in rows) / len(rows)
        avg_ms = sum(r["comp_time_ms"] for r in rows) / len(rows)
        total_stuck = sum(r["stuck_cs1"] + r["stuck_cs6"] + r["stuck_cs11"] for r in rows) / len(rows)
        total_no_move = sum(r["no_move_cs1"] + r["no_move_cs6"] + r["no_move_cs11"] for r in rows) / len(rows)

        summary_data[n] = {
            "avg_goal_pct": avg_goal_pct,
            "avg_cs1": avg_cs1, "avg_cs6": avg_cs6, "avg_cs11": avg_cs11,
            "avg_ms": avg_ms, "avg_make": avg_make,
            "total_stuck": total_stuck, "total_no_move": total_no_move,
        }

        lines.append(f"| {n:>6} | {avg_placed:>5.0f} | {avg_goal_pct:>4.1f}% | "
                      f"{avg_cs1:>3.0f}% | {avg_cs6:>3.0f}% | {avg_cs11:>3.0f}% | "
                      f"{avg_soc:>7.0f} | {avg_make:>8.0f} | {avg_wait:>8.1f}% | "
                      f"{avg_ms:>6.1f} | {total_stuck:>5.1f} | {total_no_move:>6.1f} |")

    lines.append("")

    # Find breaking points
    lines.append("## Breaking Points")
    lines.append("")

    thresholds = [90, 75, 50]
    for thresh in thresholds:
        found = None
        for n in sorted(summary_data.keys()):
            if summary_data[n]["avg_goal_pct"] < thresh:
                found = n
                break
        if found:
            lines.append(f"- **Below {thresh}% success**: first at N={found} "
                          f"(avg {summary_data[found]['avg_goal_pct']:.1f}%)")
        else:
            lines.append(f"- **Below {thresh}% success**: not reached in tested range")

    lines.append("")

    # Per-fleet failure analysis
    lines.append("## Per-Fleet Failure Analysis")
    lines.append("")
    lines.append("Which fleet types fail first as congestion increases?")
    lines.append("")

    for n in sorted(summary_data.keys()):
        sd = summary_data[n]
        lines.append(f"### N={n}")
        lines.append(f"- cs=1 (small): {sd['avg_cs1']:.1f}% goals reached")
        lines.append(f"- cs=6 (medium): {sd['avg_cs6']:.1f}% goals reached")
        lines.append(f"- cs=11 (large): {sd['avg_cs11']:.1f}% goals reached")
        lines.append(f"- Avg stuck agents: {sd['total_stuck']:.1f}")
        lines.append(f"- Avg no-move (deadlocked): {sd['total_no_move']:.1f}")
        lines.append("")

    # Performance scaling
    lines.append("## Performance Scaling")
    lines.append("")
    lines.append("| Agents | Avg comp time (ms) | Avg makespan |")
    lines.append("|--------|--------------------|--------------|")
    for n in sorted(summary_data.keys()):
        sd = summary_data[n]
        lines.append(f"| {n:>6} | {sd['avg_ms']:>18.1f} | {sd['avg_make']:>12.0f} |")
    lines.append("")

    # Failure mode analysis
    lines.append("## Failure Mode Analysis")
    lines.append("")
    lines.append("### Deadlocks vs Timeouts")
    lines.append("")
    lines.append("- **No-move agents**: agents that stayed at their start position "
                  "for the entire simulation (likely deadlocked)")
    lines.append("- **Stuck agents**: agents that made some progress but didn't reach "
                  "their goal (ran out of timesteps or couldn't navigate congestion)")
    lines.append("")

    for n in sorted(summary_data.keys()):
        rows = [r for r in all_rows if r["agent_count"] == n]
        total_agents = sum(r["n_placed"] for r in rows)
        total_no_move = sum(r["no_move_cs1"] + r["no_move_cs6"] + r["no_move_cs11"] for r in rows)
        total_stuck_but_moved = sum(
            (r["stuck_cs1"] + r["stuck_cs6"] + r["stuck_cs11"]) -
            (r["no_move_cs1"] + r["no_move_cs6"] + r["no_move_cs11"])
            for r in rows)

        if total_agents > 0:
            lines.append(f"**N={n}**: {total_no_move} deadlocked (no-move), "
                          f"{total_stuck_but_moved} stuck-but-moved, "
                          f"across {len(rows)} runs")
    lines.append("")

    # Fleet interaction failures
    lines.append("### Fleet Type Interaction Failures")
    lines.append("")
    lines.append("Large agents (cs=11) occupying 121 base cells create bottlenecks "
                  "that block smaller agents. The stuck-per-fleet breakdown shows "
                  "which fleet types are most affected by congestion.")
    lines.append("")
    lines.append("| Agents | Stuck cs=1 | Stuck cs=6 | Stuck cs=11 |")
    lines.append("|--------|------------|------------|-------------|")
    for n in sorted(summary_data.keys()):
        rows = [r for r in all_rows if r["agent_count"] == n]
        avg_s1 = sum(r["stuck_cs1"] for r in rows) / len(rows)
        avg_s6 = sum(r["stuck_cs6"] for r in rows) / len(rows)
        avg_s11 = sum(r["stuck_cs11"] for r in rows) / len(rows)
        lines.append(f"| {n:>6} | {avg_s1:>10.1f} | {avg_s6:>10.1f} | {avg_s11:>11.1f} |")
    lines.append("")

    with open(md_path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
