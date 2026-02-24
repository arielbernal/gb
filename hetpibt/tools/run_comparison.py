#!/usr/bin/env python3
"""Run comparison benchmarks between our HetPIBT solver and pibt_rs.

Both solvers now use the non-overlapping tiling model:
  - pibt_rs: reads base map + applies map_scale internally
  - ours: reads a pre-scaled map (base × map_scale)

het_bench scenario format is read directly by both solvers.

Usage:
    python run_comparison.py [--max-steps 500]
"""
import subprocess
import sys
import os
import re

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


def run_pibt_rs(scen_file, max_steps=500):
    """Run pibt_rs benchmark and parse results."""
    env = os.environ.copy()
    env["PATH"] = CARGO_BIN + os.pathsep + env.get("PATH", "")

    cmd = [PIBT_RS_BENCHMARK, BASE_MAP, scen_file, str(max_steps), str(MAP_SCALE)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"goals_reached": "TIMEOUT", "makespan": str(max_steps), "comp_time_ms": ">120s"}
    except FileNotFoundError:
        return {"goals_reached": "NOT_BUILT", "makespan": "-", "comp_time_ms": "-"}

    parsed = {}
    for line in output.split('\n'):
        line = line.strip()
        if '=' in line:
            key, _, val = line.partition('=')
            if key in ('goals_reached', 'makespan', 'comp_time_ms', 'solved', 'agents'):
                parsed[key] = val
    return parsed


def run_ours(scen_file, max_steps=500):
    """Run our solver directly on het_bench scenario with scaled map."""
    cmd = [OUR_SOLVER, "-m", SCALED_MAP, "-s", scen_file, "-v", "1",
           "--max_timesteps", str(max_steps), "--swap-xy", "-o", os.devnull]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return {"goals_reached": "TIMEOUT", "makespan": str(max_steps), "comp_time_ms": ">120s"}
    except FileNotFoundError:
        return {"goals_reached": "NOT_BUILT", "makespan": "-", "comp_time_ms": "-"}

    parsed = {"_raw": output}
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("goals_reached="):
            parsed["goals_reached"] = line.split("=", 1)[1]
        elif line.startswith("makespan="):
            parsed["makespan"] = line.split("=", 1)[1]
        elif line.startswith("comp_time(ms)="):
            parsed["comp_time_ms"] = line.split("=", 1)[1]
        elif line.startswith("feasible="):
            parsed["feasible"] = line.split("=", 1)[1]

    # Detect failures from stderr
    if "invalid instance" in output:
        parsed["goals_reached"] = parsed.get("goals_reached", "INVALID")
    if "validation failed" in output:
        parsed["goals_reached"] = parsed.get("goals_reached", "VALIDATION_FAIL")

    return parsed


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

    print(f"\n{'='*100}")
    print(f"Het-bench comparison: room-64-64-8, 9 agents, 3 fleets (cs=1,6,11)")
    print(f"Both solvers use non-overlapping tiling model. Max steps: {max_steps}")
    print(f"pibt_rs: base 64x64 + scale={MAP_SCALE}  |  ours: pre-scaled {sw}x{sh}")
    print(f"{'='*100}\n")

    hdr = (f"{'Scen':<10} {'N':>3}  "
           f"{'pibt_rs goals':>14} {'ms':>7} {'make':>6}  "
           f"{'ours goals':>14} {'ms':>7} {'make':>6}  {'notes'}")
    print(hdr)
    print("-" * len(hdr) + "---")

    totals = {"pr_goals": 0, "pr_agents": 0, "our_goals": 0, "our_agents": 0}

    for scen_file in scen_files:
        scen_path = os.path.join(HET_BENCH_DIR, scen_file)
        scen_name = scen_file.replace('.scen', '')

        # Count agents
        with open(scen_path) as f:
            n_agents = sum(1 for l in f if l.strip() and not l.startswith('#'))

        # Run both
        pr = run_pibt_rs(scen_path, max_steps)
        our = run_ours(scen_path, max_steps)

        pr_goals = pr.get("goals_reached", "?")
        pr_time = pr.get("comp_time_ms", "?")
        pr_make = pr.get("makespan", "?")

        our_goals = our.get("goals_reached", "?")
        our_time = our.get("comp_time_ms", "?")
        our_make = our.get("makespan", "?")

        # Notes
        notes = []
        raw = our.get("_raw", "")
        if "invalid instance" in raw:
            notes.append("invalid")
        if "validation failed" in raw:
            notes.append("validation")
        if "scenario validation passed" not in raw and "goals_reached" not in our:
            notes.append("error")
        notes_str = ", ".join(notes) if notes else ""

        # Accumulate totals
        for prefix, goals_str in [("pr", pr_goals), ("our", our_goals)]:
            if '/' in str(goals_str):
                g, t = goals_str.split('/')
                totals[f"{prefix}_goals"] += int(g)
                totals[f"{prefix}_agents"] += int(t)

        print(f"{scen_name:<10} {n_agents:>3}  "
              f"{pr_goals:>14} {pr_time:>7} {pr_make:>6}  "
              f"{our_goals:>14} {our_time:>7} {our_make:>6}  {notes_str}")

    print("-" * len(hdr) + "---")
    print(f"{'TOTAL':<10} {'':>3}  "
          f"{totals['pr_goals']}/{totals['pr_agents']:>13} {'':>7} {'':>6}  "
          f"{totals['our_goals']}/{totals['our_agents']:>13}")


if __name__ == "__main__":
    main()
