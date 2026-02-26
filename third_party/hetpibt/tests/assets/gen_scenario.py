"""Generate a het_bench scenario for corridor30.map with proper spacing.

Places agents largest-first, maintaining a set of occupied base-grid cells.
Designs cross-fleet conflicts by routing agents through the central bottleneck.
"""
import random

random.seed(42)

MAP_FILE = "corridor30.map"
BASE_W, BASE_H = 30, 30

# Load map to know passable cells
grid = []
with open(MAP_FILE) as f:
    in_map = False
    for line in f:
        line = line.strip()
        if in_map:
            grid.append(line)
        elif line == "map":
            in_map = True

passable = set()
for r in range(BASE_H):
    for c in range(BASE_W):
        if grid[r][c] == '.':
            passable.add((c, r))


def fleet_grid_size(cs):
    return BASE_W // cs, BASE_H // cs


def fleet_to_base_cells(fx, fy, cs):
    """Return set of (bx, by) base cells for fleet cell (fx, fy)."""
    cells = set()
    for dy in range(cs):
        for dx in range(cs):
            cells.add((fx * cs + dx, fy * cs + dy))
    return cells


def is_fleet_cell_passable(fx, fy, cs):
    """A fleet cell is passable only if ALL underlying base cells are passable."""
    return fleet_to_base_cells(fx, fy, cs).issubset(passable)


def passable_fleet_cells(cs):
    """Get all passable fleet cells for a given cell_size."""
    fw, fh = fleet_grid_size(cs)
    cells = []
    for fy in range(fh):
        for fx in range(fw):
            if is_fleet_cell_passable(fx, fy, cs):
                cells.append((fx, fy))
    return cells


# Fleet definitions
fleets = [
    {"id": 0, "cs": 1, "v": 1.0, "n_agents": 10},
    {"id": 1, "cs": 2, "v": 0.5, "n_agents": 6},
    {"id": 2, "cs": 3, "v": 0.3, "n_agents": 3},
]

# Map regions (in base grid coords) for placement strategy
# NW room: base (3-8, 3-8)
# NE room: base (21-26, 3-8)
# SW room: base (3-8, 21-26)
# SE room: base (21-26, 21-26)
# Top dead end: base (12-17, 3-8)
# Bottom dead end: base (12-17, 21-26)
# Top corridor: base (6-23, 9-11)
# Bottom corridor: base (6-23, 18-20)
# Central bottleneck: base (12-17, 12-17)


def in_region(bx, by, x0, y0, x1, y1):
    return x0 <= bx <= x1 and y0 <= by <= y1


def fleet_cell_in_region(fx, fy, cs, x0, y0, x1, y1):
    """Check if ALL base cells of fleet cell are within region."""
    for bx, by in fleet_to_base_cells(fx, fy, cs):
        if not in_region(bx, by, x0, y0, x1, y1):
            return False
    return True


def find_cells_in_region(cs, x0, y0, x1, y1):
    """Find passable fleet cells fully within a base-grid region."""
    result = []
    for fx, fy in passable_fleet_cells(cs):
        if fleet_cell_in_region(fx, fy, cs, x0, y0, x1, y1):
            result.append((fx, fy))
    return result


# Occupied base cells tracker
occupied_base = set()
agents = []
agent_id = 0


def place_agent(fleet_id, cs, vel, start_fx, start_fy, goal_fx, goal_fy):
    global agent_id, occupied_base
    start_base = fleet_to_base_cells(start_fx, start_fy, cs)
    if start_base & occupied_base:
        return False
    if not is_fleet_cell_passable(start_fx, start_fy, cs):
        return False
    if not is_fleet_cell_passable(goal_fx, goal_fy, cs):
        return False
    occupied_base |= start_base
    fw, fh = fleet_grid_size(cs)
    agents.append({
        "id": agent_id,
        "fleet": fleet_id,
        "cs": cs,
        "v": vel,
        "sx": start_fx * cs,
        "sy": start_fy * cs,
        "gx": goal_fx * cs,
        "gy": goal_fy * cs,
        "gw": fw,
        "gh": fh,
    })
    agent_id += 1
    return True


# === Place Fleet 2 (cs=3) first — 3 large AGVs ===
# Agent crossing NW -> SE through bottleneck
nw_cs3 = find_cells_in_region(3, 3, 3, 8, 8)
se_cs3 = find_cells_in_region(3, 21, 21, 26, 26)
ne_cs3 = find_cells_in_region(3, 21, 3, 26, 8)
sw_cs3 = find_cells_in_region(3, 3, 21, 8, 26)

print(f"cs=3 cells: NW={nw_cs3}, NE={ne_cs3}, SW={sw_cs3}, SE={se_cs3}")

