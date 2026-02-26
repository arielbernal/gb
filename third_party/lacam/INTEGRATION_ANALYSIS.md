# Het-RT-LaCAM Integration Analysis

Deep analysis of `lacam3` (Engineering LaCAM\*, Okumura AAMAS 2024) for
integrating heterogeneous multi-footprint, multi-speed PIBT (HetPIBT).

Repo: `gb/lacam3/` — cloned from https://github.com/Kei18/lacam3
Original lacam (lacam1) is in `gb/lacam/` — simpler but same core algorithm.

Real-Time LaCAM (Liang et al., SoCS 2025, arXiv:2504.06091) has **no public
code**. Its design is described in Section 3 below.

---

## Table of Contents

1. [Data Structures](#1-data-structures)
2. [DFS Flow — Main Search Loop](#2-dfs-flow)
3. [PIBT Interface — Configuration Generator](#3-pibt-interface)
4. [Collision Checking](#4-collision-checking)
5. [Real-Time LaCAM Design (Paper-Based)](#5-real-time-lacam)
6. [Integration Points — Where to Modify](#6-integration-points)
7. [lacam3 vs lacam1 Differences](#7-lacam3-vs-lacam1)

---

## 1. Data Structures

### 1.1 Configuration (`Config`)

**File:** `lacam3/include/graph.hpp:17`

```cpp
using Config = std::vector<Vertex*>;  // locations for all agents
```

A configuration is a length-N vector of `Vertex*`, one per agent. This is the
fundamental unit of the high-level search — each node in the DFS tree holds one
Config.

**Integration impact:** For heterogeneous agents, a configuration must also
encode each agent's **speed phase counter** κ_i ∈ {0, ..., cell_size_i - 1}.
Two configs with same positions but different κ values are **distinct** states.

### 1.2 Vertex

**File:** `lacam3/include/graph.hpp:7-15`

```cpp
struct Vertex {
  const int id;     // sequential index in V (0...|V|-1)
  const int index;  // grid index: width * y + x
  const int x;
  const int y;
  std::vector<Vertex*> neighbor;
};
```

- `V` = vector of non-null vertices (passable cells)
- `U` = full grid array indexed by `width*y+x`, with `nullptr` for walls
- `id` is the sequential index into `V`; `index` is the spatial grid position
- Neighbors are the 4-connected adjacent passable cells (no diagonal movement)

**Integration impact:** Each fleet has its own graph with its own cell size.
We need per-fleet `Graph` objects (or a multi-fleet graph structure like our
existing hetpibt design). Vertex `id` must be fleet-specific.

### 1.3 HNode — High-Level Search Node

**File:** `lacam3/include/hnode.hpp:16-38`, `lacam3/src/hnode.cpp`

```cpp
struct HNode {
  static int COUNT;
  const Config C;                    // agent positions
  HNode* parent;                     // backtrack pointer
  std::set<HNode*> neighbor;         // for Dijkstra rewriting (LaCAM*)
  int g, h, f;                       // cost values

  // Low-level search state
  std::vector<float> priorities;     // per-agent priorities
  std::vector<int> order;            // sorted agent ordering
  std::queue<LNode*> search_tree;    // BFS queue of constraint nodes
};
```

Key behaviors:
- **Priority initialization** (`hnode.cpp:30-42`): Root node uses
  `D.get(i, C[i]) / 10000` (distance-to-goal). Non-root uses dynamic priority:
  if agent not at goal, priority += 1; if at goal, fractional part preserved.
- **Agent ordering** (`hnode.cpp:45-47`): Agents sorted descending by priority.
  Higher priority = processed first in PIBT.
- **Search tree**: Queue of `LNode*` — the low-level constraint enumeration.
  Initialized with a single empty constraint (depth=0). The tree is lazily
  expanded one level at a time (see §2).
- **Neighbor set** (`hnode.cpp:24-27`): Bidirectional links for Dijkstra-based
  parent rewriting (the LaCAM* anytime mechanism).

**Integration impact:**
- `Config C` must include κ values → either augment Config or add a parallel
  `std::vector<int> kappa` field.
- Priority computation uses `D.get(i, C[i])` which assumes single-speed BFS
  distance. For heterogeneous agents, distance must account for speed
  (distance / velocity or distance * cell_size).

### 1.4 LNode — Low-Level Search Node (Constraint)

**File:** `lacam3/include/lnode.hpp:9-18`, `lacam3/src/lnode.cpp`

```cpp
struct LNode {
  static int COUNT;
  std::vector<int> who;    // agent indices constrained so far
  Vertices where;          // corresponding vertex assignments
  const int depth;         // how many agents have been constrained
};
```

- Constructed incrementally: `LNode(parent, agent_i, vertex_v)` copies parent's
  `who`/`where` and appends one new (agent, vertex) pair.
- `depth` counts how many agents have been assigned so far (0 = unconstrained).
- The low-level search tree is a **BFS** over these constraint nodes. At each
  step, the front node is popped, and if `depth < N`, children are created for
  agent `order[depth]` × each of its neighbor vertices (+ stay).

**Integration impact:**
- For footprint agents, a constraint may need to specify not just a vertex but
  a *set of base cells* (the footprint). Or, if we keep fleet-specific graphs,
  the constraint is still (agent, fleet_vertex), but collision checking must
  verify footprint-level clearance.
- The constraint could optionally include the κ phase to restrict when an agent
  actually moves vs. waits-in-place.

### 1.5 EXPLORED Set (Closed List)

**File:** `lacam3/src/planner.cpp:59`

```cpp
std::unordered_map<Config, HNode*, ConfigHasher> EXPLORED;
```

**Hash function** (`graph.cpp:105-111`):

```cpp
uint ConfigHasher::operator()(const Config& C) const {
  uint hash = C.size();
  for (auto& v : C) {
    hash ^= v->id + 0x9e3779b9 + (hash << 6) + (hash >> 2);
  }
  return hash;
}
```

Uses boost-style hash combining. Only hashes vertex IDs — no speed phase info.

**Equality check** (`graph.cpp:96-102`):
```cpp
bool is_same_config(const Config& C1, const Config& C2) {
  for (size_t i = 0; i < N; ++i) {
    if (C1[i]->id != C2[i]->id) return false;
  }
  return true;
}
```

**Integration impact (CRITICAL):** Both the hash and equality must include κ
values. Without this, the search would treat (positions, κ=[0,0]) and
(positions, κ=[1,0]) as the same configuration, causing incorrect pruning.

### 1.6 OPEN Stack

**File:** `lacam3/src/planner.cpp:58`

```cpp
std::deque<HNode*> OPEN;
```

In lacam3, OPEN is a `deque` (not a `stack` as in lacam1). New nodes are
pushed to the **front** (`push_front`), and the current node is read from the
**front** (`OPEN.front()`). This gives DFS behavior but allows random access
for the `RANDOM_INSERT_PROB2` randomization (picking a random node from the
deque when exploring after initial solution found).

In lacam1, it was `std::stack<Node*>`.

### 1.7 Agent (lacam1 only)

In lacam1 (`lacam/include/planner.hpp:37-43`):
```cpp
struct Agent {
  const int id;
  Vertex* v_now;
  Vertex* v_next;
};
```

In lacam3, there is no `Agent` struct. The PIBT module uses index-based
tracking with `occupied_now[V_size]` and `occupied_next[V_size]` arrays
(integers, not pointers).

### 1.8 PIBT Instance (lacam3)

**File:** `lacam3/include/pibt.hpp:16-50`

```cpp
struct PIBT {
  const Instance* ins;
  std::mt19937 MT;
  const int N, V_size;
  DistTable* D;
  const int NO_AGENT;                  // = N (sentinel value)
  std::vector<int> occupied_now;       // V_size, maps vertex→agent
  std::vector<int> occupied_next;      // V_size, maps vertex→agent
  std::vector<std::array<Vertex*, 5>> C_next;  // candidates per agent
  std::vector<float> tie_breakers;     // V_size, random tie-breaking
  bool flg_swap;
  Scatter* scatter;
};
```

lacam3 runs **PIBT_NUM** (default: 10) parallel PIBT instances via
Monte-Carlo configuration generation. Each produces a candidate Config; the
one with best f-value (edge_cost + heuristic) is selected.

### 1.9 DistTable — Distance Table

**File:** `lacam3/include/dist_table.hpp`, `lacam3/src/dist_table.cpp`

```cpp
struct DistTable {
  const int K;                            // number of vertices
  std::vector<std::vector<int>> table;    // [agent_id][vertex_id] → distance
  ...
};
```

- In lacam3, distances are computed eagerly using parallel BFS (one thread per
  agent, all from goals).
- In lacam1, distances use lazy BFS (Reverse Resumable A*).
- `D.get(i, v)` returns the shortest-path distance from agent i's goal to
  vertex v (reverse BFS from goal).

**Integration impact:** For heterogeneous agents, each fleet has its own
graph. The distance table needs per-fleet distance computation on the
fleet-specific graph. Distance values should be in terms of **time steps**
(accounting for speed: distance_cells * cell_size / velocity, but since
velocity == 1 cell/step on the fleet graph, it's just the BFS distance on
the fleet graph, times the cell_size for wall-clock equivalence).

---

## 2. DFS Flow — Main Search Loop

**File:** `lacam3/src/planner.cpp:61-158` (`Planner::solve()`)

### 2.1 Initialization

```
H_init = create_highlevel_node(ins->starts, nullptr)
OPEN.push_front(H_init)
set_scatter()    // SUO pre-computation (optional)
set_pibt()       // create PIBT_NUM PIBT instances
```

### 2.2 Main Loop (annotated)

```
while (!OPEN.empty() && !is_expired(deadline)):
    search_iter++

    // [lacam3 only] check refiner pool for completed refinements
    refiner_pool.remove_if(...)  // integrates improved solutions

    H = OPEN.front()              // peek, DO NOT pop

    // [lacam3 only] random diversification after finding initial solution
    if H_goal != nullptr && random < RANDOM_INSERT_PROB2:
        H = random node from OPEN  // or H_init

    // [lacam3 only] pruning: skip if f >= best known goal f
    if H_goal != nullptr && H.f >= H_goal.f:
        OPEN.pop_front()
        continue

    // Goal check (first time only in lacam3, always in lacam1)
    if H_goal == nullptr && is_same_config(H.C, ins.goals):
        H_goal = H
        if !FLG_STAR: break           // lacam1 behavior
        set_refiner()                   // start background refiners
        continue

    // === LOW-LEVEL SEARCH ===
    L = H.get_next_lowlevel_node(MT)  // pop front of search_tree queue
    if L == nullptr:                   // search_tree exhausted
        OPEN.pop_front()               // backtrack!
        continue

    // get_next_lowlevel_node also EXPANDS the tree:
    //   if L.depth < N:
    //     agent_i = order[L.depth]
    //     for each neighbor u of C[agent_i] (shuffled):
    //       search_tree.push(new LNode(L, agent_i, u))

    // === CONFIGURATION GENERATION ===
    Q_to = Config(N, nullptr)
    success = set_new_config(H, L, Q_to)   // PIBT call
    delete L
    if !success: continue

    // === HIGH-LEVEL EXPANSION ===
    iter = EXPLORED.find(Q_to)
    if iter != EXPLORED.end():
        // already explored → rewrite parent pointers (Dijkstra)
        rewrite(H, iter->second)
        OPEN.push_front(iter->second)   // re-add to OPEN
    else:
        // new configuration → create node
        H_new = create_highlevel_node(Q_to, H)
        OPEN.push_front(H_new)
```

### 2.3 Backtracking Mechanism

Backtracking is **implicit** via the DFS structure:
- A node stays in OPEN as long as its `search_tree` has unexplored LNodes.
- When `search_tree` is empty, the node is popped → search returns to its
  parent (which is still deeper in the deque).
- Each LNode represents a different partial constraint assignment. The BFS
  over LNodes enumerates all possible constraint combos for a given HNode.

### 2.4 LaCAM* Rewriting (`Planner::rewrite`)

**File:** `lacam3/src/planner.cpp:250-273`

When edge H_from → H_to is discovered:
1. Add H_to to H_from's neighbor set
2. Run BFS/Dijkstra from H_from through the neighbor graph
3. If a shorter path is found to any node, update g, f, parent
4. If a node's f improves below H_goal's f, re-add to OPEN

This is the anytime mechanism: the search continues after finding the first
solution, gradually improving cost.

### 2.5 Edge Cost

**File:** `lacam3/src/planner.cpp:275-284`

```cpp
int Planner::get_edge_cost(const Config& C1, const Config& C2) {
  auto cost = 0;
  for (uint i = 0; i < N; ++i) {
    if (C1[i] != ins->goals[i] || C2[i] != ins->goals[i]) cost += 1;
  }
  return cost;
}
```

Cost is **sum-of-loss**: each agent contributes 1 unless it was at its goal in
both C1 and C2 (already arrived and staying). This is the cumulative transition
cost that LaCAM* optimizes.

**Integration impact:** For heterogeneous agents, an agent with κ_i > 0 is
"in transit" even if staying at the same fleet cell (it's executing a
multi-step move). The cost function should still count it as moving.

---

## 3. PIBT Interface — Configuration Generator

### 3.1 Entry Point

**File:** `lacam3/src/planner.cpp:208-248` (`Planner::set_new_config`)

```cpp
bool Planner::set_new_config(HNode* H, LNode* L, Config& Q_to)
```

**Inputs:**
- `H`: current high-level node (provides `H->C` = current config, `H->order`)
- `L`: low-level constraint node (provides `L->who[]`, `L->where[]`, `L->depth`)
- `Q_to`: output config (pre-allocated, initially all nullptr)

**Flow:**
1. Set hard constraints from LNode: `Q_to[L->who[d]] = L->where[d]` for each
   constrained agent.
2. Run PIBT_NUM parallel PIBT instances (Monte-Carlo), each respecting the
   constraints and filling in unconstrained agents.
3. Pick the PIBT result with lowest f-value (edge_cost + heuristic).
4. Copy winning config to `Q_to`.

**Returns:** `true` if at least one PIBT succeeded, `false` if all failed.

### 3.2 PIBT::set_new_config

**File:** `lacam3/src/pibt.cpp:22-64`

```cpp
bool PIBT::set_new_config(const Config& Q_from, Config& Q_to,
                           const std::vector<int>& order)
```

**Inputs:**
- `Q_from`: current configuration (where agents are now)
- `Q_to`: target configuration being built (some slots pre-filled by constraints)
- `order`: priority ordering of agents

**Flow:**
1. **Setup occupancy** (`pibt.cpp:27-46`):
   - Set `occupied_now[Q_from[i]->id] = i` for all agents
   - For pre-constrained agents (Q_to[i] != nullptr):
     - Check vertex collision: if `occupied_next[Q_to[i]->id] != NO_AGENT` → fail
     - Check swap collision: if agent j is at Q_to[i] and Q_to[j] == Q_from[i] → fail
     - Set `occupied_next[Q_to[i]->id] = i`

2. **Run PIBT** (`pibt.cpp:48-55`):
   - For each unconstrained agent in priority order:
     - Call `funcPIBT(i, Q_from, Q_to)` — recursive PIBT with priority inheritance

3. **Cleanup** (`pibt.cpp:57-61`): Clear occupancy arrays.

### 3.3 funcPIBT — Core PIBT Logic

**File:** `lacam3/src/pibt.cpp:66-147`

```cpp
bool PIBT::funcPIBT(const int i, const Config& Q_from, Config& Q_to)
```

**Algorithm:**
1. Get candidate next vertices: neighbors of Q_from[i], plus stay-in-place.
2. Sort by: scatter priority (if SUO enabled) → distance-to-goal + tie_breaker.
3. Check swap heuristic (optional, `flg_swap`).
4. For each candidate u in sorted order:
   - **Vertex conflict check** (`pibt.cpp:122`):
     `if (occupied_next[u->id] != NO_AGENT) continue;`
   - **Swap conflict check** (`pibt.cpp:127`):
     `if (j != NO_AGENT && Q_to[j] == Q_from[i]) continue;`
     (agent j currently at u has already been assigned to go where i is now)
   - **Reserve** (`pibt.cpp:130-131`):
     `occupied_next[u->id] = i; Q_to[i] = u;`
   - **Priority inheritance** (`pibt.cpp:134-135`):
     If vertex u is occupied by agent j who hasn't moved yet, recursively call
     `funcPIBT(j, ...)` to push j out of the way.
   - If recursive call succeeds → return true.
   - If fails → undo reservation, try next candidate.
5. **Fallback** (`pibt.cpp:144-146`): Stay in place.
   `Q_to[i] = Q_from[i]; return false;`

### 3.4 Constraint Passing: How LNode Constraints Reach PIBT

The constraint flow is:

```
HNode::get_next_lowlevel_node(MT)  →  LNode L
    ↓
Planner::set_new_config(H, L, Q_to)
    ↓
    for d in 0..L->depth:
        Q_to[L->who[d]] = L->where[d]     // pre-fill constrained agents
    ↓
PIBT::set_new_config(Q_from, Q_to, order)
    ↓
    // Q_to entries that are non-null are treated as hard constraints
    // Only agents with Q_to[i] == nullptr enter funcPIBT
```

Constraints are **positive**: "agent i MUST go to vertex v". They are NOT
avoidance constraints. The constraint tree enumerates all possible assignments
for agents in priority order, and PIBT fills in the rest.

---

## 4. Collision Checking

### 4.1 In PIBT (during configuration generation)

Collision checking happens in two places within `PIBT::set_new_config`:

**A) Constraint validation** (`pibt.cpp:27-46`):
```cpp
// vertex collision: two constrained agents assigned same vertex
if (occupied_next[Q_to[i]->id] != NO_AGENT) → fail

// swap collision: constrained agent i goes to j's current pos,
// while j is constrained to go to i's current pos
auto j = occupied_now[Q_to[i]->id];
if (j != NO_AGENT && j != i && Q_to[j] == Q_from[i]) → fail
```

**B) PIBT inner loop** (`pibt.cpp:118-141`):
```cpp
// vertex conflict
if (occupied_next[u->id] != NO_AGENT) continue;

// swap conflict (edge conflict)
const auto j = occupied_now[u->id];
if (j != NO_AGENT && Q_to[j] == Q_from[i]) continue;
```

### 4.2 Summary of Collision Types

| Type | Check Location | Mechanism |
|------|---------------|-----------|
| Vertex conflict (same timestep) | `occupied_next[v->id]` | Array indexed by vertex id; if non-empty, vertex is taken |
| Swap/edge conflict | `occupied_now[u] && Q_to[j] == Q_from[i]` | Agent j at target u is going to agent i's current position |
| **No footprint checks** | — | Only point-agent collision is checked |

### 4.3 In Post-Processing (solution validation)

**File:** `lacam3/src/post_processing.cpp:6-55`

```cpp
// vertex conflicts: v_j_to == v_i_to
// swap conflicts:   v_j_to == v_i_from && v_j_from == v_i_to
```

O(N²) pairwise check per timestep. Point-agent only.

### 4.4 CollisionTable (used in Scatter/Refiner, not main search)

**File:** `lacam3/include/collision_table.hpp`, `lacam3/src/collision_table.cpp`

```cpp
struct CollisionTable {
  std::vector<std::vector<std::vector<int>>> body;  // [vertex][time][agents]
  std::vector<std::vector<int>> body_last;           // [vertex][last_timesteps]
  int collision_cnt;
};
```

Tracks vertex/edge/goal collisions over time for the refiner. Only used in
SUO (Scatter) and SIPP refinement, **not** in the main LaCAM search.

### 4.5 What Needs to Change for Footprint Collision Checking

Currently, collision checking is a simple array lookup: `occupied_next[v->id]`.
For footprint-based agents:

1. **An agent occupies multiple base cells** — its footprint is
   `[fx*cs, (fx+1)*cs) × [fy*cs, (fy+1)*cs)` on the base grid.

2. **Two agents from different fleets collide if their footprints overlap** on
   the base grid, not just if they're at the same vertex.

3. **The `occupied_now`/`occupied_next` arrays can't be per-vertex anymore.**
   Options:
   - (a) Maintain a **base-grid occupancy bitmap** — `occupied_base[base_x][base_y]`.
     When agent i moves to fleet cell (fx, fy), mark all base cells in its
     footprint. Check for overlap before reserving.
   - (b) Pre-compute **cross-fleet conflict tables** — which (fleet_a_cell,
     fleet_b_cell) pairs overlap. This is what our existing hetpibt does.

4. **Edge/swap conflicts also become footprint-based** — not just point swaps
   but any base-cell overlap during the transition.

---

## 5. Real-Time LaCAM (Paper-Based Analysis)

**Paper:** Liang et al., "Real-Time LaCAM", arXiv:2504.06091, SoCS 2025.
**No public code available.**

### 5.1 Core Idea

Instead of running LaCAM's DFS to completion before executing, RT-LaCAM:

1. **Time-bounded search**: Run the DFS for a fixed time budget (e.g., 1ms).
2. **Execute**: Apply the first action of the current best partial plan.
3. **Reroot**: Shift the search tree root to the new configuration.
4. **Continue**: Resume DFS from where it stopped.

### 5.2 Key Mechanisms

**Rerooting**: After executing config C₀ → C₁:
- C₁ becomes the new root
- The edge C₀→C₁ is reversed in the search tree
- All nodes reachable from C₁ remain in OPEN/EXPLORED

**Revisitation prevention**: To avoid cycles:
- Maintain a **visited set** of configurations the system has physically
  executed (not just explored in the search)
- When generating successors, skip configurations in the visited set
- This is different from EXPLORED — EXPLORED prevents re-creation of search
  nodes, while visited prevents re-execution of physical moves

**Completeness**: The paper proves that RT-LaCAM preserves LaCAM's
completeness — it will eventually explore the entire configuration space.

### 5.3 Integration Implications

For Het-RT-LaCAM:
- The **visited set** must include κ values (speed phase counters), since
  (positions, κ=[0,0]) and (positions, κ=[1,0]) are different states that
  the system might revisit.
- Rerooting requires updating κ values: after executing one step, each agent's
  κ advances by 1 (mod cell_size), and agents with κ=0 actually move while
  others stay in place.
- The time-bounded search budget interacts with the speed model: faster agents
  might need more search iterations to plan multiple moves during the time
  that a slow agent takes one step.

---

## 6. Integration Points — Where to Modify

### 6.1 Configuration Struct — Add Speed Phase Counters

**What:** Each agent i has κ_i ∈ {0, ..., cell_size_i - 1}. When κ_i = 0,
the agent can move; otherwise it must stay in place (its internal "sub-step").

**Where to modify:**

**Option A: Augmented Config type**

```
// New in graph.hpp
struct HetConfig {
  Config positions;          // fleet-specific vertex per agent
  std::vector<int> kappa;    // speed phase counter per agent
};
```

Affects:
- `lacam3/include/graph.hpp` — new type definition
- `lacam3/include/hnode.hpp:19` — `HNode::C` type changes
- `lacam3/src/planner.cpp` everywhere `Config` is used
- `lacam3/include/instance.hpp:13-14` — starts/goals become HetConfig

**Option B: Parallel κ vector in HNode**

Keep Config as `vector<Vertex*>`, add `std::vector<int> kappa` to HNode.
Less invasive but requires threading κ through all functions that use Config.

**Recommendation:** Option A is cleaner. Define `HetConfig` and update the
codebase systematically.

### 6.2 Hash Function — Must Include κ

**File:** `lacam3/src/graph.cpp:105-111`

```cpp
// BEFORE (point agents):
uint ConfigHasher::operator()(const Config& C) const {
  uint hash = C.size();
  for (auto& v : C) {
    hash ^= v->id + 0x9e3779b9 + (hash << 6) + (hash >> 2);
  }
  return hash;
}

// AFTER (heterogeneous):
uint HetConfigHasher::operator()(const HetConfig& C) const {
  uint hash = C.positions.size();
  for (size_t i = 0; i < C.positions.size(); ++i) {
    hash ^= C.positions[i]->id + 0x9e3779b9 + (hash << 6) + (hash >> 2);
    hash ^= C.kappa[i] + 0x9e3779b9 + (hash << 6) + (hash >> 2);
  }
  return hash;
}
```

Also update `is_same_config` (`graph.cpp:96-102`) to compare κ values.

### 6.3 Replace PIBT with HetPIBT

**Where the PIBT call happens:**

`lacam3/src/planner.cpp:219`:
```cpp
auto res = pibts[k]->set_new_config(H->C, Q_cands[k], H->order);
```

This is where we swap in HetPIBT. The interface must match:

```cpp
// Current PIBT interface:
bool PIBT::set_new_config(const Config& Q_from, Config& Q_to,
                           const std::vector<int>& order);

// New HetPIBT interface:
bool HetPIBT::set_new_config(const HetConfig& Q_from, HetConfig& Q_to,
                              const std::vector<int>& order);
```

Key differences in HetPIBT:
- **Speed gating**: If κ_i > 0, agent i MUST stay in place. Only agents with
  κ_i == 0 can potentially move. Q_to.kappa[i] = (Q_from.kappa[i] + 1) %
  cell_size_i.
- **Footprint collision**: Replace `occupied_next[v->id]` with base-grid
  occupancy checking.
- **Fleet-specific graphs**: Each agent moves on its own fleet's graph.

**Files to modify/replace:**
- `lacam3/include/pibt.hpp` — new HetPIBT class
- `lacam3/src/pibt.cpp` — new implementation
- `lacam3/src/planner.cpp:303-308` (`set_pibt()`) — instantiate HetPIBT
- `lacam3/src/planner.cpp:208-248` (`set_new_config`) — call HetPIBT

### 6.4 Constraint Generation — (agent, position, phase) Triples

**Current constraint structure** (`lnode.hpp`):
```cpp
std::vector<int> who;   // agent indices
Vertices where;          // target vertices
```

**Needed:**
```cpp
std::vector<int> who;
Vertices where;
std::vector<int> kappa;  // phase at constraint time
```

But actually, constraints in LaCAM are simpler than this — they just say
"agent i must go to vertex v next step." The κ is implicitly determined:
- If agent i has κ_i > 0 in the current config, it MUST stay in place
  regardless of any constraint (speed gating overrides).
- If agent i has κ_i == 0, it CAN move, and the constraint specifies where.

So the constraint structure might not need κ at all — the speed gating is
enforced in the PIBT configuration generator, not in the constraint tree.

**However**, the constraint tree enumeration (`HNode::get_next_lowlevel_node`)
currently generates children for ALL agents:

```cpp
// hnode.cpp:64-69
if (L->depth < C.size()) {
  auto i = order[L->depth];
  auto cands = C[i]->neighbor;
  cands.push_back(C[i]);  // stay option
  shuffle(cands);
  for (auto u : cands) search_tree.push(new LNode(L, i, u));
}
```

For speed-gated agents (κ_i > 0), the only valid "next location" is the
current location (stay). So the tree should NOT enumerate neighbors for these
agents — just constrain them to stay. This is a significant optimization:
if half the agents are mid-phase, the branching factor drops dramatically.

**Where to modify:**
- `lacam3/src/hnode.cpp:58-72` (`get_next_lowlevel_node`) — skip neighbor
  enumeration for agents with κ > 0, force stay.

### 6.5 Footprint Collision Checking in PIBT

**Current mechanism** (`pibt.cpp`):
- `occupied_now[V_size]`: array indexed by vertex ID → agent index or NO_AGENT
- `occupied_next[V_size]`: same for next step

**New mechanism needed:**

```cpp
// Base grid occupancy (shared across all fleets)
std::vector<std::vector<int>> base_occupied_now;   // [base_y][base_x] → agent
std::vector<std::vector<int>> base_occupied_next;  // same for next step

// For each agent, store its footprint cells for fast clear
std::vector<std::vector<std::pair<int,int>>> agent_footprint_cells;
```

When agent i (fleet f, cell_size cs) is at fleet vertex (fx, fy):
- Its footprint covers base cells `[fx*cs .. (fx+1)*cs) × [fy*cs .. (fy+1)*cs)`
- To check collision: verify all those base cells are unoccupied
- To reserve: mark all those base cells

**Files to modify:**
- `lacam3/src/pibt.cpp:27-46` — constraint validation with footprint checks
- `lacam3/src/pibt.cpp:118-147` — funcPIBT collision checks with footprints
- `lacam3/src/post_processing.cpp:6-55` — solution validation with footprints

### 6.6 Distance Table — Per-Fleet Graphs

**Current:** One graph, one BFS per agent from its goal.

**Needed:** Multiple fleet graphs. Each fleet has its own tiled graph.
Agent i in fleet f uses fleet f's graph for BFS distance.

**Files to modify:**
- `lacam3/include/graph.hpp` — fleet graph construction (tiled from base graph)
- `lacam3/include/dist_table.hpp` — support per-fleet vertex IDs
- `lacam3/src/dist_table.cpp` — BFS on fleet-specific graph

### 6.7 Heuristic

**File:** `lacam3/src/heuristic.cpp:5-10`

```cpp
int Heuristic::get(const Config& Q) {
  auto cost = 0;
  for (size_t i = 0; i < ins->N; ++i) cost += D->get(i, Q[i]);
  return cost;
}
```

Sum of individual distances to goals. For heterogeneous agents, this should
account for speed: `D->get(i, Q[i]) * cell_size_i` (since each fleet-graph
step takes cell_size_i wall-clock steps). Or, if the distance table already
returns wall-clock distance, no change needed.

### 6.8 Instance — Heterogeneous Agent Definitions

**File:** `lacam3/include/instance.hpp`

Add per-agent metadata:
```cpp
struct AgentInfo {
  int fleet_id;
  int cell_size;
  int velocity;  // = 1 cell per cell_size steps
};

struct HetInstance {
  std::vector<Graph*> fleet_graphs;  // one per fleet
  Graph* base_graph;                  // shared base grid
  Config starts;
  Config goals;
  std::vector<AgentInfo> agents;
  uint N;
};
```

### 6.9 For Real-Time LaCAM: Visited Set With Speed Phases

The visited set (configurations physically executed) must use `HetConfig`
including κ values. This prevents the system from physically revisiting the
same (positions, phases) state, which would indicate a cycle.

**Where:** This is new code (RT-LaCAM doesn't exist in lacam3). Would be
added to the `Planner` as:
```cpp
std::unordered_set<HetConfig, HetConfigHasher> visited;
```

Checked during successor generation before adding to OPEN.

---

## 7. lacam3 vs lacam1 Differences

| Feature | lacam1 (`gb/lacam/`) | lacam3 (`gb/lacam3/`) |
|---------|---------------------|----------------------|
| OPEN structure | `std::stack<Node*>` | `std::deque<HNode*>` |
| Agent struct | `struct Agent` with v_now/v_next | No Agent struct; index-based |
| PIBT | Embedded in `Planner::funcPIBT` | Separate `PIBT` class |
| Monte-Carlo PIBT | No (single PIBT run) | Yes (PIBT_NUM=10 parallel) |
| Anytime (LaCAM*) | No | Yes (FLG_STAR, rewrite) |
| Neighbor graph | No | `HNode::neighbor` set for Dijkstra |
| g/h/f values | No | Yes, on HNode |
| Refinement | No | SIPP-based refiner + recursive LaCAM |
| SUO (Scatter) | No | Yes, `Scatter` module |
| Swap technique | No | Yes (`is_swap_required_and_possible`) |
| Multi-threading | No | Yes (PIBT workers, BFS, refiners) |
| Distance table | Lazy BFS | Eager parallel BFS |
| Constraint node | `Constraint` struct | `LNode` struct (same logic) |
| Node naming | `Node`, `Constraint` | `HNode`, `LNode` |
| Vertex | id, index | id, index, x, y |

### Recommendation: Base Integration on lacam3

lacam3 is the right base because:
1. PIBT is already factored out into a separate class (easy to replace)
2. Monte-Carlo configuration generation is more robust
3. Anytime optimization helps with solution quality
4. Multi-threading support already exists
5. Better heuristic support

The modular structure (hnode, lnode, pibt as separate files) makes it easier
to swap components without touching the main planner loop.

---

## Appendix: File-by-File Modification Summary

| File | Modification | Priority |
|------|-------------|----------|
| `graph.hpp/cpp` | Add `HetConfig` type, update hash/equality, fleet graphs | HIGH |
| `hnode.hpp/cpp` | Change `Config C` → `HetConfig C`, speed-gated constraint gen | HIGH |
| `lnode.hpp/cpp` | Possibly add κ to constraints (or keep as-is if speed gating is in PIBT) | LOW |
| `pibt.hpp/cpp` | **Replace entirely** with HetPIBT: footprint collision, speed gating, fleet graphs | HIGH |
| `planner.hpp/cpp` | Update EXPLORED hash to HetConfig, update set_new_config call | HIGH |
| `instance.hpp/cpp` | Add fleet definitions, per-agent metadata, het_bench parser | HIGH |
| `dist_table.hpp/cpp` | Per-fleet BFS distance computation | HIGH |
| `heuristic.hpp/cpp` | Account for speed in heuristic (multiply by cell_size) | MEDIUM |
| `collision_table.hpp/cpp` | Footprint-aware collision tracking (for refiner) | LOW (later) |
| `post_processing.hpp/cpp` | Footprint-aware feasibility check | MEDIUM |
| `refiner.hpp/cpp` | Footprint-aware SIPP refinement | LOW (later) |
| `scatter.hpp/cpp` | Fleet-aware SUO | LOW (later) |
| `sipp.hpp/cpp` | Fleet-aware safe intervals | LOW (later) |
| `metrics.hpp/cpp` | Speed-aware cost metrics | MEDIUM |
| NEW: `rt_lacam.hpp/cpp` | Real-Time incremental execution loop | PHASE 2 |

### Suggested Implementation Order

1. **Phase 1: Core Het-LaCAM** (get it running)
   - `graph.hpp` — HetConfig, fleet graph construction
   - `instance.hpp` — het_bench scenario parser
   - `dist_table.cpp` — per-fleet BFS
   - `pibt.hpp/cpp` — HetPIBT (port from existing hetpibt)
   - `hnode.cpp` — speed-gated constraint enumeration
   - `planner.cpp` — HetConfig hash, PIBT swap
   - `post_processing.cpp` — footprint feasibility check

2. **Phase 2: Real-Time extension**
   - Add visited set with κ
   - Incremental execution loop
   - Tree rerooting

3. **Phase 3: Quality improvements**
   - Footprint-aware refiner/SIPP
   - Fleet-aware SUO scatter
   - Tuning PIBT_NUM, priorities, etc.
