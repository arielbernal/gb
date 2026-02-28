# RT-LaCAM Implementation Plan

## Overview
Extend het_rt_lacam's Planner with Real-Time incremental execution.
Algorithm: run LaCAM search for a fixed node-expansion budget, execute the
first step of the best path found so far, then repeat — preserving OPEN and
EXPLORED across steps for completeness.

## Reference
- Paper: E:/gb/docs/rt_lacam_paper.pdf (Liang et al., SoCS 2025)
- Python reference: E:/gb/third_party/ML-MAPF-with-Search/main_pys/simulator.py
  LaCAMRunner class lines 286-413 (real_time flag, persistent stack/cache)

## Pre-Analysis: What Is Already Done

### Already complete (NO changes needed):
1. **Reinsert known configs** — planner.cpp line 112: `OPEN.push_front(iter->second)` ✓
2. **OPEN/EXPLORED as class members** — planner.hpp lines 38-39 ✓
3. **Speed-gating in constraint tree** — hnode.cpp lines 129-157 ✓
4. **HetConfig hash/equality includes kappa** — graph.hpp lines 33-42 ✓

### What needs to be ADDED:
- New state members: current_root_, search_initialized_, latest_generated_
- New methods: search(), extract_next_step(), advance(), solve_one_step(), reset()
- Destructor fix: EXPLORED nodes not freed in current destructor
- solve() fix: add EXPLORED.clear() after deletion to avoid double-free
- CLI flags: --rt, --rt-budget N
- RT outer loop in main.cpp
- RT test in test_planner.cpp

## Part 3 — Algorithm Specification

### 3.1 State Members (add to planner.hpp)
```
HNode* current_root_     — config agents are currently executing from
                           init = H_init, updated by advance()
bool search_initialized_ — has H_init been created?
HNode* latest_generated_ — most recently generated/revisited node
                           used by extract_next_step()
enum SearchStatus { SEARCHING, GOAL_FOUND, NO_SOLUTION }
```

### 3.2 search(int node_budget) → SearchStatus
Same DFS loop as solve(), but:
- On first call: creates H_init, sets current_root_ = H_init
- Stops after `node_budget` OUTER LOOP ITERATIONS (not just expansions)
  Count iteration at loop top (before pruning/skipping)
- Does NOT clear OPEN or EXPLORED — they persist across calls
- Updates latest_generated_ on every new node creation or reinsert
- Returns GOAL_FOUND if H_goal != nullptr, NO_SOLUTION if OPEN empty,
  else SEARCHING

### 3.3 extract_next_step() → HetConfig (const)
```
target = H_goal if H_goal != nullptr, else latest_generated_
if target == nullptr or target == current_root_: return current_root_->C

step = target
while step->parent != nullptr and step->parent != current_root_:
    step = step->parent

if step->parent == current_root_: return step->C   // one step forward

// DFS backtracked past current_root_ — stay in place
return current_root_->C
```

### 3.4 advance(const HetConfig& next)
```
iter = EXPLORED.find(next)
if iter != EXPLORED.end(): current_root_ = iter->second
// If next == current_root_->C (stay in place), current_root_ unchanged
```

### 3.5 solve_one_step(int node_budget) → HetConfig
```
search(node_budget)
next = extract_next_step()
advance(next)
return next
```

### 3.6 reset()
Free all EXPLORED nodes, clear OPEN, reset all members to initial state.

## Part 4 — Memory Management

### Destructor fix
Current destructor does NOT free EXPLORED nodes. For RT mode (where we
never call solve()), this causes a leak. Fix: add cleanup to destructor.

After fix, solve() must ALSO clear the EXPLORED map (not just delete items)
so the destructor doesn't iterate over dangling pointers.

```cpp
// In solve(), change:
for (auto p : EXPLORED) delete p.second;
// To:
for (auto& p : EXPLORED) delete p.second;
EXPLORED.clear();

// In ~Planner(), add:
for (auto& p : EXPLORED) delete p.second;
```

## Part 5 — CLI Changes (main.cpp)

Add two new arguments:
```
--rt              (bool flag) enable real-time incremental execution
--rt-budget N     (int, default=100) node expansion budget per step
```

### RT outer loop
```cpp
if (rt_mode) {
    auto planner = Planner(&ins, verbose-1, &deadline, seed);
    vector<HetConfig> executed;
    executed.push_back(ins.make_start_config());

    bool goal_reached = false;
    while (!is_expired(&deadline) && executed.size() <= 100000) {
        auto next = planner.solve_one_step(rt_budget);
        executed.push_back(next);
        if (ins.is_goal(next)) { goal_reached = true; break; }
    }

    // Convert to Solution (vector<Config>)
    Solution solution;
    for (auto& hc : executed) solution.push_back(hc.positions);

    // Only validate if goal was reached
    if (goal_reached && !is_feasible_solution(ins, solution, verbose)) {
        info(0, verbose, "RT: invalid solution"); return 1;
    }
    print_stats(...);
    make_log(...);
}
```

## Part 6 — Testing

### RT correctness test
In test_planner.cpp: create a simple 3-agent instance, call solve_one_step()
in a loop up to 1000 steps, verify goal is reached and each step is valid.

### What to verify:
- solve() (standard mode) still works: all existing 14 tests pass
- RT mode reaches goal on all 3 test instances
- RT mode with budget=1 vs budget=100 vs budget=1000: same solvability
- Steps are single-step moves (no teleportation)
- No collisions in executed path

## Part 7 — Speedgate Analysis

ALREADY DONE in hnode.cpp lines 129-157:
- kappa > 0 agents: only "stay" constraint generated
- kappa == 0 agents (normal): all neighbors + stay generated
No changes needed.

## Part 8 — Verification Criteria

1. `cmake --build build --config Release` succeeds
2. `./Release/test_all.exe` — all 14 existing tests pass
3. `./Release/test_all.exe` — new RT test passes
4. `main.exe -m <map> -i <scen> --swap-xy --goal-lock -t 30` (standard) works
5. `main.exe -m <map> -i <scen> --swap-xy --goal-lock --rt --rt-budget 100 -t 30` works
6. RT mode on bottleneck_doors_105_00_n5_hb.scen solves successfully