# Agent 0: NW -> SE
place_agent(2, 3, 0.3, nw_cs3[0][0], nw_cs3[0][1], se_cs3[0][0], se_cs3[0][1])
# Agent 1: NE -> SW
place_agent(2, 3, 0.3, ne_cs3[0][0], ne_cs3[0][1], sw_cs3[0][0], sw_cs3[0][1])
# Agent 2: SW -> NE
place_agent(2, 3, 0.3, sw_cs3[0][0], sw_cs3[0][1], ne_cs3[0][0], ne_cs3[0][1])

# === Place Fleet 1 (cs=2) — 6 medium robots ===
nw_cs2 = find_cells_in_region(2, 3, 3, 8, 8)
ne_cs2 = find_cells_in_region(2, 21, 3, 26, 8)
sw_cs2 = find_cells_in_region(2, 3, 21, 8, 26)
se_cs2 = find_cells_in_region(2, 21, 21, 26, 26)
top_dead_cs2 = find_cells_in_region(2, 12, 3, 17, 8)
bot_dead_cs2 = find_cells_in_region(2, 12, 21, 17, 26)

print(f"cs=2 cells available: NW={len(nw_cs2)}, NE={len(ne_cs2)}, "
      f"SW={len(sw_cs2)}, SE={len(se_cs2)}, "
      f"top_dead={len(top_dead_cs2)}, bot_dead={len(bot_dead_cs2)}")

# Place cs=2 in rooms, goals in opposite rooms
cs2_pairs = [
    (nw_cs2, se_cs2, "NW->SE"),
    (se_cs2, nw_cs2, "SE->NW"),
    (ne_cs2, sw_cs2, "NE->SW"),
    (sw_cs2, ne_cs2, "SW->NE"),
    (top_dead_cs2, bot_dead_cs2, "TopD->BotD"),
    (bot_dead_cs2, top_dead_cs2, "BotD->TopD"),
]

for starts, goals, label in cs2_pairs:
    placed = False
    for s in starts:
        for g in goals:
            if place_agent(1, 2, 0.5, s[0], s[1], g[0], g[1]):
                print(f"  cs=2 {label}: ({s[0]},{s[1]}) -> ({g[0]},{g[1]})")
                placed = True
                break
        if placed:
            break
    if not placed:
        print(f"  WARNING: could not place cs=2 {label}")

# === Place Fleet 0 (cs=1) — 10 small fast robots ===
nw_cs1 = find_cells_in_region(1, 3, 3, 8, 8)
ne_cs1 = find_cells_in_region(1, 21, 3, 26, 8)
sw_cs1 = find_cells_in_region(1, 3, 21, 8, 26)
se_cs1 = find_cells_in_region(1, 21, 21, 26, 26)
corr_top_cs1 = find_cells_in_region(1, 6, 9, 23, 11)
corr_bot_cs1 = find_cells_in_region(1, 6, 18, 23, 20)
center_cs1 = find_cells_in_region(1, 12, 12, 17, 17)

print(f"cs=1 cells available: NW={len(nw_cs1)}, NE={len(ne_cs1)}, "
      f"SW={len(sw_cs1)}, SE={len(se_cs1)}, "
      f"corr_top={len(corr_top_cs1)}, corr_bot={len(corr_bot_cs1)}, "
      f"center={len(center_cs1)}")

cs1_pairs = [
    (nw_cs1, se_cs1, "NW->SE"),
    (nw_cs1, ne_cs1, "NW->NE"),
    (se_cs1, nw_cs1, "SE->NW"),
    (se_cs1, sw_cs1, "SE->SW"),
    (ne_cs1, sw_cs1, "NE->SW"),
    (ne_cs1, se_cs1, "NE->SE"),
    (sw_cs1, ne_cs1, "SW->NE"),
    (sw_cs1, nw_cs1, "SW->NW"),
    (corr_top_cs1, corr_bot_cs1, "TopC->BotC"),
    (center_cs1, corr_bot_cs1, "Ctr->BotC"),
]

for starts, goals, label in cs1_pairs:
    placed = False
    for s in starts:
        for g in goals:
            if s == g:
                continue
            if place_agent(0, 1, 1.0, s[0], s[1], g[0], g[1]):
                print(f"  cs=1 {label}: ({s[0]},{s[1]}) -> ({g[0]},{g[1]})")
                placed = True
                break
        if placed:
            break
    if not placed:
        print(f"  WARNING: could not place cs=1 {label}")

# Write scenario file
with open("corridor30.scen", "w") as f:
    for a in agents:
        f.write(f"{a['id']} {a['fleet']} {a['cs']} {a['v']} "
                f"{a['sx']} {a['sy']} {a['gx']} {a['gy']} "
                f"{a['gw']} {a['gh']}\n")

print(f"\nGenerated {len(agents)} agents in corridor30.scen")
for fl in fleets:
    n = sum(1 for a in agents if a['fleet'] == fl['id'])
    print(f"  Fleet {fl['id']}: cs={fl['cs']} v={fl['v']} agents={n}")
