#!/usr/bin/env python3
"""Visualize a benchmark map and scenario.

Displays the map with agent start positions and goals overlaid.
Each fleet gets a distinct color. Start = filled square, Goal = X marker.
Fleet grid overlays shown as dashed lines.

Usage:
    python show_map.py --map ../maps/bottleneck_64.map --scen ../scenarios/bottleneck_64.scen
"""
import argparse
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors


FLEET_COLORS = {
    1:  "#f38ba8",  # pink
    3:  "#89b4fa",  # blue
    7:  "#a6e3a1",  # green
    11: "#fab387",  # orange
}

FLEET_LABELS = {
    1:  "cs=1",
    3:  "cs=3",
    7:  "cs=7",
    11: "cs=11",
}


def load_map(map_path):
    """Parse .map file into a 2D bool grid (True = wall)."""
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
                grid.append([c in ('@', 'T') for c in line])
            elif 'width' in line:
                width = int(line.split()[1])
            elif 'height' in line:
                height = int(line.split()[1])
    return np.array(grid, dtype=bool), width, height


def load_scen(scen_path):
    """Parse .scen file. Format: fleet_cs start_x start_y goal_x goal_y"""
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


def main():
    parser = argparse.ArgumentParser(description="Visualize benchmark map + scenario")
    parser.add_argument("--map", required=True, help="Path to .map file")
    parser.add_argument("--scen", default=None, help="Path to .scen file (optional)")
    parser.add_argument("--fleet-grid", action="store_true",
                        help="Show fleet grid overlays")
    parser.add_argument("--save", default=None,
                        help="Save to PNG instead of showing (e.g. output.png)")
    args = parser.parse_args()

    grid, width, height = load_map(args.map)

    # Build RGB image
    img = np.ones((height, width, 3))
    img[grid] = [0.2, 0.2, 0.25]       # dark walls
    img[~grid] = [0.92, 0.92, 0.95]    # light floor

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    ax.imshow(img, origin="upper",
              extent=(-0.5, width - 0.5, height - 0.5, -0.5))

    # Subtle grid lines
    for x in range(width + 1):
        ax.axvline(x - 0.5, color="#ccc", linewidth=0.15, alpha=0.2)
    for y in range(height + 1):
        ax.axhline(y - 0.5, color="#ccc", linewidth=0.15, alpha=0.2)

    # Fleet grid overlays
    if args.fleet_grid:
        for cs, color in sorted(FLEET_COLORS.items()):
            if cs == 1:
                continue
            fw = width // cs
            fh = height // cs
            for fx in range(fw + 1):
                ax.axvline(fx * cs - 0.5, color=color, linewidth=0.5,
                           alpha=0.3, linestyle='--')
            for fy in range(fh + 1):
                ax.axhline(fy * cs - 0.5, color=color, linewidth=0.5,
                           alpha=0.3, linestyle='--')

    # Draw agents from scenario
    legend_entries = {}
    if args.scen:
        agents = load_scen(args.scen)

        for i, (cs, sx, sy, gx, gy) in enumerate(agents):
            color = FLEET_COLORS.get(cs, "#ffffff")

            # Start: filled rectangle showing footprint
            rect = mpatches.Rectangle(
                (sx - 0.5, sy - 0.5), cs, cs,
                linewidth=1.5, edgecolor=color, facecolor=color,
                alpha=0.6, zorder=4)
            ax.add_patch(rect)
            # Agent ID label at start
            ax.text(sx + cs / 2 - 0.5, sy + cs / 2 - 0.5, str(i),
                    color="black", fontsize=max(5, min(10, 4 + cs)),
                    ha="center", va="center", fontweight="bold", zorder=5)

            # Goal: hollow rectangle with X
            goal_rect = mpatches.Rectangle(
                (gx - 0.5, gy - 0.5), cs, cs,
                linewidth=2, edgecolor=color, facecolor='none',
                alpha=0.8, linestyle='--', zorder=3)
            ax.add_patch(goal_rect)
            # X marker at goal center
            gcx = gx + cs / 2 - 0.5
            gcy = gy + cs / 2 - 0.5
            ms = max(4, cs * 2)
            ax.plot(gcx, gcy, 'x', color=color, markersize=ms,
                    markeredgewidth=max(1, cs * 0.5), alpha=0.7, zorder=3)

            # Arrow from start to goal
            scx = sx + cs / 2 - 0.5
            scy = sy + cs / 2 - 0.5
            ax.annotate("", xy=(gcx, gcy), xytext=(scx, scy),
                        arrowprops=dict(arrowstyle="->", color=color,
                                        alpha=0.3, lw=1))

            if cs not in legend_entries:
                legend_entries[cs] = color

        # Legend
        patches = []
        for cs in sorted(legend_entries):
            n = sum(1 for a in agents if a[0] == cs)
            patches.append(mpatches.Patch(
                color=legend_entries[cs],
                label=f"Fleet cs={cs} ({n} agents)"))
        if patches:
            leg = ax.legend(handles=patches, loc="upper right", fontsize=8,
                            framealpha=0.8, facecolor="#313244",
                            edgecolor="#585b70", labelcolor="white")
            leg.set_zorder(10)

    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(height - 0.5, -0.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    map_name = os.path.basename(args.map)
    n_agents = len(agents) if args.scen else 0
    ax.set_title(f"{map_name}  ({width}x{height}, {n_agents} agents)",
                 color="white", fontsize=14, fontweight="bold")

    plt.tight_layout()
    if args.save:
        fig.savefig(args.save, dpi=150, bbox_inches='tight',
                    facecolor=fig.get_facecolor())
        print(f"Saved to {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
