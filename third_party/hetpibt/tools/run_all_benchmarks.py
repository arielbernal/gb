#!/usr/bin/env python3
"""Run HetPIBT solver on all custom benchmark scenarios.

For each map type (bottleneck_doors, corridor_speed, intersection, cooperative_clearing):
  1. Convert .scen -> het_bench format
  2. Run solver on each scenario
  3. Parse results (goals, SOC, makespan, wait%, compute time, per-fleet)
  4. Save CSV + summary markdown

Usage:
    python run_all_benchmarks.py [--max-steps 500] [--no-goal-lock]
"""
import subprocess
import sys
import os
import re
import csv
import tempfile
import shutil
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)  # hetpibt/
BENCH_DIR = os.path.join(os.path.dirname(ROOT_DIR), "benchmarks")
GENERATORS_DIR = os.path.join(BENCH_DIR, "generators")
MAPS_DIR = os.path.join(BENCH_DIR, "maps")
SCENS_DIR = os.path.join(BENCH_DIR, "scenarios")
RESULTS_DIR = os.path.join(BENCH_DIR, "results")

SOLVER = os.path.join(ROOT_DIR, "build", "Release", "main.exe")
CONVERT_SCRIPT = os.path.join(GENERATORS_DIR, "convert_to_hetbench.py")

FLEET_CS = [1, 3, 7, 11]

# Map type definitions: (map_file, scenario_pattern, num_scenarios)
MAP_TYPES = {
    "bottleneck_doors": {
        "map": "bottleneck_77.map",
        "scen_pattern": "bottleneck_77.scen",
        "num_scenarios": 1,
    },
    "corridor_speed": {
        "map": "corridor_speed_154.map",
        "scen_pattern": "corridor_speed_154_{:02d}.scen",
        "num_scenarios": 25,
    },
    "intersection": {
        "map": "intersection_77.map",
        "scen_pattern": "intersection_77_{:02d}.scen",
        "num_scenarios": 25,
    },
    "cooperative_clearing": {
        "map": "cooperative_clearing_77.map",
        "scen_pattern": "cooperative_clearing_77_{:02d}.scen",
        "num_scenarios": 25,
    },
}


def convert_scen(scen_path, map_path, output_path):
    """Convert .scen to het_bench format using convert_to_hetbench.py."""
    cmd = [sys.executable, CONVERT_SCRIPT,
           "--scen", scen_path, "--map", map_path, "--output", output_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  CONVERT ERROR: {result.stderr.strip()}")
        return False
    return True


def run_solver(map_path, scen_path, result_path, max_steps=500, goal_lock=True):
    """Run our HetPIBT solver and return parsed results."""
    cmd = [SOLVER, "-m", map_path, "-s", scen_path, "-v", "0",
           "--max_timesteps", str(max_steps), "-o", result_path]
    if goal_lock:
        cmd.append("--goal-lock")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # Filter out VALIDATE warnings (cross-fleet start/goal overlap is expected)
        lines = (result.stdout + result.stderr).split('\n')
        output = '\n'.join(l for l in lines if not l.startswith('VALIDATE:'))
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "goals_reached": "0/0", "comp_time_ms": "120000"}
    except FileNotFoundError:
        return {"status": "NOT_FOUND", "goals_reached": "0/0", "comp_time_ms": "0"}

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

    # Parse result file for per-agent trajectory details
    if os.path.exists(result_path):
        parsed.update(parse_result_file(result_path))

    return parsed


