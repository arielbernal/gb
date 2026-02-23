# gb

Monorepo containing **HetPIBT** (heterogeneous Priority Inheritance with BackTracking) and the reference **LaCAM** implementation it builds on.

## Prerequisites

- CMake 3.16+
- C++17 compiler (MSVC, GCC, or Clang)
- Python 3.8+ with `numpy` and `matplotlib` (for visualization)

## Project Structure

```
gb/
├── hetpibt/          # HetPIBT — heterogeneous multi-agent pathfinding
├── lacam/            # LaCAM — reference MAPF solver
└── docs/             # Papers and documentation
```

## Building

### HetPIBT

```bash
cd hetpibt
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### LaCAM

```bash
cd lacam
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

## Running

### HetPIBT

```bash
cd hetpibt
./build/Release/main -m assets/room-64-64-8.map -s assets/room-64-64-8.scen
```

Options:
| Flag | Description | Default |
|------|-------------|---------|
| `-m, --map` | Map file (required) | — |
| `-s, --scen` | Scenario file (required) | — |
| `-o, --output` | Output file | `result.txt` |
| `-v, --verbose` | Verbosity (0–2) | `0` |
| `-t, --time_limit` | Time limit in ms | `60000` |
| `--max_timesteps` | Max simulation steps | `1000` |
| `--seed` | Random seed | `0` |

### LaCAM

```bash
cd lacam
./build/Release/main -m assets/random-32-32-10.map -i assets/random-32-32-10-random-1.scen -N 50
```

Options:
| Flag | Description | Default |
|------|-------------|---------|
| `-m, --map` | Map file (required) | — |
| `-i, --scen` | Scenario file | `""` |
| `-N, --num` | Number of agents (required) | — |
| `-o, --output` | Output file | `./build/result.txt` |
| `-v, --verbose` | Verbosity | `0` |
| `-t, --time_limit_sec` | Time limit in seconds | `10` |
| `-s, --seed` | Random seed | `0` |

## Tests

```bash
# HetPIBT
cd hetpibt/build && ./Release/test_all.exe

# LaCAM
cd lacam/build && ./Release/test_all.exe
```

## Visualization

### HetPIBT

```bash
cd hetpibt
python visualize.py --map assets/room-64-64-8.map --result build/result.txt
```

Options: `--scen`, `--speed` (ms/frame, default 150), `--substeps` (interpolation, default 4), `--no-grid-overlay`.

### LaCAM

```bash
cd lacam
python visualize.py --result build/result.txt
```

Options: `--map` (auto-detected from result), `--speed` (ms/frame, default 150).

## Collision Checking

Verify a HetPIBT solution has no collisions:

```bash
python hetpibt/tests/assets/check_collisions.py hetpibt/build/result.txt
```
