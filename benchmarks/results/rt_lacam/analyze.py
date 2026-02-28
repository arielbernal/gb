#!/usr/bin/env python3
"""Analyze RT-LaCAM results vs standard mode and hetpibt baselines."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path("E:/gb/benchmarks/results")
RT_CSV = ROOT / "rt_lacam" / "het_rt_lacam_rt_full.csv"
STD_CSV = ROOT / "post_bfs_port" / "het_rt_lacam_full.csv"
PIBT_CSV = ROOT / "post_bfs_port" / "hetpibt_full.csv"
OUT_MD = ROOT / "rt_lacam" / "analysis.md"


def load_csv(path):
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            key = (r["category"], r["agent_label"], r["scen_id"])
            rows[key] = r
    return rows


def is_solved(row):
    if row is None:
        return False
    s = row.get("solved", "")
    return s in ("True", "true", "True", True)


def get_int(row, field, default=0):
    try:
        return int(row.get(field, default))
    except (ValueError, TypeError):
        return default


def get_float(row, field, default=0.0):
    try:
        return float(row.get(field, default))
    except (ValueError, TypeError):
        return default


def main():
    rt = load_csv(RT_CSV)
    std = load_csv(STD_CSV)
    pibt = load_csv(PIBT_CSV)

    all_keys = sorted(set(rt.keys()) | set(std.keys()))

    # ---- 1. Solve rate table ----
    cats_order = ["bottleneck_doors", "corridor_speed", "intersection",
                  "cooperative_clearing", "het_bench"]
    agents_order = ["n5", "n10", "n15", "n20", "n25", "var"]

    solve_counts = defaultdict(lambda: defaultdict(lambda: {"rt": 0, "std": 0, "pibt": 0, "total": 0}))
    for key in all_keys:
        cat, al, sid = key
        solve_counts[cat][al]["total"] += 1
        if is_solved(rt.get(key)):
            solve_counts[cat][al]["rt"] += 1
        if is_solved(std.get(key)):
            solve_counts[cat][al]["std"] += 1
        if is_solved(pibt.get(key)):
            solve_counts[cat][al]["pibt"] += 1

    # ---- 2. SOC ratios: RT vs hetpibt on mutually-solved ----
    rt_pibt_soc_ratios = []
    rt_pibt_mutual = []
    for key in all_keys:
        if is_solved(rt.get(key)) and is_solved(pibt.get(key)):
            rt_soc = get_int(rt[key], "soc")
            pibt_soc = get_int(pibt[key], "soc")
            if pibt_soc > 0 and rt_soc > 0:
                rt_pibt_soc_ratios.append(rt_soc / pibt_soc)
                rt_pibt_mutual.append((key, rt_soc, pibt_soc, rt_soc / pibt_soc))

    # RT vs STD SOC on mutually-solved
    rt_std_soc_ratios = []
    for key in all_keys:
        if is_solved(rt.get(key)) and is_solved(std.get(key)):
            rt_soc = get_int(rt[key], "soc")
            std_soc = get_int(std[key], "soc")
            if std_soc > 0 and rt_soc > 0:
                rt_std_soc_ratios.append(rt_soc / std_soc)

    # ---- 3. Exclusive solves ----
    rt_only_vs_std = []
    std_only_vs_rt = []
    rt_only_vs_pibt = []
    pibt_only_vs_rt = []
    for key in all_keys:
        rs = is_solved(rt.get(key))
        ss = is_solved(std.get(key))
        ps = is_solved(pibt.get(key))
        if rs and not ss:
            rt_only_vs_std.append(key)
        if ss and not rs:
            std_only_vs_rt.append(key)
        if rs and not ps:
            rt_only_vs_pibt.append(key)
        if ps and not rs:
            pibt_only_vs_rt.append(key)

    # ---- 4. Runtime comparison ----
    rt_runtimes_solved = []
    std_runtimes_solved = []
    pibt_runtimes_solved = []
    for key in all_keys:
        if is_solved(rt.get(key)):
            rt_runtimes_solved.append(get_int(rt[key], "runtime_ms"))
        if is_solved(std.get(key)):
            std_runtimes_solved.append(get_int(std[key], "runtime_ms"))
        if is_solved(pibt.get(key)):
            pibt_runtimes_solved.append(get_int(pibt[key], "runtime_ms"))

    # ---- Write analysis.md ----
    lines = []
    lines.append("# RT-LaCAM Full Benchmark Analysis")
    lines.append(f"Date: Feb 27, 2026 | Settings: --rt --rt-budget 100 --goal-lock -t 60")
    lines.append("")

    # Overall summary
    rt_total = sum(1 for k in all_keys if is_solved(rt.get(k)))
    std_total = sum(1 for k in all_keys if is_solved(std.get(k)))
    pibt_total = sum(1 for k in all_keys if is_solved(pibt.get(k)))
    lines.append(f"## Overall: RT {rt_total}/190 | STD {std_total}/190 | hetpibt {pibt_total}/190")
    lines.append("")

    # Section 1: Solve rate table
    lines.append("## 1. Solve Rate: Category × Agent Count")
    lines.append("")
    lines.append("| Category | Agents | RT | STD | hetpibt | Total |")
    lines.append("|----------|--------|----|-----|---------|-------|")
    for cat in cats_order:
        for al in agents_order:
            if solve_counts[cat][al]["total"] > 0:
                d = solve_counts[cat][al]
                lines.append(f"| {cat} | {al} | {d['rt']}/{d['total']} | {d['std']}/{d['total']} | {d['pibt']}/{d['total']} | {d['total']} |")
        # Category subtotal
        cat_rt = sum(solve_counts[cat][al]["rt"] for al in agents_order)
        cat_std = sum(solve_counts[cat][al]["std"] for al in agents_order)
        cat_pibt = sum(solve_counts[cat][al]["pibt"] for al in agents_order)
        cat_total = sum(solve_counts[cat][al]["total"] for al in agents_order)
        if cat_total > 0:
            lines.append(f"| **{cat} total** | | **{cat_rt}/{cat_total}** | **{cat_std}/{cat_total}** | **{cat_pibt}/{cat_total}** | {cat_total} |")
    lines.append(f"| **GRAND TOTAL** | | **{rt_total}/190** | **{std_total}/190** | **{pibt_total}/190** | 190 |")
    lines.append("")

    # Section 2: SOC ratios
    lines.append("## 2. SOC Quality: RT vs hetpibt (mutually solved)")
    lines.append("")
    if rt_pibt_soc_ratios:
        rt_pibt_soc_ratios.sort()
        n = len(rt_pibt_soc_ratios)
        mean_r = sum(rt_pibt_soc_ratios) / n
        med_r = rt_pibt_soc_ratios[n // 2]
        min_r = rt_pibt_soc_ratios[0]
        max_r = rt_pibt_soc_ratios[-1]
        lines.append(f"- Mutually solved: {n} scenarios")
        lines.append(f"- RT/hetpibt SOC ratio: mean={mean_r:.2f}x, median={med_r:.2f}x, min={min_r:.2f}x, max={max_r:.2f}x")
        lines.append(f"- (ratio > 1 means RT has higher SOC = worse quality)")
    lines.append("")

    lines.append("### RT vs STD SOC (mutually solved)")
    if rt_std_soc_ratios:
        rt_std_soc_ratios.sort()
        n2 = len(rt_std_soc_ratios)
        mean_r2 = sum(rt_std_soc_ratios) / n2
        med_r2 = rt_std_soc_ratios[n2 // 2]
        lines.append(f"- Mutually solved: {n2} scenarios")
        lines.append(f"- RT/STD SOC ratio: mean={mean_r2:.2f}x, median={med_r2:.2f}x")
        lines.append(f"- (ratio > 1 means RT has higher SOC than STD anytime search)")
    lines.append("")

    # Section 3: Exclusive solves
    lines.append("## 3. Exclusive Solves")
    lines.append("")
    lines.append(f"### RT solves but STD doesn't ({len(rt_only_vs_std)} scenarios)")
    for key in rt_only_vs_std:
        cat, al, sid = key
        r = rt[key]
        lines.append(f"- {cat}/{al}/scen{sid}: steps={get_int(r,'rt_steps')} SOC={get_int(r,'soc')} t={get_int(r,'runtime_ms')}ms")
    lines.append("")

    lines.append(f"### STD solves but RT doesn't ({len(std_only_vs_rt)} scenarios) — REGRESSIONS")
    for key in std_only_vs_rt:
        cat, al, sid = key
        s = std[key]
        lines.append(f"- {cat}/{al}/scen{sid}: STD SOC={get_int(s,'soc')} makespan={get_int(s,'makespan')}")
    lines.append("")

    lines.append(f"### RT solves but hetpibt doesn't ({len(rt_only_vs_pibt)} scenarios)")
    for key in rt_only_vs_pibt:
        cat, al, sid = key
        lines.append(f"- {cat}/{al}/scen{sid}")
    lines.append("")

    lines.append(f"### hetpibt solves but RT doesn't ({len(pibt_only_vs_rt)} scenarios)")
    for key in pibt_only_vs_rt:
        cat, al, sid = key
        lines.append(f"- {cat}/{al}/scen{sid}")
    lines.append("")

    # Section 5: Runtime comparison
    lines.append("## 4. Runtime Comparison (solved scenarios only)")
    lines.append("")
    def stats(vals):
        if not vals:
            return "N/A"
        vals.sort()
        n = len(vals)
        return f"n={n}, mean={sum(vals)/n:.0f}ms, median={vals[n//2]}ms, p95={vals[int(n*0.95)]}ms, max={vals[-1]}ms"

    lines.append(f"- **RT**: {stats(rt_runtimes_solved)}")
    lines.append(f"- **STD**: {stats(std_runtimes_solved)}")
    lines.append(f"- **hetpibt**: {stats(pibt_runtimes_solved)}")
    lines.append("")

    # RT step counts
    lines.append("### RT Step Counts (solved)")
    rt_steps_solved = []
    for key in all_keys:
        if is_solved(rt.get(key)):
            rt_steps_solved.append(get_int(rt[key], "rt_steps"))
    if rt_steps_solved:
        rt_steps_solved.sort()
        n = len(rt_steps_solved)
        lines.append(f"- n={n}, mean={sum(rt_steps_solved)/n:.0f}, median={rt_steps_solved[n//2]}, max={rt_steps_solved[-1]}")
    lines.append("")

    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    print(f"Analysis written to {OUT_MD}")
    print(f"RT: {rt_total}/190 | STD: {std_total}/190 | hetpibt: {pibt_total}/190")


if __name__ == "__main__":
    main()
