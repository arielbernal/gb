# Space-Time BFS Port Plan

> Port hetpibt's space-time BFS with reservation table into het_rt_lacam's PIBT,
> replacing the current spatial-only BFS candidate generation.

## 1. hetpibt's Reservation Table Architecture

### Data Structures

**`ReservationTable`** (`third_party/hetpibt/hetpibt/include/reservation.hpp:45-110`)

| Member | Type | Purpose |
|--------|------|---------|
| `st_map` (line 47) | `unordered_map<uint64_t, vector<int>>` | Primary index: `pack_key(time, base_cell_id)` → agent IDs. O(1) collision check. |
| `agent_cells` (line 50) | `unordered_map<int, vector<uint64_t>>` | Reverse index: `agent_id` → list of `pack_key` entries. Enables O(|traj|) removal. |
| `agent_last` (line 58) | `unordered_map<int, AgentEndpoint>` | Per-agent endpoint: `{fleet_id, cell_index, end_time}`. Where agent is "parked" after its last reservation. |
| `parked_at_cell` (line 62) | `unordered_map<int, vector<int>>` | Spatial index: `base_cell` → agent IDs parked there beyond explicit reservation. |
| `traj_log` (line 66) | `unordered_map<int, vector<pair<int,int>>>` | Chronological `(time, cell_index)` log per agent. For visualization output. |

**`AgentEndpoint`** (lines 53-57): `{fleet_id, cell_index, end_time}`

**`Trajectory`** (`reservation.hpp:16-23`): `{agent_id, fleet_id, start_time, positions[]}` — timed cell sequence.

**`ProposedPath`** (`third_party/hetpibt/hetpibt/include/planner.hpp:29-32`):
```cpp
struct ProposedPath {
  Path path;                       // untimed cells the agent would traverse
  std::vector<int> blocking_agents;  // agents that must move out
};
```

**`pack_key`** (`third_party/hetpibt/hetpibt/include/utils.hpp:55-59`):
```cpp
inline uint64_t pack_key(int a, int b) {
  return (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
         static_cast<uint64_t>(static_cast<uint32_t>(b));
}
```

### API

| Method | Signature (reservation.hpp) | Purpose |
|--------|---------------------------|---------|
| `try_reserve` (line 78) | `bool try_reserve(const Trajectory& traj)` | Check vertex+swap+parked conflicts, then reserve. Returns false on collision. |
| `reserve` (line 81) | `void reserve(const Trajectory& traj)` | Force-reserve (no collision check). Used during backtrack. |
| `move_collides` (lines 85-87) | `bool move_collides(int fleet_id, int from, int to, int time, int agent_id, bool include_parked=false)` | Vertex conflict at `(to, t+1)` AND swap conflict (agent at `to@t` moving to `from@t+1`). |
| `is_occupied` (lines 93-95) | `bool is_occupied(int fleet_id, int cell, int time, int exclude=-1, bool include_parked=false)` | Is cell occupied at time by any agent other than exclude? |
| `get_occupants` (lines 98-99) | `vector<int> get_occupants(int fleet_id, int cell, int time)` | List agents at cell (including cross-fleet projections). |

### How BFS Uses It

**Space-time BFS** (`third_party/hetpibt/hetpibt/src/planner.cpp:131-292`):

- Explores `(time, cell)` states, keyed as `pack_key(time, cell)` in visited set (line 150).
- Uses `P.move_collides()` to prune edges — if moving `A→B` at time `T` would collide with existing reservation, skip it.
- Uses `P.get_occupants()` to count blocking agents at destination (only "parked" agents count as blockers).
- Returns up to 5 `ProposedPath` candidates: each is a timed cell sequence + list of blocking agents that need pushing.
- Blocking agents are identified as occupants whose `end_time <= t` (parked, not actively moving).

**Integration with per-agent loop** (`planner.cpp:464-541`):

- Agents processed in priority order each timestep.
- Each calls `push_agent()` (line 295-436) → `get_next_locations()` (space-time BFS) → candidates → try pushing blockers recursively → `try_reserve()` the final trajectory.
- Reservations accumulate across agents within a timestep: agent A's reservation constrains agent B's BFS.

---

## 2. het_rt_lacam's Current Spatial-Only BFS

### Current Occupancy Model (`het_rt_lacam/het_rt_lacam/src/pibt.cpp`)

