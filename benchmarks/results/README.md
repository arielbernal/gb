# Benchmark Results

## What was run

Both solvers on all 105-series het_bench-format scenarios:

| Category | Map | Scenarios | Agent counts |
|----------|-----|-----------|-------------|
| intersection | intersection_105.map | 00-24 | 5, 10, 15, 20, 25 |
| bottleneck_doors | bottleneck_doors_105.map | 00-24 | 5, 10, 15, 20, 25 |
| corridor_speed | corridor_speed_105.map | 00-24 | 5, 10, 15, 20, 25 |
| cooperative_clearing | cooperative_clearing_105.map | 00-24 | 5, 10, 15, 20, 25 |
| het_bench | room120.map | 0-9 | varies (6-9) |

Total: 190 scenario files.

## Solvers

### het_rt_lacam
- Binary: `het_rt_lacam/build/Release/main.exe`
- Flags: `--goal-lock -t 30`
- het_bench scenarios also use `--swap-xy`
- Requires ALL agents at goal to count as solved

### hetpibt
- Binary: `third_party/hetpibt/build/Release/main.exe`
- Flags: `--seed 0 --swap-xy --goal-lock`
- Reports partial goal achievement (goals_reached/goals_total)
- Note: `--swap-xy` causes some agents to land on walls and get skipped,
  so hetpibt may solve with fewer agents than het_rt_lacam

## Result files

| File | Contents |
|------|----------|
| `het_rt_lacam.csv` | All het_rt_lacam results |
| `hetpibt.csv` | All hetpibt results |
| `run_log.txt` | Full console output from the run |

### CSV columns

| Column | Description |
|--------|-------------|
| solver | `het_rt_lacam` or `hetpibt` |
| category | Map category |
| agent_label | `n5`, `n10`, `n15`, `n20`, `n25`, or `var` (het_bench) |
| scen_id | Scenario number (00-24 or 0-9) |
| agents | Actual number of agents loaded |
| solved | True if all agents reached goals |
| goals_reached | Number of agents that reached their goal |
| goals_total | Total agents in the scenario |
| soc | Sum of costs (0 if not solved for het_rt_lacam) |
| soc_lb | Lower bound on SOC (het_rt_lacam only) |
| makespan | Solution makespan |
| makespan_lb | Lower bound on makespan (het_rt_lacam only) |
| runtime_ms | Wall-clock time in milliseconds |

## How to reproduce

### Prerequisites
```bash
# Build both solvers
cd E:/gb/het_rt_lacam && cmake --build build --config Release
cd E:/gb/third_party/hetpibt && cmake --build build --config Release
```

### Run all experiments
```bash
source E:/gb/venv/Scripts/activate
python E:/gb/benchmarks/run_all_experiments.py
```

### Run a specific subset
```bash
# Only intersection, n10 agents, het_rt_lacam only
python E:/gb/benchmarks/run_all_experiments.py \
    --solver het_rt_lacam --category intersection --agents n10

# Only hetpibt on all categories
python E:/gb/benchmarks/run_all_experiments.py --solver hetpibt

# Custom timeouts
python E:/gb/benchmarks/run_all_experiments.py --timeout-lacam 60 --timeout-pibt 60
```

### Run a single scenario manually

```bash
# het_rt_lacam on intersection_105 scenario 00, 10 agents
cd E:/gb/het_rt_lacam/build
./Release/main.exe \
    -m ../../benchmarks/maps/intersection_105.map \
    -i ../../benchmarks/scenarios/intersection_105_00_n10_hb.scen \
    --goal-lock -t 30 -v 1

# hetpibt on same scenario
cd E:/gb/third_party/hetpibt/build
./Release/main.exe \
    -m ../../../benchmarks/maps/intersection_105.map \
    -s ../../../benchmarks/scenarios/intersection_105_00_n10_hb.scen \
    --seed 0 --swap-xy --goal-lock -v 1
```

## Known issues

- **het_bench scen.1**: Goal footprint overlap (agents 5 and 2). Infeasible.
- **het_bench scen.9**: Agent 2 start on wall (invalid scenario).
- **hetpibt --swap-xy**: Causes some agents to land on walls; hetpibt skips
  them, so it solves with fewer agents than the scenario specifies.
- **het_rt_lacam without --swap-xy on het_bench**: Required for correct
  coordinate mapping on room120 scenarios.
