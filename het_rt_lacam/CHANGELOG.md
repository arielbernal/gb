# Het-RT-LaCAM Algorithm Changes

## Base: lacam3 (Okumura, AAMAS 2024)

Forked from lacam3 — homogeneous LaCAM* with Monte-Carlo PIBT, scatter (SUO),
SIPP-based iterative refinement, and multi-threaded configuration generation.

Source files in lacam3: `collision_table`, `dist_table`, `graph`, `heuristic`,
`hnode`, `instance`, `lacam`, `lnode`, `metrics`, `pibt`, `planner`,
`post_processing`, `refiner`, `scatter`, `sipp`, `translator`, `utils`.

---

## Changes from lacam3 → het_rt_lacam

### Removed modules (5 files deleted)

| Module | Purpose in lacam3 | Why removed |
|---|---|---|
| `scatter.cpp/.hpp` | SUO (Scatter with Unidirectional Offloading) — pre-computes collision-aware single-agent paths to guide search | Phase 1 simplification; heterogeneous footprints make SUO's homogeneous collision table invalid |
| `refiner.cpp/.hpp` | Iterative refinement — background threads that continuously improve solution quality via recursive LaCAM calls | Phase 1 simplification; requires scatter + multi-threading |
| `sipp.cpp/.hpp` | Safe Interval Path Planning — used by refiner for single-agent replanning | Only used by refiner |
| `collision_table.cpp/.hpp` | Collision counting for scatter's A* search | Only used by scatter |
| `translator.cpp/.hpp` | Converts between internal and SIPP representations | Only used by SIPP/refiner |

### New: HetConfig (graph.hpp)

Replaces `Config` (= `vector<Vertex*>`) as the search state throughout the planner.

```cpp
struct HetConfig {
  Config positions;        // fleet-specific vertex per agent
  std::vector<int> kappa;  // speed phase counter per agent [0, speed_period)
};
```

