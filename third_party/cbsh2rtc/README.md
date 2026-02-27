# CBSH2-RTC Reference Solutions

Optimal CBS solutions for the cs=1 (unit-size) agents in our het_bench scenarios.
Used as a baseline to measure solution quality of hetpibt and het_rt_lacam.

## Pre-computed Results

`reference_solutions/` contains optimal paths and SOC values — no build needed:

| Scenario | Agents | Optimal SOC |
|----------|--------|-------------|
| scen.0   | 3      | 358         |
| scen.1   | 2      | 48          |
| scen.2   | 1      | 48          |
| scen.3   | 2      | 111         |
| scen.4   | 3      | 139         |
| scen.5   | 3      | 326         |
| scen.6   | 3      | 405         |
| scen.7   | 3      | 141         |
| scen.8   | 3      | 261         |
| scen.9   | 2      | 249         |
| **Total**| **25** | **2086**    |

## Building from Source

CBSH2-RTC is not included (USC Research License). The setup scripts clone,
patch, and build it automatically:

```bash
# Linux/Mac
./setup.sh

# Windows (from Developer Command Prompt)
setup.bat
```

### Requirements
- git, cmake, curl
- C++ compiler (GCC/Clang/MSVC)
- ~500MB disk (Boost headers)

### What the scripts do
1. Clone [CBSH2-RTC](https://github.com/Jiaoyang-Li/CBSH2-RTC) at commit `a834df1`
2. Download Boost 1.86.0 headers (heap, unordered, tokenizer — all header-only)
3. Download [CLI11](https://github.com/CLIUtils/CLI11) single-header library
4. Apply `cli11_patch.diff` (replaces `boost::program_options` with CLI11)
5. Build with CMake

### Running
```bash
./build/CBSH2-RTC/build/Release/cbs -m ../../benchmarks/maps/room120.map \
    -a reference_solutions/scen.0.scen -k 3 -t 60
```

## Scenario Conversion

`reference_solutions/het2movingai.py` converts het_bench scenarios to MovingAI
format (cs=1 agents only). Uses `--swap-xy` convention (sx=row, sy=col).
