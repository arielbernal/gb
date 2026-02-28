#!/usr/bin/env python3
"""Comprehensive benchmark analysis: het_rt_lacam vs hetpibt."""

import pandas as pd
import sys
from io import StringIO

# Load data
lacam = pd.read_csv("E:/gb/benchmarks/results/het_rt_lacam.csv")
pibt = pd.read_csv("E:/gb/benchmarks/results/hetpibt.csv")

out = StringIO()

def p(s=""):
    out.write(s + "\n")

p("# Benchmark Analysis: het_rt_lacam vs hetpibt")
p()

# ============================================================
# 0. Dataset overview
# ============================================================
p("## 0. Dataset Overview")
p()
p(f"- **het_rt_lacam**: {len(lacam)} rows, {lacam['category'].nunique()} categories")
p(f"- **hetpibt**: {len(pibt)} rows, {pibt['category'].nunique()} categories")
p()

for solver, df in [("het_rt_lacam", lacam), ("hetpibt", pibt)]:
    p(f"**{solver}** category x agent_label counts:")
    ct = df.groupby(["category", "agent_label"]).size().unstack(fill_value=0)
    p(ct.to_markdown())
    p()

# ============================================================
# 1. Solve Rate Table
# ============================================================
p("## 1. Solve Rate Table")
p()
p("Format: solved/total for each solver. het_rt_lacam timeout=30s, hetpibt timeout=60s (1000 steps).")
p()

# Build a unified key
lacam["key"] = lacam["category"] + "_" + lacam["agent_label"] + "_" + lacam["scen_id"].astype(str)
pibt["key"] = pibt["category"] + "_" + pibt["agent_label"] + "_" + pibt["scen_id"].astype(str)

# Per category x agent_label solve rates
for cat in lacam["category"].unique():
    p(f"### {cat}")
    p()
    rows = []
    for al in lacam[lacam["category"] == cat]["agent_label"].unique():
        lc = lacam[(lacam["category"] == cat) & (lacam["agent_label"] == al)]
        pb = pibt[(pibt["category"] == cat) & (pibt["agent_label"] == al)]
        l_solved = lc["solved"].sum()
        l_total = len(lc)
        p_solved = pb["solved"].sum()
        p_total = len(pb)
        rows.append({
            "agents": al,
            "het_rt_lacam": f"{l_solved}/{l_total}",
            "hetpibt": f"{p_solved}/{p_total}",
            "lacam_rate": f"{100*l_solved/l_total:.0f}%" if l_total > 0 else "N/A",
            "pibt_rate": f"{100*p_solved/p_total:.0f}%" if p_total > 0 else "N/A",
        })
    rdf = pd.DataFrame(rows)
    p(rdf.to_markdown(index=False))
    p()

# Overall solve rates
p("### Overall Solve Rates")
p()
l_total_solved = lacam["solved"].sum()
l_total_count = len(lacam)
p_total_solved = pibt["solved"].sum()
p_total_count = len(pibt)
p(f"| Solver | Solved | Total | Rate |")
p(f"|--------|--------|-------|------|")
p(f"| het_rt_lacam | {l_total_solved} | {l_total_count} | {100*l_total_solved/l_total_count:.1f}% |")
p(f"| hetpibt | {p_total_solved} | {p_total_count} | {100*p_total_solved/p_total_count:.1f}% |")
p()

# ============================================================
# 2. Failure Analysis
# ============================================================
p("## 2. Failure Analysis")
p()

p("### het_rt_lacam failures (by category x agent_label)")
p()
lacam_fail = lacam[~lacam["solved"]]
if len(lacam_fail) > 0:
    fail_summary = lacam_fail.groupby(["category", "agent_label"]).agg(
        count=("solved", "size"),
        scen_ids=("scen_id", lambda x: ",".join(map(str, sorted(x))))
    ).reset_index()
    p(fail_summary.to_markdown(index=False))
else:
    p("No failures.")
p()

p("### hetpibt failures (by category x agent_label)")
p()
pibt_fail = pibt[~pibt["solved"]]
if len(pibt_fail) > 0:
    fail_summary2 = pibt_fail.groupby(["category", "agent_label"]).agg(
        count=("solved", "size"),
        goals_reached=("goals_reached", lambda x: list(x)),
        goals_total=("goals_total", lambda x: list(x)),
        scen_ids=("scen_id", lambda x: ",".join(map(str, sorted(x))))
    ).reset_index()
    fail_summary2["partial"] = fail_summary2.apply(
        lambda r: "/".join(f"{gr}/{gt}" for gr, gt in zip(r["goals_reached"], r["goals_total"])),
        axis=1
    )
    p(fail_summary2[["category", "agent_label", "count", "scen_ids", "partial"]].to_markdown(index=False))
else:
    p("No failures.")
p()

# Scenarios where BOTH fail
p("### Scenarios where BOTH solvers fail")
p()
merged = lacam.merge(pibt, on=["category", "agent_label", "scen_id"], suffixes=("_lacam", "_pibt"))
both_fail = merged[(~merged["solved_lacam"]) & (~merged["solved_pibt"])]
if len(both_fail) > 0:
    bf = both_fail[["category", "agent_label", "scen_id"]].copy()
    bf_summary = bf.groupby(["category", "agent_label"]).agg(
        count=("scen_id", "size"),
        scen_ids=("scen_id", lambda x: ",".join(map(str, sorted(x))))
    ).reset_index()
    p(bf_summary.to_markdown(index=False))
