"""
Visualizer for LaCAM multi-agent pathfinding solutions.
Reads the map file and result.txt, then animates agent movements.

Usage:
    python visualize.py
    python visualize.py --result build/result.txt --speed 200
"""

import argparse
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.animation import FuncAnimation
from pathlib import Path


def load_result(result_path):
    """Parse the LaCAM result.txt file."""
    meta = {}
    solution = []

    with open(result_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Solution timestep lines: "0:(x,y),(x,y),..."
            ts_match = re.match(r"^(\d+):", line)
            if ts_match:
                _, positions_str = line.split(":", 1)
                positions = re.findall(r"\((\d+),(\d+)\)", positions_str)
                positions = [(int(x), int(y)) for x, y in positions]
                solution.append(positions)
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            if key == "solution":
                continue
            elif key == "starts":
                meta["starts"] = re.findall(r"\((\d+),(\d+)\)", value)
                meta["starts"] = [(int(x), int(y)) for x, y in meta["starts"]]
            elif key == "goals":
                meta["goals"] = re.findall(r"\((\d+),(\d+)\)", value)
                meta["goals"] = [(int(x), int(y)) for x, y in meta["goals"]]
            else:
                meta[key] = value

    return meta, solution


def load_map(map_path):
    """Parse a .map file into a 2D grid (True = obstacle)."""
    grid = []
    reading_map = False

    with open(map_path, "r") as f:
        for line in f:
            line = line.strip()
            if line == "map":
                reading_map = True
                continue
            if reading_map and line:
                row = [c in ("@", "T") for c in line]
                grid.append(row)

    return np.array(grid, dtype=bool)


def main():
    parser = argparse.ArgumentParser(description="Visualize LaCAM solution")
    parser.add_argument(
        "--result", default="build/result.txt", help="Path to result.txt"
    )
    parser.add_argument("--map", default=None, help="Path to .map file (auto-detected from result)")
    parser.add_argument(
        "--speed", type=int, default=150, help="ms per frame (lower = faster)"
    )
    args = parser.parse_args()

    # Load result
    result_path = Path(args.result)
    if not result_path.exists():
        print(f"Error: {result_path} not found. Run the solver first.")
        return

    meta, solution = load_result(result_path)

    if not solution:
        print("No solution found in result file.")
        return

    # Load map
    map_path = args.map
    if map_path is None:
        # Try to find map from meta or common locations
        map_file = meta.get("map_file", "")
        candidates = [
            Path(map_file),
            Path("assets") / map_file,
            Path("assets") / Path(map_file).name,
        ]
        for c in candidates:
            if c.exists():
                map_path = str(c)
                break

    if map_path is None or not Path(map_path).exists():
        print(f"Error: Could not find map file. Use --map to specify.")
        return

    grid = load_map(map_path)
    height, width = grid.shape
    n_agents = len(solution[0])
    n_steps = len(solution)

    print(f"Map: {width}x{height}, Agents: {n_agents}, Timesteps: {n_steps}")
    print(f"Solved: {meta.get('solved', '?')}, Makespan: {meta.get('makespan', '?')}")

    # --- Set up the plot ---
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    # Draw grid
    map_display = np.ones((height, width, 3))  # white
    map_display[grid] = [0.2, 0.2, 0.25]  # dark obstacles
    map_display[~grid] = [0.92, 0.92, 0.95]  # light open space

    ax.imshow(map_display, origin="upper", extent=(-0.5, width - 0.5, height - 0.5, -0.5))

    # Grid lines
    for x in range(width + 1):
        ax.axvline(x - 0.5, color="#ccc", linewidth=0.3, alpha=0.5)
    for y in range(height + 1):
        ax.axhline(y - 0.5, color="#ccc", linewidth=0.3, alpha=0.5)

    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(height - 0.5, -0.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    # Generate distinct colors for agents
    cmap = plt.cm.get_cmap("tab20", max(n_agents, 20))
    colors = [cmap(i % 20) for i in range(n_agents)]

    # Draw goal markers (X marks)
    goals = meta.get("goals", solution[-1] if solution else [])
    for i, (gx, gy) in enumerate(goals):
        ax.plot(gx, gy, "x", color=colors[i], markersize=6, markeredgewidth=2, alpha=0.5)

    # Agent circles
    agent_circles = []
    for i in range(n_agents):
        circle = plt.Circle((0, 0), 0.35, color=colors[i], ec="black", linewidth=0.5, zorder=5)
        ax.add_patch(circle)
        agent_circles.append(circle)

    # Title
    title = ax.set_title(f"t = 0 / {n_steps - 1}", color="white", fontsize=14, fontweight="bold")

    def update(frame):
        t = frame
        for i, (x, y) in enumerate(solution[t]):
            agent_circles[i].center = (x, y)
            # Highlight agents that reached their goal
            if goals and (x, y) == goals[i]:
                agent_circles[i].set_edgecolor("#00ff88")
                agent_circles[i].set_linewidth(2)
            else:
                agent_circles[i].set_edgecolor("black")
                agent_circles[i].set_linewidth(0.5)
        title.set_text(f"t = {t} / {n_steps - 1}")
        return agent_circles + [title]

    # Initialize positions
    update(0)

    ani = FuncAnimation(
        fig, update, frames=n_steps, interval=args.speed, blit=True, repeat=True
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
