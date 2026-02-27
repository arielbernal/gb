# Agent Center — Status
**Started:** 2026-02-26

## Repo Verification: PASSED
Verification PASSED. Flags: --seed 0 --swap-xy --goal-lock. 6/10 exact SOC, 3 near-miss (2-8), 1 metric difference (scen.1). Goals 78/79 exact match.

### Details
- het_rt_lacam: builds clean, 14/14 tests pass
- hetpibt: builds clean, 12/12 tests pass
- het_bench regression (room120.map, 10 scenarios):
  - Exact match: scen.0, .2, .4, .7, .8, .9
  - Near-miss SOC: scen.3 (+2), scen.5 (+8), scen.6 (+8)
  - Metric difference: scen.1 (stuck-agent idle cost accounting)
- Required flags discovered: --swap-xy --goal-lock
- Map fix: scenarios need room120.map (120x120), not room-64-64-8.map (64x64)

## CBSH2-RTC Reference Solutions: COMPLETE
- CBSH2-RTC commit: a834df1e16c1668a677b68fef6699371c4233d33
- Built with CLI11 (replaced boost::program_options), header-only Boost 1.86.0
- Converted het_bench scen.0-9 to MovingAI format (cs=1 agents only, 26 total)
- All 10 scenarios solved optimally (scen.9: k=2, agent 2 excluded — wall start)
- Delivered to: E:/gb/third_party/cbsh2rtc/reference_solutions/

### Optimal SOC (cs=1 agents):
  scen.0: k=3, SOC=358 | scen.5: k=3, SOC=326
  scen.1: k=2, SOC=48  | scen.6: k=3, SOC=405
  scen.2: k=1, SOC=48  | scen.7: k=3, SOC=141
  scen.3: k=2, SOC=111 | scen.8: k=3, SOC=261
  scen.4: k=3, SOC=139 | scen.9: k=2, SOC=249
  TOTAL: 25/26 agents solved, total optimal SOC=2086
