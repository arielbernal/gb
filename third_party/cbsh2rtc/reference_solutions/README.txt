CBSH2-RTC Reference Solutions for het_bench scenarios
=====================================================

Source: https://github.com/Jiaoyang-Li/CBSH2-RTC
Commit: a834df1e16c1668a677b68fef6699371c4233d33
Build:  CLI11 replacing boost::program_options; header-only Boost 1.86.0

Map: room120.map (120x120, from het_rt_lacam/assets/)

Scenarios: het_bench scen.0-scen.9, cs=1 agents only (CBS is homogeneous)
Conversion: het2movingai.py (--swap-xy convention: sx=row, sy=col)

Solver config: WDG+GR+GC+T+BP with AStar (defaults), -t 120

Results (all OPTIMAL):
  scen.0: k=3, SOC=358
  scen.1: k=2, SOC=48
  scen.2: k=1, SOC=48
  scen.3: k=2, SOC=111
  scen.4: k=3, SOC=139
  scen.5: k=3, SOC=326
  scen.6: k=3, SOC=405
  scen.7: k=3, SOC=141
  scen.8: k=3, SOC=261
  scen.9: k=2, SOC=249 (agent 2 start at wall col=0, excluded)

Total: 26 agents, 25 solved optimally. Total optimal SOC=2086.

Files:
  scen.N.scen          - MovingAI format scenario (input to CBS)
  scen.N_results.csv   - CBS results (runtime, nodes, SOC, etc.)
  scen.N_paths.txt     - Optimal paths per agent
  het2movingai.py      - Converter script
  cbsh2_commit_hash.txt - CBSH2-RTC git hash
