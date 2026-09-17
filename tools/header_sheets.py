#!/usr/bin/env python3
"""Render reference sheets of the header options into reference/:
header-fonts.png (one strip per curated FIGlet font) and
header-render-styles.png (one strip per --header-render-style).

    tools/header_sheets.py [TEXT]
"""
import os
import sys
from pathlib import Path

# Re-exec under the project's .venv so the tools run without activating it.
_venv_py = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
if _venv_py.is_file() and Path(sys.prefix).resolve() != _venv_py.parent.parent.resolve():
    os.execv(str(_venv_py), [str(_venv_py), __file__, *sys.argv[1:]])

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import headerstyle  # noqa: E402

FONTS = ["ansi_shadow", "ansi_regular", "dos_rebel", "delta_corps_priest_1", "bloody", "electronic",
         "sub-zero", "larry3d", "calvin_s", "the_edge", "banner3-D", "colossal", "doom", "3d-ascii",
         "def_leppard", "elite"]
BG = (13, 16, 22)
W, STRIP = 1920, 250
DEJAVU = ROOT / "fonts" / "DejaVuSansMono.ttf"
LABEL = ImageFont.truetype(str(ROOT / "fonts" / "JetBrainsMono-Regular.ttf"), 22)


def strip(label, text, font, style):
    # draw at the generator's 4K scale (s=1 on a 3840 canvas) and downsample 2x, as generate.py does
    im = Image.new("RGB", (W * 2, STRIP * 2), BG)
    headerstyle.draw(im, text, font, style, W * 2, top=120, s=1, dejavu=DEJAVU)
    im = im.resize((W, STRIP), Image.LANCZOS)
    ImageDraw.Draw(im).text((16, 10), label, font=LABEL, fill=(110, 110, 110))
    return im


def sheet(rows, out):
    im = Image.new("RGB", (W, STRIP * len(rows)), BG)
    for i, r in enumerate(rows):
        im.paste(r, (0, i * STRIP))
    im.save(out)
    print("wrote", out)


def main():
    text = sys.argv[1] if len(sys.argv) > 1 else "HEADER-TEXT"
    out = ROOT / "reference"
    out.mkdir(exist_ok=True)
    sheet([strip(f"--header-font-style {f}", text, f, "gradient") for f in FONTS], out / "header-fonts.png")
    sheet([strip(f"--header-render-style {st}", text, "ansi_shadow", st) for st in headerstyle.RENDER_STYLES],
          out / "header-render-styles.png")


if __name__ == "__main__":
    sys.exit(main())