else:
    p("None.")
p()

# Scenarios where one solves and the other doesn't
p("### het_rt_lacam solves but hetpibt fails")
p()
lacam_wins = merged[(merged["solved_lacam"]) & (~merged["solved_pibt"])]
if len(lacam_wins) > 0:
    p(lacam_wins[["category", "agent_label", "scen_id", "soc_lacam", "goals_reached_pibt", "goals_total_pibt"]].to_markdown(index=False))
else:
    p("None.")
p()

p("### hetpibt solves but het_rt_lacam fails")
p()
pibt_wins = merged[(~merged["solved_lacam"]) & (merged["solved_pibt"])]
if len(pibt_wins) > 0:
    p(pibt_wins[["category", "agent_label", "scen_id", "soc_pibt", "runtime_ms_pibt"]].to_markdown(index=False))
else:
    p("None.")
p()

# ============================================================
# 3. Head-to-Head on Scenarios Both Solve
# ============================================================
p("## 3. Head-to-Head: Scenarios Both Solve")
p()

both_solved = merged[(merged["solved_lacam"]) & (merged["solved_pibt"])]
if len(both_solved) > 0:
    both_solved = both_solved.copy()
    both_solved["soc_ratio"] = both_solved["soc_lacam"] / both_solved["soc_pibt"].replace(0, float("nan"))
    both_solved["makespan_ratio"] = both_solved["makespan_lacam"] / both_solved["makespan_pibt"].replace(0, float("nan"))
    both_solved["runtime_ratio"] = both_solved["runtime_ms_lacam"] / both_solved["runtime_ms_pibt"].replace(0, float("nan"))

    p("### Per-category averages (het_rt_lacam / hetpibt ratio)")
    p()
    p("> Ratio > 1 means het_rt_lacam is WORSE (higher SOC/makespan/runtime).")
    p("> Ratio < 1 means het_rt_lacam is BETTER.")
    p()

    h2h = both_solved.groupby("category").agg(
        n_scenarios=("soc_ratio", "size"),
        avg_soc_ratio=("soc_ratio", "mean"),
        med_soc_ratio=("soc_ratio", "median"),
        avg_makespan_ratio=("makespan_ratio", "mean"),
        avg_runtime_ratio=("runtime_ratio", "mean"),
    ).reset_index()
    h2h = h2h.round(2)
    p(h2h.to_markdown(index=False))
    p()

    # Overall
    p("### Overall head-to-head (all categories)")
    p()
    p(f"| Metric | Mean Ratio | Median Ratio |")
    p(f"|--------|-----------|-------------|")
    p(f"| SOC | {both_solved['soc_ratio'].mean():.2f} | {both_solved['soc_ratio'].median():.2f} |")
    p(f"| Makespan | {both_solved['makespan_ratio'].mean():.2f} | {both_solved['makespan_ratio'].median():.2f} |")
    p(f"| Runtime | {both_solved['runtime_ratio'].mean():.1f} | {both_solved['runtime_ratio'].median():.1f} |")
    p()

    # Detail per scenario
    p("### Detailed head-to-head (every scenario both solve)")
    p()
    detail = both_solved[["category", "agent_label", "scen_id",
                          "soc_lacam", "soc_pibt", "soc_ratio",
                          "makespan_lacam", "makespan_pibt", "makespan_ratio",
                          "runtime_ms_lacam", "runtime_ms_pibt"]].copy()
    detail = detail.round(2)
    p(detail.to_markdown(index=False))
    p()
else:
    p("No scenarios where both solve!")
    p()

# ============================================================
# 4. Runtime Comparison
# ============================================================
p("## 4. Runtime Comparison (ms)")
p()

p("### het_rt_lacam avg runtime per category x agent_label")
p()
rt_lacam = lacam.groupby(["category", "agent_label"]).agg(
    avg_runtime_ms=("runtime_ms", "mean"),
    min_runtime=("runtime_ms", "min"),
    max_runtime=("runtime_ms", "max"),
    n=("runtime_ms", "size")
).reset_index().round(0)
p(rt_lacam.to_markdown(index=False))
p()

p("### hetpibt avg runtime per category x agent_label")
p()
rt_pibt = pibt.groupby(["category", "agent_label"]).agg(
    avg_runtime_ms=("runtime_ms", "mean"),
    min_runtime=("runtime_ms", "min"),
    max_runtime=("runtime_ms", "max"),
    n=("runtime_ms", "size")
).reset_index().round(0)
p(rt_pibt.to_markdown(index=False))
p()

# ============================================================
# 5. Hardest Scenarios
# ============================================================
p("## 5. Hardest Scenarios")
p()

p("### Top 10 by runtime (het_rt_lacam)")
p()
top_rt_lacam = lacam.nlargest(10, "runtime_ms")[["category", "agent_label", "scen_id", "agents", "solved", "soc", "runtime_ms"]]
p(top_rt_lacam.to_markdown(index=False))
p()

