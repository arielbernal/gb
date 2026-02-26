#!/usr/bin/env python3
"""Scaling experiment: het_lacam on intersection and cooperative_clearing.

Tests agent counts: 5, 10, 15, 20, 25.
For each count, truncates scenarios and runs het_lacam.
"""
import subprocess
import os
import sys
import re
import time
import csv

HET_LACAM = "E:/gb/het_rt_lacam/build/Release/main.exe"
SCEN_DIR = "E:/gb/benchmarks/scenarios"
MAP_DIR = "E:/gb/benchmarks/maps"
RESULT_DIR = "E:/gb/experiments/results"
TIMEOUT = 60

MAP_CONFIGS = [
    ("intersection", "intersection_105.map", "intersection_105"),
    ("cooperative_clearing", "cooperative_clearing_105.map", "cooperative_clearing_105"),
]

AGENT_COUNTS = [5, 10, 15, 20, 25]
NUM_SCENARIOS = 25


def truncate_hb_scen(hb_path, n_agents):
    """Read first n_agents lines from het_bench scenario."""
    lines = []
    with open(hb_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            lines.append(line)
            if len(lines) >= n_agents:
                break
    # Renumber agent IDs 0..n-1
    renumbered = []
    for i, line in enumerate(lines):
        parts = line.split()
        parts[0] = str(i)  # agent_id
        renumbered.append(' '.join(parts))
    return renumbered


def run_one(map_path, scen_lines, timeout_sec, tag):
    tmp_scen = os.path.join(RESULT_DIR, f"_tmp_scale_{tag}.scen")
    tmp_result = os.path.join(RESULT_DIR, f"_tmp_scale_{tag}.txt")

    with open(tmp_scen, 'w') as f:
        f.write('\n'.join(scen_lines) + '\n')

    cmd = [
        HET_LACAM,
        "-m", map_path,
        "-i", tmp_scen,
        "-t", str(timeout_sec),
        "-v", "0",
        "-l",
        "--no-star",
        "-o", tmp_result,
    ]

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_sec + 30)
        elapsed = time.time() - t0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        for f in [tmp_scen, tmp_result]:
            if os.path.exists(f):
                os.remove(f)
        return {"solved": False, "soc": 0, "makespan": 0,
                "comp_time_ms": elapsed * 1000}

    result = {"solved": False, "soc": 0, "makespan": 0,
              "comp_time_ms": elapsed * 1000}

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

    for f in [tmp_scen, tmp_result]:
        if os.path.exists(f):
            os.remove(f)

    return result


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    all_results = []

    for map_type, map_file, scen_prefix in MAP_CONFIGS:
        map_path = os.path.join(MAP_DIR, map_file)
        if not os.path.exists(map_path):
            print(f"SKIP {map_type}")
            continue

        print(f"\n{'='*60}")
        print(f"SCALING: {map_type}")
        print(f"{'='*60}")

        for n_agents in AGENT_COUNTS:
            solved_count = 0
            total_time = 0

            for i in range(NUM_SCENARIOS):
                hb_path = os.path.join(SCEN_DIR, f"{scen_prefix}_{i:02d}_hb.scen")
                if not os.path.exists(hb_path):
                    continue

                lines = truncate_hb_scen(hb_path, n_agents)
                actual_n = len(lines)

                tag = f"{map_type}_{n_agents}_{i}"
                r = run_one(map_path, lines, TIMEOUT, tag)

                if r["solved"]:
                    solved_count += 1

                total_time += r["comp_time_ms"]

                all_results.append({
                    "map_type": map_type,
                    "agents": actual_n,
                    "seed": i,
                    "solved": r["solved"],
                    "soc": r["soc"],
                    "makespan": r["makespan"],
                    "comp_time_ms": round(r["comp_time_ms"], 1),
                })

            n_run = sum(1 for r in all_results
                        if r["map_type"] == map_type and r["agents"] == n_agents)
            avg_t = total_time / max(n_run, 1)
            print(f"  N={n_agents:2d}: {solved_count}/{n_run} solved "
                  f"({solved_count/max(n_run,1)*100:.0f}%), avg_t={avg_t:.0f}ms")

    # Write CSV
    csv_path = os.path.join(RESULT_DIR, "het_lacam_scaling_105.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "map_type", "agents", "seed", "solved",
            "soc", "makespan", "comp_time_ms"])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nCSV written to {csv_path}")

    # Summary table
    print(f"\n{'='*60}")
    print("SCALING SUMMARY (het_lacam, --no-star, 60s timeout)")
    print(f"{'='*60}")
    print(f"{'Map Type':<25} {'N':>4} {'Solved':>8} {'Rate':>7} {'Avg t(ms)':>10}")
    for map_type, _, _ in MAP_CONFIGS:
        for n in AGENT_COUNTS:
            rows = [r for r in all_results
                    if r["map_type"] == map_type and r["agents"] == n]
            if not rows:
                continue
            s = sum(1 for r in rows if r["solved"])
            avg_t = sum(r["comp_time_ms"] for r in rows) / len(rows)
            print(f"  {map_type:<23} {n:>4} {s:>4}/{len(rows):>2} {s/len(rows)*100:>6.1f}% {avg_t:>10.0f}")


if __name__ == "__main__":
    main()
