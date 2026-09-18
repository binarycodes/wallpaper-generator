"""Themes for generate.py. Each theme is a module exposing the same three names:
TEXT (subtitle/prompt/footer colours), base(size, s) for the canvas and
draw_art(img, dots, pitch, s) for the centre art. Register new ones here."""
from . import constellation, matrix, plain

THEMES = {"plain": plain, "constellation": constellation, "matrix": matrix}
