"""Themes for generate.py. Each theme is a module exposing the same three names:
TEXT (subtitle/prompt/footer colours), base(size, s, seed) for the canvas and
draw_art(img, dots, pitch, s, seed) for the centre art. Register new ones here."""
from . import blueprint, constellation, matrix, outbreak, plain

THEMES = {"plain": plain, "constellation": constellation, "matrix": matrix, "blueprint": blueprint, "outbreak": outbreak}
