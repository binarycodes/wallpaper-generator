"""Navy night sky with a star field and a teal glow; every dot of the art becomes a star."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ._common import grade_greys, luminance, unit

TEXT = {"subtitle": (120, 140, 175), "prompt": (140, 160, 195), "footer": (90, 110, 145)}
SKY_CENTRE = np.array([22, 32, 62], np.float32)
SKY_EDGE = np.array([8, 12, 26], np.float32)
SKY_GLOW = np.array([0, 40, 60], np.float32)
STAR_TINT = np.array([200, 215, 235], np.float32)
ART_GLOW = np.array([20, 80, 140], np.float32)
SPARK_TINT = np.array([235, 245, 255], np.float32)
SPARK_HALO = np.array([120, 160, 200], np.float32)
HEADER_INK = (190, 210, 245)    # the brightest header grey becomes this pale starlight; darker greys sink towards SKY_CENTRE
GRADE_SAT = 24                  # pixels less saturated than this are graded onto the sky palette
DOT_DROP = 0.00                 # share of braille dots left dark
DOT_SIZE_JITTER = 0.40          # 0 uniform dots, 0.5 gentle size mix, 1 large variance
DOT_STRIDE = 2                  # keep every Nth dot in both directions: 1 all dots, 2 gaps double


def base(size, s, seed):
    """Canvas of the given size; s is the layout scale generate.py uses."""
    W, H = size
    rng = np.random.default_rng(seed)
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
    lum = unit(stars) + 0.5 * unit(halo)
    sky += lum[..., None] * STAR_TINT
    return Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))


def draw_art(img, dots, pitch, s, seed):
    """Braille dots become stars: points of varying brightness with a soft halo,
    over a faint glow of the whole shape. A stride thins the lattice evenly and
    a random share of the rest is left dark so the cluster breathes; the type
    file's colour sets each dot's brightness so its fades carry over."""
    rng = np.random.default_rng(seed)
    points = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(points)
    x_min = min(cx for cx, _, _ in dots)
    y_min = min(cy for _, cy, _ in dots)
    for cx, cy, col in dots:
        gx, gy = round((cx - x_min) / pitch), round((cy - y_min) / pitch)
        if gx % DOT_STRIDE or gy % DOT_STRIDE or rng.random() < DOT_DROP:
            continue
        r = pitch * 0.20 * rng.lognormal(0, 0.45 * DOT_SIZE_JITTER)   # median stays the medium size
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=int(255 * luminance(col) * min(1.0, 0.35 + rng.exponential(0.5))))
    halo = points.filter(ImageFilter.GaussianBlur(pitch * 0.35))
    glow = points.filter(ImageFilter.GaussianBlur(pitch * 2.5))

    a = grade_greys(img, SKY_CENTRE, HEADER_INK, GRADE_SAT)
    a += unit(glow)[..., None] * ART_GLOW
    a += unit(halo)[..., None] * SPARK_HALO
    a += unit(points)[..., None] * SPARK_TINT
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
