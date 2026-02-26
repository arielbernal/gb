#!/usr/bin/env python3
"""
Compare het_rt_lacam (or hetpibt) results against CBSH2-RTC optimal solutions.

Usage:
  python compare_vs_optimal.py \
    --our-results experiments/2026-02_hetlacam_bottleneck/results.csv \
    --reference third_party/cbsh2rtc/reference_solutions/ \
    --output experiments/2026-02_cbsh2rtc_comparison/

Validation rules:
  - If CBS solved and we solved: our SOC must be >= CBS optimal SOC
  - If our SOC < CBS optimal: BUG (better-than-optimal is impossible)
  - If CBS solved and we didn't: investigate (might be timeout, might be bug)
  - If we solved and CBS didn't: good — we scale further
"""
import argparse
import json
import csv
import os
import sys
from pathlib import Path
from datetime import datetime


def load_reference_solutions(ref_dir):
    """Load all CBSH2-RTC reference JSONs from a directory.

    Supports two formats:
    1. Individual JSON files: cbsh2_*.json
    2. Summary CSV: cbsh2_summary.csv
    """
    solutions = {}
    ref_path = Path(ref_dir)

    # Load individual JSONs
    for f in ref_path.glob("cbsh2_*.json"):
        with open(f) as jf:
            data = json.load(jf)
            key = data.get("scenario", f.stem)
            solutions[key] = data

    # Also try loading from summary CSV if JSONs are missing
    csv_path = ref_path / "cbsh2_summary.csv"
    if csv_path.exists() and not solutions:
        with open(csv_path) as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                key = row["scenario"]
                solutions[key] = {
                    "scenario": key,
                    "n_agents": int(row["n_agents"]) if row.get("n_agents") else None,
                    "map": row.get("map", ""),
                    "solved": row["solved"].lower() == "true",
                    "optimal_soc": int(row["optimal_soc"]) if row.get("optimal_soc") not in (None, "", "None") else None,
                    "optimal_makespan": int(row["optimal_makespan"]) if row.get("optimal_makespan") not in (None, "", "None") else None,
                    "runtime_ms": float(row["runtime_ms"]) if row.get("runtime_ms") not in (None, "", "None") else None,
                    "nodes_expanded": int(row["nodes_expanded"]) if row.get("nodes_expanded") not in (None, "", "None") else None,
                }

    return solutions