| Data Structure | Lines | Purpose |
|----------------|-------|---------|
| `base_occupied_now[base_cell]` | declared `pibt.hpp:28` | Flat array, one agent per base cell. Built by `mark_base_now()` (lines 36-43) from `Q_from` positions. |
| `base_occupied_next[base_cell]` | declared `pibt.hpp:29` | Same structure. Filled as agents are assigned to `Q_to` via `mark_base_next()` (lines 45-54). |
| `mark_base_now(i, v)` | lines 36-43 | Mark base cells under fleet cell `v` as occupied by agent `i` in NOW array. |
| `mark_base_next(i, v)` | lines 45-54 | Mark base cells under fleet cell `v` as occupied by agent `i` in NEXT array. |
| `clear_base_now(i, v)` | lines 56-65 | Clear NOW entries for agent `i` at fleet cell `v`. |
| `clear_base_next(i, v)` | lines 67-76 | Clear NEXT entries for agent `i` at fleet cell `v`. |
| `base_next_free(i, v)` | lines 78-90 | Check if base cells under `v` are free in NEXT array (ignoring self). |
| `check_swap_conflict(i, u_i, v_i, j, u_j, v_j)` | lines 95-129 | Check if agents `i` and `j` performing moves `u→v` swap through overlapping base cells. |

**Key limitation**: No time dimension — all agents are "at time 0". The occupancy bitmaps capture a single snapshot.

### Spatial BFS (`pibt.cpp:291-424`)

- Explores `(cost, depth, cell_index)` — no time coordinate.
- Checks `base_occupied_now[]` to count congestion (`nb` variable).
- Produces first-step → best-endpoint-cost mapping → sorted candidate list of `Vertex*`.
- No reservation table, no swap conflict checking during BFS.
- Congestion penalty (cap 3) and oscillation penalty (+2 per recent revisit in `recent_cells` deque of 10).
- Depth limit: `max(2, cell_size)`.

### funcPIBT (`pibt.cpp:443-618`)

- Iterates `C_next[i]` (single `Vertex*` candidates) at line 488.
- Uses `base_next_free()` per candidate (line ~490-495).
- Swap conflict checked via `check_swap_conflict()` (line ~500-520).
- Blocker identification: scans `base_occupied_now[]` to find who's in the way.
- On failure: clears `base_occupied_next` for agent (rollback via `clear_base_next`).

### set_new_config (`pibt.cpp:141-283`)

- Pre-constrains speed-gated agents (kappa > 0): lines 156-164, 202-221.
- Goal-lock reservation: lines 183-200.
- Agent assignment loop: iterates agents in priority order, calls `funcPIBT()`.
- Extracts `Q_to.positions[i]` directly from funcPIBT assignments.

### What's Missing

The BFS produces `Vertex*` candidates (single cells). Space-time BFS produces `ProposedPath` (timed cell sequences + blocking agents). The entire funcPIBT push logic needs adapting to work with multi-step paths and reservation-based collision checking instead of the `base_occupied_next` bitmap.

---

## 3. Diff Plan

### Architecture Choice: Lightweight Per-Timestep Reservation Table

hetpibt's reservation table is designed for a standalone solver where reservations accumulate across the entire solution. In het_rt_lacam, PIBT is called by LaCAM's high-level search to generate one configuration (one timestep transition).

**Approach**: Add a per-call reservation table inside `set_new_config()`. Created fresh each call, seeded with current config positions at `t=0`, filled as agents are sequentially assigned. This gives the BFS time-awareness within one config generation without persisting state across LaCAM iterations.

---

### File Changes

#### A. New file: `het_rt_lacam/het_rt_lacam/include/st_reservation.hpp`

Lightweight reservation table for intra-timestep use. Simplified from hetpibt's `ReservationTable` — no `traj_log`, no `agent_cells` reverse index (not needed for ephemeral table).