- **Hash function** (`HetConfigHasher`): hashes both position IDs and kappa values
  (lacam3's `ConfigHasher` only hashed positions).
- **Equality**: two HetConfigs match iff all positions AND kappa values match.
- **Goal test** (`Instance::is_goal`): agent is "arrived" only when at goal position
  AND kappa == 0.

### New: Fleet graphs (graph.hpp/cpp)

Each fleet type has its own navigation graph built by non-overlapping tiling of
the base grid (paper Section IV-B, Eq. 1, matching pibt_rs).

```cpp
void Graph::build_from_base(const Graph &base, int cell_size);
```

- Fleet cell `(fx, fy)` covers base cells `[fx*cs, (fx+1)*cs) × [fy*cs, (fy+1)*cs)`
- A fleet cell is passable only if ALL underlying base cells are passable
- Fleet graph has 4-connected edges between adjacent passable fleet cells
- `Graph` gained move semantics (move ctor + move assignment) and deleted copy
  (Graph owns Vertex memory via raw pointers)

### New: Footprint projection (graph.hpp/cpp)

```cpp
std::vector<int> to_base_cells_xy(int fx, int fy, int cell_size, int base_width);
std::vector<int> to_base_cells(int cell_index, int fleet_width, int cell_size, int base_width);
```

Maps a fleet-grid cell to the set of base-grid cell indices it occupies. Used by:
- `HetPIBT` for cross-fleet collision checking
- `HNode::get_next_lowlevel_node` for constraint pruning
- `is_feasible_solution` for solution verification
- `Instance::is_valid` for start/goal overlap detection

### New: Instance (instance.hpp/cpp) — complete rewrite

lacam3 Instance stored a single `Graph*`, `Config starts`, `Config goals`, `uint N`.

het_rt_lacam Instance stores:

| Field | Type | Purpose |
|---|---|---|
| `base_graph` | `Graph` (owned) | Shared base grid loaded from .map file |
| `fleet_graphs` | `vector<Graph>` | One navigation graph per fleet, built via tiling |
| `fleet_cell_sizes` | `vector<int>` | Footprint size per fleet (1 = unit agent) |
| `fleet_speed_periods` | `vector<int>` | Kappa modulus per fleet (from velocity, not cell_size) |
| `agents` | `vector<AgentInfo>` | Per-agent {fleet_id, cell_size} |
| `starts`, `goals` | `Config` | Fleet-specific vertices per agent |
| `N`, `base_width`, `base_height`, `num_fleets` | int | Dimensions |

Two constructors:
1. **het_bench** (`scen_filename, map_filename, swap_xy`): reads custom scenario
   format. Auto-detects simple (5-field) vs full (10-field) format. Assigns fleet
   IDs by cell_size. Supports `--swap-xy` for pibt_rs coordinate convention.
2. **Homogeneous MAPF** (`scen_filename, map_filename, N`): reads standard
   MovingAI .scen files. Single fleet with cell_size=1.

New methods:
- `fleet_graph(agent_id)`: returns agent's fleet navigation graph
- `speed_period(agent_id)`: returns agent's kappa modulus
- `make_start_config()`: builds initial HetConfig (all kappa=0)
- `is_goal(HetConfig)`: true iff all agents at goal with kappa=0
- `is_valid()`: checks N consistency, null starts/goals, AND base-grid footprint
  overlaps for both starts and goals (lacam3 only checked N)

### Changed: DistTable (dist_table.hpp/cpp)

- BFS runs on each agent's **fleet graph** (not the single shared graph)
- `table[i]` is sized to agent i's fleet graph vertex count (not global V count)
- Bounds-checked `get()` returns sentinel for out-of-range vertex IDs

### Changed: Heuristic (heuristic.hpp/cpp)

lacam3: `cost += D->get(i, Q[i])`

het_rt_lacam: `cost += D->get(i, C.positions[i]) * speed_period(i) + C.kappa[i]`

Each fleet-graph step takes `speed_period` wall-clock ticks. Remaining kappa
steps add partial cost. This makes the heuristic admissible for heterogeneous
agents with different speeds.

### Changed: HNode (hnode.hpp/cpp) — stuck-counter acceleration

lacam3 HNode:
- Stored `Config C` (positions only)
- Priorities: `parent->priorities[i] + 1` (linear growth)

het_rt_lacam HNode:
- Stores `HetConfig C` (positions + kappa)
- New field: `std::vector<int> stuck_count` per agent
- Priority update (from hetpibt):
  - Agent at goal (d=0, kappa=0): priority resets to fractional part
  - Agent made progress (d_now < d_parent): `stuck_count = 0`, priority += 1
  - Agent stuck (d_now >= d_parent): `stuck_count++`, priority += 1 + stuck_count
  - Effect: stuck agents get **quadratic** priority growth, rapidly outprioritizing
    progressing agents. Prevents livelock where low-priority agents never move.
- Initial priorities weighted by `speed_period`: `(d * sp + kappa) / 10000`
  so slow agents get fair scheduling relative to fast ones.

### Changed: HNode::get_next_lowlevel_node — footprint-aware constraint enumeration

lacam3: enumerates neighbors + stay for each agent, checks vertex collisions
against previously constrained agents.

het_rt_lacam:
1. Builds `occupied` set of base-grid cells from:
   - Explicitly constrained agents (from LNode chain)
   - Speed-gated agents (kappa > 0, must stay — free agents can't collide with them)
   - Goal-locked agents (at goal with kappa=0, permanent obstacles)
2. For speed-gated/goal-locked agents: only push the stay option (if non-colliding)
3. For free agents (kappa=0): enumerate fleet-graph neighbors + stay, prune any
   candidate whose base-grid footprint overlaps `occupied`
4. This early pruning prevents wasted PIBT calls that would inevitably fail at
   the base-grid collision check (the dominant source of step-2 failures)

### Changed: PIBT → HetPIBT (pibt.hpp/cpp) — complete rewrite

lacam3 PIBT: simple recursive funcPIBT on a single shared graph. Agents are
point-sized. Collision = two agents at same vertex. Swap = two agents exchange
positions.

het_rt_lacam HetPIBT: footprint-aware, speed-gated, push-based configuration
generator adapted from hetpibt's `push_agent`.

**Data structures:**
- `base_occupied_now[base_cell]` → agent_id or NO_AGENT (current timestep)
- `base_occupied_next[base_cell]` → agent_id or NO_AGENT (next timestep)
- Replaces lacam3's per-vertex occupancy with base-grid bitmap

**set_new_config pipeline (5 phases):**

1. **Setup**: mark all agents' current positions on `base_occupied_now`
2. **Hard constraints**: process pre-filled positions from LNode. Check footprint
   collision (`base_next_free`) and swap conflict. Mark on `base_occupied_next`.
3. **Goal lock** (optional): agents at goal with kappa=0 are permanently locked
   in place — pre-reserve their footprint
4. **Speed gating**: agents with kappa > 0 MUST stay in place — pre-reserve
   their footprint before free agents move
5. **PIBT**: run `funcPIBT` for unconstrained agents in priority order

**funcPIBT — recursive push (replaces lacam3's funcPIBT):**

Key differences from vanilla PIBT:
- `max_depth` limit (default 6) prevents exponential blowup in push chains
- `keep_out` set: pushed agents cannot land on the pusher's destination footprint
  (prevents oscillation where A pushes B, B pushes A back)
- `in_chain` set: explicit cycle detection (not just Q_to nullity check)
- **Cross-fleet depth scaling**: when a large agent (cs_i) pushes a small agent
  (cs_j), the small agent gets extra recursion depth:
  `sub_depth = max(depth-1, ceil(cs_i / cs_j))` to escape the larger footprint
- **Cascade rollback**: if pushing all blockers fails, ALL assignments from that
  cascade are undone (positions cleared, base_next unmarked, in_chain restored),
  and the next candidate is tried
- **Swap conflict check**: cross-fleet aware — projects both agents' from/to
  positions onto the base grid and checks for footprint exchange
- **Last resort stay**: if all candidates fail, agent stays in place with kappa=0
  (if footprint is free)

**Speed-phase (kappa) model in funcPIBT:**
- kappa > 0: agent is mid-phase, MUST stay. kappa advances: `(kappa+1) % speed_period`
- kappa == 0: agent CAN move. On movement: kappa becomes 1 (if speed_period > 1).
  On stay: kappa stays 0.

### Changed: Planner (planner.hpp/cpp)

| Feature | lacam3 | het_rt_lacam |
|---|---|---|
| Search state | `Config` | `HetConfig` (positions + kappa) |
| EXPLORED map | `unordered_map<Config, HNode*, ConfigHasher>` | `unordered_map<HetConfig, HNode*, HetConfigHasher>` |
| Config generator | `PIBT` (multiple, threaded) | `HetPIBT` (single by default) |
| Goal check | `is_same_config(H->C, ins->goals)` | `ins->is_goal(H->C)` (checks positions AND kappa=0) |
| Edge cost | 1 per agent not at goal position | 1 per agent not at goal position OR kappa≠0 |
| Backtrack | returns `Config` from `H->C` | returns `Config` from `H->C.positions` |
| Defaults | FLG_STAR=true, PIBT_NUM=10, scatter=on, refiner=on | FLG_STAR=false, PIBT_NUM=1, no scatter, no refiner |

New parameter: `FLG_GOAL_LOCK` — passed through to HetPIBT and HNode.

Removed from lacam3 Planner:
- `Scatter *scatter` and `set_scatter()`
- `refiner_pool` and `set_refiner()`, `get_refined_plan()`
- `seed_refiner`, `depth` parameter, `DistTable *_D` parameter
- `FLG_RANDOM_INSERT_INIT_NODE` (always false, simplified)
- `FLG_SWAP` (swap is always checked via base-grid footprint)

### Changed: post_processing.cpp

- `is_feasible_solution`: uses **footprint-based** conflict detection:
  - Vertex conflict: checks base-grid cell overlap between all agent pairs
  - Swap conflict: projects from/to positions onto base grid, checks footprint exchange
  - Connectivity: checks fleet-graph neighbor list (not base graph)
- `print_stats`: computes makespan, SOC, sum_of_loss, and lower bounds via DistTable
- `make_log`: outputs fleet definitions (`fleets=fid:cs:sp:gw:gh;...`),
  per-agent fleet assignment (`agent_fleet=0,0,1,...`), fleet-grid coordinates

### Changed: metrics.cpp

- `get_sum_of_loss`: counts timesteps where agent is NOT at goal
  (lacam3 had this but also had unused Path-based variants)
- Removed 6 dead declarations for Path-based metrics that had no implementations

### Changed: main.cpp

New CLI flags:
- `--swap-xy`: swap x/y in het_bench scenario coordinates (for pibt_rs compat)
- `-N`: when > 0, uses homogeneous MAPF benchmark mode instead of het_bench
- `--no-star`: disable anytime improvement (default: already off)
- `--multi-thread`: enable multi-threaded PIBT (default: off)
- `--pibt-num`: number of Monte-Carlo PIBT instances (default: 1)

Removed lacam3 CLI flags: `--no-all`, `--no-swap`, `--no-scatter`, `--no-refiner`,
`--scatter-margin`, `--recursive-rate`, `--recursive-time-limit`,
`--random-insert-init-node`.

### Unchanged from lacam3

- `LNode` (lnode.hpp/cpp): low-level search node structure (who/where/depth)
- Core LaCAM* search loop structure: OPEN deque, EXPLORED hash map, f-value
  pruning, cost propagation via `rewrite()`
- `Deadline` and timing utilities (utils.hpp/cpp)
- Random number generation API

---

## Summary of algorithmic contributions

1. **Heterogeneous agent model**: HetConfig (positions + kappa), per-fleet graphs,
   speed-phase gating
2. **Cross-fleet collision**: base-grid footprint projection replaces vertex equality
3. **Push-based PIBT**: depth-limited recursive push with keep_out, in_chain, and
   cross-fleet depth scaling (adapted from hetpibt)
4. **Stuck-counter acceleration**: quadratic priority growth for stuck agents
   (adapted from hetpibt)
5. **Goal locking**: optional permanent goal occupation (matching pibt_rs)
6. **Constraint pruning**: speed-gated and goal-locked agents' footprints are
   included in LNode constraint sets to prune infeasible branches early