def parse_result_file(result_path):
    """Parse solver result file for per-agent trajectory data."""
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

    n_agents = len(agent_fleets)
    if n_agents == 0:
        return {}

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
        "goals_num": goal_reached_count,
        "goals_denom": n_agents,
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
    goal_lock = True
    if "--max-steps" in sys.argv:
        idx = sys.argv.index("--max-steps")
        max_steps = int(sys.argv[idx + 1])
    if "--no-goal-lock" in sys.argv:
        goal_lock = False

    if not os.path.exists(SOLVER):
        print(f"ERROR: Solver not found at {SOLVER}")
        sys.exit(1)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="hetpibt_bench_")

    all_rows = []  # CSV data
    map_summaries = {}  # map_type -> summary stats

    print(f"HetPIBT Benchmark Runner")
    print(f"Solver: {SOLVER}")
    print(f"Max steps: {max_steps}, Goal lock: {goal_lock}")
    print(f"Temp dir: {tmp_dir}")
    print(f"{'='*100}")

    for map_type, cfg in MAP_TYPES.items():
        map_path = os.path.join(MAPS_DIR, cfg["map"])
        if not os.path.exists(map_path):
            print(f"\nSKIPPING {map_type}: map not found at {map_path}")
            continue

        print(f"\n{'='*100}")
        print(f"  {map_type.upper()} ({cfg['num_scenarios']} scenarios)")
        print(f"{'='*100}")

        type_results = []
        type_failures = []

        for i in range(cfg["num_scenarios"]):
            if cfg["num_scenarios"] == 1:
                scen_name = cfg["scen_pattern"]
            else:
                scen_name = cfg["scen_pattern"].format(i)

            scen_path = os.path.join(SCENS_DIR, scen_name)
            if not os.path.exists(scen_path):
                print(f"  SKIP: {scen_name} not found")
                continue

            # Convert to het_bench format
            hetbench_path = os.path.join(tmp_dir, scen_name.replace(".scen", "_hetbench.scen"))
            if not convert_scen(scen_path, map_path, hetbench_path):
                continue

            # Run solver
            result_path = os.path.join(tmp_dir, scen_name.replace(".scen", "_result.txt"))
            r = run_solver(map_path, hetbench_path, result_path, max_steps, goal_lock)

            # Extract metrics
            goals_str = r.get("goals_reached", "0/0")
            goals_num = r.get("goals_num", 0)
            goals_denom = r.get("goals_denom", 0)
            if goals_num == 0 and "/" in str(goals_str):
                parts = goals_str.split("/")
                goals_num = safe_int(parts[0])
                goals_denom = safe_int(parts[1])

            soc = safe_int(r.get("soc_computed", r.get("sum_of_costs", "0")))
            makespan = safe_int(r.get("makespan_computed", r.get("makespan", "0")))
            wait_ratio = safe_float(r.get("avg_wait_ratio", "0"))
            comp_time = safe_int(r.get("comp_time_ms", "0"))
            feasible = r.get("feasible", "?")
            per_fleet = r.get("per_fleet_goals", {})

            # Determine failure mode
            failure_mode = ""
            if r.get("status") == "TIMEOUT":
                failure_mode = "timeout"
            elif goals_num < goals_denom:
                if makespan >= max_steps:
                    failure_mode = "max_steps"
                else:
                    failure_mode = "deadlock"
                # Identify which fleets failed
                failed_fleets = []
                for cs in FLEET_CS:
                    fleet_str = per_fleet.get(cs, "")
                    if "/" in str(fleet_str):
                        fg, ft = fleet_str.split("/")
                        if int(fg) < int(ft):
                            failed_fleets.append(f"cs={cs}({fg}/{ft})")
                if failed_fleets:
                    failure_mode += f" [{','.join(failed_fleets)}]"

            # Build CSV row
            row = {
                "map_type": map_type,
                "scenario": scen_name,
                "seed": i,
                "agents": goals_denom,
                "goals_reached": goals_num,
                "goals_total": goals_denom,
                "goal_pct": f"{100*goals_num/goals_denom:.1f}" if goals_denom > 0 else "0",
                "soc": soc,
                "makespan": makespan,
                "wait_ratio": f"{wait_ratio:.4f}",
                "comp_time_ms": comp_time,
                "feasible": feasible,
                "failure_mode": failure_mode,
            }
            for cs in FLEET_CS:
                row[f"fleet_{cs}_goals"] = per_fleet.get(cs, "-")

            all_rows.append(row)
            type_results.append(row)
            if failure_mode:
                type_failures.append((scen_name, failure_mode))

            # Print progress
            status = "OK" if goals_num == goals_denom else f"PARTIAL({goals_num}/{goals_denom})"
            if failure_mode:
                status = failure_mode
            fleet_detail = "  ".join(f"cs{cs}={per_fleet.get(cs,'-')}" for cs in FLEET_CS)
            print(f"  {scen_name:<35} {goals_num:>2}/{goals_denom:<2} SOC={soc:<5} make={makespan:<4} "
                  f"wait={wait_ratio*100:.0f}% {comp_time:>4}ms  {fleet_detail}  {status}",
                  flush=True)

        # Compute map-type summary
        if type_results:
            total_goals = sum(r["goals_reached"] for r in type_results)
            total_agents = sum(r["goals_total"] for r in type_results)
            avg_soc = sum(r["soc"] for r in type_results) / len(type_results)
            avg_makespan = sum(r["makespan"] for r in type_results) / len(type_results)
            avg_wait = sum(safe_float(r["wait_ratio"]) for r in type_results) / len(type_results)
            avg_time = sum(r["comp_time_ms"] for r in type_results) / len(type_results)
            num_perfect = sum(1 for r in type_results if r["goals_reached"] == r["goals_total"])

            map_summaries[map_type] = {
                "num_scenarios": len(type_results),
                "total_goals": total_goals,
                "total_agents": total_agents,
                "goal_pct": 100 * total_goals / total_agents if total_agents > 0 else 0,
                "avg_soc": avg_soc,
                "avg_makespan": avg_makespan,
                "avg_wait": avg_wait,
                "avg_time": avg_time,
                "num_perfect": num_perfect,
                "failures": type_failures,
            }

            print(f"\n  Summary: {total_goals}/{total_agents} goals ({map_summaries[map_type]['goal_pct']:.1f}%), "
                  f"avg SOC={avg_soc:.0f}, avg makespan={avg_makespan:.0f}, "
                  f"avg wait={avg_wait*100:.1f}%, avg time={avg_time:.0f}ms, "
                  f"perfect={num_perfect}/{len(type_results)}")

    # Write CSV
    csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
    if all_rows:
        fieldnames = ["map_type", "scenario", "seed", "agents",
                      "goals_reached", "goals_total", "goal_pct",
                      "soc", "makespan", "wait_ratio", "comp_time_ms",
                      "feasible", "failure_mode"]
        for cs in FLEET_CS:
            fieldnames.append(f"fleet_{cs}_goals")

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nCSV saved: {csv_path}")

    # Write markdown summary
    md_path = os.path.join(RESULTS_DIR, "benchmark_summary.md")
    with open(md_path, 'w') as f:
        f.write(f"# HetPIBT Benchmark Results\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Solver: HetPIBT, max_steps={max_steps}, goal_lock={goal_lock}\n\n")

        # Overview table
        f.write("## Overview\n\n")
        f.write("| Map Type | Scenarios | Goals | Goal% | Avg SOC | Avg Makespan | Avg Wait% | Avg Time(ms) | Perfect |\n")
        f.write("|----------|-----------|-------|-------|---------|--------------|-----------|--------------|----------|\n")
        for mt, s in map_summaries.items():
            f.write(f"| {mt} | {s['num_scenarios']} | {s['total_goals']}/{s['total_agents']} | "
                    f"{s['goal_pct']:.1f}% | {s['avg_soc']:.0f} | {s['avg_makespan']:.0f} | "
                    f"{s['avg_wait']*100:.1f}% | {s['avg_time']:.0f} | "
                    f"{s['num_perfect']}/{s['num_scenarios']} |\n")

        # Per-fleet breakdown
        f.write("\n## Per-Fleet Goal Breakdown\n\n")
        for mt, s in map_summaries.items():
            f.write(f"\n### {mt}\n\n")
            mt_rows = [r for r in all_rows if r["map_type"] == mt]

            # Aggregate per-fleet
            fleet_totals = {cs: {"reached": 0, "total": 0} for cs in FLEET_CS}
            for row in mt_rows:
                for cs in FLEET_CS:
                    val = row.get(f"fleet_{cs}_goals", "-")
                    if "/" in str(val):
                        g, t = val.split("/")
                        fleet_totals[cs]["reached"] += int(g)
                        fleet_totals[cs]["total"] += int(t)

            f.write("| Fleet | Reached | Total | % |\n")
            f.write("|-------|---------|-------|---|\n")
            for cs in FLEET_CS:
                ft = fleet_totals[cs]
                if ft["total"] > 0:
                    pct = 100 * ft["reached"] / ft["total"]
                    f.write(f"| cs={cs} | {ft['reached']} | {ft['total']} | {pct:.1f}% |\n")

        # Failure analysis
        any_failures = any(s["failures"] for s in map_summaries.values())
        if any_failures:
            f.write("\n## Failure Analysis\n\n")
            for mt, s in map_summaries.items():
                if s["failures"]:
                    f.write(f"\n### {mt}\n\n")
                    f.write(f"Failed scenarios: {len(s['failures'])}/{s['num_scenarios']}\n\n")
                    for scen, mode in s["failures"]:
                        f.write(f"- **{scen}**: {mode}\n")

        # Detailed per-scenario table
        f.write("\n## Detailed Results\n\n")
        for mt in MAP_TYPES:
            mt_rows = [r for r in all_rows if r["map_type"] == mt]
            if not mt_rows:
                continue
            f.write(f"\n### {mt}\n\n")
            f.write("| Scenario | Goals | SOC | Makespan | Wait% | Time(ms) | " +
                    " | ".join(f"cs={cs}" for cs in FLEET_CS) + " | Failure |\n")
            f.write("|----------|-------|-----|----------|-------|----------|" +
                    "|".join("--------" for _ in FLEET_CS) + "|----------|\n")
            for row in mt_rows:
                scen_short = row["scenario"].replace(".scen", "")
                wait_pct = f"{safe_float(row['wait_ratio'])*100:.0f}%"
                fleet_cols = " | ".join(str(row.get(f"fleet_{cs}_goals", "-")) for cs in FLEET_CS)
                f.write(f"| {scen_short} | {row['goals_reached']}/{row['goals_total']} | "
                        f"{row['soc']} | {row['makespan']} | {wait_pct} | {row['comp_time_ms']} | "
                        f"{fleet_cols} | {row['failure_mode']} |\n")

    print(f"Markdown saved: {md_path}")

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # Print final summary
    print(f"\n{'='*100}")
    print(f"FINAL SUMMARY")
    print(f"{'='*100}")
    total_all_goals = sum(s["total_goals"] for s in map_summaries.values())
    total_all_agents = sum(s["total_agents"] for s in map_summaries.values())
    total_all_perfect = sum(s["num_perfect"] for s in map_summaries.values())
    total_all_scens = sum(s["num_scenarios"] for s in map_summaries.values())
    print(f"Total: {total_all_goals}/{total_all_agents} goals "
          f"({100*total_all_goals/total_all_agents:.1f}%), "
          f"{total_all_perfect}/{total_all_scens} perfect scenarios")
    for mt, s in map_summaries.items():
        print(f"  {mt:<25} {s['total_goals']:>4}/{s['total_agents']:<4} "
              f"({s['goal_pct']:.1f}%) "
              f"perfect={s['num_perfect']}/{s['num_scenarios']}")


if __name__ == "__main__":
    main()
