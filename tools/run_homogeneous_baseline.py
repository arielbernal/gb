#!/usr/bin/env python3
"""Run lacam3 on het_bench cs=1 homogeneous scenarios, collect CBS reference, build CSV."""
import csv
import re
import subprocess
import time
from pathlib import Path

ROOT = Path("E:/gb")
REF_DIR = ROOT / "third_party" / "cbsh2rtc" / "reference_solutions"
LACAM3 = ROOT / "third_party" / "lacam3" / "build" / "Debug" / "main.exe"
MAP = ROOT / "het_rt_lacam" / "assets" / "room120.map"
OUT_CSV = ROOT / "agents" / "debug" / "homogeneous_baseline.csv"

# From README.txt — number of cs=1 agents per scenario
AGENT_COUNTS = {0: 3, 1: 2, 2: 1, 3: 2, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3, 9: 2}
# Known infeasible in het_bench context (but CBS solved the cs=1 subproblem)
# scen.1 has goal overlap for cs≥6 agents; scen.9 has wall start for large agents
# CBS solved both cs=1 subproblems successfully

CBS_SOC = {0: 358, 1: 48, 2: 48, 3: 111, 4: 139, 5: 326, 6: 405, 7: 141, 8: 261, 9: 249}

def parse_cbs_csv(path):
    """Parse CBS results CSV, return (runtime_s, soc, solved)."""
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rt = float(row["runtime"]) if row["runtime"] else 0.0
            soc = int(float(row["solution cost"])) if row["solution cost"] else 0
            # CBS solved if runtime > 0 (it always solves optimally or times out)
            solved = soc > 0
            return rt, soc, solved
    return 0.0, 0, False


def run_lacam3(scen_id, n_agents, timeout_s=30):
    """Run lacam3 on scen N, return dict."""
    scen_path = REF_DIR / f"scen.{scen_id}.scen"
    cmd = [
        str(LACAM3),
        "-m", str(MAP),
        "-i", str(scen_path),
        "-N", str(n_agents),
        "-t", str(timeout_s),
        "-v", "1",
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 5)
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        output = ""
    elapsed_ms = int((time.time() - t0) * 1000)

    solved = "solved" in output
    soc = makespan = 0
    m = re.search(r"makespan:\s*(\d+)", output)
    if m:
        makespan = int(m.group(1))
    m = re.search(r"sum_of_costs:\s*(\d+)", output)
    if m:
        soc = int(m.group(1))

    return {
        "scenario": f"scen.{scen_id}",
        "solver": "lacam3",
        "agents": n_agents,
        "solved": solved,
        "soc": soc,
        "makespan": makespan,
        "runtime_ms": elapsed_ms,
    }


def main():
    rows = []

    # 1. CBS reference solutions (already computed, all optimal)
    print("=== CBSH2-RTC reference (pre-computed) ===")
    for i in range(10):
        csv_path = REF_DIR / f"scen.{i}_results.csv"
        rt, soc, solved = parse_cbs_csv(csv_path)
        n = AGENT_COUNTS[i]
        status = f"SOLVED optimal SOC={soc}" if solved else "FAILED"
        print(f"  scen.{i}: k={n} {status} t={rt*1000:.0f}ms")
        rows.append({
            "scenario": f"scen.{i}",
            "solver": "cbsh2_rtc",
            "agents": n,
            "solved": solved,
            "soc": soc,
            "makespan": 0,  # CBS path files have this but not in CSV
            "runtime_ms": int(rt * 1000),
        })

    # 2. lacam3
    print("\n=== LaCAM3 ===")
    for i in range(10):
        n = AGENT_COUNTS[i]
        print(f"  scen.{i} k={n} ...", end="", flush=True)
        r = run_lacam3(i, n, timeout_s=30)
        cbs_soc = CBS_SOC[i]
        ratio = f"{r['soc']/cbs_soc:.3f}x" if r["soc"] > 0 and cbs_soc > 0 else "—"
        status = "SOLVED" if r["solved"] else "TIMEOUT"
        print(f" {status} SOC={r['soc']} (CBS={cbs_soc}, ratio={ratio}) mk={r['makespan']} t={r['runtime_ms']}ms")
        rows.append(r)

    # Write CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scenario", "solver", "agents", "solved", "soc", "makespan", "runtime_ms"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nSaved: {OUT_CSV}")

    # 3. Summary table
    cbs_rows = {r["scenario"]: r for r in rows if r["solver"] == "cbsh2_rtc"}
    lc3_rows = {r["scenario"]: r for r in rows if r["solver"] == "lacam3"}

    print("\n=== Summary ===")
    print(f"{'Scen':<8} {'k':<4} {'CBS SOC':<10} {'CBS ms':<10} {'LC3 SOC':<10} {'LC3 ms':<10} {'ratio':<8}")
    for i in range(10):
        key = f"scen.{i}"
        cb = cbs_rows.get(key, {})
        lc = lc3_rows.get(key, {})
        cbs_soc = cb.get("soc", 0)
        lc3_soc = lc.get("soc", 0)
        ratio = f"{lc3_soc/cbs_soc:.3f}" if lc3_soc > 0 and cbs_soc > 0 else "—"
        lc3_status = "SOLVED" if lc.get("solved") else "TIMEOUT"
        print(f"scen.{i:<3} {AGENT_COUNTS[i]:<4} {cbs_soc:<10} {cb.get('runtime_ms',0):<10} "
              f"{lc3_soc if lc.get('solved') else lc3_status:<10} {lc.get('runtime_ms',0):<10} {ratio}")


if __name__ == "__main__":
    main()
