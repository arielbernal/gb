#!/usr/bin/env python3
"""
Run het_rt_lacam and hetpibt on all benchmark scenarios.

Usage:
    source E:/gb/venv/Scripts/activate
    python E:/gb/benchmarks/run_all_experiments.py [--solver both|het_rt_lacam|hetpibt]
                                                    [--category all|intersection|bottleneck_doors|corridor_speed|cooperative_clearing|het_bench]
                                                    [--agents all|n5|n10|n15|n20|n25]
                                                    [--timeout-lacam 30] [--timeout-pibt 30]

Output:
    E:/gb/benchmarks/results/het_rt_lacam.csv
    E:/gb/benchmarks/results/hetpibt.csv
"""
import argparse
import csv
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("E:/gb")
SCENARIOS_DIR = ROOT / "benchmarks" / "scenarios"
MAPS_DIR = ROOT / "benchmarks" / "maps"
RESULTS_DIR = ROOT / "benchmarks" / "results"

HET_RT_LACAM_EXE = ROOT / "het_rt_lacam" / "build" / "Release" / "main.exe"
HETPIBT_EXE = ROOT / "third_party" / "hetpibt" / "build" / "Release" / "main.exe"

# 105-series categories and their maps
CATEGORIES_105 = {
    "intersection": "intersection_105.map",
    "bottleneck_doors": "bottleneck_doors_105.map",
    "corridor_speed": "corridor_speed_105.map",
    "cooperative_clearing": "cooperative_clearing_105.map",
}

AGENT_COUNTS = {
    "n5": "_n5_hb.scen",
    "n10": "_n10_hb.scen",
    "n15": "_n15_hb.scen",
    "n20": "_n20_hb.scen",
    "n25": "_hb.scen",  # full 25-agent scenarios (no _nXX suffix)
}


def discover_scenarios(category_filter="all", agents_filter="all"):
    """Discover all _hb scenario files grouped by (category, agent_count, scen_id)."""
    scenarios = []

    # 105-series
    for cat, map_file in CATEGORIES_105.items():
        if category_filter != "all" and category_filter != cat:
            continue
        map_path = MAPS_DIR / map_file
        prefix = f"{cat}_105_"

        for agent_label, suffix in AGENT_COUNTS.items():
            if agents_filter != "all" and agents_filter != agent_label:
                continue

            if agent_label == "n25":
                # Full scenarios: {cat}_105_{NN}_hb.scen (no _nXX)
                pattern = re.compile(rf"^{re.escape(prefix)}(\d{{2}})_hb\.scen$")
            else:
                # Scaled: {cat}_105_{NN}_{nXX}_hb.scen
                pattern = re.compile(
                    rf"^{re.escape(prefix)}(\d{{2}})_{agent_label}_hb\.scen$"
                )

            for f in sorted(SCENARIOS_DIR.iterdir()):
                m = pattern.match(f.name)
                if m:
                    scen_id = m.group(1)
                    n_agents = int(agent_label[1:]) if agent_label != "n25" else 25
                    scenarios.append({
                        "category": cat,
                        "agents": n_agents,
                        "agent_label": agent_label,
                        "scen_id": scen_id,
                        "scen_path": str(f),
                        "map_path": str(map_path),
                    })

    # het_bench (room120)
    if category_filter in ("all", "het_bench"):
        if agents_filter == "all" or agents_filter == "n25":
            map_path = MAPS_DIR / "room120.map"
            for i in range(10):
                scen_path = SCENARIOS_DIR / "het_bench" / f"scen.{i}"
                if scen_path.exists():
                    scenarios.append({
                        "category": "het_bench",
                        "agents": -1,  # varies per scenario
                        "agent_label": "var",
                        "scen_id": str(i),
                        "scen_path": str(scen_path),
                        "map_path": str(map_path),
                    })

    return scenarios


def run_het_rt_lacam(scen, timeout_s):
    """Run het_rt_lacam on a scenario. Returns dict of results."""
    is_hetbench = scen["category"] == "het_bench"
    cmd = [
        str(HET_RT_LACAM_EXE),
        "-m", scen["map_path"],
        "-i", scen["scen_path"],
        "--goal-lock",
        "-t", str(timeout_s),
        "-v", "1",
        "-o", str(RESULTS_DIR / "tmp_lacam.txt"),
    ]
    if is_hetbench:
        cmd.append("--swap-xy")

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout_s + 10, cwd=str(ROOT)
        )
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        output = ""
    elapsed = (time.time() - t0) * 1000

    result = parse_het_rt_lacam_output(output, elapsed)
    result.update({
        "solver": "het_rt_lacam",
        "category": scen["category"],
        "agents": scen["agents"],
        "agent_label": scen["agent_label"],
        "scen_id": scen["scen_id"],
    })

    # Get actual agent count from verbose output
    m = re.search(r"agents:\s*(\d+)", output)
    if m:
        result["agents"] = int(m.group(1))

    return result


def parse_het_rt_lacam_output(output, elapsed_ms):
    """Parse het_rt_lacam verbose output into a result dict."""
    r = {
        "solved": False,
        "soc": 0,
        "makespan": 0,
        "soc_lb": 0,
        "makespan_lb": 0,
        "goals_reached": 0,
        "goals_total": 0,
        "runtime_ms": round(elapsed_ms),
    }

    # Pattern: sum_of_costs: 2582 (lb=1506, ub=1.72)
    m = re.search(r"sum_of_costs:\s*(\d+)\s*\(lb=(\d+)", output)
    if m:
        soc = int(m.group(1))
        if soc > 0:
            r["solved"] = True
            r["soc"] = soc
            r["soc_lb"] = int(m.group(2))

    m = re.search(r"makespan:\s*(\d+)\s*\(lb=(\d+)", output)
    if m:
        r["makespan"] = int(m.group(1))
        r["makespan_lb"] = int(m.group(2))

    # het_rt_lacam solves all-or-nothing
    m = re.search(r"agents:\s*(\d+)", output)
    if m:
        n = int(m.group(1))
        r["goals_total"] = n
        if r["solved"]:
            r["goals_reached"] = n

    # Check for validation failure
    if "null start" in output or "null goal" in output or "footprint overlap" in output:
        r["solved"] = False
        r["goals_reached"] = 0

    return r


