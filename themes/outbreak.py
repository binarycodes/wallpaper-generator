"""Containment breach: grimy concrete lit by a red emergency lamp, a spray-painted
biohazard stencil, and blood everywhere. Drips run down from the top of the wall,
splatter clusters hit it at random, and the art itself is blood: every braille
dot is a droplet, neighbours pool together, dots on the shape's underside drip,
and a fine spray surrounds it, all fading from fresh red at the top to near-black at
the bottom. The header is graded to blood red and its lettering bleeds from its lower
edges. Bullet holes punch through wall, header and art alike. The type file's colour
fade is ignored; blood is blood."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ._common import grade_greys, size_jitter, thin, unit

TEXT = {"subtitle": (200, 184, 168), "prompt": (176, 32, 36), "footer": (120, 26, 30)}
BG = (14, 10, 10)
LAMP = np.array([96, 0, 6], np.float32)           # emergency light colour, added where the lamp glow reaches
LAMP_POS = (0.0, 1.0)                             # lamp position as a fraction of width and height; kept away from the header
LAMP_SPREAD = (0.50, 0.60)                        # glow radius as a fraction of width and height
BLOOD = np.array([150, 8, 14], np.float32)        # fresh blood where the layer is thick
BLOOD_DARK = np.array([56, 3, 7], np.float32)     # thin rims and dried edges
GLOSS = np.array([238, 118, 118], np.float32)     # wet highlight along the top edge of every blob
GLOSS_ALPHA = 0.35
GLOSS_SHIFT = 2.5                                 # highlight thickness in layout units
SHADOW = np.array([0, 0, 0], np.float32)
SHADOW_ALPHA = 0.55                               # drop shadow under every blob, for depth
SHADOW_OFFSET = 4                                 # shadow offset down and right in layout units
SHADOW_BLUR = 5                                   # shadow softness in layout units
BLOOD_OPACITY = 0.96
THICK_BLUR = 0.5                                  # blur radius that turns coverage into thickness, in dot pitches

GRIME = 0.22                                      # strength of the concrete mottle; 0 is flat paint
GRIME_CELLS = (24, 96, 384)                       # noise octaves as cells across the width, coarse to fine
GRIME_WEIGHTS = (0.5, 0.3, 0.2)
STREAKS = 0.30                                    # darkening from vertical water streaks
STREAK_CELLS = 160                                # streak count across the width, roughly
STREAK_FADE = 1.8                                 # how quickly streaks fade towards the floor; higher is faster
SCRATCHES = 90                                    # thin light scratches on the wall
SCRATCH_ALPHA = 0.10
SCRATCH_LEN = (80, 420)                           # scratch length range in layout units

STENCIL_RADIUS = 0.27                             # biohazard symbol size as a fraction of the height
STENCIL_POS = (0.5, 0.5)                          # symbol centre as a fraction of width and height
STENCIL_TINT = np.array([150, 26, 30], np.float32)
STENCIL_ALPHA = 0.13
STENCIL_SPRAY = 0.55                              # unevenness of the spray paint; 0 is a flat stencil
STENCIL_ARM = 1.0                                 # trefoil arm radius, relative to STENCIL_RADIUS
STENCIL_ARM_HOLE = 0.58
STENCIL_ARM_OFFSET = 0.72                         # arm centre distance from the symbol centre
STENCIL_CORE_HOLE = 0.36                          # radius cleared in the middle
STENCIL_RING = (0.30, 0.22)                       # central ring outer and inner radius
STENCIL_GAP = 0.06                                # width of the three breaks in the ring, as a fraction

WALL_DRIPS = 16                                   # drips hanging from the top edge
WALL_DRIP_LEN = (320, 0.6)                        # median length in layout units and lognormal spread
WALL_DRIP_WIDTH = (7, 16)                         # width range in layout units
WALL_SPLATTERS = 3                                # splatter clusters on the wall
SPLAT_ZONE = (0.30, 0.65)                         # clusters stay outside the middle band of the width and above this share of the height
SPLAT_DROPS = 70                                  # droplets per cluster
SPLAT_SPREAD = 110                                # cluster radius (one sigma) in layout units
SPLAT_DROP_R = 5.0                                # mean droplet radius in layout units
SPLAT_STREAKS = 9                                 # radial streaks per cluster
SPLAT_STREAK_LEN = (60, 220)

DOT_R = 0.54                                      # droplet radius as a multiple of the dot pitch; over 0.5 pools everything
DOT_SQUASH = 1.08                                 # vertical stretch of each droplet
DOT_DROP = 0.00                                   # share of droplets left out
DOT_SIZE_JITTER = 0.40                            # 0 uniform droplets, 0.5 gentle size mix, 1 large variance
DOT_STRIDE = 2                                    # keep every Nth dot in both directions: 1 all dots, 2 gaps double
ART_DRIP_CHANCE = 0.10                            # share of underside dots that drip
ART_DRIP_LEN = (4.0, 0.7)                         # median length in dot pitches and lognormal spread
ART_DRIP_WIDTH = (0.25, 0.45)                     # width range in dot pitches
ART_SPRAY = 0.5                                   # spray droplets per art dot
ART_SPRAY_SPREAD = 2.5                            # spray distance (one sigma) in dot pitches
ART_SPRAY_R = 0.12                                # mean spray droplet radius in dot pitches
ART_FADE = (1.0, -0.55)                           # blood freshness at the top and bottom of the art: 1 is BLOOD, 0 is BLOOD_DARK, negative sinks towards black

WALL_HOLES = 5                                    # bullet holes in the wall and header
ART_HOLES = 3                                     # bullet holes through the art
HOLE_R = (15, 26)                                 # hole radius range in layout units
HOLE_JAG = 0.18                                   # raggedness of the hole edge; 0 is a perfect circle
HOLE_CORE = 0.55                                  # pitch-black core radius, relative to the hole
HOLE_CRATER = np.array([12, 7, 7], np.float32)
HOLE_RIM = np.array([158, 138, 124], np.float32)  # chipped concrete; kept warm so the header grade leaves it alone
HOLE_RIM_W = 0.45                                 # rim width, relative to the hole radius
HOLE_RIM_ALPHA = 0.8
HOLE_RIM_GRAIN = 0.5                              # unevenness of the chipped rim; 0 is flat
HOLE_CRACKS = (3, 6)                              # radial cracks per hole, min and max
HOLE_CRACK_LEN = (1.2, 3.5)                       # crack length range, relative to the hole radius
HOLE_SCORCH = 0.45                                # darkening of the dust halo around each hole
HOLE_SCORCH_R = 2.2                               # halo radius, relative to the hole
HOLE_ZONE = 0.72                                  # wall holes stay above this share of the height, clear of the text
HOLE_BLEED = 0.75                                 # share of holes that bleed; 0 leaves them dry
HOLE_BLEED_DROPS = 40                             # fresh spatter droplets around a bleeding hole
HOLE_BLEED_SPREAD = 1.6                           # spatter radius (one sigma), relative to the hole radius
HOLE_BLEED_DROP_R = 0.16                          # mean spatter droplet radius, relative to the hole
HOLE_BLEED_DRIPS = (1, 2)                         # drips running out of a bleeding hole, min and max
HOLE_BLEED_LEN = (6.0, 0.6)                       # median drip length relative to the hole radius, and lognormal spread
HOLE_BLEED_WIDTH = (0.25, 0.45)                   # drip width range relative to the hole radius

HEADER_INK = (214, 26, 32)                        # the brightest header grey becomes this; darker greys sink towards BG
GRADE_SAT = 24
HEADER_LUM = 0.25                                 # canvas pixels brighter than this and grey count as header
HEADER_DRIPS = 14                                 # drips hanging from the header lettering
HEADER_DRIP_SPACING = 90                          # minimum gap between header drips in layout units
HEADER_DRIP_MIN_RUN = 12                          # skip lettering thinner than this, in layout units
HEADER_DRIP_LEN = (110, 0.7)                      # median length in layout units and lognormal spread
HEADER_DRIP_WIDTH = (5, 11)


def _layer(size):
    layer = Image.new("L", size, 0)
    return layer, ImageDraw.Draw(layer)


def _noise(rng, size, cells, blur=1.0):
    """Smooth 0..1 noise field at the canvas size, generated on a coarse grid."""
    W, H = size
    grid = (max(1, round(cells * H / W)), cells)
    im = Image.fromarray((rng.random(grid) * 255).astype(np.uint8))
    return unit(im.filter(ImageFilter.GaussianBlur(blur)).resize(size, Image.BICUBIC))


def _drip(d, x, y, length, width, rng):
    """One blood run: a pooled head, a wobbling tapering trail and a drop at the end."""
    d.ellipse([x - width * 1.4, y - width * 0.9, x + width * 1.4, y + width * 0.9], fill=255)
    steps = max(2, int(length / (width * 0.5)))
    for i in range(steps):
        t = i / steps
        w = width * (1 - 0.55 * t)
        x += rng.normal(0, width * 0.06)
        yy = y + t * length
        d.ellipse([x - w / 2, yy - w / 2, x + w / 2, yy + w / 2], fill=255)
    r = width * 0.75
    d.ellipse([x - r, y + length - r * 0.4, x + r, y + length + r * 1.4], fill=255)


def _splatter(d, cx, cy, spread, rng, s):
    for _ in range(SPLAT_DROPS):
        r = rng.exponential(SPLAT_DROP_R * s) + 1
        x, y = rng.normal(cx, spread), rng.normal(cy, spread)
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    for _ in range(SPLAT_STREAKS):
        ang = rng.uniform(0, 2 * np.pi)
        ln = rng.uniform(*SPLAT_STREAK_LEN) * s
        x0, y0 = cx + np.cos(ang) * spread * 0.3, cy + np.sin(ang) * spread * 0.3
        d.line([(x0, y0), (x0 + np.cos(ang) * ln, y0 + np.sin(ang) * ln)], fill=255, width=max(1, int(2.5 * s)))
        r = rng.uniform(2, 5) * s
        d.ellipse([x0 + np.cos(ang) * ln - r, y0 + np.sin(ang) * ln - r,
                   x0 + np.cos(ang) * ln + r, y0 + np.sin(ang) * ln + r], fill=255)


def _paint_blood(a, cover, thick_blur, s, fresh=None):
    """Composite a coverage mask as blood: a soft shadow beneath, thin regions dry
    dark, thick ones stay fresh red, and the top edge of every blob catches a wet
    highlight. fresh, if given, scales freshness per pixel: 1 is BLOOD, 0 is
    BLOOD_DARK and negative values sink towards black."""
    c = unit(cover)
    off = int(round(SHADOW_OFFSET * s))
    shadow = np.roll(unit(cover.filter(ImageFilter.GaussianBlur(SHADOW_BLUR * s))), (off, off), axis=(0, 1))
    a *= 1 - (shadow * SHADOW_ALPHA * (1 - c))[..., None]
    thick = np.clip(unit(cover.filter(ImageFilter.GaussianBlur(thick_blur))) * 1.3, 0, 1)[..., None]
    if fresh is not None:
        thick = thick * np.clip(fresh, 0, 1)[..., None]
    colour = BLOOD_DARK + (BLOOD - BLOOD_DARK) * thick
    if fresh is not None:
        colour *= 1 + np.clip(fresh, -1, 0)[..., None]
    alpha = (c * BLOOD_OPACITY)[..., None]
    a *= 1 - alpha
    a += colour * alpha
    shift = max(1, int(round(GLOSS_SHIFT * s)))
    gloss = np.clip(c - np.roll(c, shift, axis=0), 0, 1) * c
    if fresh is not None:
        gloss = gloss * np.clip(fresh, 0, 1)
    a += gloss[..., None] * GLOSS * GLOSS_ALPHA
    return a


def _stencil(size, rng):
    """Biohazard trefoil as an L mask with a spray-paint texture."""
    W, H = size
    R = STENCIL_RADIUS * H
    cx, cy = STENCIL_POS[0] * W, STENCIL_POS[1] * H
    m, d = _layer(size)
    angles = [np.deg2rad(a) for a in (90, 210, 330)]
    for ang in angles:
        ax, ay = cx + np.cos(ang) * STENCIL_ARM_OFFSET * R, cy - np.sin(ang) * STENCIL_ARM_OFFSET * R
        r = STENCIL_ARM * R
        d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=255)
    for ang in angles:
        ax, ay = cx + np.cos(ang) * STENCIL_ARM_OFFSET * R, cy - np.sin(ang) * STENCIL_ARM_OFFSET * R
        r = STENCIL_ARM_HOLE * R
        d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=0)
    r = STENCIL_CORE_HOLE * R
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    ro, ri = STENCIL_RING[0] * R, STENCIL_RING[1] * R
    d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], fill=255)
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=0)
    gap = STENCIL_GAP * R
    for ang in angles:
        d.line([(cx, cy), (cx + np.cos(ang) * R * 0.5, cy - np.sin(ang) * R * 0.5)], fill=0, width=int(gap))
    spray = 1 - STENCIL_SPRAY * _noise(rng, size, 120, blur=0.8)
    return unit(m) * spray


def base(size, s, seed):
    W, H = size
    rng = np.random.default_rng(seed)
    a = np.full((H, W, 3), BG, np.float32)

    grime = sum(w * _noise(rng, size, c) for c, w in zip(GRIME_CELLS, GRIME_WEIGHTS))
    a *= 1 + GRIME * (grime[..., None] * 2 - 1)
    col = _noise(rng, (W, 1), STREAK_CELLS, blur=0.7)          # one row: streak darkness per column
    fade = (1 - np.linspace(0, 1, H)) ** STREAK_FADE
    a *= 1 - STREAKS * (col * fade[:, None])[..., None]

    scratches, d = _layer(size)
    for _ in range(SCRATCHES):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        ang = rng.normal(0, 0.6) + rng.choice([0, np.pi / 2])
        ln = rng.uniform(*SCRATCH_LEN) * s
        d.line([(x, y), (x + np.cos(ang) * ln, y + np.sin(ang) * ln)], fill=255, width=max(1, int(1.2 * s)))
    a += unit(scratches)[..., None] * SCRATCH_ALPHA * 255

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.exp(-(((xx - LAMP_POS[0] * W) / (W * LAMP_SPREAD[0])) ** 2
                    + ((yy - LAMP_POS[1] * H) / (H * LAMP_SPREAD[1])) ** 2))
    a += glow[..., None] * LAMP

    a += _stencil(size, rng)[..., None] * STENCIL_TINT * STENCIL_ALPHA

    blood, d = _layer(size)
    for _ in range(WALL_DRIPS):
        x = rng.uniform(0, W)
        w = rng.uniform(*WALL_DRIP_WIDTH) * s
        ln = WALL_DRIP_LEN[0] * s * rng.lognormal(0, WALL_DRIP_LEN[1])
        _drip(d, x, 0, ln, w, rng)
    for _ in range(WALL_SPLATTERS):
        side = rng.uniform(0.04, 0.5 - SPLAT_ZONE[0])
        x = side if rng.random() < 0.5 else 1 - side
        _splatter(d, x * W, rng.uniform(0.08, SPLAT_ZONE[1]) * H, SPLAT_SPREAD * s, rng, s)
    a = _paint_blood(a, blood, 6 * s, s)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _ragged(d, x, y, r, rng, fill, points=28):
    """Filled polygon approximating a circle with a jittered radius."""
    ang = np.linspace(0, 2 * np.pi, points, endpoint=False)
    rad = r * (1 + HOLE_JAG * rng.normal(0, 1, points))
    d.polygon(list(zip(x + np.cos(ang) * rad, y + np.sin(ang) * rad)), fill=fill)


def _bullet_hole(layers, x, y, r, rng, s):
    """One hole into the crater, core, rim and crack layers."""
    crater, core, rim, cracks = layers
    _ragged(rim, x, y, r * (1 + HOLE_RIM_W), rng, 255)
    _ragged(crater, x, y, r, rng, 255)
    _ragged(core, x, y, r * HOLE_CORE, rng, 255, points=16)
    for _ in range(rng.integers(HOLE_CRACKS[0], HOLE_CRACKS[1] + 1)):
        ang = rng.uniform(0, 2 * np.pi)
        ln = r * rng.uniform(*HOLE_CRACK_LEN)
        pts = [(x + np.cos(ang) * r * 0.8, y + np.sin(ang) * r * 0.8)]
        for k in np.linspace(0.2, 1, 4):
            ang += rng.normal(0, 0.35)
            pts.append((pts[-1][0] + np.cos(ang) * ln * 0.25, pts[-1][1] + np.sin(ang) * ln * 0.25))
        cracks.line(pts, fill=255, width=max(1, int(1.6 * s)))


def _shoot(a, holes, size, s, rng):
    """Punch bullet holes through whatever is already on the canvas, then let
    most of them bleed: fresh spatter around the rim and drips out of the bottom,
    with the core kept black so the hole still reads as a hole."""
    imgs = [Image.new("L", size, 0) for _ in range(4)]
    layers = [ImageDraw.Draw(im) for im in imgs]
    for x, y, r in holes:
        _bullet_hole(layers, x, y, r, rng, s)
    crater, core, rim, cracks = (unit(im) for im in imgs)
    rmax = max(r for _, _, r in holes)
    scorch = unit(imgs[0].filter(ImageFilter.GaussianBlur(rmax * (HOLE_SCORCH_R - 1) * 0.5)))
    a *= 1 - (scorch * HOLE_SCORCH)[..., None]
    a *= 1 - (cracks * 0.8)[..., None]
    rim = rim * (1 - crater) * HOLE_RIM_ALPHA * (1 - HOLE_RIM_GRAIN * _noise(rng, size, 400, blur=0.6))
    a = a * (1 - rim[..., None]) + HOLE_RIM * rim[..., None]
    a = a * (1 - crater[..., None]) + HOLE_CRATER * crater[..., None]
    a *= 1 - core[..., None]

    bleed, d = _layer(size)
    for x, y, r in holes:
        if rng.random() >= HOLE_BLEED:
            continue
        for _ in range(HOLE_BLEED_DROPS):
            dr = rng.exponential(HOLE_BLEED_DROP_R * r) + 0.5
            dx, dy = rng.normal(x, HOLE_BLEED_SPREAD * r), rng.normal(y, HOLE_BLEED_SPREAD * r)
            d.ellipse([dx - dr, dy - dr, dx + dr, dy + dr], fill=255)
        for _ in range(rng.integers(HOLE_BLEED_DRIPS[0], HOLE_BLEED_DRIPS[1] + 1)):
            _drip(d, x + rng.normal(0, r * 0.3), y + r * 0.7,
                  r * HOLE_BLEED_LEN[0] * rng.lognormal(0, HOLE_BLEED_LEN[1]), r * rng.uniform(*HOLE_BLEED_WIDTH), rng)
    a = _paint_blood(a, bleed, rmax * 0.3, s)
    a *= 1 - core[..., None]
    return a

def _header_anchors(img, s, rng):
    """Points along the underside of the header lettering, spaced apart, found
    from the grey pixels already on the canvas; thin strokes are skipped."""
    q = 4                                              # analyse the mask at 1/q resolution
    a = np.asarray(img)[::q, ::q].astype(np.int16)
    sat = a.max(axis=-1) - a.min(axis=-1)
    lum = (a @ np.array([0.299, 0.587, 0.114])) / 255
    m = (sat < GRADE_SAT) & (lum > HEADER_LUM)
    if not m.any():
        return []
    H, W = m.shape
    idx = np.where(m, 0, np.arange(H)[:, None])
    run = np.arange(H)[:, None] - np.maximum.accumulate(idx, axis=0)
    edge = m[:-1] & ~m[1:] & (run[:-1] >= HEADER_DRIP_MIN_RUN * s / q)
    ys, xs = np.nonzero(edge)
    order = rng.permutation(len(xs))
    picked = []
    for i in order:
        x, y = xs[i] * q, (ys[i] + 1) * q
        if all(abs(x - px) >= HEADER_DRIP_SPACING * s for px, _ in picked):
            picked.append((x, y))
        if len(picked) >= HEADER_DRIPS:
            break
    return picked


def draw_art(img, dots, pitch, s, seed):
    rng = np.random.default_rng(seed + 1)          # not the wall's stream, so art and wall detail do not correlate
    anchors = _header_anchors(img, s, rng)
    a = grade_greys(img, BG, HEADER_INK, GRADE_SAT)

    x_min = min(cx for cx, _, _ in dots)
    y_min = min(cy for _, cy, _ in dots)
    dots = list(thin(dots, pitch, rng, DOT_DROP, DOT_STRIDE))     # drips, spray and holes follow the kept dots
    grid = {(round((cx - x_min) / pitch), round((cy - y_min) / pitch)) for cx, cy, _ in dots}

    blood, d = _layer(img.size)
    for x, y in anchors:
        w = rng.uniform(*HEADER_DRIP_WIDTH) * s
        _drip(d, x, y, HEADER_DRIP_LEN[0] * s * rng.lognormal(0, HEADER_DRIP_LEN[1]), w, rng)
    for cx, cy, _ in dots:
        r = pitch * DOT_R * size_jitter(rng, DOT_SIZE_JITTER)
        d.ellipse([cx - r, cy - r * DOT_SQUASH, cx + r, cy + r * DOT_SQUASH], fill=255)
        gx, gy = round((cx - x_min) / pitch), round((cy - y_min) / pitch)
        if (gx, gy + 1) not in grid and rng.random() < ART_DRIP_CHANCE:
            w = rng.uniform(*ART_DRIP_WIDTH) * pitch
            _drip(d, cx, cy, ART_DRIP_LEN[0] * pitch * rng.lognormal(0, ART_DRIP_LEN[1]), w, rng)
    for _ in range(int(len(dots) * ART_SPRAY)):
        cx, cy, _ = dots[rng.integers(len(dots))]
        x, y = rng.normal(cx, ART_SPRAY_SPREAD * pitch), rng.normal(cy, ART_SPRAY_SPREAD * pitch)
        sr = rng.exponential(ART_SPRAY_R * pitch) + 0.5
        d.ellipse([x - sr, y - sr, x + sr, y + sr], fill=255)
    y_max = max(cy for _, cy, _ in dots)
    ty = np.clip((np.arange(img.size[1], dtype=np.float32) - y_min) / max(1, y_max - y_min), 0, 1)
    fresh = ART_FADE[0] + (ART_FADE[1] - ART_FADE[0]) * ty
    a = _paint_blood(a, blood, pitch * THICK_BLUR, s, fresh=np.broadcast_to(fresh[:, None], a.shape[:2]))

    W, H = img.size
    holes = [(rng.uniform(0.03, 0.97) * W, rng.uniform(0.03, HOLE_ZONE) * H, rng.uniform(*HOLE_R) * s)
             for _ in range(WALL_HOLES)]
    for _ in range(ART_HOLES):
        cx, cy, _ = dots[rng.integers(len(dots))]
        holes.append((cx, cy, rng.uniform(*HOLE_R) * s))
    a = _shoot(a, holes, img.size, s, rng)
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
