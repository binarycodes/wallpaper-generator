#!/usr/bin/env python3
"""Draw the source bitmap for the hand-made deathstar type into a directory,
ready for img2type.py.   tools/draw_sources.py OUT_DIR
"""
import os
import sys
from pathlib import Path

# Re-exec under the project's .venv so the tools run without activating it.
_venv_py = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
if _venv_py.is_file() and Path(sys.prefix).resolve() != _venv_py.parent.parent.resolve():
    os.execv(str(_venv_py), [str(_venv_py), __file__, *sys.argv[1:]])

import math

import numpy as np
from PIL import Image



def deathstar(size=1024):
    cx, cy, R = size / 2, size / 2, size * 0.46
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    dx, dy = (xx - cx) / R, (yy - cy) / R
    r2 = dx * dx + dy * dy
    inside = r2 <= 1.0
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    light = np.array([-0.55, -0.6, 0.58]); light /= np.linalg.norm(light)
    shade = np.clip(dx * light[0] + dy * light[1] + nz * light[2], 0, 1) ** 0.9
    img = np.where(inside, 0.12 + 0.85 * shade, 0.0)
    # superlaser dish: dark concave bowl, bright rim, bright focus lens
    ddx, ddy = dx - 0.40, dy + 0.38
    dr = np.sqrt(ddx * ddx + ddy * ddy) / 0.34
    dish = (dr <= 1.0) & inside
    bowl = 0.08 + 0.30 * dr ** 2 * shade
    img = np.where(dish, bowl, img)
    img = np.where(inside & (np.abs(dr - 1.0) < 0.07), 1.0, img)                      # outer rim
    img = np.where(dish & (np.abs(dr - 0.55) < 0.05), 0.6, img)                      # inner ring
    img = np.where(dish & (dr < 0.13), 1.0, img)                                     # focus lens
    # equatorial trench: black band with a lit upper edge
    band = dy - 0.08
    trench = inside & (np.abs(band) < 0.045) & ~dish
    img = np.where(trench, 0.0, img)
    img = np.where(inside & (band > -0.075) & (band < -0.045) & ~dish, np.minimum(1.0, img + 0.35), img)
    # sparse city-light specks on the dark side
    rng = np.random.default_rng(3)
    specks = (rng.random(img.shape) < 0.004) & inside & (shade < 0.25) & ~dish & ~trench
    img = np.where(specks, 0.9, img)
    img = np.where(inside & (r2 > 0.985), 1.0, img)                                   # rim light
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "sources")
    out.mkdir(parents=True, exist_ok=True)
    deathstar().save(out / "deathstar.png")
    print("wrote", out / "deathstar.png")
