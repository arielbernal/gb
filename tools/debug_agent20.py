#!/usr/bin/env python3
"""Debug agent 20 in corridor_speed_154_00."""
import re
import sys
from collections import deque

RESULT = "E:/gb/experiments/results/cs154_00_result.txt"
MAP_FILE = "E:/gb/benchmarks/maps/corridor_speed_154.map"

# ── Parse result file ──
fleets = {}
agent_fleets = []
starts = []
goals = []
trajectories = {}
in_solution = False

with open(RESULT) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if in_solution:
            m = re.match(r"^(\d+):(\d+):(.*)", line)
            if not m:
                continue
            aid = int(m.group(1))
            entries = re.findall(r"\((-?\d+),(-?\d+)\)@(\d+)", m.group(3))
            traj = {}
            for x, y, t in entries:
                traj[int(t)] = (int(x), int(y))
            trajectories[aid] = traj
            continue
        if line == "solution":
            in_solution = True
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key == "fleets":
            for part in value.split(";"):
                fields = part.split(":")
                if len(fields) >= 5:
                    fid = int(fields[0])
                    fleets[fid] = {"cell_size": int(fields[1]), "velocity": float(fields[2]),
                                   "grid_w": int(fields[3]), "grid_h": int(fields[4])}
        elif key == "agent_fleet":
            agent_fleets = [int(x) for x in value.split(",")]
        elif key == "starts":
            pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
            starts = [(int(x), int(y)) for x, y in pairs]
        elif key == "goals":
            pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
            goals = [(int(x), int(y)) for x, y in pairs]

# ── Parse map ──
grid = []
reading = False
with open(MAP_FILE) as f:
    for line in f:
        line = line.rstrip()
        if line == "map":
            reading = True
            continue
        if reading and line:
            grid.append([c in ('@', 'T') for c in line])

H = len(grid)
W = len(grid[0]) if grid else 0

def get_cs(aid):
    fid = agent_fleets[aid]
    return fleets[fid]["cell_size"]

def get_pos_at(aid, t):
    """Get fleet-grid position at timestep t."""
    traj = trajectories[aid]
    if t in traj:
        return traj[t]
    # Find most recent position <= t
    times = sorted(traj.keys())
    pos = times[0]
    for tt in times:
        if tt <= t:
            pos = tt
        else:
            break
    return traj[pos]

def base_footprint(fx, fy, cs):
    """Return set of base cells covered by fleet cell (fx, fy) with cell_size cs."""
    cells = set()
    for dy in range(cs):
        for dx in range(cs):
            cells.add((fx * cs + dx, fy * cs + dy))
    return cells

# ── 1. BFS shortest path for agent 20 on cs=1 grid ──
print("=" * 70)
print("1. BFS SHORTEST PATH FOR AGENT 20 (cs=1)")
print("=" * 70)

a20_cs = get_cs(20)
a20_start = starts[20]
a20_goal = goals[20]
print(f"   Agent 20: cs={a20_cs}, fleet_id={agent_fleets[20]}")
print(f"   Start: fleet ({a20_start[0]}, {a20_start[1]}) = base ({a20_start[0]*a20_cs}, {a20_start[1]*a20_cs})")
print(f"   Goal:  fleet ({a20_goal[0]}, {a20_goal[1]}) = base ({a20_goal[0]*a20_cs}, {a20_goal[1]*a20_cs})")

# BFS on base grid (cs=1 means fleet grid = base grid)
sx, sy = a20_start
gx, gy = a20_goal
queue = deque([(sx, sy, 0)])
visited = {(sx, sy)}
parent = {}
found = False

while queue:
    x, y, d = queue.popleft()
    if x == gx and y == gy:
        found = True
        # Reconstruct path
        path = [(x, y)]
        while (x, y) != (sx, sy):
            x, y = parent[(x, y)]
            path.append((x, y))
        path.reverse()
        print(f"   BFS path EXISTS, length = {len(path)-1} steps")
        print(f"   Path (first 10): {path[:10]}...")
        print(f"   Path (last 10):  ...{path[-10:]}")
        break
    for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and not grid[ny][nx] and (nx, ny) not in visited:
            visited.add((nx, ny))
            parent[(nx, ny)] = (x, y)
            queue.append((nx, ny, d + 1))

if not found:
    print("   BFS path DOES NOT EXIST!")

# ── 2. Analyze agent 20's trajectory — find where it loops ──
print()
print("=" * 70)
print("2. AGENT 20 TRAJECTORY ANALYSIS")
print("=" * 70)

traj20 = trajectories[20]
times_sorted = sorted(traj20.keys())
positions = [(t, traj20[t]) for t in times_sorted]

