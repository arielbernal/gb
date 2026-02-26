#!/usr/bin/env python3
"""Run comparison benchmarks between our HetPIBT solver and pibt_rs.

Both solvers now use the non-overlapping tiling model:
  - pibt_rs: reads base map + applies map_scale internally
  - ours: reads a pre-scaled map (base x map_scale)

Metrics: goals reached, SOC, makespan, wait ratio, per-fleet breakdowns.
Invalid agents (our solver excludes them) are normalized out of both counts.

Usage:
    python run_comparison.py [--max-steps 500]
"""
import subprocess
import sys
import os
import re
import tempfile

# Paths (relative to this script's directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
PIBT_RS_DIR = os.path.join(os.path.dirname(ROOT_DIR), "pibt_rs")
PYPIBT_DIR = os.path.join(os.path.dirname(ROOT_DIR), "pypibt")

OUR_SOLVER = os.path.join(ROOT_DIR, "build", "Release", "main.exe")
PIBT_RS_BENCHMARK = os.path.join(PIBT_RS_DIR, "target", "release", "examples", "benchmark.exe")

BASE_MAP = os.path.join(PYPIBT_DIR, "assets", "room-64-64-8.map")
HET_BENCH_DIR = os.path.join(PYPIBT_DIR, "het_bench")
SCALED_MAP = os.path.join(ROOT_DIR, "build", "room64_scaled.map")

CARGO_BIN = os.path.join(os.path.expanduser("~"), ".cargo", "bin")
MAP_SCALE = 10

FLEET_CS = [1, 6, 11]  # het_bench fleet cell sizes


