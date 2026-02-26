#!/usr/bin/env python3
"""Run hetpibt on all 100 benchmark scenarios and collect results."""
import subprocess
import re
import os

MAPS_DIR = "E:/gb/benchmarks/maps"
SCEN_DIR = "E:/gb/benchmarks/scenarios"
HETPIBT = "E:/gb/third_party/hetpibt/build/Release/main.exe"
OUTFILE = "E:/gb/experiments/results/hetpibt_all_105_feb25.csv"

MAP_TYPES = [
    "cooperative_clearing_105",
    "bottleneck_doors_105",
    "corridor_speed_105",
    "intersection_105",
]

os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

with open(OUTFILE, 'w') as fout:
    fout.write("map_type,seed,goals_reached,goals_total,goal_pct,SOC,makespan,time_ms\n")

    for mt in MAP_TYPES:
        map_file = f"{MAPS_DIR}/{mt}.map"
        for seed in range(25):
            scen = f"{SCEN_DIR}/{mt}_{seed:02d}_hb.scen"
            label = f"{mt}_{seed:02d}"

            try:
                result = subprocess.run(
                    [HETPIBT, "-m", map_file, "-s", scen, "-t", "60"],
                    capture_output=True, text=True, timeout=90
                )
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                output = ""
            except Exception as e:
                output = ""
                print(f"  {label} ERROR: {e}")

            # Parse output
            m_goals = re.search(r'goals_reached=(\d+)/(\d+)', output)
            m_soc = re.search(r'sum_of_costs=(\d+)', output)
            m_makespan = re.search(r'makespan=(\d+)', output)
            m_time = re.search(r'comp_time\(ms\)=(\d+)', output)

            goals_reached = int(m_goals.group(1)) if m_goals else 0
            goals_total = int(m_goals.group(2)) if m_goals else 0
            soc = int(m_soc.group(1)) if m_soc else 0
            makespan = int(m_makespan.group(1)) if m_makespan else 0
            time_ms = int(m_time.group(1)) if m_time else 0
            goal_pct = 100.0 * goals_reached / goals_total if goals_total > 0 else 0.0

            print(f"  {label}: {goals_reached}/{goals_total} ({goal_pct:.1f}%) SOC={soc} mk={makespan} T={time_ms}ms")
            fout.write(f"{mt},{seed:02d},{goals_reached},{goals_total},{goal_pct:.1f},{soc},{makespan},{time_ms}\n")
            fout.flush()

print(f"\nResults saved to: {OUTFILE}")
