#!/usr/bin/env python3
"""Binary-search CBS breaking point on room-64-64-8, then compare all solvers."""
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("E:/gb")
CBS     = ROOT / "agents/backup/center/temp/CBSH2-RTC/build/Release/cbs.exe"
LACAM3  = ROOT / "third_party/lacam3/build/Debug/main.exe"
HETRT   = ROOT / "het_rt_lacam/build/Release/main.exe"
MAP     = ROOT / "benchmarks/maps/room-64-64-8.map"
SCEN    = ROOT / "third_party/lacam3/scripts/scen/scen-random/room-64-64-8-random-1.scen"
OUT_MD  = ROOT / "agents/debug/cbs_breakpoint.md"
TIMEOUT = 60  # seconds


# ---------------------------------------------------------------------------
def run_cbs(n, timeout=TIMEOUT):
    cmd = [str(CBS), "-m", str(MAP), "-a", str(SCEN), "-k", str(n),
           "-t", str(timeout), "-s", "0"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout + 5)
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return False, 0, int((time.time() - t0) * 1000)
    ms = int((time.time() - t0) * 1000)

    # CBS prints "solution cost" in its results CSV line. But with -s 1 (default)
    # it prints one summary line to stdout like:
    #   runtime,...,solution cost,...
    # Actually it prints the CSV header + one data row.
    solved = False
    soc = 0
    for line in out.splitlines():
        parts = line.split(",")
        if len(parts) > 5 and parts[0].replace('.', '', 1).isdigit():
            # data row: runtime, #hl_exp, #hl_gen, #ll_exp, #ll_gen, solution_cost, ...
            try:
                soc_val = int(float(parts[5]))
                if soc_val > 0:
                    solved = True
                    soc = soc_val
                    ms = int(float(parts[0]) * 1000)
            except (ValueError, IndexError):
                pass
    return solved, soc, ms


def run_lacam3(n, timeout=TIMEOUT):
    cmd = [str(LACAM3), "-m", str(MAP), "-i", str(SCEN),
           "-N", str(n), "-t", str(timeout), "-v", "1"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout + 5)
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return False, 0, 0, int((time.time() - t0) * 1000)
    ms = int((time.time() - t0) * 1000)

    solved = "solved" in out
    soc = makespan = 0
    m = re.search(r"sum_of_costs:\s*(\d+)", out)
    if m: soc = int(m.group(1))
    m = re.search(r"makespan:\s*(\d+)", out)
    if m: makespan = int(m.group(1))
    return solved, soc, makespan, ms


def run_het_rt(n, timeout=TIMEOUT):
    cmd = [str(HETRT), "-m", str(MAP), "-i", str(SCEN),
           "-N", str(n), "--rt", "--rt-budget", "100",
           "--goal-lock", "-t", str(timeout), "-v", "1"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout + 10)
        out = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return False, 0, 0, int((time.time() - t0) * 1000)
    ms = int((time.time() - t0) * 1000)

    solved = "goal reached" in out
    soc = makespan = 0
    m = re.search(r"sum_of_costs:\s*(\d+)", out)
    if m: soc = int(m.group(1))
    m = re.search(r"makespan:\s*(\d+)", out)
    if m: makespan = int(m.group(1))
    return solved, soc, makespan, ms


# ---------------------------------------------------------------------------
def binary_search_cbs():
    """Find largest N where CBS solves within TIMEOUT seconds."""
    print("=== CBS Binary Search ===")

    # Quick bounds check
    lo, hi = 5, 200  # CBS rarely scales past ~150 in 60s on 64x64

    # First sample to validate
    print(f"  Checking N={lo}...", end="", flush=True)
    ok, soc, ms = run_cbs(lo)
    print(f" {'SOLVED' if ok else 'FAIL'} soc={soc} {ms}ms")
    if not ok:
        print("  ERROR: even N=5 failed — check binary/map/scen")
        sys.exit(1)

    best_n, best_soc, best_ms = lo, soc, ms

    # Check hi is actually too hard
    print(f"  Checking N={hi}...", end="", flush=True)
    ok, soc, ms = run_cbs(hi)
    print(f" {'SOLVED' if ok else 'FAIL'} soc={soc} {ms}ms")
    if ok:
        print(f"  N={hi} solves — CBS is stronger than expected. Raising hi to 500.")
        best_n, best_soc, best_ms = hi, soc, ms
        hi = 500
        print(f"  Checking N={hi}...", end="", flush=True)
        ok, soc, ms = run_cbs(hi)
        print(f" {'SOLVED' if ok else 'FAIL'} soc={soc} {ms}ms")
        if ok:
            print(f"  N={hi} solves too — using this as result.")
            return hi, soc, ms
        # hi=500 fails, lo=200 solves — bisect [200,500]
        lo = 200
    else:
        lo, hi = 5, hi

    # Bisect [lo, hi]: lo always solves, hi always fails
    while hi - lo > 1:
        mid = (lo + hi) // 2
        print(f"  Bisect [{lo},{hi}] → N={mid}...", end="", flush=True)
        ok, soc, ms = run_cbs(mid)
        print(f" {'SOLVED' if ok else 'FAIL'} soc={soc} {ms}ms")
        if ok:
            lo = mid
            best_n, best_soc, best_ms = mid, soc, ms
        else:
            hi = mid

    # Re-run lo to get clean timing
    print(f"  Re-running N={lo} (confirmed largest solvable)...", end="", flush=True)
    ok, soc, ms = run_cbs(lo)
    print(f" {'SOLVED' if ok else 'FAIL'} soc={soc} {ms}ms")
    return lo, soc, ms


