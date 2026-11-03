"""Merry & Bright: two-line Christmas lettering with a holly sprig and twinkle stars.

Spec:
  object:       holiday lettering for sweatshirts, totes, pillows, towels and mugs rugs
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away; towels add a topper
  threads:      red ("Merry"), green ("Bright", holly), gold ("&" and the stars),
                berry (holly berries): 4 colours
  must have:    "Merry" and "Bright" in bold script, 20 mm cap height, filled at 0.35 mm
                rows; a gold "&" between them; a holly sprig with three berries over the
                M; three four-point gold twinkle stars (4.5-6.5 mm) around the words
  font:         Segoe Script Bold (Windows `segoescb.ttf`), as in `indiana_state`
  density:      lettering does not overlap; max 3.5 layers
"""
from pathlib import Path

from cadkit.stitch import *

from _winter import C_, SIZES, fit, holly_sprig, product, standard_checks

DESCRIPTION = "Merry & Bright script lettering with holly and twinkle stars"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Merry & Bright Embroidery Design",
    "\"Merry & Bright\" in red and green script with holly and gold twinkle stars",
    ["merry and bright", "christmas lettering", "christmas quote", "christmas sweatshirt",
     "holiday saying"],
    "\"Merry & Bright\" in a bold red and green script with a gold ampersand, a sprig of holly "
    "and three twinkling gold stars. An easy, classic Christmas saying.\n\nGreat on sweatshirts, "
    "totes, pillows and tea towels.",
    mockups=("tshirt", "tote"),
)

FONT = Path("C:/Windows/Fonts/segoescb.ttf")


def checks(p):
    return standard_checks(p, 4, 12000)


def _word(s, size, x, y):
    t = text_shape(s, size, font="Segoe Script", bold=True, font_path=FONT if FONT.exists() else None)
    return move(t, x, y)


def _twinkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


def art():
    d = Design()
    merry = _word("Merry", 20, -6, 14)
    bright = _word("Bright", 20, 6, -16)
    amp = _word("&", 13, 0, -1)
    x0, y0, x1, y1 = merry.bounds
    leaves, veins, berries = holly_sprig(x0 + 6, y1 + 3, deg=0, length=12)
    stars = [_twinkle(x1 + 6, y1 - 2, 6.5), _twinkle(bright.bounds[0] - 2, -2, 4.5),
             _twinkle(bright.bounds[2] + 1, bright.bounds[3] + 5, 5.0)]
    holly = union(*leaves, *berries)
    d.fill(knockout(merry, holly), C_["red"], angle=None, spacing=0.35, name="Merry")
    d.fill(bright, C_["green"], angle=None, spacing=0.35, name="Bright")
    for g in leaves:
        d.fill(knockout(g, *berries), C_["green"], name="holly leaf")
    d.fill(amp, C_["gold"], angle=None, spacing=0.35, name="ampersand")
    for g in stars:
        d.fill(g, C_["gold"], angle=45, name="twinkle")
    for b in berries:
        d.fill(b, C_["berry"], angle=45, underlay=False, name="berry")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
