#!/usr/bin/env python3
"""Run het_lacam on all 25 scenarios x 4 map types (100 total).

Converts 5-col scenarios to het_bench format, then runs het_lacam.
Collects results into CSV.
"""
import subprocess
import os
import sys
import time
import csv

HET_LACAM = "E:/gb/het_rt_lacam/build/Release/main.exe"
CONVERTER = "E:/gb/benchmarks/generators/convert_to_hetbench.py"
MAP_DIR = "E:/gb/benchmarks/maps"
SCEN_DIR = "E:/gb/benchmarks/scenarios"
RESULT_DIR = "E:/gb/experiments/results"
TIMEOUT = 60  # seconds

MAP_CONFIGS = [
    ("corridor_speed", "corridor_speed_105.map", "corridor_speed_105"),
    ("intersection", "intersection_105.map", "intersection_105"),
    ("cooperative_clearing", "cooperative_clearing_105.map", "cooperative_clearing_105"),
    ("bottleneck_doors", "bottleneck_doors_105.map", "bottleneck_doors_105"),
]

NUM_SCENARIOS = 25


def convert_scenario(scen_path, map_path, output_path):
    """Convert 5-col to het_bench format."""
    cmd = [
        sys.executable, CONVERTER,
        "--scen", scen_path,
        "--map", map_path,
        "--output", output_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"  CONVERT FAILED: {proc.stderr}")
        return False
    # Check for warnings
    if "WARNING" in proc.stdout:
        print(f"  {proc.stdout.strip()}")
    return True


def run_one(map_path, scen_path, timeout_sec):
    """Run het_lacam. Returns dict with results."""
    tmp_result = scen_path + ".result"
    cmd = [
        HET_LACAM,
        "-m", map_path,
        "-i", scen_path,
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
        return {"solved": False, "soc": 0, "makespan": 0,
                "comp_time_ms": elapsed * 1000}

    result = {
        "solved": False, "soc": 0, "makespan": 0,
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
        os.remove(tmp_result)

    return result


def main():
    os.makedirs(RESULT_DIR, exist_ok=True)
    all_results = []

    for map_type, map_file, scen_prefix in MAP_CONFIGS:
        map_path = os.path.join(MAP_DIR, map_file)
        if not os.path.exists(map_path):
            print(f"SKIP {map_type}: map {map_path} not found")
            continue

        print(f"\n{'='*60}")
        print(f"{map_type} ({map_file}), 25 agents, {TIMEOUT}s timeout")
        print(f"{'='*60}")

        solved_count = 0

        for i in range(NUM_SCENARIOS):
            scen_name = f"{scen_prefix}_{i:02d}.scen"
            scen_path = os.path.join(SCEN_DIR, scen_name)
            hb_path = os.path.join(SCEN_DIR, f"{scen_prefix}_{i:02d}_hb.scen")

            if not os.path.exists(scen_path):
                print(f"  SKIP {scen_name} (not found)")
                continue

            # Count agents
            with open(scen_path) as f:
                n_agents = sum(1 for line in f if line.strip())

            # Convert to het_bench
            if not convert_scenario(scen_path, map_path, hb_path):
                continue

            print(f"  [{i+1:2d}/25] {scen_name} ({n_agents} agents)...", end=" ", flush=True)
            r = run_one(map_path, hb_path, TIMEOUT)

            if r["solved"]:
                solved_count += 1
                print(f"SOLVED soc={r['soc']} mk={r['makespan']} t={r['comp_time_ms']:.0f}ms")
            else:
                print(f"FAILED t={r['comp_time_ms']:.0f}ms")

            all_results.append({
                "map_type": map_type,
                "seed": i,
                "scenario": scen_name,
                "agents": n_agents,
                "solved": r["solved"],
                "soc": r["soc"],
                "makespan": r["makespan"],
                "comp_time_ms": round(r["comp_time_ms"], 1),
            })

        n_run = sum(1 for r in all_results if r["map_type"] == map_type)
        print(f"\n  Result: {solved_count}/{n_run} solved ({solved_count/max(n_run,1)*100:.1f}%)")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for map_type, _, _ in MAP_CONFIGS:
        rows = [r for r in all_results if r["map_type"] == map_type]
        if not rows:
            continue
        s = sum(1 for r in rows if r["solved"])
        t = len(rows)
        print(f"  {map_type}: {s}/{t} ({s/t*100:.1f}%)")

    # Write CSV
    csv_path = os.path.join(RESULT_DIR, "het_lacam_105_25scenarios.csv")
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "map_type", "seed", "scenario", "agents", "solved",
            "soc", "makespan", "comp_time_ms"])
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nCSV written to {csv_path}")


if __name__ == "__main__":
    main()
