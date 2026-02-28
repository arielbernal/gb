#!/usr/bin/env python3
"""Run het_rt_lacam RT+ST-BFS benchmark for a single category."""
import argparse
import csv
import re
import subprocess
import time
from pathlib import Path

ROOT = Path("E:/gb")
EXE = ROOT / "het_rt_lacam" / "build" / "Release" / "main.exe"
SCEN_DIR = ROOT / "benchmarks" / "scenarios"
MAPS_DIR = ROOT / "benchmarks" / "maps"
OUT_DIR = ROOT / "benchmarks" / "results" / "rt_stbfs"

CATEGORIES_105 = {
    "intersection": "intersection_105.map",
    "bottleneck_doors": "bottleneck_doors_105.map",
    "corridor_speed": "corridor_speed_105.map",
    "cooperative_clearing": "cooperative_clearing_105.map",
}

AGENT_COUNTS = ["n5", "n10", "n15", "n20", "n25"]

CSV_HEADER = [
    "solver", "category", "agent_label", "scen_id", "agents",
    "solved", "goals_reached", "goals_total",
    "soc", "soc_lb", "makespan", "makespan_lb",
    "runtime_ms", "rt_steps",
]


def discover_105(cat):
    scenarios = []
    map_path = MAPS_DIR / CATEGORIES_105[cat]
    for al in AGENT_COUNTS:
        if al == "n25":
            for f in sorted(SCEN_DIR.glob(f"{cat}_105_*_hb.scen")):
                m = re.match(rf"^{re.escape(cat)}_105_(\d{{2}})_hb\.scen$", f.name)
                if m:
                    scenarios.append({
                        "category": cat, "agent_label": "n25",
                        "scen_id": m.group(1), "agents": 25,
                        "scen_path": str(f), "map_path": str(map_path),
                        "swap_xy": False,
                    })
        else:
            for f in sorted(SCEN_DIR.glob(f"{cat}_105_*_{al}_hb.scen")):
                m = re.match(
                    rf"^{re.escape(cat)}_105_(\d{{2}})_{al}_hb\.scen$", f.name
                )
                if m:
                    scenarios.append({
                        "category": cat, "agent_label": al,
                        "scen_id": m.group(1), "agents": int(al[1:]),
                        "scen_path": str(f), "map_path": str(map_path),
                        "swap_xy": False,
                    })
    return scenarios


def discover_het_bench():
    scenarios = []
    map_path = MAPS_DIR / "room120.map"
    for i in range(10):
        sp = SCEN_DIR / "het_bench" / f"scen.{i}"
        if sp.exists():
            scenarios.append({
                "category": "het_bench", "agent_label": "var",
                "scen_id": str(i), "agents": -1,
                "scen_path": str(sp), "map_path": str(map_path),
                "swap_xy": True,
            })
    return scenarios


def run_one(scen, timeout_s, rt_budget):
    cmd = [
        str(EXE),
        "-m", scen["map_path"],
        "-i", scen["scen_path"],
        "--goal-lock",
        "--rt", "--rt-budget", str(rt_budget),
        "-t", str(timeout_s),
        "-v", "1",
    ]
    if scen["swap_xy"]:
        cmd.append("--swap-xy")

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout_s + 10, cwd=str(ROOT),
        )
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        output = ""
    elapsed_ms = int((time.time() - t0) * 1000)

    solved = "goal reached" in output
    rt_steps = 0
    m = re.search(r"(?:goal reached in|timeout after)\s+(\d+)", output)
    if m:
        rt_steps = int(m.group(1))

    makespan = soc = makespan_lb = soc_lb = 0
    goals_reached = goals_total = 0
    agents = scen["agents"]

    m = re.search(r"agents:\s*(\d+)", output)
    if m:
        agents = int(m.group(1))
        goals_total = agents

    if solved:
        goals_reached = agents
        m = re.search(r"makespan:\s*(\d+)\s*\(lb=(\d+)", output)
        if m:
            makespan, makespan_lb = int(m.group(1)), int(m.group(2))
        m = re.search(r"sum_of_costs:\s*(\d+)\s*\(lb=(\d+)", output)
        if m:
            soc, soc_lb = int(m.group(1)), int(m.group(2))

    return {
        "solver": "het_rt_lacam_rt_stbfs",
        "category": scen["category"],
        "agent_label": scen["agent_label"],
        "scen_id": scen["scen_id"],
        "agents": agents,
        "solved": solved,
        "goals_reached": goals_reached,
        "goals_total": goals_total,
        "soc": soc,
        "soc_lb": soc_lb,
        "makespan": makespan,
        "makespan_lb": makespan_lb,
        "runtime_ms": elapsed_ms,
        "rt_steps": rt_steps,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--category", required=True)
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--rt-budget", type=int, default=100)
    args = p.parse_args()

    cat = args.category
    if cat == "het_bench":
        scenarios = discover_het_bench()
        csv_name = "lacam_het_bench.csv"
    else:
        scenarios = discover_105(cat)
        csv_name = f"lacam_{cat}.csv"

    results = []
    for i, scen in enumerate(scenarios):
        label = f"{scen['category']}/{scen['agent_label']}/scen{scen['scen_id']}"
        print(f"  [{i+1}/{len(scenarios)}] {label} ...", end="", flush=True)
        r = run_one(scen, args.timeout, args.rt_budget)
        status = "SOLVED" if r["solved"] else "TIMEOUT"
        if r["solved"]:
            detail = f"steps={r['rt_steps']} soc={r['soc']} ms={r['makespan']} t={r['runtime_ms']}ms"
        else:
            detail = f"steps={r['rt_steps']} t={r['runtime_ms']}ms"
        print(f" {status} {detail}")
        results.append(r)

    csv_path = OUT_DIR / csv_name
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER)
        w.writeheader()
        w.writerows(results)

    solved = sum(1 for r in results if r["solved"])
    print(f"\n=== {cat}: {solved}/{len(results)} solved ===")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
