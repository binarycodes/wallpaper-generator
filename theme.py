"""Themes for generate.py: the base canvas, how the centre art is drawn on it,
and the text colours that read well against it.

`plain` is the near-black terminal look; `constellation` is a navy night sky
where every dot of the art becomes a star.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

THEMES = ("plain", "constellation")

PLAIN_BG = (13, 16, 22)
PLAIN_TEXT = {"subtitle": (85, 85, 85), "prompt": (120, 120, 120), "footer": (70, 70, 70)}
SKY_TEXT = {"subtitle": (120, 140, 175), "prompt": (140, 160, 195), "footer": (90, 110, 145)}
SKY_CENTRE = np.array([22, 32, 62], np.float32)
SKY_EDGE = np.array([8, 12, 26], np.float32)
SKY_GLOW = np.array([0, 40, 60], np.float32)
STAR_TINT = np.array([200, 215, 235], np.float32)
ART_GLOW = np.array([20, 80, 140], np.float32)
SPARK_TINT = np.array([235, 245, 255], np.float32)
SPARK_HALO = np.array([120, 160, 200], np.float32)
DOT_DROP = 0.00                 # share of braille dots left dark in the constellation theme
DOT_SIZE_JITTER = 0.40          # 0 uniform dots, 0.5 gentle size mix, 1 large variance
DOT_STRIDE = 2                  # keep every Nth dot in both directions: 1 all dots, 2 gaps double


def text_colours(theme):
    return SKY_TEXT if theme == "constellation" else PLAIN_TEXT


def base(theme, size, s):
    """Canvas of the given size; s is the layout scale generate.py uses."""
    if theme == "plain":
        return Image.new("RGB", size, PLAIN_BG)
    return _sky(size, s)


def _sky(size, s):
    W, H = size
    rng = np.random.default_rng(3)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * 0.45) / W) ** 2 + ((yy - H * 0.45) / H) ** 2)
    t = np.clip(r / 0.7, 0, 1)[..., None]
    sky = SKY_CENTRE * (1 - t) + SKY_EDGE * t
    glow = np.exp(-(((xx - W * 0.85) / (W * 0.25)) ** 2 + ((yy - H * 0.9) / (H * 0.35)) ** 2))
    sky += glow[..., None] * SKY_GLOW

    stars = Image.new("L", size, 0)
    d = ImageDraw.Draw(stars)
    n = int(2800 * (W * H) / (s * s) / (3840 * 2160))     # constant density in layout units
    xs, ys = rng.uniform(0, W, n), rng.uniform(0, H, n)
    rad = (rng.exponential(0.6, n) + 0.5) * s
    bright = np.clip(rng.exponential(60, n) + 25, 0, 255)
    for x, y, rr, b in zip(xs, ys, rad, bright):
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=int(b))
    halo = stars.filter(ImageFilter.GaussianBlur(4 * s))
    lum = _f(stars) + 0.5 * _f(halo)
    sky += lum[..., None] * STAR_TINT
    return Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))


def draw_art(img, theme, dots, pitch, s):
    """dots is [(cx, cy, colour)] on the supersampled canvas; pitch is the dot spacing."""
    if theme == "plain":
        d = ImageDraw.Draw(img)
        rad = pitch * 0.30
        for cx, cy, col in dots:
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
        return
    _constellation_art(img, dots, pitch, s)


def _constellation_art(img, dots, pitch, s):
    """Braille dots become stars: points of varying brightness with a soft halo,
    over a faint glow of the whole shape. A stride thins the lattice evenly and
    a random share of the rest is left dark so the cluster breathes; the type
    file's colour sets each dot's brightness so its fades carry over."""
    rng = np.random.default_rng(3)
    points = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(points)
    x_min = min(cx for cx, _, _ in dots)
    y_min = min(cy for _, cy, _ in dots)
    for cx, cy, col in dots:
        gx, gy = round((cx - x_min) / pitch), round((cy - y_min) / pitch)
        if gx % DOT_STRIDE or gy % DOT_STRIDE or rng.random() < DOT_DROP:
            continue
        lum = (0.299 * col[0] + 0.587 * col[1] + 0.114 * col[2]) / 255
        r = pitch * 0.20 * rng.lognormal(0, 0.45 * DOT_SIZE_JITTER)   # median stays the medium size
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(255 * lum * min(1.0, 0.35 + rng.exponential(0.5))))
    halo = points.filter(ImageFilter.GaussianBlur(pitch * 0.35))
    glow = points.filter(ImageFilter.GaussianBlur(pitch * 2.5))

    a = np.asarray(img).astype(np.float32)
    a += _f(glow)[..., None] * ART_GLOW
    a += _f(halo)[..., None] * SPARK_HALO
    a += _f(points)[..., None] * SPARK_TINT
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))


def _f(im):
    return np.asarray(im).astype(np.float32) / 255
