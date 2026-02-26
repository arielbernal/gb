# Output Audit

## A) Where Results Currently Exist

| Path | Type | Contents |
|------|------|----------|
| `benchmarks/results/benchmark_results.csv` | CSV | hetpibt results on bottleneck, corridor, intersection, cooperative clearing (76 rows) |
| `benchmarks/results/benchmark_summary.md` | Markdown | Summary tables from run_all_benchmarks.py |
| `het_lacam/BENCHMARK_COMPARISON.md` | Markdown | het_lacam vs hetpibt on het_bench scen.0-9 (8 valid scenarios) |
| `hetpibt/BENCHMARK_RESULTS.md` | Markdown | (hetpibt benchmark notes) |
| `hetpibt/scaling_results/scaling_data.csv` | CSV | Scaling experiment data (agent counts vs goal%) |
| `hetpibt/scaling_results/scaling_summary.md` | Markdown | Scaling experiment summary |
| `hetpibt/scaling_results/n15_seed0_result.txt` | Solver log | Raw solver output from scaling run |
| `hetpibt/scaling_results/n15_seed3_result.txt` | Solver log | Raw solver output from scaling run |
| `RESULTS_SUMMARY.md` | Markdown | Combined summary of all results |
| `baselines.csv` | CSV | run_baselines.py output (bottleneck test run) |
| `lacam/build/result.txt` | Solver log | Stale lacam run output |
| `result.txt` | Solver log | Stale solver output at repo root |
| `het_lacam/assets/room-64-64-8-scaled.map` | Map | 640x640 upscaled map (generated, not a result) |
| `pypibt/docs/results/results.aaccbs.csv` | CSV | pypibt reference results (upstream) |
| `pypibt/docs/results/results.pibt.csv` | CSV | pypibt reference results (upstream) |
| `pypibt/output.old.txt` | Text | Stale pypibt output |

## B) Where Each Script Writes Output

| Script | Writes To | Description |
|--------|-----------|-------------|
| `hetpibt/tools/run_comparison.py` | `hetpibt/build/room64_scaled.map` | Generated 640x640 scaled map |
| | `<tmpdir>/<scen>_result.txt` | Per-scenario solver logs (cleaned up) |
| | stdout | Comparison tables |
| `hetpibt/tools/run_scaling.py` | `hetpibt/build/room64_scaled.map` | Generated scaled map (if missing) |
| | `hetpibt/scaling_results/scaling_data.csv` | Per-run metrics CSV |
| | `hetpibt/scaling_results/scaling_summary.md` | Markdown summary |
| | `<tmpdir>/scen_n*_s*.scen` | Generated scenarios (cleaned up) |
| | `<tmpdir>/result_n*_s*.txt` | Solver logs (cleaned up) |
| `hetpibt/tools/run_all_benchmarks.py` | `benchmarks/results/benchmark_results.csv` | Per-scenario metrics CSV |
| | `benchmarks/results/benchmark_summary.md` | Markdown summary |
| | `<tmpdir>/*_hetbench.scen` | Converted scenarios (cleaned up) |
| | `<tmpdir>/*_result.txt` | Solver logs (cleaned up) |
| `tools/run_baselines.py` | `-o` flag (default `baselines.csv`) | Combined solver comparison CSV |
| | `<tmpdir>/het_lacam_result_*.txt` | het_lacam logs (cleaned up) |

## C) C++ Solver Default Output Paths

| Solver | Flag | Default | Format |
|--------|------|---------|--------|
| het_lacam | `-o, --output` | `./build/result.txt` | Key=value log: agents, solved, soc, makespan, comp_time, solution trajectories |
| hetpibt | `-o, --output` | `result.txt` | Key=value log: agents, fleets, goals_reached, makespan, sum_of_costs, solution trajectories |

Note: Both solvers write to CWD-relative paths by default. Runner scripts override with `-o <tmpdir>/...` to avoid clobbering.
