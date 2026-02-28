#!/usr/bin/env python3
"""Analyze RT+ST-BFS benchmark results vs RT+spatial-BFS and hetpibt."""
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path("E:/gb/benchmarks/results")
STBFS_DIR = ROOT / "rt_stbfs"
OLD_RT_CSV = ROOT / "rt_lacam" / "het_rt_lacam_rt_full.csv"
HETPIBT_CSV = ROOT / "post_bfs_port" / "hetpibt_full.csv"

CATEGORIES = ["bottleneck_doors", "corridor_speed", "intersection",
              "cooperative_clearing", "het_bench"]
AGENT_LABELS = ["n5", "n10", "n15", "n20", "n25", "var"]


def load_csv(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            r["solved"] = r["solved"] == "True"
            for k in ["agents", "soc", "soc_lb", "makespan", "makespan_lb", "runtime_ms"]:
                if k in r:
                    r[k] = int(r[k]) if r[k] else 0
            if "rt_steps" in r:
                r["rt_steps"] = int(r["rt_steps"]) if r["rt_steps"] else 0
            rows.append(r)
    return rows


def key(r):
    return (r["category"], r["agent_label"], r["scen_id"])


def build_index(rows):
    return {key(r): r for r in rows}


def main():
    # Load new RT+ST-BFS
    stbfs_rows = []
    for cat in CATEGORIES:
        fname = f"lacam_{cat}.csv"
        p = STBFS_DIR / fname
        if p.exists():
            stbfs_rows.extend(load_csv(p))

    # Load old RT+spatial-BFS
    old_rt_rows = load_csv(OLD_RT_CSV) if OLD_RT_CSV.exists() else []

    # Load hetpibt
    hetpibt_rows = load_csv(HETPIBT_CSV) if HETPIBT_CSV.exists() else []

    stbfs = build_index(stbfs_rows)
    old_rt = build_index(old_rt_rows)
    hetpibt = build_index(hetpibt_rows)

    lines = []
    def w(s=""):
        lines.append(s)

    # ---------------------------------------------------------------
    # A. Overall solve rates
    # ---------------------------------------------------------------
    w("# RT+ST-BFS Benchmark Analysis")
    w()
    w("## A. Overall Solve Rates")
    w()

    total = {"stbfs": [0, 0], "old_rt": [0, 0], "hetpibt": [0, 0]}
    cat_stats = defaultdict(lambda: {"stbfs": [0, 0], "old_rt": [0, 0], "hetpibt": [0, 0]})

    for k, r in stbfs.items():
        cat = r["category"]
        cat_stats[cat]["stbfs"][1] += 1
        total["stbfs"][1] += 1
        if r["solved"]:
            cat_stats[cat]["stbfs"][0] += 1
            total["stbfs"][0] += 1

    for k, r in old_rt.items():
        cat = r["category"]
        cat_stats[cat]["old_rt"][1] += 1
        total["old_rt"][1] += 1
        if r["solved"]:
            cat_stats[cat]["old_rt"][0] += 1
            total["old_rt"][0] += 1

    for k, r in hetpibt.items():
        cat = r["category"]
        cat_stats[cat]["hetpibt"][1] += 1
        total["hetpibt"][1] += 1
        if r["solved"]:
            cat_stats[cat]["hetpibt"][0] += 1
            total["hetpibt"][0] += 1

    w("| Category | RT+ST-BFS | RT+spatial | hetpibt |")
    w("|----------|-----------|------------|---------|")
    for cat in CATEGORIES:
        cs = cat_stats[cat]
        def fmt(s):
            return f"{s[0]}/{s[1]} ({100*s[0]//max(s[1],1)}%)" if s[1] > 0 else "—"
        w(f"| {cat} | {fmt(cs['stbfs'])} | {fmt(cs['old_rt'])} | {fmt(cs['hetpibt'])} |")
    w(f"| **TOTAL** | **{total['stbfs'][0]}/{total['stbfs'][1]}** | **{total['old_rt'][0]}/{total['old_rt'][1]}** | **{total['hetpibt'][0]}/{total['hetpibt'][1]}** |")
    w()

    # ---------------------------------------------------------------
    # B. Solve rate by category × agent_count
    # ---------------------------------------------------------------
    w("## B. Solve Rate by Category × Agent Count")
    w()

    for cat in CATEGORIES:
        w(f"### {cat}")
        w()
        als = ["n5", "n10", "n15", "n20", "n25"] if cat != "het_bench" else ["var"]
        w("| Agents | RT+ST-BFS | RT+spatial | hetpibt |")
        w("|--------|-----------|------------|---------|")
        for al in als:
            counts = {"stbfs": [0, 0], "old_rt": [0, 0], "hetpibt": [0, 0]}
            for k, r in stbfs.items():
                if r["category"] == cat and r["agent_label"] == al:
                    counts["stbfs"][1] += 1
                    if r["solved"]: counts["stbfs"][0] += 1
            for k, r in old_rt.items():
                if r["category"] == cat and r["agent_label"] == al:
                    counts["old_rt"][1] += 1
                    if r["solved"]: counts["old_rt"][0] += 1
            for k, r in hetpibt.items():
                if r["category"] == cat and r["agent_label"] == al:
                    counts["hetpibt"][1] += 1
                    if r["solved"]: counts["hetpibt"][0] += 1
            def fmt(s):
                return f"{s[0]}/{s[1]}" if s[1] > 0 else "—"
            w(f"| {al} | {fmt(counts['stbfs'])} | {fmt(counts['old_rt'])} | {fmt(counts['hetpibt'])} |")
        w()

    # ---------------------------------------------------------------
    # C. New solves vs old RT (ST-BFS solved, spatial-BFS didn't)
    # ---------------------------------------------------------------
    w("## C. New Solves (RT+ST-BFS solved, RT+spatial did not)")
    w()
    new_solves = []
    for k, r in stbfs.items():
        if r["solved"]:
            old = old_rt.get(k)
            if old and not old["solved"]:
                new_solves.append(r)

    if new_solves:
        w(f"**{len(new_solves)} new solves:**")
        w()
        w("| Category | Agents | Scen | SOC | Makespan | Steps | Time |")
        w("|----------|--------|------|-----|----------|-------|------|")
        for r in sorted(new_solves, key=lambda x: (x["category"], x["agent_label"], x["scen_id"])):
            w(f"| {r['category']} | {r['agent_label']} | {r['scen_id']} | {r['soc']} | {r['makespan']} | {r['rt_steps']} | {r['runtime_ms']}ms |")
    else:
        w("No new solves.")
    w()

    # ---------------------------------------------------------------
    # D. Regressions (old RT solved, ST-BFS didn't)
    # ---------------------------------------------------------------
    w("## D. Regressions (RT+spatial solved, RT+ST-BFS did not)")
    w()
    regressions = []
    for k, r in old_rt.items():
        if r["solved"]:
            new = stbfs.get(k)
            if new and not new["solved"]:
                regressions.append((r, new))

    if regressions:
        w(f"**{len(regressions)} regressions:**")
        w()
        w("| Category | Agents | Scen | Old SOC | Old Steps | Old Time |")
        w("|----------|--------|------|---------|-----------|----------|")
        for old_r, new_r in sorted(regressions, key=lambda x: (x[0]["category"], x[0]["agent_label"], x[0]["scen_id"])):
            w(f"| {old_r['category']} | {old_r['agent_label']} | {old_r['scen_id']} | {old_r['soc']} | {old_r['rt_steps']} | {old_r['runtime_ms']}ms |")
    else:
        w("0 regressions.")
    w()

    # ---------------------------------------------------------------
    # E. SOC ratios on mutually solved scenarios
    # ---------------------------------------------------------------
    w("## E. SOC Comparison on Mutually Solved Scenarios")
    w()

    # ST-BFS vs old RT
    stbfs_vs_oldrt_socs = []
    for k in stbfs:
        if k in old_rt and stbfs[k]["solved"] and old_rt[k]["solved"]:
            s_new = stbfs[k]["soc"]
            s_old = old_rt[k]["soc"]
            if s_old > 0 and s_new > 0:
                stbfs_vs_oldrt_socs.append((s_new / s_old, k, s_new, s_old))

    if stbfs_vs_oldrt_socs:
        ratios = [x[0] for x in stbfs_vs_oldrt_socs]
        ratios.sort()
        mean_r = sum(ratios) / len(ratios)
        median_r = ratios[len(ratios) // 2]
        better = sum(1 for r in ratios if r < 0.95)
        worse = sum(1 for r in ratios if r > 1.05)
        same = len(ratios) - better - worse
        w(f"### RT+ST-BFS vs RT+spatial ({len(ratios)} mutual solves)")
        w()
        w(f"- Mean SOC ratio (ST-BFS / spatial): **{mean_r:.3f}**")
        w(f"- Median SOC ratio: **{median_r:.3f}**")
        w(f"- ST-BFS better (ratio < 0.95): {better}")
        w(f"- Similar (0.95-1.05): {same}")
        w(f"- ST-BFS worse (ratio > 1.05): {worse}")
        w()

        # Category breakdown
        cat_ratios = defaultdict(list)
        for ratio, k, s_new, s_old in stbfs_vs_oldrt_socs:
            cat_ratios[k[0]].append(ratio)

        w("| Category | Mutual | Mean ratio | Median | Better | Worse |")
        w("|----------|--------|------------|--------|--------|-------|")
        for cat in CATEGORIES:
            rs = cat_ratios.get(cat, [])
            if rs:
                rs.sort()
                mr = sum(rs) / len(rs)
                mdr = rs[len(rs) // 2]
                b = sum(1 for r in rs if r < 0.95)
                wr = sum(1 for r in rs if r > 1.05)
                w(f"| {cat} | {len(rs)} | {mr:.3f} | {mdr:.3f} | {b} | {wr} |")
        w()

    # ST-BFS vs hetpibt
    stbfs_vs_pibt_socs = []
    for k in stbfs:
        if k in hetpibt and stbfs[k]["solved"] and hetpibt[k]["solved"]:
            s_new = stbfs[k]["soc"]
            s_pibt = hetpibt[k]["soc"]
            if s_pibt > 0 and s_new > 0:
                stbfs_vs_pibt_socs.append((s_new / s_pibt, k, s_new, s_pibt))

    if stbfs_vs_pibt_socs:
        ratios = [x[0] for x in stbfs_vs_pibt_socs]
        ratios.sort()
        mean_r = sum(ratios) / len(ratios)
        median_r = ratios[len(ratios) // 2]
        w(f"### RT+ST-BFS vs hetpibt ({len(ratios)} mutual solves)")
        w()
        w(f"- Mean SOC ratio (ST-BFS / hetpibt): **{mean_r:.3f}**")
        w(f"- Median SOC ratio: **{median_r:.3f}**")
        w()

    # ---------------------------------------------------------------
    # F. Runtime comparison
    # ---------------------------------------------------------------
    w("## F. Runtime Comparison")
    w()

    stbfs_solved_times = [r["runtime_ms"] for r in stbfs.values() if r["solved"]]
    old_solved_times = [r["runtime_ms"] for r in old_rt.values() if r["solved"]]
    pibt_solved_times = [r["runtime_ms"] for r in hetpibt.values() if r["solved"]]

    def time_stats(times, label):
        if not times:
            return f"- {label}: no data"
        times.sort()
        med = times[len(times) // 2]
        p95 = times[int(len(times) * 0.95)]
        mx = times[-1]
        return f"- {label}: median={med}ms, p95={p95}ms, max={mx}ms (n={len(times)})"

    w(time_stats(stbfs_solved_times, "RT+ST-BFS"))
    w(time_stats(old_solved_times, "RT+spatial"))
    w(time_stats(pibt_solved_times, "hetpibt"))
    w()

    # Write output
    out_path = STBFS_DIR / "analysis.md"
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Analysis written to {out_path}")
    print(f"\nTotal RT+ST-BFS: {total['stbfs'][0]}/{total['stbfs'][1]} solved")


if __name__ == "__main__":
    main()
