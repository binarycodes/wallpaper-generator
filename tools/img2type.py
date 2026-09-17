#!/usr/bin/env python3
"""Convert an image into a braille-art type file for generate.py.

    tools/img2type.py logo.png types/logo.txt --cols 48
    tools/img2type.py photo.png types/photo.txt --cols 56 --dither --color '#DDDDDD' --color2 '#666666'

Each braille cell is 2x4 dots and generate.py draws dots on a square pitch, so the
image is simply resized to (cols*2) x (rows*4) dots with its aspect ratio kept.
Transparent pixels count as background. --threshold keeps pixels brighter than the
cutoff; --dither keeps grey levels as Floyd-Steinberg dot density instead.
"""
import os
import sys
from pathlib import Path

# Re-exec under the project's .venv so the tools run without activating it.
_venv_py = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
if _venv_py.is_file() and Path(sys.prefix).resolve() != _venv_py.parent.parent.resolve():
    os.execv(str(_venv_py), [str(_venv_py), __file__, *sys.argv[1:]])

import argparse

import numpy as np
from PIL import Image

BITS = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08),
        (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]


def to_gray(img):
    """Grey image where background is black, regardless of alpha or polarity."""
    img = img.convert("RGBA")
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return lum * a[..., 3]


def lerp(c1, c2, t):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("out", help="types/<name>.txt")
    ap.add_argument("--cols", type=int, default=48, help="braille columns (2 dots each); default %(default)s")
    ap.add_argument("--dither", action="store_true", help="Floyd-Steinberg instead of a hard threshold")
    ap.add_argument("--threshold", type=float, default=0.5, help="0..1 cutoff; default %(default)s")
    ap.add_argument("--invert", action="store_true", help="for dark-on-light images")
    ap.add_argument("--exact", action="store_true", help="image is already one pixel per dot; do not resize")
    ap.add_argument("--color", default="#CCCCCC")
    ap.add_argument("--color2", help="if given, rows fade from --color (top) to --color2 (bottom)")
    args = ap.parse_args()

    g = to_gray(Image.open(args.image))
    if args.invert:
        g = 1.0 - g
    ys, xs = np.where(g > 0.02)             # trim empty margins
    g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    if not args.exact:
        h, w = g.shape
        dw = args.cols * 2
        dh = max(4, int(round(h * dw / w / 4)) * 4)
        g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((dw, dh), Image.LANCZOS)) / 255.0
    dh, dw = g.shape
    dw += dw % 2; dh += (-dh) % 4
    pad = np.zeros((dh, dw)); pad[:g.shape[0], :g.shape[1]] = g; g = pad

    if args.dither:
        on = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).convert("1", dither=Image.FLOYDSTEINBERG)) > 0
    else:
        on = g > args.threshold

    rows, cols = dh // 4, dw // 2
    c1 = hexrgb(args.color); c2 = hexrgb(args.color2) if args.color2 else c1
    lines = []
    for r in range(rows):
        col = lerp(c1, c2, r / max(1, rows - 1))
        cells = []
        for c in range(cols):
            code = 0x2800
            for dx, dy, bit in BITS:
                if on[r * 4 + dy, c * 2 + dx]:
                    code |= bit
            cells.append(chr(code))
        lines.append("[#%02X%02X%02X]%s[/]" % (*col, "".join(cells)))
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}: {cols} cols x {rows} rows ({int(on.sum())} dots)")


if __name__ == "__main__":
    sys.exit(main())
