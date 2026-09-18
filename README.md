# wallpaper generator

Monochrome terminal-style wallpaper: block-letter header, braille Jolly Roger,
subtitle and footer.

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync
```

This creates `.venv` from `uv.lock`. No activation is needed: `generate.py` and
the tools run themselves under `.venv` automatically, or use `uv run ./generate.py`.
Dependencies live in `pyproject.toml`; `uv lock --upgrade` refreshes the lockfile.

## Usage

```sh
./generate.py
./generate.py --header "MY AGENT" --subtitle "ship it" --footer "" -o my.png
```

| Option | Config key | Meaning |
|---|---|---|
| `-H`, `--header` | `header` | block-letter title; `""` omits it and shifts the art up |
| `--header-font-style` | `header_font_style` | FIGlet font for the header |
| `--header-render-style` | `header_render_style` | how the header lettering is drawn |
| `-s`, `--subtitle` | `subtitle` | small text under the art; `""` to omit |
| `-f`, `--footer` | `footer` | small text bottom-right; `""` to omit |
| `-p`, `--prompt` | `prompt` | small text bottom-left; `""` to omit |
| `-t`, `--type` | `type` | centre art, any `types/<name>.txt` |
| `--theme` | `theme` | `plain` or `constellation`; sets canvas, dot treatment and text colours |
| `-o`, `--out` | `out` | output PNG path |
| `--size` | `size` | `WIDTHxHEIGHT` |
| `-c`, `--config` | | TOML file to read instead of `config.toml` |
| `--list-types` | | print available types and exit |
| `--list-header-fonts` | | print FIGlet font names and exit |

All defaults live in `config.toml` next to the script, which must define every
key; edit it once and run `./generate.py` bare. Command-line options override
the file. The header auto-shrinks to fit the width.

## Header styles

`--header-font-style` takes any pyfiglet font name (`--list-header-fonts`);
fonts made of full blocks are drawn as crisp rectangles, all others through
DejaVu Sans Mono. `--header-render-style` is one of `outline` (gradient with the
double-line strokes), `gradient`, `solid`, `hollow`, `dotted`, `hgradient`,
`scanlines`, `shadow`, `dither`. Run `tools/header_sheets.py` to render
comparison sheets of both into `reference/` (git-ignored).

## Themes

- `plain` is the near-black terminal look
- `constellation` is a navy night sky with a star field and a teal glow

## Types

The centre art comes from `types/<name>.txt`, selected with `--type`. Included:
`arch` (default), `skull`, `debian`, `macos`, `kali`, `deathstar`, `vaadin`. Art of any
size is scaled to fit between header and footer.

Each line is `[#RRGGBB]<braille>[/]`, so those can be dropped in directly. To make one from an image:

```sh
tools/svg2png.py icon.svg icon.png                       # single-colour SVG -> mask
tools/img2type.py icon.png types/icon.txt --cols 48      # flat logo, hard threshold
tools/img2type.py photo.png types/photo.txt --cols 56 --dither   # shaded image
```

`--color`/`--color2` set a top-to-bottom fade; `--exact` uses one image pixel per
dot. `tools/draw_sources.py DIR` redraws the `deathstar` source bitmap.

Arch, Debian, Apple, Kali and Vaadin marks are trademarks of their owners; the type files are
derived from [simple-icons](https://simpleicons.org) for personal use.
