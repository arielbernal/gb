#!/usr/bin/env python3
"""Budget sweep: run 8 representative unsolved scenarios at budgets 10,100,1000,10000."""
import csv
import re
import subprocess
import time
from pathlib import Path

ROOT = Path("E:/gb")
EXE = ROOT / "het_rt_lacam" / "build" / "Release" / "main.exe"
OUT = ROOT / "benchmarks" / "results" / "rt_lacam" / "budget_sweep.csv"

SCENARIOS = [
    # (category, agent_label, scen_id, map, scen_path, type)
    ("bottleneck_doors", "n10", "01", "bottleneck_doors_105.map",
     "bottleneck_doors_105_01_n10_hb.scen", "high-step"),
    ("bottleneck_doors", "n15", "02", "bottleneck_doors_105.map",
     "bottleneck_doors_105_02_n15_hb.scen", "high-step"),
    ("corridor_speed", "n10", "04", "corridor_speed_105.map",
     "corridor_speed_105_04_n10_hb.scen", "high-step"),
    ("corridor_speed", "n15", "04", "corridor_speed_105.map",
     "corridor_speed_105_04_n15_hb.scen", "mid-step"),
    ("intersection", "n10", "03", "intersection_105.map",
     "intersection_105_03_n10_hb.scen", "high-step"),
    ("intersection", "n10", "04", "intersection_105.map",
     "intersection_105_04_n10_hb.scen", "high-step"),
    ("cooperative_clearing", "n15", "04", "cooperative_clearing_105.map",
     "cooperative_clearing_105_04_n15_hb.scen", "low-step"),
    ("cooperative_clearing", "n20", "02", "cooperative_clearing_105.map",
     "cooperative_clearing_105_02_n20_hb.scen", "low-step"),
]

BUDGETS = [10, 100, 1000, 10000]

def run(map_file, scen_file, budget, timeout=60):
    cmd = [
        str(EXE),
        "-m", str(ROOT / "benchmarks" / "maps" / map_file),
        "-i", str(ROOT / "benchmarks" / "scenarios" / scen_file),
        "--goal-lock", "--rt", "--rt-budget", str(budget),
        "-t", str(timeout), "-v", "1",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout + 10, cwd=str(ROOT))
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        out = ""

    solved = "goal reached" in out
    steps = 0
    m = re.search(r"(?:goal reached in|timeout after)\s+(\d+)", out)
    if m:
        steps = int(m.group(1))
    soc = 0
    m = re.search(r"sum_of_costs:\s*(\d+)", out)
    if m:
        soc = int(m.group(1))
    ms = 0
    m = re.search(r"makespan:\s*(\d+)", out)
    if m:
        ms = int(m.group(1))
    t_ms = 0
    # Get last elapsed value
    for m2 in re.finditer(r"elapsed:\s*(\d+)ms", out):
        t_ms = int(m2.group(1))
    if t_ms == 0:
        # Try alternate format
        m = re.search(r"elapsed:\s+(\d+)ms", out)
        if m:
            t_ms = int(m.group(1))

    return solved, steps, soc, ms, t_ms, out


def main():
    rows = []
    header = ["category", "agent_label", "scen_id", "type", "budget",
              "solved", "steps", "soc", "makespan", "time_ms"]

    for cat, al, sid, mapf, scenf, stype in SCENARIOS:
        for budget in BUDGETS:
            label = f"{cat}/{al}/scen{sid}"
            print(f"  {label} budget={budget:>5} ...", end="", flush=True)
            solved, steps, soc, ms, t_ms, out = run(mapf, scenf, budget)

            # Fallback time parsing
            if t_ms == 0 and out:
                for m in re.finditer(r"elapsed:\s+(\d+)", out):
                    t_ms = int(m.group(1))

            status = "SOLVED" if solved else "TIMEOUT"
            detail = f"steps={steps} soc={soc} t={t_ms}ms" if solved else f"steps={steps} t={t_ms}ms"
            print(f" {status} {detail}")

            rows.append({
                "category": cat, "agent_label": al, "scen_id": sid,
                "type": stype, "budget": budget, "solved": solved,
                "steps": steps, "soc": soc, "makespan": ms, "time_ms": t_ms,
            })

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
