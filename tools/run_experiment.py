#!/usr/bin/env python3
"""
Create and run a documented experiment.

Usage:
  python run_experiment.py \
    --name "cbsh2rtc_comparison" \
    --solver het_rt_lacam \
    --solver-bin ../het_rt_lacam/build/het_rt_lacam \
    --map ../benchmarks/maps/room-64-64-8.map \
    --scenarios ../benchmarks/scenarios/het_bench/ \
    --purpose "Validate het_rt_lacam against CBS optimal on homogeneous instances"

Creates:
  experiments/YYYY-MM-DD_<name>/
  +-- README.md
  +-- results.csv
  +-- replays/
"""
import argparse
import os
import re
import subprocess
import csv
from datetime import datetime
from pathlib import Path


def create_experiment_dir(base_dir, name):
    """Create timestamped experiment directory."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    exp_dir = Path(base_dir) / f"{date_str}_{name}"
    (exp_dir / "replays").mkdir(parents=True, exist_ok=True)
    return exp_dir


def parse_hetpibt_stdout(stdout):
    """Parse hetpibt stdout output.

    Expected format (one key=value per line):
      comp_time(ms)=42
      feasible=1
      makespan=89
      sum_of_costs=312
      goals_reached=4/4
    """
    result = {}
    for line in stdout.split('\n'):
        line = line.strip()
        if '=' not in line:
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip()

        if key == "comp_time(ms)":
            result["comp_time_ms"] = float(val)
        elif key == "feasible":
            result["solved"] = val in ("1", "true", "True")
        elif key == "makespan":
            result["makespan"] = int(val)
        elif key == "sum_of_costs":
            result["soc"] = int(val)
        elif key == "goals_reached":
            # Format: "N/M"
            parts = val.split('/')
            result["goals_reached"] = int(parts[0])
            result["goals_total"] = int(parts[1]) if len(parts) > 1 else None
            # Solved = all goals reached
            if result.get("goals_total"):
                result["solved"] = result["goals_reached"] == result["goals_total"]

    return result


def parse_hetlacam_stdout(stdout):
    """Parse het_rt_lacam (het_lacam) stdout output.

    Expected format (tab-separated on one line):
      solved\tmakespan: 89 (lb=50, ub=2)\tsum_of_costs: 312 (lb=200, ub=2)\tsum_of_loss: 50
    Also may print comp_time separately.
    """
    result = {}
    for line in stdout.split('\n'):
        line = line.strip()

        # Check for "solved" or "unsolved" indicator
        if "solved" in line.lower() and "makespan" in line.lower():
            result["solved"] = not line.lower().startswith("unsolved")

            # Extract makespan: N
            mk_match = re.search(r'makespan:\s*(\d+)', line)
            if mk_match:
                result["makespan"] = int(mk_match.group(1))

            # Extract sum_of_costs: N
            soc_match = re.search(r'sum_of_costs:\s*(\d+)', line)
            if soc_match:
                result["soc"] = int(soc_match.group(1))

            # Extract sum_of_loss: N
            loss_match = re.search(r'sum_of_loss:\s*(\d+)', line)
            if loss_match:
                result["sum_of_loss"] = int(loss_match.group(1))

        # Look for comp_time in output file or stdout
        if "comp_time" in line.lower():
            ct_match = re.search(r'comp_time[^=]*=\s*([\d.]+)', line)
            if ct_match:
                result["comp_time_ms"] = float(ct_match.group(1))

    return result


def parse_solver_output_file(output_path):
    """Parse a solver output file (key=value format, shared by both solvers).

    Both het_lacam and hetpibt write:
      agents=N
      solved=1/0
      soc=N
      makespan=N
      comp_time=N (het_lacam) or comp_time(ms)=N (hetpibt)
    """
    result = {}
    if not os.path.exists(output_path):
        return result

    with open(output_path) as f:
        for line in f:
            line = line.strip()
            if '=' not in line or line.startswith("solution"):
                break
            key, _, val = line.partition('=')
            key = key.strip()
            val = val.strip()

            if key == "agents":
                result["n_agents"] = int(val)
            elif key == "solved":
                result["solved"] = val in ("1", "true", "True")
            elif key == "soc":
                result["soc"] = int(val)
            elif key == "makespan":
                result["makespan"] = int(val)
            elif key in ("comp_time", "comp_time(ms)"):
                result["comp_time_ms"] = float(val)
            elif key == "sum_of_costs":
                result["soc"] = int(val)

    return result


def run_solver(solver_bin, map_path, scen_path, output_path, timeout, solver_type,
               extra_args=None):
    """Run solver and capture output. Returns parsed results dict."""
    cmd = [str(solver_bin), "-m", str(map_path), "-s", str(scen_path),
           "-o", str(output_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(f"  Running: {' '.join(cmd)}")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        # Parse stdout based on solver type
        if solver_type == "hetpibt":
            parsed = parse_hetpibt_stdout(proc.stdout)
        else:
            parsed = parse_hetlacam_stdout(proc.stdout)

        # Also try parsing the output file for additional fields
        if os.path.exists(output_path):
            file_parsed = parse_solver_output_file(output_path)
            # File data fills in missing fields (stdout takes priority)
            for k, v in file_parsed.items():
                if k not in parsed:
                    parsed[k] = v

        parsed["returncode"] = proc.returncode
        parsed["timeout"] = False
        return parsed

    except subprocess.TimeoutExpired:
        return {"timeout": True, "solved": False, "returncode": -1}


def write_readme(exp_dir, args, results_summary=""):
    """Write experiment README."""
    readme = f"""# Experiment: {args.name}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
