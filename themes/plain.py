"""Near-black terminal look: flat canvas, art as filled dots in the type file's colours."""
from PIL import Image, ImageDraw

BG = (13, 16, 22)
TEXT = {"subtitle": (85, 85, 85), "prompt": (120, 120, 120), "footer": (70, 70, 70)}


def base(size, s, seed):
    return Image.new("RGB", size, BG)


def draw_art(img, dots, pitch, s, seed):
    """dots is [(cx, cy, colour)] on the supersampled canvas; pitch is the dot spacing."""
    d = ImageDraw.Draw(img)
    rad = pitch * 0.30
    for cx, cy, col in dots:
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=col)
