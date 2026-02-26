#!/usr/bin/env python3
"""Diagnose fleet graph connectivity for different cell sizes.

For each cell_size, enumerates all valid positions (sliding window),
builds the connectivity graph, finds connected components, and
optionally renders them on the map.
"""
import sys
from collections import deque


def load_map(path):
    with open(path) as f:
        lines = f.readlines()
    grid_start = 0
    width = height = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if line == "map":
            grid_start = i + 1
            break
        parts = line.split()
        if len(parts) == 2:
            if parts[0] == "width":
                width = int(parts[1])
            elif parts[0] == "height":
                height = int(parts[1])
    grid = []
    for i in range(grid_start, grid_start + height):
        row = lines[i].rstrip("\n")
        grid.append([c in ".GS" for c in row])
    return width, height, grid


def find_fleet_positions(w, h, grid, cs):
    """Find all valid fleet positions for cell_size cs.
    Non-overlapping tiling: fleet cell (fx, fy) covers base cells
    [fx*cs, (fx+1)*cs) x [fy*cs, (fy+1)*cs)."""
    fw = w // cs
    fh = h // cs
    if fw <= 0 or fh <= 0:
        return fw, fh, set()

    valid = set()
    for fy in range(fh):
        for fx in range(fw):
            ok = True
            for dy in range(cs):
                for dx in range(cs):
                    bx = fx * cs + dx
                    by = fy * cs + dy
                    if by >= h or bx >= w or not grid[by][bx]:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                valid.add((fx, fy))
    return fw, fh, valid


def find_components(valid):
    """Find connected components via BFS on 4-connected grid."""
    visited = set()
    components = []
    for pos in sorted(valid):
        if pos in visited:
            continue
        comp = []
        queue = deque([pos])
        visited.add(pos)
        while queue:
            x, y = queue.popleft()
            comp.append((x, y))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in valid and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        components.append(comp)
    return components


def render_fleet_on_map(w, h, grid, cs, valid, components):
    """Render fleet positions on the base map using component colors."""
    # assign a letter per component (A, B, C, ...)
    cell_comp = {}
    for i, comp in enumerate(components):
        letter = chr(ord('A') + i % 26)
        for (fx, fy) in comp:
            cell_comp[(fx, fy)] = letter

    # build output grid
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            if grid[y][x]:
                row.append('.')
            else:
                row.append('@')
        out.append(row)

    # mark fleet positions: color the top-left cell of each valid position
    for (fx, fy) in valid:
        letter = cell_comp[(fx, fy)]
        out[fy][fx] = letter

    return ["".join(row) for row in out]


def analyze_doorways(w, h, grid):
    """Find doorway cells: passable cells with <=2 passable neighbors
    that connect two larger open areas."""
    doorways = []
    for y in range(h):
        for x in range(w):
            if not grid[y][x]:
                continue
            nbrs = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and grid[ny][nx]:
                    nbrs += 1
            if nbrs <= 2:
                # check if it's a true doorway (has wall on both sides)
                h_wall = ((x == 0 or not grid[y][x-1]) or (x == w-1 or not grid[y][x+1]))
                v_wall = ((y == 0 or not grid[y-1][x]) or (y == h-1 or not grid[y+1][x]))
                if h_wall or v_wall:
                    doorways.append((x, y, nbrs))
    return doorways


def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_fleet_graph.py <map_file> [max_cell_size]")
        sys.exit(1)

    map_file = sys.argv[1]
    max_cs = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    w, h, grid = load_map(map_file)
    total_passable = sum(sum(row) for row in grid)
    print(f"Map: {w}x{h}, passable cells: {total_passable}")

    # analyze doorways
    doorways = analyze_doorways(w, h, grid)
    print(f"\nDoorway cells (<=2 neighbors with wall on at least one side): {len(doorways)}")
    # find the minimum width of any corridor
    # check horizontal corridors: passable cells in a row bounded by walls above and below
    h_corridors = []
    for y in range(1, h - 1):
        for x in range(w):
            if grid[y][x] and not grid[y-1][x] and not grid[y+1][x]:
                h_corridors.append((x, y))
    v_corridors = []
    for y in range(h):
        for x in range(1, w - 1):
            if grid[y][x] and not grid[y][x-1] and not grid[y][x+1]:
                v_corridors.append((x, y))
    print(f"  Horizontal 1-wide corridors: {len(h_corridors)} cells")
    print(f"  Vertical 1-wide corridors: {len(v_corridors)} cells")

    for cs in range(1, max_cs + 1):
        print(f"\n{'='*60}")
        print(f"Cell size = {cs}")
        print(f"{'='*60}")

        fw, fh, valid = find_fleet_positions(w, h, grid, cs)
        print(f"Fleet grid dimensions: {fw}x{fh}")
        print(f"Valid fleet positions: {len(valid)}")

        if not valid:
            print("  NO VALID POSITIONS")
            continue

        components = find_components(valid)
        print(f"Connected components: {len(components)}")

        # sort by size descending
        components.sort(key=len, reverse=True)
        for i, comp in enumerate(components[:10]):
            # bounding box
            xs = [p[0] for p in comp]
            ys = [p[1] for p in comp]
            print(f"  Component {chr(ord('A')+i)}: {len(comp)} positions, "
                  f"bbox=({min(xs)},{min(ys)})-({max(xs)},{max(ys)})")

        if len(components) > 10:
            remaining = sum(len(c) for c in components[10:])
            print(f"  ... {len(components)-10} more components ({remaining} positions total)")

        # render fleet map (only for cs >= 2)
        if cs >= 2:
            rendered = render_fleet_on_map(w, h, grid, cs, valid, components)
            print(f"\nFleet graph visualization (top-left corner of each {cs}x{cs} position):")
            print(f"Letters = component ID, '.' = passable (no fleet pos), '@' = wall")
            for row in rendered:
                print(f"  {row}")


if __name__ == "__main__":
    sys.exit(main() or 0)
