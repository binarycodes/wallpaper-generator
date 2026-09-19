import numpy as np


def unit(im):
    """Greyscale image as a float array in 0..1."""
    return np.asarray(im).astype(np.float32) / 255


def luminance(rgb):
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255


JITTER_SIGMA = 0.45             # lognormal sigma at DOT_SIZE_JITTER = 1


def thin(dots, pitch, rng, drop, stride):
    """The dots that survive thinning: every stride-th lattice row and column,
    minus a random share drop of the rest. Lazy, so a caller's own draws from
    rng interleave per dot and no draws happen when drop is 0."""
    x_min = min(cx for cx, _, _ in dots)
    y_min = min(cy for _, cy, _ in dots)
    for cx, cy, col in dots:
        gx, gy = round((cx - x_min) / pitch), round((cy - y_min) / pitch)
        if gx % stride or gy % stride or (drop and rng.random() < drop):
            continue
        yield cx, cy, col


def size_jitter(rng, amount):
    """Multiplier for one dot's size; the median stays 1 so the typical dot keeps its size."""
    return rng.lognormal(0, JITTER_SIGMA * amount) if amount else 1.0


def grade_greys(img, low, high, max_sat):
    """Float array of img with its low-saturation pixels (the header, which is
    pasted in grey) remapped by luminance onto the low..high colour ramp, so a
    coloured theme has nothing off-palette. Pixels more saturated than max_sat
    are left alone; the blend fades in between so antialiased edges stay smooth."""
    a = np.asarray(img).astype(np.float32)
    sat = a.max(axis=-1) - a.min(axis=-1)
    w = np.clip(1 - sat / max_sat, 0, 1)[..., None]
    lum = (a @ np.array([0.299, 0.587, 0.114], np.float32) / 255)[..., None]
    low, high = np.asarray(low, np.float32), np.asarray(high, np.float32)
    return a * (1 - w) + (low + lum * (high - low)) * w
