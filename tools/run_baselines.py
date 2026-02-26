#!/usr/bin/env python3
"""Run multiple solvers on het_bench scenarios and collect results into one CSV.

Usage:
  python run_baselines.py -m MAP -i SCEN [SCEN ...] [-o results.csv]
  python run_baselines.py -m MAP --scen-dir DIR [-o results.csv]
  python run_baselines.py -m MAP -i scen.0.scen scen.1.scen --swap-xy --goal-lock

Solvers run: hetpibt, het_lacam (skipped if binary missing).
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile

HETPIBT = os.environ.get(
    "HETPIBT", r"E:\gb\hetpibt\build\Release\main.exe")
HET_LACAM = os.environ.get(
    "HET_LACAM", r"E:\gb\het_lacam\build\Release\main.exe")

TIMEOUT_SEC = 30


def parse_hetpibt_output(text):
    """Parse hetpibt stdout/stderr for key=value metrics."""
    d = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("goals_reached="):
            d["goals_reached"] = line.split("=", 1)[1]
        elif line.startswith("makespan="):
            d["makespan"] = line.split("=", 1)[1]
        elif line.startswith("comp_time(ms)="):
            d["comp_time_ms"] = line.split("=", 1)[1]
        elif line.startswith("sum_of_costs="):
            d["soc"] = line.split("=", 1)[1]
        elif line.startswith("feasible="):
            d["feasible"] = line.split("=", 1)[1]
    return d


def parse_het_lacam_log(path):
    """Parse het_lacam log file (key=value per line)."""
    d = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                d[key] = val
    except FileNotFoundError:
        pass
    return d


def run_hetpibt(map_path, scen_path, swap_xy, goal_lock, max_steps):
    """Run hetpibt solver. Returns metrics dict."""
    if not os.path.isfile(HETPIBT):
        return None
    cmd = [HETPIBT, "-m", map_path, "-s", scen_path,
           "-t", str(TIMEOUT_SEC * 1000),
           "--max_timesteps", str(max_steps)]
    if swap_xy:
        cmd.append("--swap-xy")
    if goal_lock:
        cmd.append("--goal-lock")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=TIMEOUT_SEC + 5)
        return parse_hetpibt_output(r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return {"_timeout": True}
    except Exception as e:
        return {"_error": str(e)}


def run_het_lacam(map_path, scen_path, swap_xy, tmp_dir, run_index=0):
    """Run het_lacam solver. Returns metrics dict."""
    if not os.path.isfile(HET_LACAM):
        return None
    log_path = os.path.join(tmp_dir, f"het_lacam_result_{run_index}.txt")
    cmd = [HET_LACAM, "-m", map_path, "-i", scen_path,
           "-t", str(TIMEOUT_SEC), "-o", log_path, "-v", "1"]
    if swap_xy:
        cmd.append("--swap-xy")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=TIMEOUT_SEC + 5)
        d = parse_het_lacam_log(log_path)
        # het_lacam writes solved=0/1
        d["_returncode"] = r.returncode
        return d
    except subprocess.TimeoutExpired:
        return {"_timeout": True}
    except Exception as e:
        return {"_error": str(e)}


def extract_row(solver_name, scen_name, raw):
    """Normalize a solver's raw output into a CSV row."""
    if raw is None:
        return None  # solver binary missing, skip entirely

    row = {"scenario": scen_name, "solver": solver_name}

    if raw.get("_timeout"):
        row.update({"N": "", "solved": False, "goals_reached": "",
                    "goal_pct": "", "SOC": "", "makespan": "",
                    "comp_time_ms": TIMEOUT_SEC * 1000})
        return row

    if raw.get("_error"):
        row.update({"N": "", "solved": False, "goals_reached": "",
                    "goal_pct": "", "SOC": "", "makespan": "",
                    "comp_time_ms": ""})
        return row

    # hetpibt: goals_reached="7/9", soc, makespan, comp_time_ms
    # het_lacam: solved=0/1, soc, makespan, comp_time, agents
    goals_str = raw.get("goals_reached", "")
    n = ""
    reached = 0
    total = 0
    if "/" in goals_str:
        reached, total = int(goals_str.split("/")[0]), int(goals_str.split("/")[1])
        n = total

    # het_lacam uses "agents" and "solved"
    if "agents" in raw and not n:
        n = safe_int(raw["agents"])
    solved_flag = raw.get("solved", "")
    if solved_flag in ("0", "false"):
        solved = False
    elif solved_flag in ("1", "true"):
        solved = True
    elif total > 0:
        solved = (reached == total)
    else:
        solved = False

    soc = raw.get("soc", raw.get("sum_of_costs", ""))
    makespan = raw.get("makespan", "")
    comp_time = raw.get("comp_time_ms", raw.get("comp_time", ""))

    goal_pct = ""
    if total > 0:
        goal_pct = f"{100 * reached / total:.1f}"

    # het_lacam solved=1 means all agents reached goals
    if solver_name == "het_lacam" and solved_flag == "1" and not goals_str:
        goals_str = f"{n}/{n}" if n else ""
        reached = safe_int(n)
        total = safe_int(n)
        goal_pct = "100.0" if n else ""

    row.update({
        "N": n,
        "solved": solved,
        "goals_reached": goals_str if goals_str else (f"{reached}/{total}" if total else ""),
        "goal_pct": goal_pct,
        "SOC": soc,
        "makespan": makespan,
        "comp_time_ms": comp_time,
    })
    return row


