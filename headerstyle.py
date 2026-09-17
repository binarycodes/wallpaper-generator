"""Header lettering for generate.py: a FIGlet font choice and a render style.

The FIGlet text is first rasterised to a binary mask, then the style decides how
that mask is coloured and composited. Fonts built only from full blocks and
double-line box characters (ansi_shadow, ansi_regular) are drawn as exact
rectangles; every other font is drawn with DejaVu Sans Mono, which covers the
shade and box glyphs those fonts use.
"""
import numpy as np
import pyfiglet
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

RENDER_STYLES = ("outline", "gradient", "solid", "hollow", "dotted",
                 "hgradient", "scanlines", "shadow", "dither")
GRADIENT = [(255, 255, 255), (221, 221, 221), (187, 187, 187),
            (153, 153, 153), (119, 119, 119), (85, 85, 85)]
BOX_CHARS = set("═║╔╗╚╝")
SOLID = (235, 235, 235)


def dim(c, f):
    return tuple(int(v * f) for v in c)


def font_names():
    return sorted(pyfiglet.FigletFont.getFonts())


def figlet_lines(text, font):
    lines = pyfiglet.Figlet(font=font, width=10_000).renderText(text).split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return lines


def draw_box_char(d, x0, y0, w, h, ch, col, lw):
    """Double-line box-drawing character as two thin parallel strokes."""
    cx, cy = x0 + w / 2, y0 + h / 2
    g = w * 0.18
    L = []
    if ch == "═":
        L = [((x0, cy - g), (x0 + w, cy - g)), ((x0, cy + g), (x0 + w, cy + g))]
    elif ch == "║":
        L = [((cx - g, y0), (cx - g, y0 + h)), ((cx + g, y0), (cx + g, y0 + h))]
    elif ch == "╔":
        L = [((cx - g, cy - g), (x0 + w, cy - g)), ((cx - g, cy - g), (cx - g, y0 + h)),
             ((cx + g, cy + g), (x0 + w, cy + g)), ((cx + g, cy + g), (cx + g, y0 + h))]
    elif ch == "╗":
        L = [((x0, cy - g), (cx + g, cy - g)), ((cx + g, cy - g), (cx + g, y0 + h)),
             ((x0, cy + g), (cx - g, cy + g)), ((cx - g, cy + g), (cx - g, y0 + h))]
    elif ch == "╚":
        L = [((cx - g, y0), (cx - g, cy + g)), ((cx - g, cy + g), (x0 + w, cy + g)),
             ((cx + g, y0), (cx + g, cy - g)), ((cx + g, cy - g), (x0 + w, cy - g))]
    elif ch == "╝":
        L = [((cx + g, y0), (cx + g, cy + g)), ((x0, cy + g), (cx + g, cy + g)),
             ((cx - g, y0), (cx - g, cy - g)), ((x0, cy - g), (cx - g, cy - g))]
    for a, b in L:
        d.line([a, b], fill=col, width=lw)


