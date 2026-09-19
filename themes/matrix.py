"""Green on black: glyph rain with bright heads and fading trails, phosphor glow,
faint CRT scanlines. The art is rebuilt from glyphs with the rain dimmed behind
it, and grey pixels already on the canvas (the header) are graded to green so
nothing on the page is off-palette."""
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ._common import grade_greys, luminance, size_jitter, thin, unit

FONT = Path(__file__).resolve().parent.parent / "fonts" / "DejaVuSansMono.ttf"
TEXT_FONT = FONT.with_name("VT323-Regular.ttf")   # boxy CRT face for subtitle and footer
TEXT_SCALE = 1.3                # VT323 draws small for its point size
GLYPHS = "0123456789ABCDEFXZ+-*/<>=[]{}|;:#$%&@ΞΨΩΣΔΛΠΘΦЖДЯЦ"
TEXT = {"subtitle": (70, 200, 100), "prompt": (110, 235, 140), "footer": (40, 140, 70)}
BG = (0, 6, 2)
TRAIL = np.array([0, 255, 70], np.float32)
HEAD = np.array([190, 255, 200], np.float32)
GLOW = np.array([0, 120, 40], np.float32)
GRADE_INK = (64, 255, 89)       # the brightest header grey becomes this; darker greys sink towards BG

RAIN_GLYPH = 24                 # glyph size in layout units
RAIN_ROW = 1.05                 # vertical glyph pitch as a multiple of the glyph size
RAIN_FILL = 0.7                 # share of column slots that carry a trail
RAIN_TRAILS = (1, 2)            # trails attempted per column, min and max
TRAIL_LEN = (8, 40)             # glyphs per trail, min and max
TRAIL_FADE = 1.6                # exponent of the fade along a trail; higher dies faster
RAIN_INTENSITY = 0.55           # trail brightness; 1 is full phosphor green
RAIN_GLOW_BLUR = 0.6            # glow radius as a multiple of the glyph size
RAIN_GLOW_HEAD = 0.5            # share of the glow that comes from the heads rather than the trails
SCANLINES = 0.12                # darkening of every other scanline; 0 disables
SCANLINE_PX = 3                 # scanline period in output pixels

ART_GLYPH = 1.35                # art glyph size as a multiple of the dot pitch
DOT_DROP = 0.00                 # share of art glyphs left out
DOT_SIZE_JITTER = 0.40          # 0 uniform glyphs, 0.5 gentle size mix, 1 large variance
DOT_STRIDE = 2                  # keep every Nth dot in both directions: 1 all dots, 2 gaps double
ART_HEADS = 0.04                # share of art glyphs drawn in the bright head colour
ART_BRIGHT = (0.55, 1.0)        # brightness range of the other art glyphs before the type colour
ART_GLOW_BLUR = 0.9             # art glow radius as a multiple of the dot pitch
ART_GLOW_HEAD = 0.4             # share of the art glow that comes from the heads
ART_DIM = 0.65                  # how much the rain fades behind the art
ART_DIM_MARGIN = 2              # dimmed margin around the art, in dot pitches
ART_DIM_BLUR = 3                # softness of that margin, in dot pitches
GRADE_SAT = 40                  # pixels less saturated than this are graded to green


@lru_cache(maxsize=None)
def _font(size):
    return ImageFont.truetype(str(FONT), max(1, int(size)))


def base(size, s, seed):
    W, H = size
    rng = np.random.default_rng(seed)
    gs = int(RAIN_GLYPH * s)
    font = ImageFont.truetype(str(FONT), gs)
    cw, rh = gs, int(gs * RAIN_ROW)
    trail = Image.new("L", size, 0)
    head = Image.new("L", size, 0)
    dt, dh = ImageDraw.Draw(trail), ImageDraw.Draw(head)
    rows = H // rh + 2
    for col in range(W // cw + 1):
        for _ in range(rng.integers(RAIN_TRAILS[0], RAIN_TRAILS[1] + 1)):
            if rng.random() > RAIN_FILL:
                continue
            length = int(rng.integers(*TRAIL_LEN))
            start = int(rng.integers(-length, rows))
            x = col * cw + cw // 2
            for i in range(length):
                y = (start + i) * rh
                if not 0 <= y < H:
                    continue
                ch = GLYPHS[rng.integers(len(GLYPHS))]
                if i == length - 1:
                    dh.text((x, y), ch, font=font, fill=255, anchor="mm")
                else:
                    dt.text((x, y), ch, font=font, fill=int(255 * ((i + 1) / length) ** TRAIL_FADE), anchor="mm")
    glow = Image.blend(trail, head, RAIN_GLOW_HEAD).filter(ImageFilter.GaussianBlur(gs * RAIN_GLOW_BLUR))
    a = np.full((H, W, 3), BG, np.float32)
    a += unit(trail)[..., None] * TRAIL * RAIN_INTENSITY
    a += unit(head)[..., None] * HEAD
    a += unit(glow)[..., None] * GLOW
    if SCANLINES:
        period = max(2, int(SCANLINE_PX * s))
        dark = (np.arange(H) // period % 2 == 1)[:, None, None]
        a *= np.where(dark, 1 - SCANLINES, 1.0)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))



def draw_art(img, dots, pitch, s, seed):
    rng = np.random.default_rng(seed)
    a = grade_greys(img, BG, GRADE_INK, GRADE_SAT)

    xs = [cx for cx, _, _ in dots]
    ys = [cy for _, cy, _ in dots]
    shade = Image.new("L", img.size, 0)
    m = pitch * ART_DIM_MARGIN
    ImageDraw.Draw(shade).rounded_rectangle([min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m],
                                            radius=m, fill=255)
    shade = shade.filter(ImageFilter.GaussianBlur(pitch * ART_DIM_BLUR))
    a *= 1 - ART_DIM * unit(shade)[..., None]

    body = Image.new("L", img.size, 0)
    head = Image.new("L", img.size, 0)
    db, dh = ImageDraw.Draw(body), ImageDraw.Draw(head)
    for cx, cy, col in thin(dots, pitch, rng, DOT_DROP, DOT_STRIDE):
        ch = GLYPHS[rng.integers(len(GLYPHS))]
        font = _font(pitch * ART_GLYPH * size_jitter(rng, DOT_SIZE_JITTER))
        if rng.random() < ART_HEADS:
            dh.text((cx, cy), ch, font=font, fill=255, anchor="mm")
        else:
            lo, hi = ART_BRIGHT
            db.text((cx, cy), ch, font=font, fill=int(255 * luminance(col) * rng.uniform(lo, hi)), anchor="mm")
    glow = Image.blend(body, head, ART_GLOW_HEAD).filter(ImageFilter.GaussianBlur(pitch * ART_GLOW_BLUR))
    a += unit(glow)[..., None] * GLOW
    a += unit(body)[..., None] * TRAIL
    a += unit(head)[..., None] * HEAD
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
