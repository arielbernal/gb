#!/usr/bin/env python3
"""Analyze RT+ST-BFS+stay benchmark results vs RT+ST-BFS and hetpibt."""
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path("E:/gb/benchmarks/results")
STAY_DIR = ROOT / "rt_stbfs_stay"
OLD_STBFS_DIR = ROOT / "rt_stbfs"
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
            for k in ["move_steps", "stay_steps", "explored"]:
                if k in r:
                    r[k] = int(r[k]) if r[k] else 0
            rows.append(r)
    return rows


def key(r):
    return (r["category"], r["agent_label"], r["scen_id"])


def build_index(rows):
    return {key(r): r for r in rows}


def main():
    # Load RT+ST-BFS+stay
    stay_rows = []
    for cat in CATEGORIES:
        fname = f"lacam_{cat}.csv"
        p = STAY_DIR / fname
        if p.exists():
            stay_rows.extend(load_csv(p))

    # Load old RT+ST-BFS
    old_rows = []
    for cat in CATEGORIES:
        fname = f"lacam_{cat}.csv"
        p = OLD_STBFS_DIR / fname
        if p.exists():
            old_rows.extend(load_csv(p))

    # Load hetpibt
    hetpibt_rows = load_csv(HETPIBT_CSV) if HETPIBT_CSV.exists() else []

    stay = build_index(stay_rows)
    old = build_index(old_rows)
    hetpibt = build_index(hetpibt_rows)

    lines = []
    def w(s=""):
        lines.append(s)

    # ---------------------------------------------------------------
    # A. Overall solve rates
    # ---------------------------------------------------------------
    w("# RT+ST-BFS+Stay Benchmark Analysis")
    w()
    w("## A. Overall Solve Rates")
    w()

    total = {"stay": [0, 0], "old": [0, 0], "hetpibt": [0, 0]}
    cat_stats = defaultdict(lambda: {"stay": [0, 0], "old": [0, 0], "hetpibt": [0, 0]})

    for k, r in stay.items():
        cat = r["category"]
        cat_stats[cat]["stay"][1] += 1
        total["stay"][1] += 1
        if r["solved"]:
            cat_stats[cat]["stay"][0] += 1
            total["stay"][0] += 1

    for k, r in old.items():
        cat = r["category"]
        cat_stats[cat]["old"][1] += 1
        total["old"][1] += 1
        if r["solved"]:
            cat_stats[cat]["old"][0] += 1
            total["old"][0] += 1

    for k, r in hetpibt.items():
        cat = r["category"]
        cat_stats[cat]["hetpibt"][1] += 1
        total["hetpibt"][1] += 1
        if r["solved"]:
            cat_stats[cat]["hetpibt"][0] += 1
            total["hetpibt"][0] += 1

    w("| Category | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |")
    w("|----------|----------------|-----------|---------|")
    for cat in CATEGORIES:
        cs = cat_stats[cat]
        def fmt(s):
            return f"{s[0]}/{s[1]} ({100*s[0]//max(s[1],1)}%)" if s[1] > 0 else "—"
        w(f"| {cat} | {fmt(cs['stay'])} | {fmt(cs['old'])} | {fmt(cs['hetpibt'])} |")
    w(f"| **TOTAL** | **{total['stay'][0]}/{total['stay'][1]}** | **{total['old'][0]}/{total['old'][1]}** | **{total['hetpibt'][0]}/{total['hetpibt'][1]}** |")
    w()

    # ---------------------------------------------------------------
    # B. Solve rate by category x agent_count
    # ---------------------------------------------------------------
    w("## B. Solve Rate by Category x Agent Count")
    w()

    for cat in CATEGORIES:
        w(f"### {cat}")
        w()
        als = ["n5", "n10", "n15", "n20", "n25"] if cat != "het_bench" else ["var"]
        w("| Agents | RT+ST-BFS+stay | RT+ST-BFS | hetpibt |")
        w("|--------|----------------|-----------|---------|")
        for al in als:
            counts = {"stay": [0, 0], "old": [0, 0], "hetpibt": [0, 0]}
            for k, r in stay.items():
                if r["category"] == cat and r["agent_label"] == al:
                    counts["stay"][1] += 1
                    if r["solved"]: counts["stay"][0] += 1
            for k, r in old.items():
                if r["category"] == cat and r["agent_label"] == al:
                    counts["old"][1] += 1
                    if r["solved"]: counts["old"][0] += 1
            for k, r in hetpibt.items():
                if r["category"] == cat and r["agent_label"] == al:
                    counts["hetpibt"][1] += 1
                    if r["solved"]: counts["hetpibt"][0] += 1
            def fmt(s):
                return f"{s[0]}/{s[1]}" if s[1] > 0 else "—"
            w(f"| {al} | {fmt(counts['stay'])} | {fmt(counts['old'])} | {fmt(counts['hetpibt'])} |")
        w()

    # ---------------------------------------------------------------
    # C. New solves vs old ST-BFS
    # ---------------------------------------------------------------
    w("## C. New Solves (stay solved, old ST-BFS did not)")
    w()
    new_solves = []
    for k, r in stay.items():
        if r["solved"]:
            o = old.get(k)
            if o and not o["solved"]:
                new_solves.append(r)

    if new_solves:
        w(f"**{len(new_solves)} new solves:**")
        w()
        w("| Category | Agents | Scen | SOC | Makespan | Steps | Move | Stay | Time |")
        w("|----------|--------|------|-----|----------|-------|------|------|------|")
        for r in sorted(new_solves, key=lambda x: (x["category"], x["agent_label"], x["scen_id"])):
            mv = r.get("move_steps", "")
            st = r.get("stay_steps", "")
            w(f"| {r['category']} | {r['agent_label']} | {r['scen_id']} | {r['soc']} | {r['makespan']} | {r['rt_steps']} | {mv} | {st} | {r['runtime_ms']}ms |")
    else:
        w("No new solves.")
    w()

    # ---------------------------------------------------------------
    # D. Regressions
    # ---------------------------------------------------------------
    w("## D. Regressions (old ST-BFS solved, stay did not)")
    w()
    regressions = []
    for k, r in old.items():
        if r["solved"]:
            new = stay.get(k)
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
    # E. SOC ratios on mutual solves
    # ---------------------------------------------------------------
    w("## E. SOC Comparison on Mutually Solved Scenarios")
    w()

    # stay vs old ST-BFS
    stay_vs_old_socs = []
    for k in stay:
        if k in old and stay[k]["solved"] and old[k]["solved"]:
            s_new = stay[k]["soc"]
            s_old = old[k]["soc"]
            if s_old > 0 and s_new > 0:
                stay_vs_old_socs.append((s_new / s_old, k, s_new, s_old))

    if stay_vs_old_socs:
        ratios = [x[0] for x in stay_vs_old_socs]
        ratios.sort()
        mean_r = sum(ratios) / len(ratios)
        median_r = ratios[len(ratios) // 2]
        better = sum(1 for r in ratios if r < 0.95)
        worse = sum(1 for r in ratios if r > 1.05)
        same = len(ratios) - better - worse
        w(f"### Stay vs old ST-BFS ({len(ratios)} mutual solves)")
        w()
        w(f"- Mean SOC ratio (stay / old): **{mean_r:.3f}**")
        w(f"- Median SOC ratio: **{median_r:.3f}**")
        w(f"- Stay better (ratio < 0.95): {better}")
        w(f"- Similar (0.95-1.05): {same}")
        w(f"- Stay worse (ratio > 1.05): {worse}")
        w()

        cat_ratios = defaultdict(list)
        for ratio, k, s_new, s_old in stay_vs_old_socs:
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

    # stay vs hetpibt
    stay_vs_pibt_socs = []
    for k in stay:
        if k in hetpibt and stay[k]["solved"] and hetpibt[k]["solved"]:
            s_new = stay[k]["soc"]
            s_pibt = hetpibt[k]["soc"]
            if s_pibt > 0 and s_new > 0:
                stay_vs_pibt_socs.append((s_new / s_pibt, k, s_new, s_pibt))

    if stay_vs_pibt_socs:
        ratios = [x[0] for x in stay_vs_pibt_socs]
        ratios.sort()
        mean_r = sum(ratios) / len(ratios)
        median_r = ratios[len(ratios) // 2]
        w(f"### Stay vs hetpibt ({len(ratios)} mutual solves)")
        w()
        w(f"- Mean SOC ratio (stay / hetpibt): **{mean_r:.3f}**")
        w(f"- Median SOC ratio: **{median_r:.3f}**")
        w()

    # ---------------------------------------------------------------
    # F. Runtime comparison
    # ---------------------------------------------------------------
    w("## F. Runtime Comparison")
    w()

    stay_solved_times = [r["runtime_ms"] for r in stay.values() if r["solved"]]
    old_solved_times = [r["runtime_ms"] for r in old.values() if r["solved"]]
    pibt_solved_times = [r["runtime_ms"] for r in hetpibt.values() if r["solved"]]

    def time_stats(times, label):
        if not times:
            return f"- {label}: no data"
        times.sort()
        med = times[len(times) // 2]
        p95 = times[int(len(times) * 0.95)]
        mx = times[-1]
        return f"- {label}: median={med}ms, p95={p95}ms, max={mx}ms (n={len(times)})"

    w(time_stats(stay_solved_times, "RT+ST-BFS+stay"))
    w(time_stats(old_solved_times, "RT+ST-BFS"))
    w(time_stats(pibt_solved_times, "hetpibt"))
    w()

    # ---------------------------------------------------------------
    # G. Stay/Move step analysis
    # ---------------------------------------------------------------
    w("## G. Stay vs Move Steps")
    w()

    total_move = sum(r.get("move_steps", 0) for r in stay.values())
    total_stay = sum(r.get("stay_steps", 0) for r in stay.values())
    total_explored = sum(r.get("explored", 0) for r in stay.values())

    solved_move = sum(r.get("move_steps", 0) for r in stay.values() if r["solved"])
    solved_stay = sum(r.get("stay_steps", 0) for r in stay.values() if r["solved"])
    failed_move = sum(r.get("move_steps", 0) for r in stay.values() if not r["solved"])
    failed_stay = sum(r.get("stay_steps", 0) for r in stay.values() if not r["solved"])

    w(f"**All scenarios**: move={total_move}, stay={total_stay}, "
      f"stay%={100*total_stay//max(total_move+total_stay,1)}%, "
      f"total_explored={total_explored}")
    w(f"- Solved: move={solved_move}, stay={solved_stay}, "
      f"stay%={100*solved_stay//max(solved_move+solved_stay,1)}%")
    w(f"- Failed: move={failed_move}, stay={failed_stay}, "
      f"stay%={100*failed_stay//max(failed_move+failed_stay,1)}%")
    w()

    # Per-category breakdown
    w("| Category | Solved move | Solved stay | Failed move | Failed stay |")
    w("|----------|------------|------------|-------------|-------------|")
    for cat in CATEGORIES:
        sm = sum(r.get("move_steps", 0) for r in stay.values() if r["category"] == cat and r["solved"])
        ss = sum(r.get("stay_steps", 0) for r in stay.values() if r["category"] == cat and r["solved"])
        fm = sum(r.get("move_steps", 0) for r in stay.values() if r["category"] == cat and not r["solved"])
        fs = sum(r.get("stay_steps", 0) for r in stay.values() if r["category"] == cat and not r["solved"])
        w(f"| {cat} | {sm} | {ss} | {fm} | {fs} |")
    w()

    # Write output
    out_path = STAY_DIR / "analysis.md"
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Analysis written to {out_path}")
    print(f"\nTotal RT+ST-BFS+stay: {total['stay'][0]}/{total['stay'][1]} solved")


if __name__ == "__main__":
    main()