class Raster:
    """Binary mask of the lettering plus the geometry the styles need."""

    def __init__(self, lines, W, s, dejavu):
        ncols = max(len(ln) for ln in lines)
        self.nrows = len(lines)
        max_h = 400 * s
        self.boxes = []
        if all(ch in BOX_CHARS or ch in "█ " for ln in lines for ch in ln):
            cw = int(min(29 * s, W * 0.92 / ncols, max_h / (2 * self.nrows)))
            ch_ = cw * 2
            self.mask = Image.new("L", (ncols * cw, self.nrows * ch_), 0)
            d = ImageDraw.Draw(self.mask)
            for r, ln in enumerate(lines):
                for c, ch in enumerate(ln):
                    if ch == "█":
                        d.rectangle([c * cw, r * ch_, (c + 1) * cw, (r + 1) * ch_], fill=255)
                    elif ch in BOX_CHARS:
                        self.boxes.append((c * cw, r * ch_, ch, r))
            cmin = min(min(i for i, ch in enumerate(ln) if ch != " ") for ln in lines)
            cmax = max(max(i for i, ch in enumerate(ln) if ch != " ") for ln in lines) + 1
            self.extent = (cmin * cw, cmax * cw)
            self.cell = (cw, ch_)
            self.row_h = ch_
        else:
            size = int(min(W * 0.92 / (ncols * 0.602), max_h / self.nrows))
            font = ImageFont.truetype(str(dejavu), size)
            adv = font.getlength("█")
            self.mask = Image.new("L", (int(ncols * adv) + size, self.nrows * size + size), 0)
            d = ImageDraw.Draw(self.mask)
            for r, ln in enumerate(lines):
                d.text((0, r * size), ln, font=font, fill=255)
            bbox = self.mask.getbbox()
            self.extent = (bbox[0], bbox[2])
            self.cell = (adv, size)
            self.row_h = size
        self.pitch = self.cell[0] / 2

    def row_colours(self):
        """One gradient colour per FIGlet row."""
        return [GRADIENT[min(r * len(GRADIENT) // self.nrows, len(GRADIENT) - 1)] for r in range(self.nrows)]

    def field(self, style):
        """RGB image giving each mask pixel its colour."""
        w, h = self.mask.size
        yy, xx = np.mgrid[0:h, 0:w]
        if style == "solid" or style == "shadow":
            rgb = np.full((h, w, 3), SOLID, dtype=np.uint8)
        elif style == "hgradient":
            v = (255 - 150 * xx / max(1, w - 1)).astype(np.uint8)
            rgb = np.stack([v, v, v], axis=-1)
        else:
            rows = np.clip(yy // self.row_h, 0, self.nrows - 1)
            table = np.array(self.row_colours(), dtype=np.uint8)
            rgb = table[rows]
            if style == "scanlines":
                band = max(2, int(self.row_h / 16))
                dark = ((yy // band) % 2 == 1)[..., None]
                rgb = np.where(dark, (rgb * 0.45).astype(np.uint8), rgb)
        return Image.fromarray(rgb)

    def shaped_mask(self, style):
        """Mask after the style's shape change (hollow, dotted, dither)."""
        m = self.mask
        if style == "hollow":
            k = max(3, int(self.cell[0] * 0.12)) | 1
            return ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(k)))
        if style == "dotted":
            p = self.pitch
            rad = p * 0.30
            out = Image.new("L", m.size, 0)
            d = ImageDraw.Draw(out)
            px = m.load()
            for gy in range(int(m.height / p)):
                for gx in range(int(m.width / p)):
                    cx, cy = gx * p + p / 2, gy * p + p / 2
                    if px[int(cx), int(cy)]:
                        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=255)
            return out
        if style == "dither":
            step = max(2, int(self.cell[0] / 7))
            a = np.asarray(m).copy()
            yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
            rows = yy // self.row_h
            checker = ((xx // step + yy // step) % 2) == (rows % 2)
            a[(rows >= self.nrows / 2) & checker] = 0
            return Image.fromarray(a)
        return m


def draw(img, text, font, style, W, top, s, dejavu):
    """Composite the header onto img. Band is the six-row ansi_shadow height so
    the layout below does not move when the font changes."""
    lines = figlet_lines(text, font)
    if not lines:
        return
    r = Raster(lines, W, s, dejavu)
    band = int(29 * s) * 2 * 6
    x0 = (W - (r.extent[1] - r.extent[0])) // 2 - r.extent[0]
    y0 = int(top + (band - r.mask.height) / 2)
    if style == "shadow":
        off = int(r.pitch)
        img.paste((60, 60, 60), (x0 + off, y0 + off), r.mask)
    if style == "outline" and r.boxes:          # strokes go under the blocks so they never bleed onto them
        d = ImageDraw.Draw(img)
        cols = r.row_colours()
        cw, ch_ = r.cell
        for bx, by, ch, row in r.boxes:
            draw_box_char(d, x0 + bx, y0 + by, cw, ch_, ch, dim(cols[row], 0.55), max(2, int(s)))
    img.paste(r.field(style), (x0, y0), r.shaped_mask(style))
