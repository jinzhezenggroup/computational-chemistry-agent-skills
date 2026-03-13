#!/usr/bin/env python3
"""Convert a LAMMPS dump (lammpstrj) with xs/ys/zs (scaled coords)
into x/y/z (absolute coords) using the per-frame BOX BOUNDS.

Assumptions:
- Orthorhombic boxes: BOX BOUNDS lines are "lo hi" (no tilt factors).
- ATOMS header includes xs ys zs.

Streaming conversion (no full-file load).
"""

from __future__ import annotations

import argparse


def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True, help="Input .lammpstrj (with xs/ys/zs)")
    ap.add_argument("-o", "--output", required=True, help="Output .lammpstrj (with x/y/z)")
    ap.add_argument("--precision", type=int, default=8)
    args = ap.parse_args()

    fmt = "{:." + str(args.precision) + "f}"

    frames = 0
    with open(args.input, "r", errors="replace") as fin, open(args.output, "w") as fout:
        while True:
            line = fin.readline()
            if not line:
                break
            if not line.startswith("ITEM: TIMESTEP"):
                die(f"Expected 'ITEM: TIMESTEP', got: {line.strip()!r}")

            fout.write(line)
            timestep = fin.readline();
            if not timestep:
                die("EOF after ITEM: TIMESTEP")
            fout.write(timestep)

            line = fin.readline()
            if not line or not line.startswith("ITEM: NUMBER OF ATOMS"):
                die(f"Expected 'ITEM: NUMBER OF ATOMS', got: {line.strip() if line else 'EOF'}")
            fout.write(line)
            natoms_line = fin.readline()
            if not natoms_line:
                die("EOF after ITEM: NUMBER OF ATOMS")
            fout.write(natoms_line)
            try:
                natoms = int(natoms_line.strip())
            except Exception:
                die(f"Cannot parse atom count: {natoms_line.strip()!r}")

            line = fin.readline()
            if not line or not line.startswith("ITEM: BOX BOUNDS"):
                die(f"Expected 'ITEM: BOX BOUNDS', got: {line.strip() if line else 'EOF'}")
            fout.write(line)

            bounds = []
            for _ in range(3):
                bline = fin.readline()
                if not bline:
                    die("EOF while reading BOX BOUNDS")
                fout.write(bline)
                parts = bline.split()
                if len(parts) < 2:
                    die(f"Bad BOX BOUNDS line: {bline.strip()!r}")
                # If tilt factors exist, parts would be 3; we don't support that yet.
                if len(parts) >= 3:
                    die("Triclinic BOX BOUNDS (tilt factors) not supported. Re-dump with x/y/z or use orthorhombic box.")
                lo, hi = float(parts[0]), float(parts[1])
                bounds.append((lo, hi))

            (xlo, xhi), (ylo, yhi), (zlo, zhi) = bounds
            lx, ly, lz = (xhi - xlo), (yhi - ylo), (zhi - zlo)

            line = fin.readline()
            if not line or not line.startswith("ITEM: ATOMS"):
                die(f"Expected 'ITEM: ATOMS ...', got: {line.strip() if line else 'EOF'}")

            header_parts = line.strip().split()
            keys = header_parts[2:]

            try:
                i_xs = keys.index("xs")
                i_ys = keys.index("ys")
                i_zs = keys.index("zs")
            except ValueError:
                die(f"ATOMS header must include xs/ys/zs. Got keys={keys}")

            new_keys = list(keys)
            new_keys[i_xs] = "x"
            new_keys[i_ys] = "y"
            new_keys[i_zs] = "z"
            fout.write("ITEM: ATOMS " + " ".join(new_keys) + "\n")

            for _ in range(natoms):
                aline = fin.readline()
                if not aline:
                    die("EOF while reading ATOMS")
                parts = aline.split()
                if len(parts) < len(keys):
                    die(f"Atom line too short. Expected >= {len(keys)} cols, got {len(parts)}: {aline.strip()!r}")

                xs = float(parts[i_xs]); ys = float(parts[i_ys]); zs = float(parts[i_zs])
                x = xlo + xs * lx
                y = ylo + ys * ly
                z = zlo + zs * lz

                parts[i_xs] = fmt.format(x)
                parts[i_ys] = fmt.format(y)
                parts[i_zs] = fmt.format(z)

                fout.write(" ".join(parts) + "\n")

            frames += 1

    print(f"Converted {frames} frame(s): {args.input} -> {args.output}")


if __name__ == "__main__":
    main()
