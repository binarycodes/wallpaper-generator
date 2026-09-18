# Contributing

Developer notes for the wallpaper generator. The README covers generating images.

## Setup

```sh
uv sync
git config core.hooksPath .githooks
```

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`; run
`uv lock --upgrade` to refresh the pins and commit both files. Every script
re-executes itself under `.venv`, so nothing needs activating.

## Layout

| Path | Role |
|---|---|
| `generate.py` | CLI, config loading, page layout, braille dot placement, final vignette and grain |
| `headerstyle.py` | FIGlet header: font rasterising and the render styles |
| `themes/` | one module per theme, registered in `themes/__init__.py` |
| `types/` | braille art files, one per `--type` |
| `tools/` | scripts that make type files and comparison sheets |
| `fonts/` | bundled monospace faces: JetBrains Mono, DejaVu Sans Mono, VT323, Share Tech Mono |
| `reference/` | rendered comparison sheets (tracked PNGs) |

Everything in `generate.py` is laid out in 3840-wide units and drawn at a 2x
supersample, then downscaled once at the end. `s` is that combined scale factor
and every size in the themes and header code is multiplied by it.

## Themes

A theme is a module in `themes/` exposing exactly three names:

- `TEXT`: dict with `subtitle`, `prompt` and `footer` RGB tuples
- `base(size, s)`: returns the RGB canvas of `size`
- `draw_art(img, dots, pitch, s)`: draws the centre art onto `img`

Optionally `TEXT_FONT`, a path to the font for subtitle and footer (default
JetBrains Mono), and `TEXT_SCALE` to correct a face that draws small or large
for its point size. All three text lines use it; any glyph the face lacks, such
as the prompt's `❯` and `▉`, is drawn from DejaVu Sans Mono instead.
Bundled fonts in `fonts/` are all SIL Open Font License; VT323 and Share Tech
Mono come from Google Fonts.

`dots` is a list of `(cx, cy, colour)` on the supersampled canvas, one entry per
braille dot in the type file, and `pitch` is the distance between neighbouring
dots. The type file is the only input; a theme may skip, resize or recolour dots
but must not depend on any other stored shape. Shared helpers live in
`themes/_common.py`. Register the module in `THEMES` in `themes/__init__.py`;
the CLI choices and their order come from that dict.

Every visual parameter is a named constant at the top of the theme module with
a one-line comment, grouped by concern, so the look can be tuned without reading
the drawing code; `themes/matrix.py` is the fullest example. No magic numbers in
the drawing functions.

## Types

Each line of `types/<name>.txt` is `[#RRGGBB]<braille>[/]`. Files of any size
work; `generate.py` scales the grid to fit between header and footer.

```sh
tools/svg2png.py icon.svg icon.png                       # single-colour SVG -> mask
tools/img2type.py icon.png types/icon.txt --cols 48      # flat logo, hard threshold
tools/img2type.py photo.png types/photo.txt --cols 56 --dither   # shaded image
```

`--color`/`--color2` set a top-to-bottom fade, `--exact` uses one image pixel per
dot. The existing logos use 48 columns and a `#DDDDDD` to `#888888` fade.
`tools/draw_sources.py DIR` redraws the hand-made `deathstar` source bitmap;
put any new procedurally drawn source there so it stays reproducible. Add new
types to the list in the README, and to its trademark note when the mark is
someone's.

## Header styles

Render styles are the `RENDER_STYLES` tuple in `headerstyle.py`, each a branch
in `Raster.field()` or `Raster.shaped_mask()`. `tools/header_sheets.py` renders
comparison sheets of a curated font set and of every render style into
`reference/`; regenerate them when a style changes.

## Commits

The `commit-msg` hook enforces a single-line Conventional Commits subject
(`feat`, `fix`, `docs`, `chore`, ...) under 100 characters, with no body and no
trailers. `main` is protected; work on a branch and open a pull request.
