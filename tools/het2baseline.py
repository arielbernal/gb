#!/usr/bin/env python3
"""Convert het_bench .scen files to standard MovingAI .scen format.

het_bench input format (10 fields):
  agent_id fleet_id cell_size velocity sx sy gx gy grid_w grid_h

MovingAI output format (tab-separated, 9 fields):
  bucket  map_name  map_w  map_h  sx  sy  gx  gy  optimal_length

Modes:
  --homogeneous  All agents become unit-size unit-speed. Coordinates as-is.
  --size-only    Strip velocity, keep cell_size. Comment header notes cs per agent.
  --speed-only   Strip cell_size (all cs=1), keep velocity. Comment header notes
                 velocity per agent.

Usage:
  python het2baseline.py --input scen.0.scen --output scen.0_homo.scen \\
      --map room-64-64-8.map --map-w 640 --map-h 640 --homogeneous
"""
import argparse
import sys


def parse_het_bench(path):
    """Parse het_bench scenario. Returns list of agent dicts."""
    agents = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 10:
                continue
            agents.append({
                'agent_id': int(parts[0]),
                'fleet_id': int(parts[1]),
                'cell_size': int(float(parts[2])),
                'velocity': float(parts[3]),
                'sx': int(float(parts[4])),
                'sy': int(float(parts[5])),
                'gx': int(float(parts[6])),
                'gy': int(float(parts[7])),
                'grid_w': int(parts[8]),
                'grid_h': int(parts[9]),
            })
    return agents


def write_movingai(agents, output_path, map_name, map_w, map_h, mode):
    """Write MovingAI .scen format with optional comment header."""
    with open(output_path, 'w') as f:
        f.write("version 1\n")

        # Comment header with het_bench metadata for non-homogeneous modes
        if mode == 'size-only':
            f.write(f"# Converted from het_bench ({mode}): cell_size preserved\n")
            f.write("# agent_index cell_size\n")
            for i, a in enumerate(agents):
                f.write(f"# {i} {a['cell_size']}\n")
        elif mode == 'speed-only':
            f.write(f"# Converted from het_bench ({mode}): velocity preserved\n")
            f.write("# agent_index velocity\n")
            for i, a in enumerate(agents):
                f.write(f"# {i} {a['velocity']}\n")

        for i, a in enumerate(agents):
            bucket = 0
            optimal = 0.0
            f.write(f"{bucket}\t{map_name}\t{map_w}\t{map_h}\t"
                    f"{a['sx']}\t{a['sy']}\t{a['gx']}\t{a['gy']}\t"
                    f"{optimal:.8f}\n")

    print(f"Wrote {len(agents)} agents to {output_path} (mode={mode})")


def main():
    parser = argparse.ArgumentParser(
        description="Convert het_bench .scen to MovingAI .scen format")
    parser.add_argument("--input", "-i", required=True,
                        help="Input het_bench .scen file")
    parser.add_argument("--output", "-o", required=True,
                        help="Output MovingAI .scen file")
    parser.add_argument("--map", required=True,
                        help="Map filename to embed in output (e.g. room-64-64-8.map)")
    parser.add_argument("--map-w", type=int, required=True,
                        help="Map width (base grid)")
    parser.add_argument("--map-h", type=int, required=True,
                        help="Map height (base grid)")

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--homogeneous", action="store_true",
                            help="All agents become unit-size unit-speed")
    mode_group.add_argument("--size-only", action="store_true",
                            help="Keep cell_size, strip velocity")
    mode_group.add_argument("--speed-only", action="store_true",
                            help="Keep velocity, strip cell_size (all cs=1)")

    args = parser.parse_args()

    agents = parse_het_bench(args.input)
    if not agents:
        print(f"ERROR: no agents parsed from {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.homogeneous:
        mode = 'homogeneous'
    elif args.size_only:
        mode = 'size-only'
    elif args.speed_only:
        mode = 'speed-only'

    write_movingai(agents, args.output, args.map,
                   args.map_w, args.map_h, mode)


if __name__ == "__main__":
    main()
