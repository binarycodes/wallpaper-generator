#!/usr/bin/env python3
"""Rasterise a single-colour SVG icon (e.g. from simple-icons) to a white-on-black PNG
without any native graphics library, for img2type.py.

    tools/svg2png.py archlinux.svg arch.png [--size 1024]

Curves are flattened to polygons and each subpath is XOR-filled, which reproduces
even-odd holes in typical icon paths.
"""
import os
import sys
from pathlib import Path

# Re-exec under the project's .venv so the tools run without activating it.
_venv_py = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
if _venv_py.is_file() and Path(sys.prefix).resolve() != _venv_py.parent.parent.resolve():
    os.execv(str(_venv_py), [str(_venv_py), __file__, *sys.argv[1:]])

import argparse

from PIL import Image, ImageChops, ImageDraw
from svgelements import SVG, Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("svg")
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--pad", type=float, default=0.06, help="margin fraction; default %(default)s")
    args = ap.parse_args()

    svg = SVG.parse(args.svg)
    vb = svg.viewbox
    size = args.size
    scale = size * (1 - 2 * args.pad) / max(vb.width, vb.height)
    ox = (size - vb.width * scale) / 2 - vb.x * scale
    oy = (size - vb.height * scale) / 2 - vb.y * scale
    mask = Image.new("1", (size, size), 0)
    for path in (e for e in svg.elements() if isinstance(e, Path)):
        for sub in path.as_subpaths():
            pts = []
            for seg in Path(sub):
                kind = seg.__class__.__name__
                if kind == "Move":
                    continue
                n = 1 if kind in ("Line", "Close") else 24
                for i in range(n + 1):
                    p = seg.point(i / n)
                    pts.append((p.x * scale + ox, p.y * scale + oy))
            if len(pts) >= 3:
                m = Image.new("1", (size, size), 0)
                ImageDraw.Draw(m).polygon(pts, fill=1)
                mask = ImageChops.logical_xor(mask, m)
    mask.convert("L").save(args.out)
    print("wrote", args.out)


if __name__ == "__main__":
    sys.exit(main())
