# gb — Heterogeneous Multi-Agent Pathfinding

Monorepo for heterogeneous MAPF research, containing **het_rt_lacam** (our solver) and reference implementations.

## Prerequisites

- CMake 3.16+
- C++17 compiler (MSVC, GCC, or Clang)
- Python 3.8+ with `numpy` and `matplotlib` (for visualization)

## Project Structure

```
gb/
├── het_rt_lacam/       # Our solver (heterogeneous real-time LaCAM)
├── benchmarks/         # Maps, scenarios, and generators
│   ├── maps/           # .map files (64, 77, 105, 154 grids)
│   ├── scenarios/      # .scen files (het_bench + MAPF format)
│   └── generators/     # Python scenario/map generators
├── experiments/        # Results, replays, and visualizations
├── tools/              # Runner scripts, analysis, utilities
├── third_party/        # Reference implementations
│   ├── hetpibt/        # HetPIBT solver
│   ├── lacam/          # LaCAM reference
│   ├── lacam3/         # LaCAM3 reference
│   ├── pibt_rs/        # pibt_rs (Rust)
│   ├── pypibt/         # pypibt (Python)
│   └── cbsh2rtc/       # CBS-H2 reference solutions
├── docs/               # Papers (hetpibt.pdf, G-MAPF.pdf)
└── venv/               # Python virtual environment
```

## Building

### het_rt_lacam (primary solver)

```bash
cd het_rt_lacam
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release
```

### HetPIBT (reference)

```bash
cd third_party/hetpibt
cmake -B build -G "Visual Studio 17 2022"
cmake --build build --config Release
```

## Running

### het_rt_lacam

```bash
cd het_rt_lacam
./build/Release/main.exe -m ../benchmarks/maps/corridor_speed_105.map \
  -i ../benchmarks/scenarios/corridor_speed_105_00_hb.scen \
  --swap-xy -v 1 -t 60
```

| Flag | Description | Default |
|------|-------------|---------|
| `-m, --map` | Map file (required) | — |
| `-i, --scen` | Scenario file (het_bench or MAPF) | `""` |
| `-N, --num` | Number of agents (MAPF mode) | `0` |
| `-o, --output` | Output file | `./build/result.txt` |
| `-v, --verbose` | Verbosity (0–2) | `0` |
| `-t, --time_limit_sec` | Time limit in seconds | `10` |
| `-s, --seed` | Random seed | `0` |
| `--swap-xy` | Swap x/y in het_bench coords | `false` |

## Tests

```bash
cd het_rt_lacam/build && ./Release/test_all.exe   # 14 tests
cd third_party/hetpibt/build && ./Release/test_all.exe  # 12 tests
```

## Visualization

```bash
# het_rt_lacam native visualizer
python het_rt_lacam/visualize.py \
  --result experiments/replays/replay_hetlacam_corridor_speed.txt \
  --map benchmarks/maps/corridor_speed_105.map

# HetPIBT visualizer
python third_party/hetpibt/visualize.py \
  --map third_party/hetpibt/assets/room-64-64-8.map \
  --result third_party/hetpibt/build/result.txt
```

Controls: `Space` (pause/play), `Left/Right` (step), `Up/Down` (speed), `g` (goal lines), `Q` (quit).
