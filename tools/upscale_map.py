"""Upscale a .map file by an integer factor."""
import sys

def upscale_map(infile, outfile, scale):
    with open(infile) as f:
        lines = f.readlines()
    # Parse header
    assert lines[0].strip().startswith("type")
    h = int(lines[1].strip().split()[1])
    w = int(lines[2].strip().split()[1])
    assert lines[3].strip() == "map"
    rows = []
    for i in range(4, 4 + h):
        row = lines[i].rstrip('\n').rstrip('\r')
        # Pad to width if needed
        row = row.ljust(w, '@')[:w]
        rows.append(row)
    # Upscale
    new_h = h * scale
    new_w = w * scale
    with open(outfile, 'w', newline='\n') as f:
        f.write(f"type octile\n")
        f.write(f"height {new_h}\n")
        f.write(f"width {new_w}\n")
        f.write(f"map\n")
        for row in rows:
            scaled_row = ''.join(c * scale for c in row)
            for _ in range(scale):
                f.write(scaled_row + '\n')
    print(f"Wrote {outfile}: {new_w}x{new_h} (scale {scale}x from {w}x{h})")

if __name__ == "__main__":
    infile = sys.argv[1]
    outfile = sys.argv[2]
    scale = int(sys.argv[3])
    upscale_map(infile, outfile, scale)