**Structs:**
```cpp
struct ProposedPath {
  std::vector<int> path;             // fleet cell indices the agent would traverse
  std::vector<int> blocking_agents;  // agents that must move out of the way
};

struct STReservation {
  // primary index: pack_key(time, base_cell) -> vector of agent IDs
  std::unordered_map<uint64_t, std::vector<int>> st_map;

  // agent endpoint tracking
  struct AgentEndpoint {
    int fleet_id;
    int cell_index;
    int end_time;
  };
  std::unordered_map<int, AgentEndpoint> agent_last;

  // spatial index for parked agents: base_cell -> set of agent IDs
  std::unordered_map<int, std::vector<int>> parked_at_cell;

  const Instance* ins;  // for to_base_cells() and fleet info

  STReservation(const Instance* _ins);

  // reserve a path for an agent (force-reserve, no collision check)
  void reserve_path(int agent_id, int fleet_id, int start_time,
                    const std::vector<int>& positions);

  // reserve agent staying in place from start_time to end_time
  void reserve_stay(int agent_id, int fleet_id, int cell_index,
                    int start_time, int end_time);

  // check if moving from→to at time collides with existing reservation
  // checks vertex conflict at (to, t+1) AND swap conflict
  bool move_collides(int fleet_id, int from, int to, int time,
                     int agent_id) const;

  // check if cell is occupied at time by anyone other than exclude_agent
  bool is_occupied(int fleet_id, int cell_index, int time,
                   int exclude_agent = -1) const;

  // get agents occupying a cell at time (for blocker identification)
  std::vector<int> get_occupants(int fleet_id, int cell_index,
                                 int time) const;

private:
  void insert_cell(int agent_id, int fleet_id, int cell_index, int time);
  void update_parked_index(int agent_id, const AgentEndpoint* old_ep,
                           const AgentEndpoint* new_ep);
};
```

**Key differences from hetpibt's `ReservationTable`**:
- References `Instance*` instead of `CollisionChecker*` / `Fleets*` (het_rt_lacam uses `Instance` directly for `to_base_cells()`).
- No `agent_cells` reverse index (no need for trajectory removal in ephemeral table).
- No `traj_log` (visualization handled differently in het_rt_lacam).
- Added `reserve_stay()` convenience for goal-locked and speed-gated agents.

#### B. New file: `het_rt_lacam/het_rt_lacam/src/st_reservation.cpp`

Implementation of the above. Port core logic from `third_party/hetpibt/hetpibt/src/reservation.cpp`:
- `insert_cell()`: project fleet cell to base cells, insert into `st_map` (from hetpibt lines ~58-90).
- `move_collides()`: vertex + swap check (from hetpibt lines 102-144).
- `is_occupied()`: cell occupancy check (from hetpibt lines ~146-180).
- `reserve_path()`: insert trajectory into st_map, update `agent_last` (from hetpibt `reserve()` lines 187-214).
- `get_occupants()`: return agent IDs at cell (from hetpibt lines ~158-180).

#### C. Modify: `het_rt_lacam/het_rt_lacam/include/pibt.hpp`

Current class definition: lines 17-70.

Changes:
- Add `#include "st_reservation.hpp"`.
- Add member: `STReservation* st_res_;` (non-owning pointer, set per `set_new_config()` call).
- Change `bfs_get_candidates()` (line 60) signature:
  ```cpp
  // OLD:
  void bfs_get_candidates(int i, Vertex* start, Vertex* goal);
  // NEW:
  std::vector<ProposedPath> st_bfs_get_candidates(int i, Vertex* start, Vertex* goal);
  ```
- Keep `C_next` member (line 32) for now — populated from `ProposedPath` first-steps for backwards compatibility during incremental port.

#### D. Modify: `het_rt_lacam/het_rt_lacam/src/pibt.cpp`

Three functions change:

##### D1. `bfs_get_candidates()` → `st_bfs_get_candidates()` (lines 291-424)

| Aspect | Current (spatial) | New (space-time) |
|--------|-------------------|-------------------|
| BFS state | `(cost, depth, cell)` | `(cost, num_blocking, time, cell)` |
| Visited set | `unordered_map<int,int> best_cost` | `unordered_set<uint64_t>` keyed on `pack_key(time, cell)` |
| Edge pruning | `base_occupied_now[]` congestion count | `st_res_->move_collides()` |
| Occupancy count | `base_occupied_now[bc]` | `st_res_->get_occupants()` |
| Output | Populates `C_next[i]` with `Vertex*` | Returns `vector<ProposedPath>` |
| Depth limit | `max(2, cell_size)` | Same (keep existing depth logic) |
| Congestion penalty | Cap 3, add to cost | Same (count via `is_occupied()` instead of bitmap) |
| Oscillation penalty | +2 per recent revisit (`recent_cells`) | Unchanged |

The BFS should reconstruct full paths (cell sequences from start to endpoint) for each candidate, grouped by first-step vertex as before but now including the full path. Blocking agents are collected via `st_res_->get_occupants()` for cells where `move_collides()` returned true due to parked agents.

##### D2. `funcPIBT()` (lines 443-618)

