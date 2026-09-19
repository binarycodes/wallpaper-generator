# wallpaper generator

Monochrome terminal-style wallpaper: block-letter header, braille Jolly Roger,
subtitle and footer.

## Setup

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync
```

This creates `.venv`. No activation is needed: `generate.py` runs itself under
`.venv` automatically, or use `uv run ./generate.py`.

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
| `--theme` | `theme` | `plain`, `constellation`, `matrix`, `blueprint` or `outbreak`; sets canvas, dot treatment and text colours |
| `--seed` | `seed` | integer seed for everything a theme places at random; change it to reroll drips, stars or bullet holes |
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
`scanlines`, `shadow`, `dither`. `reference/` has comparison sheets of both.

## Themes

- `plain` is the near-black terminal look
- `constellation` is a navy night sky with a star field and a teal glow
- `matrix` is green glyph rain on black; the art is built from glyphs and the header goes green
- `blueprint` is a cyanotype drafting sheet: gridded blue paper, the art outlined in white ink over section hatching, with dimension lines giving its size in dots
- `outbreak` is a containment breach: grimy concrete under a red emergency lamp, a spray-painted biohazard stencil, blood dripping from the top of the wall and from the header lettering, the art itself rendered as pooled, dripping blood that fades from fresh red to black, and bullet holes punched through wall, header and art

## Types

The centre art comes from `types/<name>.txt`, selected with `--type`. Included:
`arch` (default), `skull`, `debian`, `macos`, `kali`, `deathstar`, `vaadin`. Art of any
size is scaled to fit between header and footer.

Arch, Debian, Apple, Kali and Vaadin marks are trademarks of their owners; the type files are
derived from [simple-icons](https://simpleicons.org) for personal use.

Making your own types or themes is covered in [CONTRIBUTING.md](CONTRIBUTING.md).