def run_hetpibt(scen, timeout_s):
    """Run hetpibt on a scenario. Returns dict of results."""
    cmd = [
        str(HETPIBT_EXE),
        "-m", scen["map_path"],
        "-s", scen["scen_path"],
        "--seed", "0",
        "--swap-xy",
        "--goal-lock",
        "-v", "1",
        "-o", str(RESULTS_DIR / "tmp_pibt.txt"),
    ]

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout_s + 10, cwd=str(ROOT)
        )
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        output = ""
    elapsed = (time.time() - t0) * 1000

    result = parse_hetpibt_output(output, elapsed)
    result.update({
        "solver": "hetpibt",
        "category": scen["category"],
        "agents": scen["agents"],
        "agent_label": scen["agent_label"],
        "scen_id": scen["scen_id"],
    })

    # Get actual agent count
    m = re.search(r"N=(\d+)", output)
    if m:
        result["agents"] = int(m.group(1))

    return result


def parse_hetpibt_output(output, elapsed_ms):
    """Parse hetpibt verbose output into a result dict."""
    r = {
        "solved": False,
        "soc": 0,
        "makespan": 0,
        "soc_lb": 0,
        "makespan_lb": 0,
        "goals_reached": 0,
        "goals_total": 0,
        "runtime_ms": round(elapsed_ms),
    }

    m = re.search(r"goals_reached=(\d+)/(\d+)", output)
    if m:
        r["goals_reached"] = int(m.group(1))
        r["goals_total"] = int(m.group(2))
        r["solved"] = r["goals_reached"] == r["goals_total"]

    m = re.search(r"sum_of_costs=(\d+)", output)
    if m:
        r["soc"] = int(m.group(1))

    m = re.search(r"makespan=(\d+)", output)
    if m:
        r["makespan"] = int(m.group(1))

    r["runtime_ms"] = round(elapsed_ms)
    return r


CSV_FIELDS = [
    "solver", "category", "agent_label", "scen_id", "agents",
    "solved", "goals_reached", "goals_total",
    "soc", "soc_lb", "makespan", "makespan_lb", "runtime_ms",
]


def write_csv(results, path):
    """Write results list to CSV."""
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"  Written {len(results)} rows to {path}")


def main():
    parser = argparse.ArgumentParser(description="Run all benchmark experiments")
    parser.add_argument("--solver", default="both",
                        choices=["both", "het_rt_lacam", "hetpibt"])
    parser.add_argument("--category", default="all",
                        choices=["all", "intersection", "bottleneck_doors",
                                 "corridor_speed", "cooperative_clearing", "het_bench"])
    parser.add_argument("--agents", default="all",
                        choices=["all", "n5", "n10", "n15", "n20", "n25"])
    parser.add_argument("--timeout-lacam", type=int, default=30,
                        help="Timeout in seconds for het_rt_lacam")
    parser.add_argument("--timeout-pibt", type=int, default=30,
                        help="Timeout in seconds for hetpibt")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = discover_scenarios(args.category, args.agents)
    print(f"Discovered {len(scenarios)} scenarios")
    if not scenarios:
        print("No scenarios found!")
        return

    lacam_results = []
    pibt_results = []

    for idx, scen in enumerate(scenarios):
        label = f"{scen['category']}/{scen['agent_label']}/scen.{scen['scen_id']}"
        progress = f"[{idx+1}/{len(scenarios)}]"

        if args.solver in ("both", "het_rt_lacam"):
            print(f"{progress} het_rt_lacam  {label} ...", end=" ", flush=True)
            r = run_het_rt_lacam(scen, args.timeout_lacam)
            status = f"soc={r['soc']}" if r["solved"] else "FAIL"
            print(f"{status}  ({r['runtime_ms']}ms)")
            lacam_results.append(r)

        if args.solver in ("both", "hetpibt"):
            print(f"{progress} hetpibt       {label} ...", end=" ", flush=True)
            r = run_hetpibt(scen, args.timeout_pibt)
            status = f"{r['goals_reached']}/{r['goals_total']} soc={r['soc']}"
            print(f"{status}  ({r['runtime_ms']}ms)")
            pibt_results.append(r)

    # Write results
    if lacam_results:
        write_csv(lacam_results, RESULTS_DIR / "het_rt_lacam.csv")
    if pibt_results:
        write_csv(pibt_results, RESULTS_DIR / "hetpibt.csv")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, results in [("het_rt_lacam", lacam_results), ("hetpibt", pibt_results)]:
        if not results:
            continue
        solved = sum(1 for r in results if r["solved"])
        total = len(results)
        print(f"\n{name}: {solved}/{total} solved ({100*solved/total:.0f}%)")

        # Per-category breakdown
        cats = sorted(set(r["category"] for r in results))
        for cat in cats:
            cr = [r for r in results if r["category"] == cat]
            cs = sum(1 for r in cr if r["solved"])
            ct = len(cr)
            avg_soc = 0
            solved_socs = [r["soc"] for r in cr if r["solved"] and r["soc"] > 0]
            if solved_socs:
                avg_soc = sum(solved_socs) / len(solved_socs)
            print(f"  {cat:25s}  {cs:3d}/{ct:3d} solved  avg_soc={avg_soc:.0f}")


if __name__ == "__main__":
    main()