| Aspect | Current | New |
|--------|---------|-----|
| Candidate loop | `for (auto *u : C_next[i])` (line 488) — single `Vertex*` | `for (auto& pp : candidates)` — `ProposedPath` |
| Collision check | `base_next_free(i, u)` + `check_swap_conflict()` | `st_res_->move_collides()` for first step; full path checked via reservation table |
| Blocker identification | Scan `base_occupied_now[]` under target cell | Use `pp.blocking_agents` from BFS output |
| On success | `mark_base_next(i, u)`, set `Q_to.positions[i] = u` | `st_res_->reserve_path(i, fleet, 0, pp.path)`, set `Q_to.positions[i] = fleet_vertex(pp.path[1])` |
| On failure/backtrack | `clear_base_next(i, ...)` | No reservation undo (see Backtracking section) |

Goal-lock guard (lines 451-455) and kappa check (lines 457-473) stay unchanged — they short-circuit before BFS.

##### D3. `set_new_config()` (lines 141-283)

Changes at the top of the function:
```cpp
// Create ephemeral reservation table
STReservation reservation(ins);
st_res_ = &reservation;
```

Seed with `Q_from` positions at `t=0`:
```cpp
for (int i = 0; i < N; ++i) {
  if (Q_from.positions[i] == nullptr) continue;
  reservation.reserve_stay(i, ins->agent_fleet[i],
                           Q_from.positions[i]->index, 0, 0);
}
```

Pre-reserve goal-locked agents (lines 183-200): change from `mark_base_next()` to `reservation.reserve_stay(i, fleet, cell, 0, BFS_DEPTH)`.

Pre-reserve speed-gated agents (lines 202-221): change from `mark_base_next()` to `reservation.reserve_stay(i, fleet, cell, 0, BFS_DEPTH)`.

After agent assignment loop, extract `Q_to` from reservation table:
```cpp
Q_to.positions[i] = /* agent's position at t=1 from reserved path */
```

At function exit, `st_res_ = nullptr;` (stack-allocated reservation table is destroyed).

#### E. Add to: `het_rt_lacam/het_rt_lacam/include/utils.hpp`

Add `pack_key` (from `third_party/hetpibt/hetpibt/include/utils.hpp:55-59`):
```cpp
inline uint64_t pack_key(int a, int b) {
  return (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
         static_cast<uint64_t>(static_cast<uint32_t>(b));
}
```

#### F. Modify: `het_rt_lacam/CMakeLists.txt`

Add `het_rt_lacam/src/st_reservation.cpp` to the source list.

---

### RT Outer Loop Interaction

**None.** The reservation table is ephemeral — created and destroyed inside each `set_new_config()` call.

- No interaction with `solve_one_step()` / `search()` / `advance()`.
- The RT loop calls `set_new_config()` indirectly through LaCAM search; each call gets a fresh reservation table.
- No state carries over between LaCAM iterations or RT steps.

---

### Backtracking Approach: Option 3 — Match hetpibt (No Undo)

Three options were considered:

1. **Snapshot/restore**: Copy the reservation table before each candidate attempt, restore on failure. Simple but O(table_size) per backtrack.
2. **Incremental undo**: Track entries added during cascade, remove on failure. More efficient but more code.
3. **Match hetpibt**: Don't undo reservations on push failure. Rely on `in_chain` to prevent re-processing and `move_collides()` to reject conflicting paths.

**Chosen: Option 3.** hetpibt doesn't undo reservations on push failure — it relies on `in_chain` to prevent re-processing and `try_reserve()` / `move_collides()` to reject conflicting paths. This works because:
- Agents are processed top-level one at a time.
- A failed push chain means the agent stays put (its "stay" is naturally conflict-free since it was already there).
- The reservation table is per-call anyway, so stale entries from failed pushes don't persist across iterations.
- funcPIBT already has undo logic for `Q_to.positions` and `base_occupied_next` — the reservation-based approach replaces `base_occupied_next` undo with a no-op.

---

### What Stays the Same

| Component | Reason |
|-----------|--------|
| `base_occupied_now[]` / `base_occupied_next[]` | Keep as-is for `set_new_config` pre-constraint steps (goal-lock detection, speed-gate pre-reservation). Reservation table supplements but doesn't replace the bitmap for these simple checks. Can be removed in a follow-up cleanup. |
| `check_swap_conflict()` (`pibt.cpp:95-129`) | Replaced by `move_collides()` inside BFS, but kept as fallback in funcPIBT's candidate loop during incremental port. Can be removed once fully wired. |
| Oscillation history (`recent_cells`) | Unchanged, fed into BFS same as before. |
| Stuck-counter acceleration | Unchanged, operates at HNode level (`hnode.cpp`). |
| Goal locking logic | Same semantics, different mechanism (reservation table instead of bitmap). |
| LaCAM high-level search | No changes to `search()`, `rewrite()`, constraint tree, or HNode. |
| RT-LaCAM (`solve_one_step`, `advance`, `extract_next_step`) | No changes. |