# ---------------------------------------------------------------------------
def main():
    # Step 1: binary search
    best_n, cbs_soc, cbs_ms = binary_search_cbs()
    print(f"\n>>> CBS breaking point: N={best_n}, SOC={cbs_soc}, {cbs_ms}ms\n")

    # Step 2: het_rt_lacam on same N
    print(f"=== het_rt_lacam RT --rt-budget 100 --goal-lock N={best_n} ===")
    het_solved, het_soc, het_mk, het_ms = run_het_rt(best_n)
    print(f"  {'SOLVED' if het_solved else 'TIMEOUT'} soc={het_soc} mk={het_mk} {het_ms}ms")

    # Step 3: lacam3 on same N
    print(f"\n=== LaCAM3 N={best_n} ===")
    lc3_solved, lc3_soc, lc3_mk, lc3_ms = run_lacam3(best_n)
    print(f"  {'SOLVED' if lc3_solved else 'TIMEOUT'} soc={lc3_soc} mk={lc3_mk} {lc3_ms}ms")

    # Step 4: write report
    lines = []
    def w(s=""): lines.append(s)

    w("# CBS Breaking Point — room-64-64-8")
    w()
    w(f"Date: 2026-02-28")
    w(f"Map: `{MAP}`")
    w(f"Scen: `{SCEN}` (first {best_n} entries)")
    w(f"CBS timeout: {TIMEOUT}s")
    w()
    w(f"## Result: largest N CBS solves in {TIMEOUT}s = **{best_n}**")
    w()
    w("## Solver Comparison")
    w()
    w(f"| Solver | N | Solved | SOC | Makespan | Runtime |")
    w(f"|--------|---|--------|-----|----------|---------|")
    w(f"| CBSH2-RTC (optimal) | {best_n} | {'Yes' if cbs_soc > 0 else 'No'} | {cbs_soc} | — | {cbs_ms}ms |")
    w(f"| het_rt_lacam RT+ST-BFS | {best_n} | {'Yes' if het_solved else 'No'} | {het_soc if het_solved else '—'} | {het_mk if het_solved else '—'} | {het_ms}ms |")
    w(f"| LaCAM3 | {best_n} | {'Yes' if lc3_solved else 'No'} | {lc3_soc if lc3_solved else '—'} | {lc3_mk if lc3_solved else '—'} | {lc3_ms}ms |")
    w()

    if het_solved and cbs_soc > 0:
        w(f"**het_rt_lacam SOC ratio vs CBS optimal**: {het_soc/cbs_soc:.3f}x")
    if lc3_solved and cbs_soc > 0:
        w(f"**LaCAM3 SOC ratio vs CBS optimal**: {lc3_soc/cbs_soc:.3f}x")
    w()
    w("## Notes")
    w(f"- CBSH2-RTC: WDG+GR+GC+T+BP with AStar (defaults), `-k {best_n} -t {TIMEOUT}`")
    w(f"- het_rt_lacam: `--rt --rt-budget 100 --goal-lock -t {TIMEOUT}` in MAPF benchmark mode (`-N {best_n}`)")
    w(f"- LaCAM3: default settings, `-N {best_n} -t {TIMEOUT}`")
    w(f"- LaCAM3 binary is Debug build (expected ~10x slower than Release)")
    w(f"- CBS gives optimal SOC; LaCAM3 and het_rt_lacam give approximate solutions")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines))
    print(f"\nReport saved: {OUT_MD}")


if __name__ == "__main__":
    main()
