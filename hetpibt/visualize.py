"""
Visualizer for HetPIBT heterogeneous multi-agent pathfinding solutions.
Reads the map file and result.txt (+ optional .scen), then animates
agent movements with fleet-aware rendering.

Changes from LaCAM visualizer:
  - Agent circles scaled by fleet cell_size
  - Agents colored by fleet, not individually
  - Fleet grid overlays showing different resolution nav-graphs
  - Asynchronous movement — agents interpolate at their own velocity
  - Parses het_bench scenario format for starts/goals/fleet info

Usage:
    python visualize.py
    python visualize.py --result build/result.txt --speed 150
    python visualize.py --result build/result.txt --scen scenario.scen --substeps 4
"""

import argparse
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
from pathlib import Path


# ---------------------------------------------------------------------------
# Fleet palette — visually distinct, dark-theme friendly
# ---------------------------------------------------------------------------
FLEET_COLORS = [
    "#f38ba8",  # rosewater / red-pink
    "#89b4fa",  # blue
    "#a6e3a1",  # green
    "#fab387",  # peach / orange
    "#cba6f7",  # mauve / purple
    "#94e2d5",  # teal
    "#f9e2af",  # yellow
    "#eba0ac",  # maroon-pink
    "#89dceb",  # sky blue
    "#b4befe",  # lavender
]


def fleet_color(fleet_id):
    return FLEET_COLORS[fleet_id % len(FLEET_COLORS)]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
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