---

## 4. Implementation Sequence

### Task A: `st_reservation.hpp/cpp` + Unit Test (Independent)

**Scope**: New files only — no modifications to existing code.

**Deliverables**:
1. `het_rt_lacam/het_rt_lacam/include/st_reservation.hpp` — struct + API declarations.
2. `het_rt_lacam/het_rt_lacam/src/st_reservation.cpp` — implementation ported from hetpibt's `reservation.cpp`.
3. Unit test in `het_rt_lacam/tests/` — test `reserve_path`, `reserve_stay`, `move_collides`, `is_occupied`, `get_occupants` with single-fleet and cross-fleet scenarios.
4. Update `CMakeLists.txt` to include new source file.

**Dependencies**: None. Can be developed and tested independently.

**Key porting decisions**:
- Use `Instance::to_base_cells()` instead of hetpibt's `CollisionChecker::fleet_to_base()` for cross-fleet cell projection.
- Constructor takes `const Instance*` instead of `(const CollisionChecker*, const Fleets*)`.
- Skip `agent_cells` reverse index and `traj_log` — not needed for ephemeral table.

### Task B: `st_bfs_get_candidates()` Replacing Spatial BFS

**Scope**: Modify `pibt.hpp` (new method signature) and `pibt.cpp` (new BFS function).

**Deliverables**:
1. Add `st_bfs_get_candidates()` method to `HetPIBT` struct.
2. Implement space-time BFS in `pibt.cpp` — same structure as current `bfs_get_candidates()` (lines 291-424) but with time dimension and reservation table queries.
3. Keep old `bfs_get_candidates()` temporarily for A/B comparison.
4. Add `pack_key()` to `utils.hpp`.

**Dependencies**: Task A (needs `STReservation`).

**Validation**: Run `bfs_get_candidates()` and `st_bfs_get_candidates()` side-by-side on het_bench scen.0 — verify ST-BFS produces valid candidates and first-step vertices are a subset of spatial BFS candidates.

### Task C: funcPIBT + set_new_config Wiring

**Scope**: Full integration — modify `funcPIBT()` and `set_new_config()` to use reservation table and ST-BFS.

**Deliverables**:
1. Modify `set_new_config()`: create `STReservation`, seed with `Q_from`, pre-reserve goal-locked and speed-gated agents.
2. Modify `funcPIBT()`: use `st_bfs_get_candidates()` output, iterate `ProposedPath` candidates, use `reserve_path()` on success.
3. Remove old `bfs_get_candidates()` and `C_next` member (if no longer used).
4. Optionally remove `base_occupied_next[]` and related functions if fully replaced.

**Dependencies**: Tasks A and B.

**Validation**:
1. All 16 existing unit tests pass.
2. het_bench scen.0: SOC matches or improves vs current.
3. Full 190-scenario benchmark: solve rate >= 94/190 (no regressions), SOC ratios closer to hetpibt.
4. RT mode: 0 regressions vs current RT results (98/190).

---

## Source File Cross-Reference

| File | Role | Key Lines |
|------|------|-----------|
| `third_party/hetpibt/hetpibt/include/reservation.hpp` | Reference reservation table | 45-110 (struct), 78 (try_reserve), 85-87 (move_collides) |
| `third_party/hetpibt/hetpibt/src/reservation.cpp` | Reference implementation | 102-144 (move_collides), 187-214 (reserve), 216-261 (try_reserve) |
| `third_party/hetpibt/hetpibt/include/planner.hpp` | Reference BFS API | 29-32 (ProposedPath), 57-59 (get_next_locations) |
| `third_party/hetpibt/hetpibt/src/planner.cpp` | Reference BFS + push | 131-292 (BFS), 295-436 (push_agent), 495-511 (per-agent loop) |
| `third_party/hetpibt/hetpibt/include/utils.hpp` | pack_key source | 55-59 |
| `het_rt_lacam/het_rt_lacam/include/pibt.hpp` | Target class | 17-70 (HetPIBT), 28-29 (bitmaps), 32 (C_next), 60 (bfs decl) |
| `het_rt_lacam/het_rt_lacam/src/pibt.cpp` | Target implementation | 36-90 (mark/clear/free), 95-129 (swap check), 141-283 (set_new_config), 291-424 (bfs), 443-618 (funcPIBT) |
| `het_rt_lacam/het_rt_lacam/include/utils.hpp` | Target for pack_key | (add at end) |