def safe_int(s, default=0):
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def collect_scenarios(args):
    """Build list of scenario file paths from args."""
    paths = []
    if args.input:
        paths.extend(args.input)
    if args.scen_dir:
        d = args.scen_dir
        paths.extend(
            os.path.join(d, f)
            for f in sorted(os.listdir(d))
            if f.endswith(".scen")
        )
    return paths


def main():
    parser = argparse.ArgumentParser(
        description="Run solvers on het_bench scenarios, collect CSV results")
    parser.add_argument("-m", "--map", required=True, help="Map file (.map)")
    parser.add_argument("-i", "--input", nargs="+",
                        help="Scenario file(s) (.scen)")
    parser.add_argument("--scen-dir",
                        help="Directory of .scen files (alternative to -i)")
    parser.add_argument("-o", "--output", default="baselines.csv",
                        help="Output CSV path (default: baselines.csv)")
    parser.add_argument("--swap-xy", action="store_true",
                        help="Pass --swap-xy to solvers")
    parser.add_argument("--goal-lock", action="store_true",
                        help="Pass --goal-lock to hetpibt")
    parser.add_argument("--max-steps", type=int, default=1000,
                        help="Max timesteps for hetpibt (default: 1000)")
    parser.add_argument("--timeout", type=int, default=30,
                        help="Timeout per solver per scenario in seconds (default: 30)")
    args = parser.parse_args()

    global TIMEOUT_SEC
    TIMEOUT_SEC = args.timeout

    scen_paths = collect_scenarios(args)
    if not scen_paths:
        print("ERROR: no scenario files specified", file=sys.stderr)
        sys.exit(1)

    map_path = args.map
    if not os.path.isfile(map_path):
        print(f"ERROR: map not found: {map_path}", file=sys.stderr)
        sys.exit(1)

    # Check which solvers are available
    solvers = []
    if os.path.isfile(HETPIBT):
        solvers.append("hetpibt")
    else:
        print(f"WARNING: hetpibt not found at {HETPIBT}, skipping")
    if os.path.isfile(HET_LACAM):
        solvers.append("het_lacam")
    else:
        print(f"WARNING: het_lacam not found at {HET_LACAM}, skipping")

    if not solvers:
        print("ERROR: no solvers available", file=sys.stderr)
        sys.exit(1)

    tmp_dir = tempfile.mkdtemp(prefix="baselines_")
    fields = ["scenario", "solver", "N", "solved", "goals_reached",
              "goal_pct", "SOC", "makespan", "comp_time_ms"]
    rows = []

    print(f"Map: {map_path}")
    print(f"Solvers: {', '.join(solvers)}")
    print(f"Scenarios: {len(scen_paths)}")
    print(f"Timeout: {TIMEOUT_SEC}s")
    print()
    print(f"{'Scenario':<35} {'Solver':<12} {'Goals':>10} "
          f"{'Pct':>6} {'SOC':>7} {'Make':>6} {'ms':>8}")
    print("-" * 90)

    for si, scen_path in enumerate(scen_paths):
        scen_name = os.path.basename(scen_path)

        if "hetpibt" in solvers:
            raw = run_hetpibt(map_path, scen_path,
                              args.swap_xy, args.goal_lock, args.max_steps)
            row = extract_row("hetpibt", scen_name, raw)
            if row:
                rows.append(row)
                print(f"{scen_name:<35} {'hetpibt':<12} "
                      f"{row['goals_reached']:>10} {row['goal_pct']:>6} "
                      f"{row['SOC']:>7} {row['makespan']:>6} "
                      f"{row['comp_time_ms']:>8}")

        if "het_lacam" in solvers:
            raw = run_het_lacam(map_path, scen_path,
                                args.swap_xy, tmp_dir, si)
            row = extract_row("het_lacam", scen_name, raw)
            if row:
                rows.append(row)
                print(f"{scen_name:<35} {'het_lacam':<12} "
                      f"{row['goals_reached']:>10} {row['goal_pct']:>6} "
                      f"{row['SOC']:>7} {row['makespan']:>6} "
                      f"{row['comp_time_ms']:>8}")

    # Write CSV
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{len(rows)} results written to {args.output}")

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