def load_our_results(results_path):
    """Load our solver's results from CSV.

    Handles column name variations from run_experiment.py output:
      scenario, solved, soc, makespan, comp_time_ms, goals_reached, goals_total
    """
    results = {}
    with open(results_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get("scenario", row.get("scen", ""))

            # Normalize 'solved' from various column names
            solved_raw = row.get("solved", row.get("feasible", ""))
            solved = solved_raw.lower() in ("true", "1", "yes")

            # Parse SOC from various column names
            soc_raw = row.get("soc", row.get("sum_of_costs", ""))
            soc = int(soc_raw) if soc_raw and soc_raw not in ("", "None", "0") else None

            # Parse makespan
            mk_raw = row.get("makespan", "")
            makespan = int(mk_raw) if mk_raw and mk_raw not in ("", "None") else None

            # Parse runtime
            rt_raw = row.get("comp_time_ms", row.get("runtime_ms", ""))
            runtime = float(rt_raw) if rt_raw and rt_raw not in ("", "None") else None

            # Goals reached (hetpibt-specific)
            gr_raw = row.get("goals_reached", "")
            gt_raw = row.get("goals_total", "")

            results[key] = {
                "scenario": key,
                "solved": solved,
                "soc": soc,
                "makespan": makespan,
                "runtime_ms": runtime,
                "goals_reached": gr_raw,
                "goals_total": gt_raw,
            }
    return results


def compare(our_results, ref_solutions):
    """Compare our results against CBS optimal solutions."""
    comparisons = []
    bugs = []
    wins = []
    failures = []

    for scenario_key, ref in sorted(ref_solutions.items()):
        ours = our_results.get(scenario_key)

        row = {
            "scenario": scenario_key,
            "n_agents": ref.get("n_agents"),
            "map": ref.get("map"),
            "cbs_solved": ref["solved"],
            "cbs_soc": ref.get("optimal_soc"),
            "cbs_makespan": ref.get("optimal_makespan"),
            "cbs_ms": ref.get("runtime_ms"),
            "our_solved": ours["solved"] if ours else None,
            "our_soc": ours.get("soc") if ours else None,
            "our_makespan": ours.get("makespan") if ours else None,
            "our_ms": ours.get("runtime_ms") if ours else None,
            "subopt_ratio": None,
            "status": "MISSING",
        }

        if ours is None:
            row["status"] = "MISSING"
            comparisons.append(row)
            continue

        if ref["solved"] and ours["solved"]:
            if ours["soc"] is not None and ref.get("optimal_soc") is not None:
                row["subopt_ratio"] = ours["soc"] / ref["optimal_soc"]
                if ours["soc"] < ref["optimal_soc"]:
                    row["status"] = "BUG"
                    bugs.append(row)
                elif ours["soc"] == ref["optimal_soc"]:
                    row["status"] = "OPTIMAL"
                else:
                    row["status"] = f"SUBOPTIMAL ({row['subopt_ratio']:.3f}x)"
            else:
                row["status"] = "SOLVED (no SOC data)"

        elif ref["solved"] and not ours["solved"]:
            row["status"] = "FAIL"
            failures.append(row)

        elif not ref["solved"] and ours["solved"]:
            row["status"] = "WIN"
            wins.append(row)

        elif not ref["solved"] and not ours["solved"]:
            row["status"] = "BOTH_TIMEOUT"

        comparisons.append(row)

    return comparisons, bugs, wins, failures


def print_summary(comparisons, bugs, wins, failures, solver_name):
    """Print human-readable summary."""
    print("\n" + "=" * 110)
    print(f"COMPARISON: {solver_name} vs CBSH2-RTC (Optimal)")
    print("=" * 110)

    print(f"\n{'Scenario':<30} {'N':>4} {'CBS SOC':>8} {'Our SOC':>8} "
          f"{'Ratio':>7} {'CBS ms':>8} {'Our ms':>8}  Status")
    print("-" * 110)

    for r in comparisons:
        cbs_soc = str(r['cbs_soc']) if r['cbs_soc'] is not None else "-"
        our_soc = str(r['our_soc']) if r['our_soc'] is not None else "-"
        ratio = f"{r['subopt_ratio']:.3f}" if r['subopt_ratio'] is not None else "-"
        cbs_ms = f"{r['cbs_ms']:.0f}" if r['cbs_ms'] is not None else "-"
        our_ms = f"{r['our_ms']:.0f}" if r['our_ms'] is not None else "-"
        n = str(r['n_agents']) if r['n_agents'] is not None else "?"

        print(f"{r['scenario']:<30} {n:>4} {cbs_soc:>8} {our_soc:>8} "
              f"{ratio:>7} {cbs_ms:>8} {our_ms:>8}  {r['status']}")

    # Summary stats
    solved_both = [r for r in comparisons if r['cbs_solved'] and r.get('our_solved')]
    ratios = [r['subopt_ratio'] for r in solved_both if r['subopt_ratio'] is not None]

    print(f"\n--- SUMMARY ---")
    print(f"Total scenarios:    {len(comparisons)}")
    print(f"Both solved:        {len(solved_both)}")
    if ratios:
        print(f"Avg subopt ratio:   {sum(ratios)/len(ratios):.3f}")
        print(f"Max subopt ratio:   {max(ratios):.3f}")
        print(f"Optimal matches:    {sum(1 for r in ratios if r == 1.0)}/{len(ratios)}")
    print(f"Wins (ours only):   {len(wins)}")
    print(f"Failures (CBS only):{len(failures)}")
    print(f"BUGS (< optimal):   {len(bugs)}")

    if bugs:
        print(f"\n*** CRITICAL: {len(bugs)} BUG(S) — solver claims better-than-optimal! ***")
        for b in bugs:
            print(f"  {b['scenario']}: our SOC={b['our_soc']} < optimal={b['cbs_soc']}")

    return len(bugs) == 0


def save_csv(comparisons, output_path):
    """Save comparison results as CSV."""
    fields = ["scenario", "n_agents", "map", "cbs_solved", "cbs_soc", "cbs_makespan",
              "cbs_ms", "our_solved", "our_soc", "our_makespan", "our_ms",
              "subopt_ratio", "status"]
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(comparisons)
    print(f"\nCSV saved to {output_path}")


def save_markdown(comparisons, output_path, solver_name):
    """Save as markdown table for paper."""
    with open(output_path, 'w') as f:
        f.write(f"# {solver_name} vs CBSH2-RTC (Optimal)\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("| Scenario | N | CBS SOC | Ours SOC | Ratio | CBS ms | Ours ms | Status |\n")
        f.write("|----------|---|---------|----------|-------|--------|---------|--------|\n")
        for r in comparisons:
            cbs_soc = str(r['cbs_soc']) if r['cbs_soc'] is not None else "-"
            our_soc = str(r['our_soc']) if r['our_soc'] is not None else "-"
            ratio = f"{r['subopt_ratio']:.3f}" if r['subopt_ratio'] is not None else "-"
            cbs_ms = f"{r['cbs_ms']:.0f}" if r['cbs_ms'] is not None else "-"
            our_ms = f"{r['our_ms']:.0f}" if r['our_ms'] is not None else "-"
            n = str(r['n_agents']) if r['n_agents'] is not None else "?"
            f.write(f"| {r['scenario']} | {n} | {cbs_soc} | {our_soc} | {ratio} | {cbs_ms} | {our_ms} | {r['status']} |\n")

        # Summary section
        solved_both = [r for r in comparisons if r['cbs_solved'] and r.get('our_solved')]
        ratios = [r['subopt_ratio'] for r in solved_both if r['subopt_ratio'] is not None]
        bugs = [r for r in comparisons if r['status'] == 'BUG']
        wins = [r for r in comparisons if r['status'] == 'WIN']
        failures = [r for r in comparisons if r['status'] == 'FAIL']

        f.write(f"\n## Summary\n")
        f.write(f"- Total: {len(comparisons)} scenarios\n")
        f.write(f"- Both solved: {len(solved_both)}\n")
        if ratios:
            f.write(f"- Avg subopt ratio: {sum(ratios)/len(ratios):.3f}\n")
            f.write(f"- Max subopt ratio: {max(ratios):.3f}\n")
            f.write(f"- Optimal matches: {sum(1 for r in ratios if r == 1.0)}/{len(ratios)}\n")
        f.write(f"- Wins: {len(wins)}, Failures: {len(failures)}, Bugs: {len(bugs)}\n")

    print(f"Markdown saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Compare solver results against CBS optimal")
    parser.add_argument("--our-results", required=True, help="Path to our solver's results CSV")
    parser.add_argument("--reference", required=True, help="Path to CBS reference solutions dir")
    parser.add_argument("--output", required=True, help="Output directory for comparison results")
    parser.add_argument("--solver-name", default="het_rt_lacam", help="Name of our solver")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    ref = load_reference_solutions(args.reference)
    if not ref:
        print(f"ERROR: No reference solutions found in {args.reference}")
        sys.exit(1)

    ours = load_our_results(args.our_results)
    if not ours:
        print(f"ERROR: No results found in {args.our_results}")
        sys.exit(1)

    print(f"Loaded {len(ref)} reference solutions")
    print(f"Loaded {len(ours)} results from {args.solver_name}")

    comparisons, bugs, wins, failures = compare(ours, ref)

    ok = print_summary(comparisons, bugs, wins, failures, args.solver_name)

    save_csv(comparisons, os.path.join(args.output, "comparison.csv"))
    save_markdown(comparisons, os.path.join(args.output, "comparison.md"), args.solver_name)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
