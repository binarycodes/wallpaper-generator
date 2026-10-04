#!/usr/bin/env python3
"""Draw the source bitmaps for the hand-made types into a directory,
ready for img2type.py.   tools/draw_sources.py OUT_DIR

denied.png is already one pixel per dot, so convert it with --exact.
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
from PIL import Image, ImageDraw



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


# 5x7 glyphs for the banner, '#' = dot
GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    " ": ["....."] * 7,
}


def denied(w=208, h=128, ss=8):
    """Padlock inside a scanner reticle, crossed by a hazard banner reading ACCESS DENIED.
    Returned one pixel per dot: shapes are drawn at ss x and box-filtered, text is stamped exactly."""
    big = Image.new("L", (w * ss, h * ss), 0)
    d = ImageDraw.Draw(big)
    cx, cy = w / 2 * ss, 60 * ss

    def ring(r0, r1, a0=0, a1=360):
        d.pieslice([cx - r1, cy - r1, cx + r1, cy + r1], a0, a1, fill=255)
        d.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], fill=0)

    def spoke(ang, r0, r1, width):
        t = math.radians(ang)
        d.line([cx + r0 * math.cos(t), cy + r0 * math.sin(t), cx + r1 * math.cos(t), cy + r1 * math.sin(t)],
               fill=255, width=int(width))

    # reticle, drawn outside-in because each ring clears its own hole
    ring(58.5 * ss, 60.5 * ss)                                                       # outer rim
    ring(56 * ss, 56 * ss)                                                           # clear hole only
    for i in range(36):                                                              # tick dial
        major = i % 3 == 0
        spoke(i * 10, (51 if major else 53) * ss, 56 * ss, (2.5 if major else 1.5) * ss)
    d.ellipse([cx - 49 * ss, cy - 49 * ss, cx + 49 * ss, cy + 49 * ss], fill=0)
    for i in range(10):                                                              # segmented scan ring
        a0 = -90 + i * 36 + 4
        if i in (6, 7):                                                              # a dead segment pair
            continue
        d.pieslice([cx - 47 * ss, cy - 47 * ss, cx + 47 * ss, cy + 47 * ss], a0, a0 + 28, fill=255)
    d.ellipse([cx - 43 * ss, cy - 43 * ss, cx + 43 * ss, cy + 43 * ss], fill=0)
    for ang in (0, 90, 180, 270):                                                    # cardinal notches
        spoke(ang, 36 * ss, 42 * ss, 2 * ss)

    # padlock: shackle arc + legs, body with an inset panel and a keyhole
    sx, sy, ro, ri = cx, 42 * ss, 15 * ss, 10 * ss
    d.pieslice([sx - ro, sy - ro, sx + ro, sy + ro], 180, 360, fill=255)
    d.pieslice([sx - ri, sy - ri, sx + ri, sy + ri], 180, 360, fill=0)
    d.rectangle([sx - ro, sy, sx - ri, 54 * ss], fill=255)
    d.rectangle([sx + ri, sy, sx + ro, 54 * ss], fill=255)
    bx0, by0, bx1, by1 = cx - 21 * ss, 50 * ss, cx + 21 * ss, 80 * ss
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=4 * ss, fill=255)
    d.rounded_rectangle([bx0 + 3 * ss, by0 + 3 * ss, bx1 - 3 * ss, by1 - 3 * ss], radius=2 * ss, fill=0)
    d.rounded_rectangle([bx0 + 5 * ss, by0 + 5 * ss, bx1 - 5 * ss, by1 - 5 * ss], radius=1 * ss, fill=255)
    kx, ky = cx, 62 * ss
    d.ellipse([kx - 4 * ss, ky - 4 * ss, kx + 4 * ss, ky + 4 * ss], fill=0)
    d.polygon([(kx - 2 * ss, ky), (kx + 2 * ss, ky), (kx + 3 * ss, ky + 10 * ss), (kx - 3 * ss, ky + 10 * ss)], fill=0)

    img = np.asarray(big.resize((w, h), Image.BOX)) > 127

    # banner at exact dot resolution: rails above and below, hazard stripes at the ends, 2x lettering
    by, bh, text, k = 86, 24, "ACCESS DENIED", 2
    img[by - 2:by + bh + 2, :] = False
    img[by, :] = img[by + bh - 1, :] = True
    tw = (len(text) * 6 - 1) * k
    tx, ty = (w - tw) // 2, by + (bh - 7 * k) // 2
    yy, xx = np.mgrid[by + 3:by + bh - 3, 0:w]
    ends = (xx < tx - 4) | (xx >= tx + tw + 4)
    img[by + 3:by + bh - 3, :] = ends & (((xx + yy) // 4) % 2 == 0)
    for i, ch in enumerate(text):
        for r, row in enumerate(GLYPHS[ch]):
            for c, px in enumerate(row):
                if px == "#":
                    x, y = tx + (i * 6 + c) * k, ty + r * k
                    img[y:y + k, x:x + k] = True
    return Image.fromarray(img.astype(np.uint8) * 255)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "sources")
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in (("deathstar", deathstar), ("denied", denied)):
        draw().save(out / f"{name}.png")
        print("wrote", out / f"{name}.png")
