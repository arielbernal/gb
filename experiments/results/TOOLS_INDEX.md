# GB Monorepo — Tools Index

## hetpibt/tools/

| Tool | Purpose | Inputs | Outputs |
|------|---------|--------|---------|
| `run_comparison.py` | Run hetpibt vs pibt_rs on all het_bench scenarios; print side-by-side goals/SOC/makespan/wait%/time tables. Also contains `create_scaled_map()` used to upscale a .map file. | `--max-steps N` (default 500). Reads `pypibt/assets/room-64-64-8.map`, `pypibt/het_bench/scen.*.scen`. | Stdout comparison tables (main + per-fleet). Creates `hetpibt/build/room64_scaled.map` (640x640). |
| `run_scaling.py` | Scale hetpibt to failure: generate random het scenarios at increasing agent counts, run solver, record metrics to CSV + markdown. | `--counts 15,50,...` `--seeds N` `--max-steps N` `--min-horizon N` `--time-limit ms` | `hetpibt/scaling_results/scaling_data.csv`, `scaling_summary.md` |
| `run_all_benchmarks.py` | Run hetpibt on all custom benchmark maps (bottleneck, corridor, intersection, cooperative clearing). Converts .scen to het_bench format via `convert_to_hetbench.py`, runs solver, saves CSV + markdown. | `--max-steps N` `--no-goal-lock` | `benchmarks/results/benchmark_results.csv`, `benchmark_summary.md` |
| `gen_scenario.py` | Generate a het_bench scenario file for any .map. Places agents with non-overlapping footprints, BFS-reachable goals, cross-fleet collision checks. Default fleets: cs=1,2,3. | `--map FILE --out FILE --seed N --agents 10,5,3` | `.scen` file in het_bench format (coords in base-grid space) |
| `gen_pibt_rs_scenario.py` | Convert hetpibt's internal result/scenario format to pibt_rs format (real-world coordinates). | `<our_scen> <map_w> <map_h> [output]` | pibt_rs-format `.scen` file (stdout or file) |
| `diagnose_cluster.py` | Post-mortem analysis of a solver result file. Finds dense agent clusters, identifies unreached goals, detects oscillation patterns. | `<map_file> <result_file> [timestep]` | Stdout diagnostic report (clusters, unreached agents, oscillation) |

## benchmarks/generators/

| Tool | Purpose | Inputs | Outputs |
|------|---------|--------|---------|
| `bottleneck_doors.py` | Generate bottleneck benchmark: two rooms separated by a wall with doors of varying widths. Agents must pass through doors they fit through. | argparse (map dimensions, door widths, agent counts) | `.map` + `.scen` files |
| `corridor_speed.py` | Generate corridor speed benchmark: parallel horizontal corridors of varying widths with head-on traffic. Each fleet uses corridors matching its footprint. | argparse | `.map` + `.scen` files |
| `intersection.py` | Generate intersection benchmark: central open area with 4 corridors (N/S/E/W). Agents cross through center to reach opposite side. | argparse | `.map` + `.scen` files |
| `cooperative_clearing.py` | Generate cooperative clearing benchmark: two asymmetric rooms connected by a single passage. Large agents block the passage, forcing cooperative yielding. | argparse | `.map` + `.scen` files |
| `convert_to_hetbench.py` | Convert simple `.scen` format (`cs sx sy gx gy`) to het_bench format (`agent_id fleet_id cs velocity sx sy gx gy grid_w grid_h`). Snaps positions to fleet grid boundaries. | `--scen FILE --map FILE --output FILE` | het_bench `.scen` file |
| `validate.py` | Validate a `.map` + `.scen` pair: checks footprint validity, start/goal overlaps, BFS reachability for NxN blocks. | `--map FILE --scen FILE` | Stdout pass/fail report (exit 0/1) |
| `show_map.py` | Visualize a benchmark map with agent starts/goals overlaid. Each fleet gets a distinct color; fleet grid shown as dashed lines. | `--map FILE --scen FILE` | Matplotlib plot |

## tools/ (monorepo-level)

| Tool | Purpose | Inputs | Outputs |
|------|---------|--------|---------|
| `het2baseline.py` | Convert het_bench `.scen` to standard MovingAI `.scen` format. Three modes: `--homogeneous` (all unit-size/speed), `--size-only` (keep cell_size, strip velocity), `--speed-only` (keep velocity, all cs=1). | `-i FILE -o FILE --map NAME --map-w N --map-h N` + mode flag | MovingAI `.scen` file (`version 1` header, tab-separated 9-field lines). Comment header with per-agent metadata in size-only/speed-only modes. |

## Notes
- **Map scaling:** `create_scaled_map()` lives in both `run_comparison.py` and `run_scaling.py` (duplicated). It upscales a .map file by repeating each cell NxN times. Used to create the 640x640 map from the 64x64 base for het_bench scenarios.
- **het_bench format:** `agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h` — coordinates are in base-grid (real-world) space; the solver divides by cell_size to get fleet-grid coords.
- **Simple .scen format:** `cell_size sx sy gx gy` — used by custom benchmarks; must be converted to het_bench via `convert_to_hetbench.py` before running with the solver.