Solver: {args.solver}

## Purpose
{args.purpose}

## Parameters
- Map: {args.map}
- Scenarios: {args.scenarios}
- Timeout: {args.timeout}s
- Extra args: {args.extra_args or "none"}

## Reproduce
```bash
python tools/run_experiment.py \\
  --name "{args.name}" \\
  --solver {args.solver} \\
  --solver-bin {args.solver_bin} \\
  --map {args.map} \\
  --scenarios {args.scenarios} \\
  --timeout {args.timeout} \\
  --purpose "{args.purpose}"
```

## Results
{results_summary}

See results.csv for full data. Replay files in replays/.
"""
    with open(exp_dir / "README.md", 'w') as f:
        f.write(readme)


def main():
    parser = argparse.ArgumentParser(description="Run a documented experiment")
    parser.add_argument("--name", required=True, help="Experiment name (used in directory)")
    parser.add_argument("--solver", required=True, choices=["het_rt_lacam", "hetpibt"],
                        help="Solver type (for output parsing)")
    parser.add_argument("--solver-bin", required=True, help="Path to solver binary")
    parser.add_argument("--map", required=True, help="Path to .map file")
    parser.add_argument("--scenarios", required=True,
                        help="Directory of .scen files, or single .scen file")
    parser.add_argument("--purpose", default="", help="Experiment purpose (for README)")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per scenario (s)")
    parser.add_argument("--experiments-dir", default="experiments",
                        help="Base directory for experiments")
    parser.add_argument("--extra-args", nargs="*", default=None,
                        help="Extra args to pass to solver (e.g. --swap-xy --goal-lock)")
    args = parser.parse_args()

    if not os.path.exists(args.solver_bin):
        print(f"ERROR: Solver binary not found: {args.solver_bin}")
        sys.exit(1)

    exp_dir = create_experiment_dir(args.experiments_dir, args.name)
    print(f"Experiment directory: {exp_dir}")

    # Find scenarios
    scen_path = Path(args.scenarios)
    if scen_path.is_dir():
        scenarios = sorted(scen_path.glob("*.scen"))
    else:
        scenarios = [scen_path]

    if not scenarios:
        print(f"ERROR: No .scen files found in {args.scenarios}")
        sys.exit(1)

    print(f"Found {len(scenarios)} scenarios")

    # Map solver name to parser type
    solver_type = "hetpibt" if "pibt" in args.solver else "het_lacam"

    # Run solver on each scenario
    all_results = []
    for i, scen in enumerate(scenarios):
        scen_name = scen.stem
        replay_path = str(exp_dir / "replays" / f"replay_{scen_name}.txt")

        print(f"[{i+1}/{len(scenarios)}] {scen_name}")
        result = run_solver(args.solver_bin, args.map, str(scen), replay_path,
                            args.timeout, solver_type, args.extra_args)
        result["scenario"] = scen_name
        all_results.append(result)

        # Progress indicator
        status = "SOLVED" if result.get("solved") else ("TIMEOUT" if result.get("timeout") else "FAIL")
        soc = result.get("soc", "-")
        ms = result.get("comp_time_ms", "-")
        print(f"  -> {status}  SOC={soc}  time={ms}ms")

    # Write results CSV
    csv_fields = ["scenario", "solved", "soc", "makespan", "comp_time_ms",
                  "goals_reached", "goals_total", "timeout", "returncode"]
    csv_path = exp_dir / "results.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_results)

    # Summary
    n_solved = sum(1 for r in all_results if r.get("solved"))
    n_timeout = sum(1 for r in all_results if r.get("timeout"))
    socs = [r["soc"] for r in all_results if r.get("soc")]
    avg_soc = sum(socs) / len(socs) if socs else 0

    summary = (f"Scenarios: {len(scenarios)}, Solved: {n_solved}, "
               f"Timeouts: {n_timeout}, Avg SOC (solved): {avg_soc:.0f}")
    print(f"\n{summary}")

    write_readme(exp_dir, args, summary)

    print(f"\nResults:  {csv_path}")
    print(f"Replays:  {exp_dir / 'replays'}")
    print(f"README:   {exp_dir / 'README.md'}")


if __name__ == "__main__":
    main()
