#!/usr/bin/env python3
"""Combine post-BFS CSVs and produce full analysis."""
import csv
import os
from collections import defaultdict
from pathlib import Path
import statistics

DIR = Path("E:/gb/benchmarks/results/post_bfs_port")

# 1. Concatenate 5 CSVs into het_rt_lacam_full.csv
INPUT_FILES = [
    "lacam_bottleneck_doors.csv",
    "lacam_corridor_speed.csv",
    "lacam_intersection.csv",
    "lacam_cooperative_clearing.csv",
    "lacam_het_bench.csv",
]

all_rows = []
header = None
for fname in INPUT_FILES:
    with open(DIR / fname) as f:
        reader = csv.DictReader(f)
        if header is None:
            header = reader.fieldnames
        for row in reader:
            all_rows.append(row)

with open(DIR / "het_rt_lacam_full.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
    w.writeheader()
    w.writerows(all_rows)
print(f"Combined CSV: {len(all_rows)} rows written to het_rt_lacam_full.csv")

# 2. Load all datasets
def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

post_bfs = all_rows
pre_bfs = load_csv(DIR / "het_rt_lacam_pre_bfs.csv")
hetpibt = load_csv(DIR / "hetpibt_full.csv")

def is_solved(row):
    return row["solved"] == "True"

def key(row):
    return (row["category"], row["agent_label"], row["scen_id"])

# Index by key
post_by_key = {key(r): r for r in post_bfs}
pre_by_key = {key(r): r for r in pre_bfs}
pibt_by_key = {key(r): r for r in hetpibt}

# Categories and agent counts
CATEGORIES = ["bottleneck_doors", "corridor_speed", "intersection", "cooperative_clearing", "het_bench"]
AGENT_LABELS_105 = ["n5", "n10", "n15", "n20", "n25"]

# ============ ANALYSIS ============
lines = []
def w(s=""):
    lines.append(s)

w("# Full Post-BFS Benchmark Analysis")
w(f"Date: Feb 27, 2026")
w(f"Total scenarios: {len(post_bfs)} post-BFS, {len(pre_bfs)} pre-BFS, {len(hetpibt)} hetpibt")
w()

# a. Solve rate table: category x agent_count
w("## A. Solve Rate: het_rt_lacam (post-BFS) vs hetpibt")
w()
w("### 105-series categories")
w()
w("| Category | Agents | lacam solved | pibt solved | lacam % | pibt % |")
w("|----------|--------|-------------|-------------|---------|--------|")

cat_totals = defaultdict(lambda: {"lacam_s": 0, "lacam_t": 0, "pibt_s": 0, "pibt_t": 0})

for cat in CATEGORIES:
    if cat == "het_bench":
        continue
    for al in AGENT_LABELS_105:
        lacam_rows = [r for r in post_bfs if r["category"] == cat and r["agent_label"] == al]
        pibt_rows = [r for r in hetpibt if r["category"] == cat and r["agent_label"] == al]
        ls = sum(1 for r in lacam_rows if is_solved(r))
        lt = len(lacam_rows)
        ps = sum(1 for r in pibt_rows if is_solved(r))
        pt = len(pibt_rows)
        lp = f"{100*ls/lt:.0f}" if lt else "—"
        pp = f"{100*ps/pt:.0f}" if pt else "—"
        w(f"| {cat} | {al} | {ls}/{lt} | {ps}/{pt} | {lp}% | {pp}% |")
        cat_totals[cat]["lacam_s"] += ls
        cat_totals[cat]["lacam_t"] += lt
        cat_totals[cat]["pibt_s"] += ps
        cat_totals[cat]["pibt_t"] += pt

w()
w("### Category totals (105-series)")
w()
w("| Category | lacam solved | pibt solved | lacam % | pibt % |")
w("|----------|-------------|-------------|---------|--------|")
for cat in CATEGORIES:
    if cat == "het_bench":
        continue
    ct = cat_totals[cat]
    lp = f"{100*ct['lacam_s']/ct['lacam_t']:.0f}" if ct['lacam_t'] else "—"
    pp = f"{100*ct['pibt_s']/ct['pibt_t']:.0f}" if ct['pibt_t'] else "—"
    w(f"| {cat} | {ct['lacam_s']}/{ct['lacam_t']} | {ct['pibt_s']}/{ct['pibt_t']} | {lp}% | {pp}% |")

# Totals
total_ls = sum(ct["lacam_s"] for ct in cat_totals.values())
total_lt = sum(ct["lacam_t"] for ct in cat_totals.values())
total_ps = sum(ct["pibt_s"] for ct in cat_totals.values())
total_pt = sum(ct["pibt_t"] for ct in cat_totals.values())
w(f"| **105-series total** | **{total_ls}/{total_lt}** | **{total_ps}/{total_pt}** | **{100*total_ls/total_lt:.0f}%** | **{100*total_ps/total_pt:.0f}%** |")

w()
w("### het_bench (room120)")
w()
hb_lacam = [r for r in post_bfs if r["category"] == "het_bench"]
hb_pibt = [r for r in hetpibt if r["category"] == "het_bench"]
hb_ls = sum(1 for r in hb_lacam if is_solved(r))
hb_ps = sum(1 for r in hb_pibt if is_solved(r))
w(f"| Solver | Solved | Total | % |")
w(f"|--------|--------|-------|---|")
w(f"| het_rt_lacam | {hb_ls} | {len(hb_lacam)} | {100*hb_ls/len(hb_lacam):.0f}% |")
w(f"| hetpibt | {hb_ps} | {len(hb_pibt)} | {100*hb_ps/len(hb_pibt):.0f}% |")

grand_ls = total_ls + hb_ls
grand_lt = total_lt + len(hb_lacam)
grand_ps = total_ps + hb_ps
grand_pt = total_pt + len(hb_pibt)
w()
w(f"**Grand total: het_rt_lacam {grand_ls}/{grand_lt} ({100*grand_ls/grand_lt:.0f}%), hetpibt {grand_ps}/{grand_pt} ({100*grand_ps/grand_pt:.0f}%)**")

# b. Comparison to pre-BFS
w()
w("## B. Pre-BFS vs Post-BFS Comparison")
w()
w("| Category | Pre-BFS solved | Post-BFS solved | Delta | Pre % | Post % |")
w("|----------|---------------|----------------|-------|-------|--------|")

pre_total_s = 0
post_total_s = 0
for cat in CATEGORIES:
    pre_cat = [r for r in pre_bfs if r["category"] == cat]
    post_cat = [r for r in post_bfs if r["category"] == cat]
    pre_s = sum(1 for r in pre_cat if is_solved(r))
    post_s = sum(1 for r in post_cat if is_solved(r))
    pre_t = len(pre_cat)
    post_t = len(post_cat)
    delta = post_s - pre_s
    sign = "+" if delta >= 0 else ""
    pre_p = f"{100*pre_s/pre_t:.0f}" if pre_t else "—"
    post_p = f"{100*post_s/post_t:.0f}" if post_t else "—"
    w(f"| {cat} | {pre_s}/{pre_t} | {post_s}/{post_t} | {sign}{delta} | {pre_p}% | {post_p}% |")
    pre_total_s += pre_s
    post_total_s += post_s

pre_total_t = len(pre_bfs)
post_total_t = len(post_bfs)
delta_total = post_total_s - pre_total_s
w(f"| **TOTAL** | **{pre_total_s}/{pre_total_t}** | **{post_total_s}/{post_total_t}** | **+{delta_total}** | **{100*pre_total_s/pre_total_t:.0f}%** | **{100*post_total_s/post_total_t:.0f}%** |")

# c. Head-to-head SOC ratios on mutually-solved scenarios
w()
w("## C. SOC Comparison on Mutually-Solved Scenarios")
w()

# lacam post-BFS vs hetpibt
w("### het_rt_lacam (post-BFS) vs hetpibt SOC ratios")
w()
w("| Category | Mutual solves | Mean SOC ratio | Median SOC ratio | Mean lacam SOC | Mean pibt SOC |")
w("|----------|--------------|----------------|-----------------|----------------|---------------|")

all_ratios = []
for cat in CATEGORIES:
    ratios = []
    lacam_socs = []
    pibt_socs = []
    for k, lr in post_by_key.items():
        if k[0] != cat:
            continue
        pr = pibt_by_key.get(k)
        if pr and is_solved(lr) and is_solved(pr):
            ls = int(lr["soc"])
            ps = int(pr["soc"])
            if ps > 0 and ls > 0:
                ratios.append(ls / ps)
                lacam_socs.append(ls)
                pibt_socs.append(ps)
                all_ratios.append(ls / ps)
    if ratios:
        mean_r = statistics.mean(ratios)
        med_r = statistics.median(ratios)
        mean_ls = statistics.mean(lacam_socs)
        mean_ps = statistics.mean(pibt_socs)
        w(f"| {cat} | {len(ratios)} | {mean_r:.2f}x | {med_r:.2f}x | {mean_ls:.0f} | {mean_ps:.0f} |")
    else:
        w(f"| {cat} | 0 | — | — | — | — |")

if all_ratios:
    w(f"| **Overall** | **{len(all_ratios)}** | **{statistics.mean(all_ratios):.2f}x** | **{statistics.median(all_ratios):.2f}x** | — | — |")

# lacam post-BFS vs pre-BFS SOC on mutually-solved
w()
w("### het_rt_lacam post-BFS vs pre-BFS SOC ratios (both must solve)")
w()
w("| Category | Mutual solves | Mean post/pre ratio | Median | Improved | Regressed | Same |")
w("|----------|--------------|--------------------|---------|---------|-----------| -----|")

for cat in CATEGORIES:
    ratios = []
    improved = 0
    regressed = 0
    same = 0
    for k, post_r in post_by_key.items():
        if k[0] != cat:
            continue
        pre_r = pre_by_key.get(k)
        if pre_r and is_solved(post_r) and is_solved(pre_r):
            post_s = int(post_r["soc"])
            pre_s = int(pre_r["soc"])
            if pre_s > 0 and post_s > 0:
                ratios.append(post_s / pre_s)
                if post_s < pre_s:
                    improved += 1
                elif post_s > pre_s:
                    regressed += 1
                else:
                    same += 1
    if ratios:
        w(f"| {cat} | {len(ratios)} | {statistics.mean(ratios):.2f}x | {statistics.median(ratios):.2f}x | {improved} | {regressed} | {same} |")
    else:
        w(f"| {cat} | 0 | — | — | — | — | — |")

# d. Exclusive solves
w()
w("## D. Exclusive Solves")
w()

# het_rt_lacam solves but hetpibt doesn't
w("### het_rt_lacam solves, hetpibt fails")
w()
lacam_exclusive = []
for k, lr in post_by_key.items():
    pr = pibt_by_key.get(k)
    if is_solved(lr) and pr and not is_solved(pr):
        lacam_exclusive.append(k)
if lacam_exclusive:
    w(f"**{len(lacam_exclusive)} scenarios:**")
    w()
    for k in sorted(lacam_exclusive):
        lr = post_by_key[k]
        pr = pibt_by_key[k]
        w(f"- {k[0]}/{k[1]}/scen.{k[2]}: lacam SOC={lr['soc']}, pibt goals={pr['goals_reached']}/{pr['goals_total']}")
else:
    w("None")

w()
w("### hetpibt solves, het_rt_lacam fails")
w()
pibt_exclusive = []
for k, pr in pibt_by_key.items():
    lr = post_by_key.get(k)
    if is_solved(pr) and lr and not is_solved(lr):
        pibt_exclusive.append(k)
if pibt_exclusive:
    w(f"**{len(pibt_exclusive)} scenarios:**")
    w()
    for k in sorted(pibt_exclusive):
        pr = pibt_by_key[k]
        w(f"- {k[0]}/{k[1]}/scen.{k[2]}: pibt SOC={pr['soc']}")
else:
    w("None")

# e. Regressions
w()
w("## E. Regressions (solved pre-BFS, fails post-BFS)")
w()
regressions = []
for k, pre_r in pre_by_key.items():
    post_r = post_by_key.get(k)
    if is_solved(pre_r) and post_r and not is_solved(post_r):
        regressions.append(k)

if regressions:
    w(f"**{len(regressions)} regressions:**")
    w()
    for k in sorted(regressions):
        pre_r = pre_by_key[k]
        w(f"- {k[0]}/{k[1]}/scen.{k[2]}: pre-BFS SOC={pre_r['soc']}, post-BFS FAIL")
else:
    w("**No regressions found.**")

# Also check new solves (solved post-BFS, failed pre-BFS)
w()
w("## F. New Solves (failed pre-BFS, solved post-BFS)")
w()
new_solves = []
for k, post_r in post_by_key.items():
    pre_r = pre_by_key.get(k)
    if is_solved(post_r) and pre_r and not is_solved(pre_r):
        new_solves.append(k)

if new_solves:
    w(f"**{len(new_solves)} new solves:**")
    w()
    for k in sorted(new_solves):
        post_r = post_by_key[k]
        w(f"- {k[0]}/{k[1]}/scen.{k[2]}: post-BFS SOC={post_r['soc']}")
else:
    w("None")

# f. Overall summary
w()
w("## G. Overall Summary")
w()
w(f"- **Pre-BFS**: {pre_total_s}/{pre_total_t} solved ({100*pre_total_s/pre_total_t:.0f}%)")
w(f"- **Post-BFS**: {post_total_s}/{post_total_t} solved ({100*post_total_s/post_total_t:.0f}%)")
w(f"- **Net improvement**: +{delta_total} scenarios ({100*delta_total/pre_total_t:.0f}% of total)")
w(f"- **Regressions**: {len(regressions)}")
w(f"- **New solves**: {len(new_solves)}")
w(f"- **hetpibt reference**: {grand_ps}/{grand_pt} solved ({100*grand_ps/grand_pt:.0f}%)")
w()
w(f"- het_rt_lacam exclusively solves {len(lacam_exclusive)} scenarios that hetpibt cannot")
w(f"- hetpibt exclusively solves {len(pibt_exclusive)} scenarios that het_rt_lacam cannot")
if all_ratios:
    w(f"- On {len(all_ratios)} mutually-solved scenarios, het_rt_lacam SOC is {statistics.mean(all_ratios):.2f}x hetpibt (median {statistics.median(all_ratios):.2f}x)")

# Write output
output = "\n".join(lines) + "\n"
with open(DIR / "full_analysis.md", "w") as f:
    f.write(output)
print(f"\nAnalysis written to full_analysis.md")
print(output)