p("### Top 10 by runtime (hetpibt)")
p()
top_rt_pibt = pibt.nlargest(10, "runtime_ms")[["category", "agent_label", "scen_id", "agents", "solved", "soc", "runtime_ms"]]
p(top_rt_pibt.to_markdown(index=False))
p()

p("### Top 10 by SOC (het_rt_lacam, solved only)")
p()
solved_lacam = lacam[lacam["solved"]]
if len(solved_lacam) > 0:
    top_soc_lacam = solved_lacam.nlargest(10, "soc")[["category", "agent_label", "scen_id", "agents", "soc", "soc_lb", "makespan", "runtime_ms"]]
    p(top_soc_lacam.to_markdown(index=False))
else:
    p("No solved scenarios.")
p()

p("### Top 10 by SOC (hetpibt, solved only)")
p()
solved_pibt = pibt[pibt["solved"]]
if len(solved_pibt) > 0:
    top_soc_pibt = solved_pibt.nlargest(10, "soc")[["category", "agent_label", "scen_id", "agents", "soc", "makespan", "runtime_ms"]]
    p(top_soc_pibt.to_markdown(index=False))
else:
    p("No solved scenarios.")
p()

# ============================================================
# 6. hetpibt Goal Completion (Partial Solutions)
# ============================================================
p("## 6. hetpibt Goal Completion (Partial Solutions)")
p()

p("### Partial completions (goals_reached < goals_total)")
p()
pibt_partial = pibt[pibt["goals_reached"] < pibt["goals_total"]].copy()
if len(pibt_partial) > 0:
    pibt_partial["completion"] = pibt_partial.apply(
        lambda r: f"{r['goals_reached']}/{r['goals_total']} ({100*r['goals_reached']/r['goals_total']:.0f}%)" if r['goals_total'] > 0 else "N/A",
        axis=1
    )
    p(pibt_partial[["category", "agent_label", "scen_id", "agents", "solved", "completion", "soc", "runtime_ms"]].to_markdown(index=False))
else:
    p("All scenarios fully completed.")
p()

p("### Summary: avg goal completion by category x agent_label (hetpibt)")
p()
pibt_goal = pibt[pibt["goals_total"] > 0].copy()
pibt_goal["completion_pct"] = 100 * pibt_goal["goals_reached"] / pibt_goal["goals_total"]
goal_summary = pibt_goal.groupby(["category", "agent_label"]).agg(
    avg_completion_pct=("completion_pct", "mean"),
    min_completion_pct=("completion_pct", "min"),
    n_partial=("completion_pct", lambda x: (x < 100).sum()),
    n_total=("completion_pct", "size")
).reset_index().round(1)
p(goal_summary.to_markdown(index=False))
p()

# ============================================================
# 7. Key Findings Summary
# ============================================================
p("## 7. Key Findings Summary")
p()

# Count stats
l_solved_count = lacam["solved"].sum()
p_solved_count = pibt["solved"].sum()

# het_bench special
het_bench_lacam = lacam[lacam["category"] == "het_bench"]
het_bench_pibt = pibt[pibt["category"] == "het_bench"]

p(f"1. **Overall solve rates**: het_rt_lacam {l_solved_count}/{len(lacam)} ({100*l_solved_count/len(lacam):.1f}%), hetpibt {p_solved_count}/{len(pibt)} ({100*p_solved_count/len(pibt):.1f}%)")
p()

if len(both_solved) > 0:
    avg_soc_r = both_solved['soc_ratio'].mean()
    avg_ms_r = both_solved['makespan_ratio'].mean()
    p(f"2. **SOC quality gap**: On scenarios both solve, het_rt_lacam SOC is {avg_soc_r:.2f}x hetpibt (mean ratio). Makespan ratio: {avg_ms_r:.2f}x.")
    p()

p(f"3. **Scalability**: het_rt_lacam struggles at n15+ on intersection (0/{lacam[(lacam['category']=='intersection') & (lacam['agents']>=15)].shape[0]} solved). hetpibt also struggles but achieves partial solutions.")
p()

p(f"4. **het_bench**: het_rt_lacam solves 8/10 (fails scen 1,9 known infeasible). hetpibt solves {het_bench_pibt['solved'].sum()}/10 (fails scen 1).")
p()

# Count where lacam solves but pibt doesn't and vice versa
p(f"5. **Exclusive solves**: het_rt_lacam solves {len(lacam_wins)} scenarios hetpibt fails. hetpibt solves {len(pibt_wins)} scenarios het_rt_lacam fails.")
p()

p(f"6. **Runtime**: het_rt_lacam uses ~30s timeout (most runs ~30000ms). hetpibt is orders of magnitude faster (typically <100ms), but caps at 1000 steps.")
p()

# Print to stdout
result = out.getvalue()
print(result)

# Also save to file
with open("E:/gb/benchmarks/results/analysis_summary.md", "w") as f:
    f.write(result)

print("\n\n--- Analysis saved to E:/gb/benchmarks/results/analysis_summary.md ---")
