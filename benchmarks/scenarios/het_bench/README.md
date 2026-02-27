# Het-Bench Scenarios (scen.0 – scen.9)

Map: room120.map (120x120 base grid)
Fleets: 3 types (cs=1, cs=6, cs=11)
Agents: 6-9 per scenario

## Reproducing baseline results

```bash
cd third_party/hetpibt/build
./Release/main.exe -m ../../../benchmarks/maps/room120.map -s ../../../benchmarks/scenarios/het_bench/scen.X --seed 0 --swap-xy --goal-lock
```

## Expected results

| Scen  | Goals | SOC  |
|-------|-------|------|
| 0     | 9/9   | 404  |
| 1     | 6/7   | 118  |
| 2     | 7/7   | 130  |
| 3     | 7/7   | 152  |
| 4     | 8/8   | 179  |
| 5     | 6/6   | 338  |
| 6     | 9/9   | 452  |
| 7     | 9/9   | 184  |
| 8     | 9/9   | 308  |
| 9     | 8/8   | 279  |
| TOTAL | 78/79 | 2544 |

Note: SOC for scen.1 counts stuck-agent idle time differently. Actual measured
SOC=1103 includes idle steps for the 1 stuck agent.