# Deduplicate consecutive same positions
unique_moves = [positions[0]]
for i in range(1, len(positions)):
    if positions[i][1] != positions[i-1][1]:
        unique_moves.append(positions[i])

print(f"   Total timesteps: {times_sorted[-1]}")
print(f"   Unique positions visited: {len(set(p for _, p in positions))}")
print(f"   Actual moves (position changes): {len(unique_moves)-1}")

# Find leftward progress (goal is at x=2, start at x=127)
min_x = min(p[0] for _, p in positions)
max_x = max(p[0] for _, p in positions)
min_y = min(p[1] for _, p in positions)
max_y = max(p[1] for _, p in positions)
print(f"   X range: [{min_x}, {max_x}]  (needs to reach x={a20_goal[0]})")
print(f"   Y range: [{min_y}, {max_y}]")

# Find when it stops making leftward progress
best_x = positions[0][1][0]
last_progress_t = 0
for t, (x, y) in positions:
    if x < best_x:
        best_x = x
        last_progress_t = t

print(f"   Best leftward x reached: {best_x} at t={last_progress_t}")
print(f"   Goal x: {a20_goal[0]}")
print(f"   Distance remaining: {best_x - a20_goal[0]} cells")

# Show trajectory around where progress stops
print(f"\n   Trajectory near t={last_progress_t}:")
for t, pos in positions:
    if last_progress_t - 5 <= t <= last_progress_t + 20:
        print(f"     t={t:4d}: ({pos[0]:3d}, {pos[1]:3d})")

# Detect the repeating cycle
print(f"\n   Trajectory from t=10 to t=50 (looking for cycle):")
for t, pos in positions:
    if 10 <= t <= 50:
        print(f"     t={t:4d}: ({pos[0]:3d}, {pos[1]:3d})")

# ── 3. What blocks agent 20? Check agents 2 (cs=11) and 7 (cs=7) ──
print()
print("=" * 70)
print("3. BLOCKING ANALYSIS AT KEY TIMESTEPS")
print("=" * 70)

# Agent 20 seems stuck around x=121-122. Check what's at x < 121.
# Let's check multiple timesteps in the stuck region

for check_t in [10, 20, 30, 40, 50]:
    print(f"\n   --- Timestep t={check_t} ---")

    a20_pos = get_pos_at(20, check_t)
    print(f"   Agent 20 (cs=1): fleet ({a20_pos[0]}, {a20_pos[1]}) = base ({a20_pos[0]}, {a20_pos[1]})")

    # Get all agents' positions and footprints at this timestep
    all_occupied = {}  # base_cell -> (agent_id, cs)
    for aid in range(len(agent_fleets)):
        cs = get_cs(aid)
        pos = get_pos_at(aid, check_t)
        for cell in base_footprint(pos[0], pos[1], cs):
            all_occupied[cell] = (aid, cs)

    # Check what's around agent 20
    a20_bx, a20_by = a20_pos  # cs=1, so fleet = base

    # Check the cells to the LEFT of agent 20 (direction toward goal x=2)
    print(f"   Cells to the LEFT of agent 20 (toward goal):")
    for dx in range(-3, 1):
        for dy in range(-2, 3):
            cx, cy = a20_bx + dx, a20_by + dy
            if (cx, cy) in all_occupied:
                aid, cs = all_occupied[(cx, cy)]
                if aid != 20:
                    pos = get_pos_at(aid, check_t)
                    print(f"     base ({cx}, {cy}) occupied by agent {aid} (cs={cs}) at fleet ({pos[0]}, {pos[1]})")

    # Specifically check agents 2 and 7
    for aid in [2, 7]:
        cs = get_cs(aid)
        pos = get_pos_at(aid, check_t)
        fp = base_footprint(pos[0], pos[1], cs)
        print(f"   Agent {aid} (cs={cs}): fleet ({pos[0]}, {pos[1]}) -> base footprint rows [{pos[1]*cs}, {pos[1]*cs+cs}) cols [{pos[0]*cs}, {pos[0]*cs+cs})")

# ── 4. Corridor analysis — does the blocking span the full width? ──
print()
print("=" * 70)
print("4. CORRIDOR WIDTH ANALYSIS — DO AGENTS 2+7 SPAN THE CORRIDOR?")
print("=" * 70)

# Agent 20 is in corridor 4 (rows 110-131, width=22) based on start y=127
# Find which corridor agent 20 is in
print(f"   Agent 20 base position: ({a20_start[0]}, {a20_start[1]})")

