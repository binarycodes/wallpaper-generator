"""Cyanotype drafting sheet: mottled blueprint blue with a fine grid and a
double frame, the art drawn in white ink as an outline of dots over section
hatching, with dimension lines giving its size in braille dots. Grey pixels
already on the canvas (the header) are graded to ink so nothing is off-palette."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ._common import grade_greys, luminance, unit

TEXT_FONT = Path(__file__).resolve().parent.parent / "fonts" / "ShareTechMono-Regular.ttf"
TEXT_SCALE = 1.1                # Share Tech Mono draws a little small for its point size
TEXT = {"subtitle": (200, 220, 245), "prompt": (225, 238, 255), "footer": (150, 180, 220)}
INK = np.array((222, 236, 255), np.float32)       # everything drawn on the paper is this, at some alpha
PAPER = np.array((18, 60, 122), np.float32)
PAPER_EDGE = np.array((10, 38, 84), np.float32)

MOTTLE = 0.14                   # strength of the cyanotype blotching; 0 is flat paper
MOTTLE_CELLS = 48               # blotch size: cells across the width, fewer is coarser
MOTTLE_BLUR = 1.5               # softness of the blotches, in cells

GRID_MINOR = 40                 # minor grid pitch in layout units
GRID_MAJOR = 5                  # a major line every N minor lines
GRID_MINOR_ALPHA = 0.06
GRID_MAJOR_ALPHA = 0.14
GRID_LINE = 1.5                 # line width in layout units

FRAME_MARGIN = 60               # outer frame inset in layout units; the grid is anchored to it
FRAME_INNER = 14                # gap to the inner frame line
FRAME_OUTER_W = 3
FRAME_INNER_W = 1.5
FRAME_ALPHA = 0.55

EDGE_R = 0.22                   # radius of the outline dots as a multiple of the dot pitch
EDGE_ALPHA = 1.0
INNER_R = 0.07                  # radius of the interior dots
INNER_ALPHA = 0.45
FILL_R = 0.55                   # dot radius used to close the shape into a solid mask for hatching
HATCH_PITCH = 0.9               # hatch spacing as a multiple of the dot pitch
HATCH_W = 0.08                  # hatch line width as a multiple of the dot pitch
HATCH_ALPHA = 0.40
HALO_BLUR = 0.6                 # soft bleed around the ink, as a multiple of the dot pitch
HALO_ALPHA = 0.18

DIM_GAP = 1.3                   # dimension line offset from the art, in dot pitches
DIM_TICK = 0.45                 # half-length of the end ticks, in dot pitches
DIM_W = 2                       # dimension line width in layout units
DIM_FONT = 30                   # label size in layout units
DIM_ALPHA = 0.7

GRADE_SAT = 24                  # pixels less saturated than this are graded to ink


def _alpha_layer(size):
    layer = Image.new("L", size, 0)
    return layer, ImageDraw.Draw(layer)


def base(size, s, seed):
    W, H = size
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    t = np.clip(r / 0.6, 0, 1)[..., None]
    a = PAPER * (1 - t) + PAPER_EDGE * t

    cells = (max(1, round(MOTTLE_CELLS * H / W)), MOTTLE_CELLS)
    noise = Image.fromarray((rng.normal(0.5, 0.18, cells).clip(0, 1) * 255).astype(np.uint8))
    noise = noise.filter(ImageFilter.GaussianBlur(MOTTLE_BLUR)).resize(size, Image.BICUBIC)
    a *= 1 + MOTTLE * (unit(noise)[..., None] * 2 - 1)

    lw = max(1, int(GRID_LINE * s))
    m = int(FRAME_MARGIN * s)
    minor, d = _alpha_layer(size)
    major, dm = _alpha_layer(size)
    step = GRID_MINOR * s
    for i, x in enumerate(np.arange(m, W - m + 1, step)):
        (dm if i % GRID_MAJOR == 0 else d).line([(x, m), (x, H - m)], fill=255, width=lw)
    for i, y in enumerate(np.arange(m, H - m + 1, step)):
        (dm if i % GRID_MAJOR == 0 else d).line([(m, y), (W - m, y)], fill=255, width=lw)
    frame, df = _alpha_layer(size)
    df.rectangle([m, m, W - m, H - m], outline=255, width=max(1, int(FRAME_OUTER_W * s)))
    g = m + int(FRAME_INNER * s)
    df.rectangle([g, g, W - g, H - g], outline=255, width=max(1, int(FRAME_INNER_W * s)))

    a += unit(minor)[..., None] * INK * GRID_MINOR_ALPHA
    a += unit(major)[..., None] * INK * GRID_MAJOR_ALPHA
    a += unit(frame)[..., None] * INK * FRAME_ALPHA
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))



def _dimension(d, font, a0, a1, off, label, pitch, s, vertical):
    """A dimension line with end ticks and the label sitting in a gap at its middle."""
    tick = DIM_TICK * pitch
    lw = max(1, int(DIM_W * s))
    tw = font.getlength(label) + 2 * tick
    mid = (a0 + a1) / 2
    if vertical:
        x = off
        d.line([(x, a0), (x, mid - tw / 2)], fill=255, width=lw)
        d.line([(x, mid + tw / 2), (x, a1)], fill=255, width=lw)
        for y in (a0, a1):
            d.line([(x - tick, y), (x + tick, y)], fill=255, width=lw)
        d.text((x, mid), label, font=font, fill=255, anchor="mm")
    else:
        y = off
        d.line([(a0, y), (mid - tw / 2, y)], fill=255, width=lw)
        d.line([(mid + tw / 2, y), (a1, y)], fill=255, width=lw)
        for x in (a0, a1):
            d.line([(x, y - tick), (x, y + tick)], fill=255, width=lw)
        d.text((mid, y), label, font=font, fill=255, anchor="mm")


def draw_art(img, dots, pitch, s, seed):
    """Dots on the shape's boundary are drawn as full ink, interior dots as faint
    points, and the closed shape is section-hatched. Boundary means a dot with a
    missing four-neighbour in the braille lattice, so the type file is the only input."""
    a = grade_greys(img, PAPER, INK, GRADE_SAT)
    x_min, x_max = min(cx for cx, _, _ in dots), max(cx for cx, _, _ in dots)
    y_min, y_max = min(cy for _, cy, _ in dots), max(cy for _, cy, _ in dots)
    grid = {(round((cx - x_min) / pitch), round((cy - y_min) / pitch)) for cx, cy, _ in dots}

    ink, di = _alpha_layer(img.size)
    fill, dfill = _alpha_layer(img.size)
    for cx, cy, col in dots:
        gx, gy = round((cx - x_min) / pitch), round((cy - y_min) / pitch)
        edge = any((gx + dx, gy + dy) not in grid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        r = pitch * (EDGE_R if edge else INNER_R)
        di.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=int(255 * luminance(col) * (EDGE_ALPHA if edge else INNER_ALPHA)))
        fr = pitch * FILL_R
        dfill.ellipse([cx - fr, cy - fr, cx + fr, cy + fr], fill=int(255 * luminance(col)))

    hatch, dh = _alpha_layer(img.size)
    span = (x_max - x_min) + (y_max - y_min) + 2 * pitch
    hw = max(1, int(pitch * HATCH_W))
    for k in np.arange(-span, span, pitch * HATCH_PITCH):
        dh.line([(x_min - pitch + k, y_min - pitch), (x_min - pitch + k + span, y_min - pitch + span)],
                fill=255, width=hw)
    hatch = unit(hatch) * unit(fill) * HATCH_ALPHA

    font = ImageFont.truetype(str(TEXT_FONT), int(DIM_FONT * s * TEXT_SCALE))
    dim, dd = _alpha_layer(img.size)
    cols, rows = round((x_max - x_min) / pitch) + 1, round((y_max - y_min) / pitch) + 1
    _dimension(dd, font, x_min, x_max, y_max + DIM_GAP * pitch, str(cols), pitch, s, vertical=False)
    _dimension(dd, font, y_min, y_max, x_max + DIM_GAP * pitch, str(rows), pitch, s, vertical=True)

    halo = ink.filter(ImageFilter.GaussianBlur(pitch * HALO_BLUR))
    a += unit(halo)[..., None] * INK * HALO_ALPHA
    a += hatch[..., None] * INK
    a += unit(ink)[..., None] * INK
    a += unit(dim)[..., None] * INK * DIM_ALPHA
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
