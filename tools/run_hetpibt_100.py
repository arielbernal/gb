#!/usr/bin/env python3
"""Run hetpibt on all 25 scenarios x 4 map types (100 total).

Captures goals_reached from stdout for partial completion tracking.
"""
import subprocess
import os
import sys
import re
import time
import csv

HETPIBT = "E:/gb/third_party/hetpibt/build/Release/main.exe"
CONVERTER = "E:/gb/benchmarks/generators/convert_to_hetbench.py"
MAP_DIR = "E:/gb/benchmarks/maps"
SCEN_DIR = "E:/gb/benchmarks/scenarios"
RESULT_DIR = "E:/gb/experiments/results"
TIMEOUT_MS = 60000

MAP_CONFIGS = [
    ("corridor_speed", "corridor_speed_105.map", "corridor_speed_105"),
    ("intersection", "intersection_105.map", "intersection_105"),
    ("cooperative_clearing", "cooperative_clearing_105.map", "cooperative_clearing_105"),
    ("bottleneck_doors", "bottleneck_doors_105.map", "bottleneck_doors_105"),
]

NUM_SCENARIOS = 25


def ensure_hb(scen_path, map_path, hb_path):
    if os.path.exists(hb_path):
        return True
    cmd = [sys.executable, CONVERTER,
           "--scen", scen_path, "--map", map_path, "--output", hb_path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0


def run_one(map_path, scen_path, timeout_ms):
    cmd = [
        HETPIBT,
        "-m", map_path,
        "-s", scen_path,
        "-t", str(timeout_ms),
        "--verbose", "1",
    ]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=(timeout_ms / 1000) + 30)
        elapsed = time.time() - t0
        stdout = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        stdout = ""

    result = {
        "solved": False,
        "goals_reached": 0,
        "goals_total": 0,
        "soc": 0,
        "makespan": 0,
        "comp_time_ms": round(elapsed * 1000, 1),
    }

    for line in stdout.split('\n'):
        # goals_reached=X/Y
        m = re.search(r'goals_reached=(\d+)/(\d+)', line)
        if m:
            result["goals_reached"] = int(m.group(1))
            result["goals_total"] = int(m.group(2))
        # goal_reached=X/Y (alternative)
        m = re.search(r'goal_reached=(\d+)/(\d+)', line)
        if m:
            result["goals_reached"] = int(m.group(1))
            result["goals_total"] = int(m.group(2))
        if "feasible=1" in line:
            result["solved"] = True
        m = re.search(r'sum_of_costs=(\d+)', line)
        if m:
            result["soc"] = int(m.group(1))
        m = re.search(r'makespan=(\d+)', line)
        if m:
            result["makespan"] = int(m.group(1))

    return result


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    all_results = []

    for map_type, map_file, scen_prefix in MAP_CONFIGS:
        map_path = os.path.join(MAP_DIR, map_file)
        if not os.path.exists(map_path):
            print(f"SKIP {map_type}: map not found")
            continue

        print(f"\n{'='*60}")
        print(f"{map_type} ({map_file}), {TIMEOUT_MS/1000:.0f}s timeout")
        print(f"{'='*60}")

        for i in range(NUM_SCENARIOS):
            scen_path = os.path.join(SCEN_DIR, f"{scen_prefix}_{i:02d}.scen")
            hb_path = os.path.join(SCEN_DIR, f"{scen_prefix}_{i:02d}_hb.scen")

            if not os.path.exists(scen_path):
                continue

            with open(scen_path) as f:
                n_agents = sum(1 for line in f if line.strip())

            ensure_hb(scen_path, map_path, hb_path)

            print(f"  [{i+1:2d}/25] {scen_prefix}_{i:02d} ({n_agents}ag)...", end=" ", flush=True)
            r = run_one(map_path, hb_path, TIMEOUT_MS)
            if r["goals_total"] == 0:
                r["goals_total"] = n_agents

            pct = r["goals_reached"] / max(r["goals_total"], 1) * 100
            print(f"goals={r['goals_reached']}/{r['goals_total']} ({pct:.0f}%) "
                  f"soc={r['soc']} mk={r['makespan']} t={r['comp_time_ms']:.0f}ms")

            all_results.append({
                "map_type": map_type,
                "seed": i,
                "agents": n_agents,
                "solved": r["solved"],
                "goals_reached": r["goals_reached"],
                "goals_total": r["goals_total"],
                "soc": r["soc"],
                "makespan": r["makespan"],
                "comp_time_ms": r["comp_time_ms"],
            })

        rows = [r for r in all_results if r["map_type"] == map_type]
        s = sum(1 for r in rows if r["solved"])
        gr = sum(r["goals_reached"] for r in rows)
        gt = sum(r["goals_total"] for r in rows)
        print(f"\n  Solved: {s}/{len(rows)}, Goals: {gr}/{gt} ({gr/max(gt,1)*100:.1f}%)")

    # Write CSV
    csv_path = os.path.join(RESULT_DIR, "hetpibt_105_25scenarios.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "map_type", "seed", "agents", "solved",
            "goals_reached", "goals_total", "soc", "makespan", "comp_time_ms"])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nCSV written to {csv_path}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Map Type':<25} {'Solve%':>8} {'Goals%':>8} {'Avg Goals':>12}")
    for map_type, _, _ in MAP_CONFIGS:
        rows = [r for r in all_results if r["map_type"] == map_type]
        if not rows:
            continue
        s = sum(1 for r in rows if r["solved"])
        gr = sum(r["goals_reached"] for r in rows)
        gt = sum(r["goals_total"] for r in rows)
        print(f"  {map_type:<23} {s/len(rows)*100:>7.1f}% {gr/max(gt,1)*100:>7.1f}% {gr:>5}/{gt}")


if __name__ == "__main__":
    main()