def load_het_scen(scen_path):
    """Parse het_bench scenario file.

    Format (space-separated, no header):
        agent_id fleet_id footprint velocity sx sy gx gy grid_w grid_h

    Returns:
        fleets:  {fleet_id: {"cell_size": int, "velocity": float,
                              "grid_w": int, "grid_h": int}}
        agents:  [{"id": int, "fleet_id": int,
                   "start": (fx, fy), "goal": (gx, gy)}]
    """
    fleets = {}
    agents = []

    with open(scen_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 10:
                continue

            aid = int(parts[0])
            fid = int(parts[1])
            cs = int(parts[2])
            vel = float(parts[3])
            sx, sy = int(parts[4]), int(parts[5])
            gx, gy = int(parts[6]), int(parts[7])
            gw, gh = int(parts[8]), int(parts[9])

            if fid not in fleets:
                fleets[fid] = {
                    "cell_size": cs,
                    "velocity": vel,
                    "grid_w": gw,
                    "grid_h": gh,
                }

            # het_bench coords are absolute free-space; convert to fleet grid
            fx_s, fy_s = sx // cs, sy // cs
            fx_g, fy_g = gx // cs, gy // cs

            agents.append({
                "id": len(agents),
                "fleet_id": fid,
                "start": (fx_s, fy_s),
                "goal": (fx_g, fy_g),
            })

    return fleets, agents


def load_het_result(result_path):
    """Parse HetPIBT result.txt.

    Returns:
        meta:         dict of key=value metadata
        fleets:       {fleet_id: {"cell_size", "velocity", "grid_w", "grid_h"}}
        agent_fleets: [fleet_id_for_agent_0, fleet_id_for_agent_1, ...]
        starts:       [(fx, fy), ...]  in fleet grid coords
        goals:        [(fx, fy), ...]
        trajectories: {agent_id: [(t, fx, fy), ...] sorted by t}
    """
    meta = {}
    fleets = {}
    agent_fleets = []
    starts = []
    goals = []
    trajectories = {}
    in_solution = False

    with open(result_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # solution section: lines are "agent_id:fleet_id:(x,y)@t,..."
            if in_solution:
                m = re.match(r"^(\d+):(\d+):(.*)", line)
                if not m:
                    continue
                aid = int(m.group(1))
                # fid = int(m.group(2))  # already in agent_fleets
                entries_str = m.group(3)
                entries = re.findall(r"\((-?\d+),(-?\d+)\)@(\d+)", entries_str)
                traj = [(int(t), int(x), int(y)) for x, y, t in entries]
                traj.sort(key=lambda e: e[0])
                # deduplicate: keep last entry per timestep
                deduped = {}
                for t_val, fx, fy in traj:
                    deduped[t_val] = (t_val, fx, fy)
                traj = sorted(deduped.values())
                trajectories[aid] = traj
                continue

            if line == "solution":
                in_solution = True
                continue

            if "=" not in line:
                continue

            key, value = line.split("=", 1)

            if key == "fleets":
                # format: id:cs:vel:gw:gh;id:cs:vel:gw:gh;...
                for part in value.split(";"):
                    fields = part.split(":")
                    if len(fields) >= 5:
                        fid = int(fields[0])
                        fleets[fid] = {
                            "cell_size": int(fields[1]),
                            "velocity": float(fields[2]),
                            "grid_w": int(fields[3]),
                            "grid_h": int(fields[4]),
                        }
            elif key == "agent_fleet":
                agent_fleets = [int(x) for x in value.split(",")]
            elif key == "starts":
                pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
                starts = [(int(x), int(y)) for x, y in pairs]
            elif key == "goals":
                pairs = re.findall(r"\((-?\d+),(-?\d+)\)", value)
                goals = [(int(x), int(y)) for x, y in pairs]
            else:
                meta[key] = value

    return meta, fleets, agent_fleets, starts, goals, trajectories


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------
def fleet_to_base(fx, fy, cell_size):
    """Convert fleet grid cell (fx, fy) to base grid center coordinates."""
    bx = fx * cell_size + (cell_size - 1) / 2.0
    by = fy * cell_size + (cell_size - 1) / 2.0
    return bx, by


def get_position_at_time(traj, t, cell_size):
    """Get interpolated base-grid position for an agent at fractional time t.

    traj: [(time, fx, fy), ...] sorted by time
    Returns: (base_x, base_y)
    """
    if not traj:
        return 0.0, 0.0

    # before first keyframe
    if t <= traj[0][0]:
        fx, fy = traj[0][1], traj[0][2]
        return fleet_to_base(fx, fy, cell_size)

    # after last keyframe
    if t >= traj[-1][0]:
        fx, fy = traj[-1][1], traj[-1][2]
        return fleet_to_base(fx, fy, cell_size)

    # find surrounding keyframes
    for i in range(len(traj) - 1):
        t0, fx0, fy0 = traj[i]
        t1, fx1, fy1 = traj[i + 1]
        if t0 <= t <= t1:
            if t1 == t0:
                alpha = 0.0
            else:
                alpha = (t - t0) / (t1 - t0)
            bx0, by0 = fleet_to_base(fx0, fy0, cell_size)
            bx1, by1 = fleet_to_base(fx1, fy1, cell_size)
            return bx0 + alpha * (bx1 - bx0), by0 + alpha * (by1 - by0)

    # fallback
    fx, fy = traj[-1][1], traj[-1][2]
    return fleet_to_base(fx, fy, cell_size)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
# Distinct dash patterns per fleet overlay, cycling if >4 fleets
FLEET_LINE_STYLES = [
    (0, (4, 2)),       # "- - - -"  (dashed)
    (0, (1, 1)),       # ". . . ."  (dotted)
    (0, (4, 1, 1, 1)), # "-. -. -." (dash-dot)
    (0, (6, 2, 1, 2)), # "-- . -- ." (long-dash-dot)
]


def draw_fleet_grid(ax, cell_size, base_w, base_h, color, label,
                    style_idx=0):
    """Draw fleet grid overlay on the base map."""
    fleet_w = base_w // cell_size
    fleet_h = base_h // cell_size
    ls = FLEET_LINE_STYLES[style_idx % len(FLEET_LINE_STYLES)]

    # vertical lines
    for i in range(fleet_w + 1):
        x = i * cell_size - 0.5
        ax.axvline(x, color=color, linewidth=1.2, alpha=0.5,
                   linestyle=ls, zorder=2)

    # horizontal lines
    for j in range(fleet_h + 1):
        y = j * cell_size - 0.5
        ax.axhline(y, color=color, linewidth=1.2, alpha=0.5,
                   linestyle=ls, zorder=2)

    # label in top-left of the grid
    ax.text(cell_size * 0.5 - 0.5, cell_size * 0.5 - 0.5, label,
            color=color, fontsize=8, ha="center", va="center",
            alpha=0.6, fontweight="bold", zorder=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Visualize HetPIBT heterogeneous MAPF solution"
    )
    parser.add_argument(
        "--result", default="build/result.txt",
        help="Path to HetPIBT result.txt",
    )
    parser.add_argument(
        "--scen", default=None,
        help="Path to het_bench .scen file (optional; supplements result)",
    )
    parser.add_argument(
        "--map", default=None,
        help="Path to .map file (auto-detected from result if omitted)",
    )
    parser.add_argument(
        "--speed", type=int, default=150,
        help="ms per frame (lower = faster)",
    )
    parser.add_argument(
        "--substeps", type=int, default=4,
        help="interpolation substeps between integer timesteps (1 = none)",
    )
    parser.add_argument(
        "--no-grid-overlay", action="store_true",
        help="hide fleet grid overlays",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load result
    # ------------------------------------------------------------------
    result_path = Path(args.result)
    if not result_path.exists():
        print(f"Error: {result_path} not found. Run the solver first.")
        return

    meta, fleets, agent_fleets, starts, goals, trajectories = \
        load_het_result(result_path)

    # Optionally enrich from .scen file
    if args.scen:
        scen_fleets, scen_agents = load_het_scen(args.scen)
        # scen can fill in missing fleet info
        for fid, fdef in scen_fleets.items():
            if fid not in fleets:
                fleets[fid] = fdef
        # if result had no starts/goals, use scen
        if not starts:
            starts = [a["start"] for a in scen_agents]
        if not goals:
            goals = [a["goal"] for a in scen_agents]
        if not agent_fleets:
            agent_fleets = [a["fleet_id"] for a in scen_agents]

    n_agents = len(agent_fleets)
    if n_agents == 0:
        print("No agents found in result or scenario file.")
        return

    # ------------------------------------------------------------------
    # Load map
    # ------------------------------------------------------------------
    map_path = args.map
    if map_path is None:
        map_name = meta.get("map_name", "")
        candidates = [
            Path(map_name),
            Path("assets") / map_name,
            Path("assets") / Path(map_name).name,
        ]
        for c in candidates:
            if c.exists():
                map_path = str(c)
                break

    if map_path is None or not Path(map_path).exists():
        print("Error: Could not find map file. Use --map to specify.")
        return

    grid = load_map(map_path)
    base_h, base_w = grid.shape

    # ------------------------------------------------------------------
    # Compute time range
    # ------------------------------------------------------------------
    makespan = int(meta.get("makespan", 0))
    for traj in trajectories.values():
        if traj:
            makespan = max(makespan, traj[-1][0])

    substeps = max(1, args.substeps)
    n_frames = makespan * substeps + 1

    # build per-agent cell_size lookup
    agent_cs = []
    for i in range(n_agents):
        fid = agent_fleets[i]
        cs = fleets.get(fid, {}).get("cell_size", 1)
        agent_cs.append(cs)

    print(f"Map: {base_w}x{base_h}, Agents: {n_agents}, "
          f"Fleets: {len(fleets)}, Makespan: {makespan}")
    for fid in sorted(fleets):
        f = fleets[fid]
        n_in = sum(1 for af in agent_fleets if af == fid)
        print(f"  Fleet {fid}: cell_size={f['cell_size']}, "
              f"vel={f['velocity']}, "
              f"grid={f['grid_w']}x{f['grid_h']}, agents={n_in}")

    # ------------------------------------------------------------------
    # Set up the plot
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    fig.patch.set_facecolor("#1e1e2e")
    ax.set_facecolor("#1e1e2e")

    # Draw base grid
    map_display = np.ones((base_h, base_w, 3))
    map_display[grid] = [0.2, 0.2, 0.25]       # dark obstacles
    map_display[~grid] = [0.92, 0.92, 0.95]     # light open space

    ax.imshow(map_display, origin="upper",
              extent=(-0.5, base_w - 0.5, base_h - 0.5, -0.5))

    # Base grid lines (thin, subtle)
    for x in range(base_w + 1):
        ax.axvline(x - 0.5, color="#ccc", linewidth=0.2, alpha=0.3)
    for y in range(base_h + 1):
        ax.axhline(y - 0.5, color="#ccc", linewidth=0.2, alpha=0.3)

    # Fleet grid overlays
    if not args.no_grid_overlay:
        style_idx = 0
        for fid in sorted(fleets):
            f = fleets[fid]
            cs = f["cell_size"]
            if cs <= 1:
                continue  # skip cell_size=1 (same as base grid)
            draw_fleet_grid(ax, cs, base_w, base_h,
                            fleet_color(fid), f"F{fid}",
                            style_idx=style_idx)
            style_idx += 1

    ax.set_xlim(-0.5, base_w - 0.5)
    ax.set_ylim(base_h - 0.5, -0.5)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    # ------------------------------------------------------------------
    # Draw goal markers — sized by fleet
    # ------------------------------------------------------------------
    for i in range(n_agents):
        if i < len(goals):
            gx, gy = goals[i]
            cs = agent_cs[i]
            bx, by = fleet_to_base(gx, gy, cs)
            marker_size = cs * 6  # scales linearly with fleet cell_size
            ax.plot(bx, by, "x", color=fleet_color(agent_fleets[i]),
                    markersize=marker_size, markeredgewidth=max(1.0, cs * 0.8),
                    alpha=0.35, zorder=3)

    # ------------------------------------------------------------------
    # Agent circles — radius proportional to cell_size, colored by fleet
    # ------------------------------------------------------------------
    agent_circles = []
    agent_labels = []
    for i in range(n_agents):
        cs = agent_cs[i]
        fid = agent_fleets[i]
        radius = cs * 0.4  # linear with cell_size
        color = fleet_color(fid)

        circle = plt.Circle(
            (0, 0), radius,
            facecolor=color, edgecolor="black",
            linewidth=0.5, alpha=0.9, zorder=5,
        )
        ax.add_patch(circle)
        agent_circles.append(circle)

        # agent ID label — scale font to fit the circle
        label = ax.text(0, 0, str(i), color="black",
                        fontsize=max(5, min(9, 5 + cs)),
                        ha="center", va="center",
                        fontweight="bold", zorder=6)
        agent_labels.append(label)

    # ------------------------------------------------------------------
    # Legend — one entry per fleet
    # ------------------------------------------------------------------
    legend_patches = []
    for fid in sorted(fleets):
        f = fleets[fid]
        n_in = sum(1 for af in agent_fleets if af == fid)
        legend_patches.append(
            mpatches.Patch(
                color=fleet_color(fid),
                label=f"Fleet {fid}  cs={f['cell_size']}  "
                      f"v={f['velocity']}  ({n_in} agents)",
            )
        )
    if legend_patches:
        leg = ax.legend(
            handles=legend_patches, loc="upper right",
            fontsize=7, framealpha=0.7,
            facecolor="#313244", edgecolor="#585b70",
            labelcolor="white",
        )
        leg.set_zorder(10)

    # Title
    title = ax.set_title(
        f"t = 0.0 / {makespan}", color="white",
        fontsize=14, fontweight="bold",
    )

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------
    def update(frame):
        t = frame / substeps  # fractional global time

        for i in range(n_agents):
            cs = agent_cs[i]
            fid = agent_fleets[i]
            traj = trajectories.get(i, [])

            if traj:
                bx, by = get_position_at_time(traj, t, cs)
            elif i < len(starts):
                bx, by = fleet_to_base(starts[i][0], starts[i][1], cs)
            else:
                bx, by = 0.0, 0.0

            agent_circles[i].center = (bx, by)
            agent_labels[i].set_position((bx, by))

            # highlight when agent is at its goal
            at_goal = False
            if i < len(goals):
                gx, gy = fleet_to_base(goals[i][0], goals[i][1], cs)
                if abs(bx - gx) < 0.01 and abs(by - gy) < 0.01:
                    at_goal = True

            if at_goal:
                agent_circles[i].set_edgecolor("white")
                agent_circles[i].set_linewidth(3.0)
                agent_circles[i].set_alpha(1.0)
            else:
                agent_circles[i].set_edgecolor("black")
                agent_circles[i].set_linewidth(0.5)
                agent_circles[i].set_alpha(0.9)

        title.set_text(f"t = {t:.1f} / {makespan}")
        return agent_circles + agent_labels + [title]

    # Initialize
    update(0)

    ani = FuncAnimation(
        fig, update, frames=n_frames,
        interval=args.speed, blit=True, repeat=True,
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
