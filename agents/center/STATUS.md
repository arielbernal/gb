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

## Next Phase: CBSH2-RTC
- Waiting for Right (audit) and Left (push) to finish
- Workspace: E:/gb/agents/center/temp/
- Delivery target: E:/gb/third_party/cbsh2rtc/reference_solutions/
