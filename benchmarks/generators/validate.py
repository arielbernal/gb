#!/usr/bin/env python3
"""Validate a benchmark .map + .scen pair.

Checks:
  1. All start positions in bounds and on free cells (NxN footprint)
  2. All goal positions in bounds and on free cells (NxN footprint)
  3. Wall-overlap check: explicit per-cell wall character detection
  4. Fleet grid alignment: all coords divisible by cell_size
  5. No two agents' start footprints overlap
  6. No two agents' goal footprints overlap
  7. Each agent's goal is BFS-reachable from start (treating agent as NxN block)

Usage:
    python validate.py --map ../maps/bottleneck_64.map --scen ../scenarios/bottleneck_64.scen
"""
import argparse
from collections import deque


def load_map(map_path):
    grid = []
    width = height = 0
    reading = False
    with open(map_path) as f:
        for line in f:
            line = line.rstrip('\n\r')
            if line == "map":
                reading = True
                continue
            if reading and line:
                grid.append(line)
            elif 'width' in line:
                width = int(line.split()[1])
            elif 'height' in line:
                height = int(line.split()[1])
    return grid, width, height


def load_scen(scen_path):
    agents = []
    with open(scen_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            cs = int(parts[0])
            sx, sy = int(parts[1]), int(parts[2])
            gx, gy = int(parts[3]), int(parts[4])
            agents.append((cs, sx, sy, gx, gy))
    return agents


FREE_CHARS = {'.', 'G'}  # passable terrain characters


def is_free(grid, x, y, cs, width, height):
    """Check if NxN footprint at (x, y) is all free and in bounds."""
    if x < 0 or y < 0 or x + cs > width or y + cs > height:
        return False
    for dy in range(cs):
        for dx in range(cs):
            if grid[y + dy][x + dx] not in FREE_CHARS:
                return False
    return True


def footprint(x, y, cs):
    """Return set of (col, row) for NxN block at (x, y)."""
    cells = set()
    for dy in range(cs):
        for dx in range(cs):
            cells.add((x + dx, y + dy))
    return cells


def bfs_reachable(grid, sx, sy, gx, gy, cs, width, height):
    """BFS check: can NxN block move from (sx,sy) to (gx,gy)?
    Movement: 4-directional, 1 cell at a time."""
    if (sx, sy) == (gx, gy):
        return True

    visited = set()
    visited.add((sx, sy))
    queue = deque([(sx, sy)])

    while queue:
        x, y = queue.popleft()
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in visited:
                continue
            if not is_free(grid, nx, ny, cs, width, height):
                continue
            if (nx, ny) == (gx, gy):
                return True
            visited.add((nx, ny))
            queue.append((nx, ny))

    return False


def validate(map_path, scen_path):
    grid, width, height = load_map(map_path)
    agents = load_scen(scen_path)

    print(f"Map: {map_path} ({width}x{height})")
    print(f"Scen: {scen_path} ({len(agents)} agents)")
    print()

    all_ok = True

    # Check 1: Start positions valid
    print("=== Check 1: Start positions valid ===")
    for i, (cs, sx, sy, gx, gy) in enumerate(agents):
        if not is_free(grid, sx, sy, cs, width, height):
            print(f"  FAIL: agent {i} cs={cs} start ({sx},{sy}) footprint not all free")
            # Show which cells are blocked
            for dy in range(cs):
                for dx in range(cs):
                    cx, cy = sx + dx, sy + dy
                    if cx >= width or cy >= height:
                        print(f"    ({cx},{cy}) OUT OF BOUNDS")
                    elif grid[cy][cx] != '.':
                        print(f"    ({cx},{cy}) = '{grid[cy][cx]}' (wall)")
            all_ok = False
    if all_ok:
        print("  PASS")

    # Check 2: Goal positions valid
    check2_ok = True
    print("\n=== Check 2: Goal positions valid ===")
    for i, (cs, sx, sy, gx, gy) in enumerate(agents):
        if not is_free(grid, gx, gy, cs, width, height):
            print(f"  FAIL: agent {i} cs={cs} goal ({gx},{gy}) footprint not all free")
            for dy in range(cs):
                for dx in range(cs):
                    cx, cy = gx + dx, gy + dy
                    if cx >= width or cy >= height:
                        print(f"    ({cx},{cy}) OUT OF BOUNDS")
                    elif grid[cy][cx] != '.':
                        print(f"    ({cx},{cy}) = '{grid[cy][cx]}' (wall)")
            check2_ok = False
            all_ok = False
    if check2_ok:
        print("  PASS")

    # Check 3: Explicit wall-overlap check (per-cell)
    check3_ok = True
    print("\n=== Check 3: Wall-overlap check (explicit per-cell) ===")
    for i, (cs, sx, sy, gx, gy) in enumerate(agents):
        for label, px, py in [("start", sx, sy), ("goal", gx, gy)]:
            if px < 0 or py < 0 or px + cs > width or py + cs > height:
                continue  # already caught by checks 1/2
            for dy in range(cs):
                for dx in range(cs):
                    bx, by = px + dx, py + dy
                    ch = grid[by][bx]
                    if ch not in FREE_CHARS:
                        print(f"  FAIL: agent {i} cs={cs} {label} ({px},{py}) "
                              f"footprint overlaps wall at ({bx},{by}) = '{ch}'")
                        check3_ok = False
                        all_ok = False
    if check3_ok:
        print("  PASS")

    # Check 4: Fleet grid alignment
    check4_ok = True
    print("\n=== Check 4: Fleet grid alignment (coords % cell_size == 0) ===")
    for i, (cs, sx, sy, gx, gy) in enumerate(agents):
        for label, px, py in [("start", sx, sy), ("goal", gx, gy)]:
            if px % cs != 0:
                print(f"  FAIL: agent {i} cs={cs} {label} x={px} not aligned ({px}%{cs}={px%cs})")
                check4_ok = False
                all_ok = False
            if py % cs != 0:
                print(f"  FAIL: agent {i} cs={cs} {label} y={py} not aligned ({py}%{cs}={py%cs})")
                check4_ok = False
                all_ok = False
    if check4_ok:
        print("  PASS")

    # Check 5: No start overlap
    check5_ok = True
    print("\n=== Check 5: No start footprint overlaps ===")
    for i in range(len(agents)):
        fp_i = footprint(agents[i][1], agents[i][2], agents[i][0])
        for j in range(i + 1, len(agents)):
            fp_j = footprint(agents[j][1], agents[j][2], agents[j][0])
            overlap = fp_i & fp_j
            if overlap:
                print(f"  FAIL: agent {i} cs={agents[i][0]} and agent {j} cs={agents[j][0]} "
                      f"starts overlap at {len(overlap)} cells")
                check5_ok = False
                all_ok = False
    if check5_ok:
        print("  PASS")

    # Check 6: No goal overlap
    check6_ok = True
    print("\n=== Check 6: No goal footprint overlaps ===")
    for i in range(len(agents)):
        fp_i = footprint(agents[i][3], agents[i][4], agents[i][0])
        for j in range(i + 1, len(agents)):
            fp_j = footprint(agents[j][3], agents[j][4], agents[j][0])
            overlap = fp_i & fp_j
            if overlap:
                print(f"  FAIL: agent {i} cs={agents[i][0]} and agent {j} cs={agents[j][0]} "
                      f"goals overlap at {len(overlap)} cells")
                check6_ok = False
                all_ok = False
    if check6_ok:
        print("  PASS")

    # Check 7: BFS reachability
    print("\n=== Check 7: BFS reachability (NxN block) ===")
    check7_ok = True
    for i, (cs, sx, sy, gx, gy) in enumerate(agents):
        reachable = bfs_reachable(grid, sx, sy, gx, gy, cs, width, height)
        if not reachable:
            print(f"  FAIL: agent {i} cs={cs} CANNOT reach goal ({gx},{gy}) from start ({sx},{sy})")
            check7_ok = False
            all_ok = False
        else:
            print(f"  OK:   agent {i} cs={cs} ({sx},{sy}) -> ({gx},{gy})")
    if check7_ok:
        print("  PASS")

    # Summary
    print(f"\n{'='*40}")
    if all_ok:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Validate benchmark map + scenario")
    parser.add_argument("--map", required=True)
    parser.add_argument("--scen", required=True)
    args = parser.parse_args()
    ok = validate(args.map, args.scen)
    exit(0 if ok else 1)


if __name__ == "__main__":
    main()