# Read corridor info from the map
corr_rows = []
in_corr = False
corr_start = None
for r in range(H):
    row_free = not grid[r][W//2]  # check middle column
    if row_free and not in_corr:
        in_corr = True
        corr_start = r
    elif not row_free and in_corr:
        corr_rows.append((corr_start, r))
        in_corr = False
if in_corr:
    corr_rows.append((corr_start, H))

print(f"   Corridors: {corr_rows}")

# Find agent 20's corridor
a20_corr = None
for sr, er in corr_rows:
    if sr <= a20_start[1] < er:
        a20_corr = (sr, er)
        break
print(f"   Agent 20 is in corridor rows [{a20_corr[0]}, {a20_corr[1]}) width={a20_corr[1]-a20_corr[0]}")

# At t=10, check ALL agents in the same corridor and their column ranges
check_t = 10
print(f"\n   All agents in agent 20's corridor at t={check_t}:")
agents_in_corridor = []
for aid in range(len(agent_fleets)):
    cs = get_cs(aid)
    pos = get_pos_at(aid, check_t)
    by = pos[1] * cs
    by_end = by + cs
    if by >= a20_corr[0] and by_end <= a20_corr[1]:
        bx = pos[0] * cs
        agents_in_corridor.append((aid, cs, pos, bx, by, bx + cs, by_end))
        print(f"     Agent {aid:2d} (cs={cs:2d}): fleet ({pos[0]:3d}, {pos[1]:3d}) -> base cols [{bx}, {bx+cs}) rows [{by}, {by_end})")

# Sort by base x to show the left-to-right arrangement
agents_in_corridor.sort(key=lambda a: a[3])
print(f"\n   Sorted by column (left to right) at t={check_t}:")
for aid, cs, pos, bx, by, bx_end, by_end in agents_in_corridor:
    direction = "->" if goals[aid][0] > starts[aid][0] else "<-"
    at_goal = pos == goals[aid]
    status = " (AT GOAL)" if at_goal else ""
    print(f"     Agent {aid:2d} (cs={cs:2d}) cols [{bx:3d}, {bx_end:3d}) rows [{by:3d}, {by_end:3d}) {direction}{status}")

# Check if the corridor cross-section is fully blocked at agent 20's x
print(f"\n   Cross-section analysis at agent 20's column (x~{a20_start[0]}):")
for check_x in range(a20_start[0] - 5, a20_start[0] + 2):
    blocked_rows = set()
    blockers = []
    for aid, cs, pos, bx, by, bx_end, by_end in agents_in_corridor:
        if aid == 20:
            continue
        if bx <= check_x < bx_end:
            for r in range(by, by_end):
                blocked_rows.add(r)
            blockers.append(f"a{aid}(cs={cs})")
    corr_width = a20_corr[1] - a20_corr[0]
    blocked_count = len([r for r in blocked_rows if a20_corr[0] <= r < a20_corr[1]])
    pct = 100 * blocked_count / corr_width
    blocker_str = "+".join(blockers) if blockers else "none"
    print(f"     col {check_x}: {blocked_count}/{corr_width} rows blocked ({pct:.0f}%) by {blocker_str}")

# ── 5. Agent 20's candidate moves at the stuck timestep ──
print()
print("=" * 70)
print("5. AGENT 20 CANDIDATE MOVES AT STUCK TIMESTEP")
print("=" * 70)

for check_t in [10, 11, 12]:
    print(f"\n   --- t={check_t} ---")
    a20_pos = get_pos_at(20, check_t)
    print(f"   Agent 20 at ({a20_pos[0]}, {a20_pos[1]})")

    # All occupied base cells at this timestep (by other agents)
    occupied = {}
    for aid in range(len(agent_fleets)):
        if aid == 20:
            continue
        cs = get_cs(aid)
        pos = get_pos_at(aid, check_t)
        for cell in base_footprint(pos[0], pos[1], cs):
            occupied[cell] = aid

    # Candidate moves for cs=1: stay, up, down, left, right
    moves = {"stay": (0, 0), "left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
    for name, (dx, dy) in moves.items():
        nx, ny = a20_pos[0] + dx, a20_pos[1] + dy
        if nx < 0 or nx >= W or ny < 0 or ny >= H:
            print(f"     {name:5s} -> ({nx:3d}, {ny:3d}): REJECTED (out of bounds)")
            continue
        if grid[ny][nx]:
            print(f"     {name:5s} -> ({nx:3d}, {ny:3d}): REJECTED (wall)")
            continue
        if (nx, ny) in occupied:
            blocker = occupied[(nx, ny)]
            bcs = get_cs(blocker)
            bpos = get_pos_at(blocker, check_t)
            print(f"     {name:5s} -> ({nx:3d}, {ny:3d}): BLOCKED by agent {blocker} (cs={bcs}) at fleet ({bpos[0]}, {bpos[1]})")
        else:
            print(f"     {name:5s} -> ({nx:3d}, {ny:3d}): FREE")