def create_scaled_map(base_map, scale, output_map):
    """Create a scaled-up version of a .map file."""
    with open(base_map) as f:
        lines = f.readlines()

    width = height = 0
    grid_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "map":
            grid_start = i + 1
            break
        parts = stripped.split()
        if len(parts) == 2:
            if parts[0] == "width":
                width = int(parts[1])
            elif parts[0] == "height":
                height = int(parts[1])

    grid = []
    for i in range(grid_start, grid_start + height):
        row = lines[i].rstrip('\n\r')
        grid.append(row)

    new_w = width * scale
    new_h = height * scale
    with open(output_map, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {new_h}\n")
        f.write(f"width {new_w}\n")
        f.write("map\n")
        for row in grid:
            scaled_row = ''.join(c * scale for c in row)
            for _ in range(scale):
                f.write(scaled_row + '\n')

    return new_w, new_h


def parse_scen(scen_path):
    """Parse het_bench scenario. Returns list of (fleet_id, cs, sx, sy, gx, gy)."""
    agents = []
    with open(scen_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 10:
                continue
            agents.append({
                'fleet_id': int(parts[1]),
                'cs': int(float(parts[2])),
            })
    return agents


def run_pibt_rs(scen_file, max_steps=500):
    """Run pibt_rs benchmark and parse all metrics."""
    env = os.environ.copy()
    env["PATH"] = CARGO_BIN + os.pathsep + env.get("PATH", "")

    cmd = [PIBT_RS_BENCHMARK, BASE_MAP, scen_file, str(max_steps), str(MAP_SCALE)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"goals_reached": "TIMEOUT", "comp_time_ms": ">120s"}
    except FileNotFoundError:
        return {"goals_reached": "NOT_BUILT", "comp_time_ms": "-"}

    parsed = {"_raw": output}
    for line in output.split('\n'):
        line = line.strip()
        if '=' in line:
            key, _, val = line.partition('=')
            parsed[key] = val
    return parsed


def run_ours(scen_file, result_file, max_steps=500):
    """Run our solver, save result file, parse stdout + result."""
    cmd = [OUR_SOLVER, "-m", SCALED_MAP, "-s", scen_file, "-v", "1",
           "--max_timesteps", str(max_steps), "--swap-xy", "--goal-lock",
           "-o", result_file]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"goals_reached": "TIMEOUT", "comp_time_ms": ">120s"}
    except FileNotFoundError:
        return {"goals_reached": "NOT_BUILT", "comp_time_ms": "-"}

    parsed = {"_raw": output}
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

    # Parse result file for per-agent details
    if os.path.exists(result_file):
        parsed.update(parse_result_file(result_file))

    return parsed


def parse_result_file(result_path):
    """Parse our solver's result file for per-agent trajectory data.

    Returns dict with:
      - agent_fleets: [fleet_id, ...]
      - fleet_defs: {fleet_id: cell_size}
      - per_fleet_goals: {cs: "reached/total"}
      - soc: sum of costs (first goal arrival for goal-reached agents)
      - makespan: max goal arrival time
      - avg_wait_ratio: average wait ratio for goal-reached agents
    """
    agent_fleets = []
    fleet_defs = {}
    starts = []
    goals = []
    trajectories = {}
    in_solution = False

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
                traj.sort(key=lambda e: e[0])
                # Deduplicate: keep last entry per timestep
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
                        fleet_defs[fid] = int(fields[1])  # cell_size
            elif key == "agent_fleet":
                agent_fleets = [int(x) for x in value.split(",")]
            elif key == "starts":
                pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
                starts = [(int(x), int(y)) for x, y in pairs]
            elif key == "goals":
                pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
                goals = [(int(x), int(y)) for x, y in pairs]

    n_agents = len(agent_fleets)
    if n_agents == 0:
        return {}

    # Compute per-agent metrics
    soc = 0
    makespan = 0
    total_wait_ratio = 0.0
    goal_reached_count = 0

    per_fleet_reached = {}
    per_fleet_total = {}

    for aid in range(n_agents):
        fid = agent_fleets[aid]
        cs = fleet_defs.get(fid, 1)
        per_fleet_total[cs] = per_fleet_total.get(cs, 0) + 1

        if aid not in trajectories or aid >= len(goals):
            continue

        traj = trajectories[aid]
        gx, gy = goals[aid]

        # Find first timestep agent reaches its goal
        goal_time = None
        for t_val, fx, fy in traj:
            if fx == gx and fy == gy:
                goal_time = t_val
                break

        if goal_time is not None:
            per_fleet_reached[cs] = per_fleet_reached.get(cs, 0) + 1
            soc += goal_time
            if goal_time > makespan:
                makespan = goal_time

            # Wait ratio: count timesteps where position unchanged
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

    avg_wait = total_wait_ratio / goal_reached_count if goal_reached_count > 0 else 0.0

    per_fleet_goals = {}
    for cs in sorted(per_fleet_total):
        r = per_fleet_reached.get(cs, 0)
        t = per_fleet_total[cs]
        per_fleet_goals[cs] = f"{r}/{t}"

    return {
        "soc_computed": str(soc),
        "makespan_computed": str(makespan),
        "avg_wait_ratio": f"{avg_wait:.4f}",
        "per_fleet_goals": per_fleet_goals,
    }


def safe_int(s, default=0):
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def safe_float(s, default=0.0):
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def main():
    max_steps = 500
    if "--max-steps" in sys.argv:
        idx = sys.argv.index("--max-steps")
        max_steps = int(sys.argv[idx + 1])

    # Check prerequisites
    for path, name in [(PIBT_RS_BENCHMARK, "pibt_rs"), (OUR_SOLVER, "our solver")]:
        if not os.path.exists(path):
            print(f"ERROR: {name} not found at {path}")
            sys.exit(1)

    # Create scaled map
    print(f"Creating {MAP_SCALE}x scaled map...")
    sw, sh = create_scaled_map(BASE_MAP, MAP_SCALE, SCALED_MAP)
    print(f"  Scaled map: {sw}x{sh}")

    # Collect het_bench scenarios
    scen_files = sorted(
        [f for f in os.listdir(HET_BENCH_DIR) if f.endswith('.scen')],
        key=lambda f: int(re.search(r'(\d+)', f).group(1))
    )

    # Temp dir for result files
    tmp_dir = tempfile.mkdtemp(prefix="hetpibt_cmp_")

    print(f"\n{'='*120}")
    print(f"Het-bench comparison: room-64-64-8, 3 fleets (cs=1,6,11)")
    print(f"Both solvers use non-overlapping tiling model. Max steps: {max_steps}")
    print(f"pibt_rs: base 64x64 + scale={MAP_SCALE}  |  ours: pre-scaled {sw}x{sh} + --goal-lock + --swap-xy")
    print(f"{'='*120}")

    # ---- TABLE 1: Main comparison ----
    print(f"\n--- Table 1: Solution Quality ---\n")
    hdr = (f"{'Scen':<8} {'N':>2} "
           f"{'Goals':>8} {'SOC':>6} {'Make':>5} {'Wait%':>6} {'ms':>6}  "
           f"{'Goals':>8} {'SOC':>6} {'Make':>5} {'Wait%':>6} {'ms':>6}  {'Note'}")
    col_hdr = (f"{'':8} {'':>2} "
               f"{'--- pibt_rs ---':^33}  "
               f"{'--- ours ---':^33}")
    print(col_hdr)
    print(hdr)
    print("-" * 110)

    all_results = []
    totals = {
        "pr_goals": 0, "pr_agents": 0, "pr_soc": 0,
        "our_goals": 0, "our_agents": 0, "our_soc": 0,
    }
    footnotes = []

    for scen_file in scen_files:
        scen_path = os.path.join(HET_BENCH_DIR, scen_file)
        scen_name = scen_file.replace('.scen', '')

        # Parse scenario for fleet info
        scen_agents = parse_scen(scen_path)
        n_total = len(scen_agents)

        # Run both solvers
        pr = run_pibt_rs(scen_path, max_steps)
        result_file = os.path.join(tmp_dir, f"{scen_name}_result.txt")
        our = run_ours(scen_path, result_file, max_steps)

        # Parse pibt_rs metrics
        pr_goals_str = pr.get("goals_reached", "?")
        pr_make = pr.get("makespan", "?")
        pr_time = pr.get("comp_time_ms", "?")
        pr_soc = pr.get("soc", "?")
        pr_wait = pr.get("avg_wait_ratio", "?")

        # Parse our metrics
        our_goals_str = our.get("goals_reached", "?")
        our_make = our.get("makespan_computed", our.get("makespan", "?"))
        our_time = our.get("comp_time_ms", "?")
        our_soc = our.get("soc_computed", our.get("sum_of_costs", "?"))
        our_wait = our.get("avg_wait_ratio", "?")

        # Determine valid agent count (our solver may exclude some)
        our_denom = 0
        if '/' in str(our_goals_str):
            our_denom = int(our_goals_str.split('/')[1])
        pr_denom = 0
        if '/' in str(pr_goals_str):
            pr_denom = int(pr_goals_str.split('/')[1])

        n_valid = our_denom if our_denom > 0 else n_total
        n_excluded = n_total - n_valid

        # Normalize pibt_rs denominator to valid agents
        note = ""
        if n_excluded > 0:
            # pibt_rs includes invalid agents; adjust denominator
            pr_num = int(pr_goals_str.split('/')[0]) if '/' in str(pr_goals_str) else 0
            pr_goals_str = f"{pr_num}/{n_valid}"
            note = f"*{n_excluded} excl"
            footnotes.append(f"  {scen_name}: {n_excluded} agent(s) excluded (invalid start/goal placement)")

        # Format wait ratio as percentage
        pr_wait_pct = f"{safe_float(pr_wait)*100:.0f}%" if pr_wait != "?" else "?"
        our_wait_pct = f"{safe_float(our_wait)*100:.0f}%" if our_wait != "?" else "?"

        # Accumulate totals
        for prefix, goals_str, soc_val in [
            ("pr", pr_goals_str, pr_soc),
            ("our", our_goals_str, our_soc)
        ]:
            if '/' in str(goals_str):
                g, t = goals_str.split('/')
                totals[f"{prefix}_goals"] += int(g)
                totals[f"{prefix}_agents"] += int(t)
            totals[f"{prefix}_soc"] += safe_int(soc_val)

        print(f"{scen_name:<8} {n_valid:>2} "
              f"{pr_goals_str:>8} {pr_soc:>6} {pr_make:>5} {pr_wait_pct:>6} {pr_time:>6}  "
              f"{our_goals_str:>8} {our_soc:>6} {our_make:>5} {our_wait_pct:>6} {our_time:>6}  {note}")

        # Save per-fleet data
        all_results.append({
            "scen": scen_name,
            "n_valid": n_valid,
            "pr": pr,
            "our": our,
            "scen_agents": scen_agents,
            "n_excluded": n_excluded,
        })

    print("-" * 110)
    print(f"{'TOTAL':<8} {'':>2} "
          f"{totals['pr_goals']}/{totals['pr_agents']:>7} {totals['pr_soc']:>6} {'':>5} {'':>6} {'':>6}  "
          f"{totals['our_goals']}/{totals['our_agents']:>7} {totals['our_soc']:>6}")

    if footnotes:
        print(f"\nFootnotes (invalid agent exclusions):")
        for fn in footnotes:
            print(fn)

    # ---- TABLE 2: Per-fleet breakdown ----
    print(f"\n--- Table 2: Per-Fleet Goal Breakdown ---\n")
    fleet_hdr_parts = [f"{'Scen':<8} {'N':>2}"]
    for cs in FLEET_CS:
        fleet_hdr_parts.append(f"{'cs='+str(cs)+' pr':>9} {'cs='+str(cs)+' us':>9}")
    fleet_hdr = "  ".join(fleet_hdr_parts)
    print(fleet_hdr)
    print("-" * len(fleet_hdr))

    fleet_totals = {cs: {"pr_g": 0, "pr_t": 0, "our_g": 0, "our_t": 0} for cs in FLEET_CS}

    for r in all_results:
        scen_name = r["scen"]
        n_valid = r["n_valid"]
        pr = r["pr"]
        our = r["our"]
        scen_agents = r["scen_agents"]

        # pibt_rs per-fleet goals from stdout
        pr_fleet = {}
        for cs in FLEET_CS:
            key = f"fleet_{cs}_goals"
            val = pr.get(key, "?")
            pr_fleet[cs] = val

        # Our per-fleet goals from result file parsing
        our_fleet = our.get("per_fleet_goals", {})

        parts = [f"{scen_name:<8} {n_valid:>2}"]
        for cs in FLEET_CS:
            pr_val = pr_fleet.get(cs, "?")
            our_val = our_fleet.get(cs, "?")
            parts.append(f"{pr_val:>9} {our_val:>9}")

            # Accumulate fleet totals
            if '/' in str(pr_val):
                g, t = str(pr_val).split('/')
                fleet_totals[cs]["pr_g"] += int(g)
                fleet_totals[cs]["pr_t"] += int(t)
            if '/' in str(our_val):
                g, t = str(our_val).split('/')
                fleet_totals[cs]["our_g"] += int(g)
                fleet_totals[cs]["our_t"] += int(t)

        print("  ".join(parts))

    # Fleet totals row
    print("-" * len(fleet_hdr))
    total_parts = [f"{'TOTAL':<8} {'':>2}"]
    for cs in FLEET_CS:
        ft = fleet_totals[cs]
        pr_str = f"{ft['pr_g']}/{ft['pr_t']}" if ft['pr_t'] > 0 else "-"
        our_str = f"{ft['our_g']}/{ft['our_t']}" if ft['our_t'] > 0 else "-"
        total_parts.append(f"{pr_str:>9} {our_str:>9}")
    print("  ".join(total_parts))

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
