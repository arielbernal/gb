#!/usr/bin/env python3
"""Run hetpibt scaling experiment: varying agent counts on intersection and cooperative_clearing."""
import subprocess
import re
import os

MAPS_DIR = "E:/gb/benchmarks/maps"
SCEN_DIR = "E:/gb/benchmarks/scenarios"
HETPIBT = "E:/gb/third_party/hetpibt/build/Release/main.exe"
OUTFILE = "E:/gb/experiments/results/hetpibt_scaling_feb25.csv"

MAP_TYPES = ["intersection_105", "cooperative_clearing_105"]
AGENT_COUNTS = [5, 10, 15, 20, 25]
SEEDS = range(5)

os.makedirs(os.path.dirname(OUTFILE), exist_ok=True)

with open(OUTFILE, 'w') as fout:
    fout.write("map_type,seed,agents,goals_reached,goals_total,goal_pct,SOC,makespan,time_ms\n")

    for mt in MAP_TYPES:
        map_file = f"{MAPS_DIR}/{mt}.map"
        for n in AGENT_COUNTS:
            for seed in SEEDS:
                if n == 25:
                    scen = f"{SCEN_DIR}/{mt}_{seed:02d}_hb.scen"
                else:
                    scen = f"{SCEN_DIR}/{mt}_{seed:02d}_n{n}_hb.scen"

                try:
                    result = subprocess.run(
                        [HETPIBT, "-m", map_file, "-s", scen, "-t", "60"],
                        capture_output=True, text=True, timeout=90
                    )
                    output = result.stdout + result.stderr
                except Exception as e:
                    output = ""

                m_goals = re.search(r'goals_reached=(\d+)/(\d+)', output)
                m_soc = re.search(r'sum_of_costs=(\d+)', output)
                m_makespan = re.search(r'makespan=(\d+)', output)
                m_time = re.search(r'comp_time\(ms\)=(\d+)', output)

                gr = int(m_goals.group(1)) if m_goals else 0
                gt = int(m_goals.group(2)) if m_goals else 0
                soc = int(m_soc.group(1)) if m_soc else 0
                mk = int(m_makespan.group(1)) if m_makespan else 0
                tms = int(m_time.group(1)) if m_time else 0
                pct = 100.0 * gr / gt if gt > 0 else 0.0

                print(f"  {mt} seed={seed:02d} n={n:2d}: {gr}/{gt} ({pct:.0f}%) SOC={soc} mk={mk} T={tms}ms")
                fout.write(f"{mt},{seed:02d},{n},{gr},{gt},{pct:.1f},{soc},{mk},{tms}\n")
                fout.flush()

print(f"\nResults: {OUTFILE}")
