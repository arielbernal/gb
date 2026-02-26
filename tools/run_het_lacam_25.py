#!/usr/bin/env python3
"""Run het_lacam on 25-scenario sets with truncated agent counts."""

import subprocess
import os
import sys
import re
import time

HET_LACAM = "E:/gb/het_rt_lacam/build/Release/main.exe"
SCEN_DIR = "E:/gb/benchmarks/scenarios"
MAP_DIR = "E:/gb/benchmarks/maps"
RESULT_DIR = "E:/gb/experiments/results"
TIMEOUT = 60  # seconds
MAX_AGENTS = 10

MAP_CONFIGS = [
    ("corridor_speed", "corridor_speed_77.map", "corridor_speed_77"),
    ("intersection", "intersection_77.map", "intersection_77"),
    ("cooperative_clearing", "cooperative_clearing_77.map", "cooperative_clearing_77"),
]


def truncate_scenario(scen_path, n_agents):
    """Read first n_agents lines from scenario file."""
    lines = []
    with open(scen_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            lines.append(line)
            if len(lines) >= n_agents:
                break
    return lines


def run_one(map_file, scen_lines, timeout_sec, idx):
    """Run het_lacam on a truncated scenario. Returns dict with results."""
    # Write truncated scenario to temp file
    tmp_scen = os.path.join(RESULT_DIR, f"_tmp_scen_{idx}.scen")
    tmp_result = os.path.join(RESULT_DIR, f"_tmp_result_{idx}.txt")
    with open(tmp_scen, 'w') as f:
        f.write('\n'.join(scen_lines) + '\n')

    cmd = [
        HET_LACAM,
        "-m", map_file,
        "-i", tmp_scen,
        "-t", str(timeout_sec),
        "-v", "1",
        "-l",  # log_short (skip solution dump)
        "--no-star",  # exit after first solution
        "-o", tmp_result,
    ]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_sec + 30)
        elapsed = time.time() - t0
        returncode = proc.returncode
        stderr = proc.stderr
        stdout = proc.stdout
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        returncode = -1
        stderr = "TIMEOUT"
        stdout = ""

    # Parse result file
    result = {
        "solved": False,
        "agents": len(scen_lines),
        "soc": 0,
        "makespan": 0,
        "comp_time_ms": elapsed * 1000,
    }

    if os.path.exists(tmp_result):
        with open(tmp_result) as f:
            for line in f:
                line = line.strip()
                if line.startswith("solved="):
                    result["solved"] = line.split("=")[1] == "1"
                elif line.startswith("soc="):
                    result["soc"] = int(line.split("=")[1])
                elif line.startswith("makespan="):
                    result["makespan"] = int(line.split("=")[1])
                elif line.startswith("comp_time="):
                    result["comp_time_ms"] = float(line.split("=")[1])

    # Parse fleet info from stdout
    fleet_info = ""
    for line in (stdout + stderr).split('\n'):
        if "fleet" in line and "cs=" in line:
            fleet_info += line.strip() + " "

    # Cleanup
    for f in [tmp_scen, tmp_result]:
        if os.path.exists(f):
            os.remove(f)

    return result


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)

    all_results = {}

    for map_type, map_file, scen_prefix in MAP_CONFIGS:
        map_path = os.path.join(MAP_DIR, map_file)
        print(f"\n{'='*60}")
        print(f"Map: {map_type} ({map_file}), {MAX_AGENTS} agents, {TIMEOUT}s timeout")
        print(f"{'='*60}")

        results = []
        solved_count = 0

        for i in range(25):
            scen_name = f"{scen_prefix}_{i:02d}.scen"
            scen_path = os.path.join(SCEN_DIR, scen_name)

            if not os.path.exists(scen_path):
                print(f"  SKIP {scen_name} (not found)")
                continue

            scen_lines = truncate_scenario(scen_path, MAX_AGENTS)
            n = len(scen_lines)

            print(f"  [{i+1:2d}/25] {scen_name} ({n} agents)...", end=" ", flush=True)
            r = run_one(map_path, scen_lines, TIMEOUT, i)
            r["scenario"] = scen_name

            status = "SOLVED" if r["solved"] else "FAILED"
            if r["solved"]:
                solved_count += 1
                print(f"{status} soc={r['soc']} mk={r['makespan']} t={r['comp_time_ms']:.0f}ms")
            else:
                print(f"{status} t={r['comp_time_ms']:.0f}ms")

            results.append(r)

        rate = solved_count / len(results) * 100 if results else 0
        print(f"\n  Result: {solved_count}/{len(results)} solved ({rate:.1f}%)")
        all_results[map_type] = {"results": results, "solved": solved_count, "total": len(results)}

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for map_type, data in all_results.items():
        s, t = data["solved"], data["total"]
        print(f"  {map_type}: {s}/{t} ({s/t*100:.1f}%)")

    # Write CSV
    csv_path = os.path.join(RESULT_DIR, "het_lacam_25scenarios.csv")
    with open(csv_path, 'w') as f:
        f.write("map_type,scenario,agents,solved,soc,makespan,comp_time_ms\n")
        for map_type, data in all_results.items():
            for r in data["results"]:
                f.write(f"{map_type},{r['scenario']},{r['agents']},{r['solved']},{r['soc']},{r['makespan']},{r['comp_time_ms']:.1f}\n")
    print(f"\nCSV written to {csv_path}")


if __name__ == "__main__":
    main()
