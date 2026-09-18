#!/usr/bin/env python3
"""Render a monochrome terminal-style wallpaper: block-letter header, braille
art (types/<name>.txt), subtitle and footer.

    ./generate.py                                   # everything from config.toml
    ./generate.py --header "TITLE" --type kali      # override some keys

Defaults come only from config.toml next to this script (or --config PATH), which
must define every key; command-line options override it.
"""
import argparse
import os
import re
import sys
import tomllib
from pathlib import Path

# Re-exec under the sibling .venv so `./generate.py` works without activating it.
_venv_py = Path(__file__).resolve().parent / ".venv" / "bin" / "python"
if _venv_py.is_file() and Path(sys.prefix).resolve() != _venv_py.parent.parent.resolve():
    os.execv(str(_venv_py), [str(_venv_py), __file__, *sys.argv[1:]])

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import headerstyle
import theme

HERE = Path(__file__).resolve().parent
TYPES_DIR = HERE / "types"                # one braille-art file per type: types/<name>.txt
CONFIG = HERE / "config.toml"             # the only source of defaults; every key is required
CONFIG_KEYS = ("header", "header_font_style", "header_render_style", "subtitle", "footer",
               "prompt", "type", "theme", "out", "size")
SS = 2                                  # supersample factor for smooth dots
DEJAVU = HERE / "fonts" / "DejaVuSansMono.ttf"
BRAILLE_BITS = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08),
                (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_skull(path):
    rows = []
    for ln in path.read_text(encoding="utf-8").strip("\n").split("\n"):
        m = re.match(r"\[(?:bold |dim )?(#[0-9A-Fa-f]{6})\](.*)\[/\]\s*$", ln)
        text = m.group(2)
        if any(0x2800 <= ord(ch) <= 0x28FF and ch != "⠀" for ch in text):
            rows.append((hexrgb(m.group(1)), text))
    return rows


def draw_skull(img, theme_name, rows, W, top, max_pitch, band_h, s):
    """Draw braille rows as dots, shrinking the pitch so the art fits band_h tall and 90% of W wide."""
    ncols = max(len(t) for _, t in rows)
    pitch = min(max_pitch, band_h // (len(rows) * 4), int(W * 0.9) // (ncols * 2))
    dots = []
    for r, (col, text) in enumerate(rows):
        for c, ch in enumerate(text):
            code = ord(ch)
            if not 0x2800 <= code <= 0x28FF:
                continue
            for dx, dy, bit in BRAILLE_BITS:
                if (code - 0x2800) & bit:
                    dots.append((c * 2 + dx, r * 4 + dy, col))
    gx_min = min(x for x, _, _ in dots)
    gx_max = max(x for x, _, _ in dots) + 1
    x0 = (W - (gx_max - gx_min) * pitch) // 2 - gx_min * pitch
    theme.draw_art(img, theme_name, [(x0 + gx * pitch + pitch / 2, top + gy * pitch + pitch / 2, col)
                                     for gx, gy, col in dots], pitch, s)
    cx = x0 + (gx_min + gx_max) * pitch / 2
    return cx, top + len(rows) * 4 * pitch


def finish(img, W, H):
    out = img.resize((W, H), Image.LANCZOS)
    a = np.asarray(out).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    rad = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a *= (1.0 - 0.28 * np.clip(rad - 0.35, 0, 1) ** 1.6)[..., None]
    a += np.random.default_rng(7).normal(0, 2.2, size=(H, W, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main():
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("-c", "--config", default=str(CONFIG), help=f"TOML file with the defaults (normally {CONFIG.name})")
    cfg_path = Path(pre.parse_known_args()[0].config)
    if not cfg_path.is_file():
        sys.exit(f"config file not found: {cfg_path}")
    with open(cfg_path, "rb") as fh:
        cfg = tomllib.load(fh)
    missing = [k for k in CONFIG_KEYS if k not in cfg]
    unknown = sorted(set(cfg) - set(CONFIG_KEYS))
    if missing or unknown:
        sys.exit(f"{cfg_path}: " + "; ".join(filter(None, [
            missing and f"missing keys: {', '.join(missing)}",
            unknown and f"unknown keys: {', '.join(unknown)}"])))
    bad = [k for k in CONFIG_KEYS if not isinstance(cfg[k], str)]
    if bad:
        sys.exit(f"{cfg_path}: values must be strings: {', '.join(bad)}")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
                                 parents=[pre])
    ap.add_argument("-H", "--header", default=cfg["header"],
                    help="block-letter title (A-Z, 0-9, punctuation); '' to omit")
    ap.add_argument("--header-font-style", default=cfg["header_font_style"], metavar="FONT",
                    help="FIGlet font for the header; see --list-header-fonts")
    ap.add_argument("--header-render-style", default=cfg["header_render_style"],
                    choices=headerstyle.RENDER_STYLES, metavar="STYLE",
                    help="how the header is drawn: " + ", ".join(headerstyle.RENDER_STYLES))
    ap.add_argument("--list-header-fonts", action="store_true", help="list FIGlet fonts and exit")
    ap.add_argument("-s", "--subtitle", default=cfg["subtitle"],
                    help="small text under the art; '' to omit")
    ap.add_argument("-f", "--footer", default=cfg["footer"],
                    help="small text bottom-right; '' to omit")
    ap.add_argument("-p", "--prompt", default=cfg["prompt"],
                    help="text bottom-left; '' to omit")
    types = sorted(p.stem for p in TYPES_DIR.glob("*.txt"))
    ap.add_argument("-t", "--type", default=cfg["type"], choices=types, metavar="TYPE",
                    help="art from types/TYPE.txt; see --list-types")
    ap.add_argument("--list-types", action="store_true", help="list the available types and exit")
    ap.add_argument("--theme", default=cfg["theme"], choices=theme.THEMES,
                    help="canvas, art treatment and text colours; constellation draws the art as a starry outline")
    ap.add_argument("-o", "--out", default=cfg["out"], help="output PNG path")
    ap.add_argument("--size", default=cfg["size"], help="WIDTHxHEIGHT")
    args = ap.parse_args()
    if args.list_types:
        print("\n".join(types))
        return
    if args.list_header_fonts:
        print("\n".join(headerstyle.font_names()))
        return
    if args.header_font_style not in headerstyle.font_names():
        ap.error(f"unknown header font {args.header_font_style!r}; see --list-header-fonts")

    W, H = (int(v) for v in args.size.lower().split("x"))
    s = SS * W / 3840                    # everything below is laid out in 3840-wide units
    img = theme.base(args.theme, (W * SS, H * SS), s)

    art_top = 640
    if args.header.strip():
        headerstyle.draw(img, args.header, args.header_font_style, args.header_render_style,
                         W * SS, top=int(170 * s), s=s, dejavu=DEJAVU)
    else:
        art_top = 400                    # no header: centre art + subtitle in the freed space
    skull_cx, skull_bottom = draw_skull(img, args.theme, load_skull(TYPES_DIR / f"{args.type}.txt"), W * SS,
                                          top=int(art_top * s), max_pitch=int(22 * s), band_h=int(1232 * s), s=s)
    d = ImageDraw.Draw(img)
    colours = theme.text_colours(args.theme)

    mono = ImageFont.truetype(str(HERE / "fonts/JetBrainsMono-Regular.ttf"), int(46 * s))
    small = ImageFont.truetype(str(HERE / "fonts/JetBrainsMono-Regular.ttf"), int(30 * s))
    symbols = ImageFont.truetype(str(HERE / "fonts/DejaVuSansMono.ttf"), int(30 * s))
    if args.subtitle:
        tw = d.textlength(args.subtitle, font=mono)
        d.text((skull_cx - tw / 2, skull_bottom + 70 * s), args.subtitle, font=mono, fill=colours["subtitle"])
    if args.prompt:
        d.text((120 * s, H * SS - 120 * s), args.prompt, font=symbols, fill=colours["prompt"])
    if args.footer:
        fw = d.textlength(args.footer, font=small)
        d.text((W * SS - 120 * s - fw, H * SS - 120 * s), args.footer, font=small, fill=colours["footer"])

    finish(img, W, H).save(args.out, optimize=True)
    print(f"saved {args.out} ({W}x{H})")


if __name__ == "__main__":
    sys.exit(main())
