"""
Visualizer for het_lacam heterogeneous multi-agent pathfinding solutions.
Reads het_lacam's native output format (timestep-oriented solution),
a .scen file for fleet definitions, and the .map file.

Controls:
  Space     - pause / play
  Right     - step forward
  Left      - step backward
  Up/Down   - speed up / slow down
  Q / Esc   - quit

Usage:
    python visualize.py -r result.txt -i scenario.scen -m map.map
    python visualize.py -r result.txt -i scenario.scen -m map.map --speed 100
    python visualize.py -r result.txt -i scenario.scen -m map.map --substeps 4
"""

import argparse
import re
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation


# ---------------------------------------------------------------------------
# Fleet palette — visually distinct, dark-theme friendly (same as hetpibt)
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


def load_scen(scen_path):
    """Parse scenario file (auto-detects 5-col simple or 10-col het_bench).

    Returns:
        fleets:  {fleet_id: {"cell_size", "velocity", "grid_w", "grid_h"}}
        agents:  [{"id", "fleet_id", "cell_size", "start_fg", "goal_fg"}]
    """
    fleets = {}
    agents = []

    with open(scen_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 10:
                # het_bench 10-column
                aid = int(parts[0])
                fid = int(parts[1])
                cs = int(parts[2])
                vel = float(parts[3])
                sx, sy = int(parts[4]), int(parts[5])
                gx, gy = int(parts[6]), int(parts[7])
                gw, gh = int(parts[8]), int(parts[9])
                if fid not in fleets:
                    fleets[fid] = {"cell_size": cs, "velocity": vel,
                                   "grid_w": gw, "grid_h": gh}
                agents.append({
                    "id": len(agents), "fleet_id": fid, "cell_size": cs,
                    "start_fg": (sx // cs, sy // cs),
                    "goal_fg": (gx // cs, gy // cs),
                })
            elif len(parts) >= 5:
                # simple 5-column: cs sx sy gx gy
                cs = int(parts[0])
                sx, sy = int(parts[1]), int(parts[2])
                gx, gy = int(parts[3]), int(parts[4])
                # auto-assign fleet by cell_size
                fid = cs
                if fid not in fleets:
                    fleets[fid] = {"cell_size": cs, "velocity": float(cs),
                                   "grid_w": 0, "grid_h": 0}
                agents.append({
                    "id": len(agents), "fleet_id": fid, "cell_size": cs,
                    "start_fg": (sx // cs, sy // cs),
                    "goal_fg": (gx // cs, gy // cs),
                })

    return fleets, agents


def load_result(result_path):
    """Parse het_lacam native result file.

    het_lacam format:
        key=value metadata lines
        fleets=fid:cs:sp:gw:gh;...  # fleet definitions
        agent_fleet=fid0,fid1,...    # per-agent fleet assignment
        starts=(fx,fy),(fx,fy),...   # fleet-grid coords
        goals=(fx,fy),(fx,fy),...    # fleet-grid coords
        solution=
        t:(fx0,fy0),(fx1,fy1),...    # fleet-grid coords per agent

    Returns:
        meta, fleets, agent_fleets, starts_fg, goals_fg, solution
    """
    meta = {}
    fleets = {}
    agent_fleets = []
    starts_fg = []
    goals_fg = []
    solution = []

    with open(result_path, "r") as f:
        in_solution = False
        for line in f:
            line = line.rstrip("\n\r")
            if in_solution:
                m = re.match(r"^(\d+):(.*)", line)
                if m:
                    coords = re.findall(r"\((-?\d+),(-?\d+)\)", m.group(2))
                    solution.append([(int(x), int(y)) for x, y in coords])
                continue
            if line.startswith("solution="):
                in_solution = True
                rest = line[len("solution="):]
                if rest.strip():
                    m = re.match(r"^(\d+):(.*)", rest.strip())
                    if m:
                        coords = re.findall(r"\((-?\d+),(-?\d+)\)", m.group(2))
                        solution.append([(int(x), int(y)) for x, y in coords])
                continue
            if line.startswith("fleets="):
                for part in line[len("fleets="):].split(";"):
                    fields = part.split(":")
                    if len(fields) >= 5:
                        fid = int(fields[0])
                        fleets[fid] = {
                            "cell_size": int(fields[1]),
                            "velocity": float(fields[2]),
                            "grid_w": int(fields[3]),
                            "grid_h": int(fields[4]),
                        }
                continue
            if line.startswith("agent_fleet="):
                agent_fleets = [int(x) for x in line[len("agent_fleet="):].split(",") if x]
                continue
            if line.startswith("starts="):
                pairs = re.findall(r"\((-?\d+),(-?\d+)\)", line)
                starts_fg = [(int(x), int(y)) for x, y in pairs]
                continue
            if line.startswith("goals="):
                pairs = re.findall(r"\((-?\d+),(-?\d+)\)", line)
                goals_fg = [(int(x), int(y)) for x, y in pairs]
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                meta[key] = val

    return meta, fleets, agent_fleets, starts_fg, goals_fg, solution


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------
def fleet_to_base_center(fx, fy, cell_size):
    """Fleet grid cell (fx, fy) -> base grid center (bx, by)."""
    bx = fx * cell_size + (cell_size - 1) / 2.0
    by = fy * cell_size + (cell_size - 1) / 2.0
    return bx, by


def get_interpolated_pos(solution, agent_idx, t, cell_size):
    """Get interpolated base-grid center position at fractional time t."""
    t0 = int(t)
    t1 = t0 + 1

    if t0 < 0:
        t0 = 0
    if t0 >= len(solution):
        t0 = len(solution) - 1
    if t1 >= len(solution):
        t1 = len(solution) - 1

    if agent_idx >= len(solution[t0]):
        return 0.0, 0.0

    fx0, fy0 = solution[t0][agent_idx]
    fx1, fy1 = solution[t1][agent_idx]
    bx0, by0 = fleet_to_base_center(fx0, fy0, cell_size)
    bx1, by1 = fleet_to_base_center(fx1, fy1, cell_size)

    alpha = t - t0
    return bx0 + alpha * (bx1 - bx0), by0 + alpha * (by1 - by0)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
FLEET_LINE_STYLES = [
    (0, (4, 2)),
    (0, (1, 1)),
    (0, (4, 1, 1, 1)),
    (0, (6, 2, 1, 2)),
]


def draw_fleet_grid(ax, cell_size, base_w, base_h, color, label,
                    style_idx=0):
    """Draw fleet grid overlay on the base map."""
    fleet_w = base_w // cell_size
    fleet_h = base_h // cell_size
    if fleet_w <= 0 or fleet_h <= 0:
        return
    ls = FLEET_LINE_STYLES[style_idx % len(FLEET_LINE_STYLES)]

    for fx in range(fleet_w + 1):
        x = fx * cell_size - 0.5
        ax.axvline(x, color=color, linewidth=0.6, linestyle=ls,
                   alpha=0.35, zorder=2)
    for fy in range(fleet_h + 1):
        y = fy * cell_size - 0.5
        ax.axhline(y, color=color, linewidth=0.6, linestyle=ls,
                   alpha=0.35, zorder=2)

    ax.text(cell_size * 0.5, cell_size * 0.5, label,
            color=color, fontsize=8, ha="center", va="center",
            alpha=0.6, fontweight="bold", zorder=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Visualize het_lacam heterogeneous MAPF solution"
    )
    parser.add_argument(
        "-r", "--result", required=True,
        help="Path to het_lacam result file",
    )
    parser.add_argument(
        "-i", "--scen", default=None,
        help="Path to .scen file (optional; enriches fleet info)",
    )
    parser.add_argument(
        "-m", "--map", required=True,
        help="Path to .map file",
    )
    parser.add_argument(
        "--speed", type=int, default=150,
        help="ms per frame (lower = faster, default 150)",
    )
    parser.add_argument(
        "--substeps", type=int, default=4,
        help="interpolation substeps between integer timesteps (default 4)",
    )
    parser.add_argument(
        "--time-scale", type=float, default=1.0,
        help="speed multiplier: 2 = twice as fast, etc.",
    )
    parser.add_argument(
        "--no-grid-overlay", action="store_true",
        help="hide fleet grid overlays",
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="save animation to file (e.g. out.mp4, out.gif)",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    grid = load_map(args.map)
    base_h, base_w = grid.shape

    meta, fleets, agent_fleets_r, starts_fg, goals_fg, solution = \
        load_result(args.result)

    # Optionally enrich from .scen file
    if args.scen:
        scen_fleets, scen_agents = load_scen(args.scen)
        if not fleets:
            fleets = scen_fleets
        if not agent_fleets_r:
            agent_fleets_r = [a["fleet_id"] for a in scen_agents]
        if not starts_fg:
            starts_fg = [a["start_fg"] for a in scen_agents]
        if not goals_fg:
            goals_fg = [a["goal_fg"] for a in scen_agents]

    N = int(meta.get("agents", 0))
    if N == 0 and solution:
        N = len(solution[0])
    makespan = len(solution) - 1 if solution else 0

    if not solution:
        print("No solution data to visualize.")
        sys.exit(1)

    # Per-agent fleet/cell_size lookup
    agent_fleets = agent_fleets_r if agent_fleets_r else [0] * N
    agent_cs = [1] * N
    for i in range(N):
        if i < len(agent_fleets):
            fid = agent_fleets[i]
            if fid in fleets:
                agent_cs[i] = fleets[fid]["cell_size"]

    # Ensure goals_fg is populated (fallback to last solution frame)
    if not goals_fg and solution:
        goals_fg = list(solution[-1][:N])
    if len(goals_fg) < N:
        goals_fg.extend([(0, 0)] * (N - len(goals_fg)))

    substeps = max(1, args.substeps)
    time_scale = max(0.1, args.time_scale)
    n_frames = int(makespan * substeps / time_scale) + 1

    print(f"Map: {base_w}x{base_h}, Agents: {N}, "
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

    # Draw base grid via imshow
    map_display = np.ones((base_h, base_w, 3))
    map_display[grid] = [0.2, 0.2, 0.25]
    map_display[~grid] = [0.92, 0.92, 0.95]

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
                continue
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
    # Goal markers — hollow dashed rectangles + X at center
    # ------------------------------------------------------------------
    for i in range(N):
        if i >= len(goals_fg):
            break
        gx, gy = goals_fg[i]
        cs = agent_cs[i]
        fid = agent_fleets[i]
        bx0 = gx * cs - 0.5
        by0 = gy * cs - 0.5
        goal_rect = mpatches.Rectangle(
            (bx0, by0), cs, cs,
            linewidth=2, edgecolor=fleet_color(fid),
            facecolor='none', linestyle='--', alpha=0.5, zorder=3)
        ax.add_patch(goal_rect)
        cx = gx * cs + (cs - 1) / 2.0
        cy = gy * cs + (cs - 1) / 2.0
        ax.plot(cx, cy, "x", color=fleet_color(fid),
                markersize=max(4, cs * 2),
                markeredgewidth=max(1.0, cs * 0.5),
                alpha=0.4, zorder=3)

    # ------------------------------------------------------------------
    # Agent rectangles — full cs×cs footprint, colored by fleet
    # ------------------------------------------------------------------
    agent_rects = []
    agent_labels = []
    for i in range(N):
        cs = agent_cs[i]
        fid = agent_fleets[i]
        color = fleet_color(fid)

        rect = mpatches.Rectangle(
            (0, 0), cs, cs,
            facecolor=color, edgecolor="black",
            linewidth=0.8, alpha=0.85, zorder=5,
        )
        ax.add_patch(rect)
        agent_rects.append(rect)

        label = ax.text(0, 0, str(i), color="black",
                        fontsize=max(5, min(10, 4 + cs)),
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
    # Goal lines (toggled with 'g')
    # ------------------------------------------------------------------
    goal_lines = []
    for i in range(N):
        fid = agent_fleets[i]
        line, = ax.plot([], [], color=fleet_color(fid), alpha=0.4,
                        linewidth=1.2, zorder=4, visible=False)
        goal_lines.append(line)

    # ------------------------------------------------------------------
    # Animation state (for keyboard controls)
    # ------------------------------------------------------------------
    state = {"frame": 0, "playing": True, "show_goal_lines": False}
    anim_ref = [None]  # mutable ref for the FuncAnimation object

    def render_at_frame(frame):
        t = frame * time_scale / substeps

        for i in range(N):
            cs = agent_cs[i]
            fid = agent_fleets[i]
            bx, by = get_interpolated_pos(solution, i, t, cs)

            agent_rects[i].set_xy((bx - (cs - 1) / 2.0 - 0.5,
                                   by - (cs - 1) / 2.0 - 0.5))
            agent_labels[i].set_position((bx, by))

            # Highlight when agent is at its goal
            at_goal = False
            if i < len(goals_fg):
                gx_c, gy_c = fleet_to_base_center(
                    goals_fg[i][0], goals_fg[i][1], cs)
                if abs(bx - gx_c) < 0.01 and abs(by - gy_c) < 0.01:
                    at_goal = True

            if at_goal:
                agent_rects[i].set_edgecolor("white")
                agent_rects[i].set_linewidth(2.5)
                agent_rects[i].set_alpha(1.0)
            else:
                agent_rects[i].set_edgecolor("black")
                agent_rects[i].set_linewidth(0.8)
                agent_rects[i].set_alpha(0.85)

        # Goal lines
        for i in range(N):
            if state["show_goal_lines"] and i < len(goals_fg):
                cs = agent_cs[i]
                bx, by = get_interpolated_pos(solution, i, t, cs)
                gx_c, gy_c = fleet_to_base_center(
                    goals_fg[i][0], goals_fg[i][1], cs)
                goal_lines[i].set_data([bx, gx_c], [by, gy_c])
                goal_lines[i].set_visible(True)
            else:
                goal_lines[i].set_visible(False)

        play_str = "PLAY" if state["playing"] else "PAUSE"
        title.set_text(f"t = {t:.1f} / {makespan}  [{play_str}]")
        return agent_rects + agent_labels + goal_lines + [title]

    def animate(frame):
        if state["playing"]:
            state["frame"] += 1
            if state["frame"] >= n_frames:
                state["frame"] = n_frames - 1
                state["playing"] = False
        return render_at_frame(state["frame"])

    def on_key(event):
        if event.key == " ":
            state["playing"] = not state["playing"]
            render_at_frame(state["frame"])
            fig.canvas.draw_idle()
        elif event.key == "right":
            state["playing"] = False
            state["frame"] = min(state["frame"] + substeps, n_frames - 1)
            render_at_frame(state["frame"])
            fig.canvas.draw_idle()
        elif event.key == "left":
            state["playing"] = False
            state["frame"] = max(state["frame"] - substeps, 0)
            render_at_frame(state["frame"])
            fig.canvas.draw_idle()
        elif event.key == "up":
            args.speed = max(10, args.speed - 20)
            if anim_ref[0]:
                anim_ref[0].event_source.interval = args.speed
            render_at_frame(state["frame"])
            fig.canvas.draw_idle()
        elif event.key == "down":
            args.speed = min(1000, args.speed + 20)
            if anim_ref[0]:
                anim_ref[0].event_source.interval = args.speed
            render_at_frame(state["frame"])
            fig.canvas.draw_idle()
        elif event.key == "g":
            state["show_goal_lines"] = not state["show_goal_lines"]
            render_at_frame(state["frame"])
            fig.canvas.draw_idle()
        elif event.key in ("q", "escape"):
            plt.close(fig)

    # Initialize
    render_at_frame(0)

    if args.save:
        anim = FuncAnimation(
            fig, render_at_frame, frames=n_frames,
            interval=args.speed, blit=True, repeat=False,
        )
        anim.save(args.save,
                  writer="pillow" if args.save.endswith(".gif") else "ffmpeg",
                  fps=max(1, 1000 // args.speed))
        print(f"Saved to {args.save}")
    else:
        fig.canvas.mpl_connect("key_press_event", on_key)
        anim = FuncAnimation(
            fig, animate, frames=None,
            interval=args.speed, blit=True, repeat=True,
            cache_frame_data=False,
        )
        anim_ref[0] = anim
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
