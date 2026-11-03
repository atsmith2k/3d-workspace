"""Christmas Lights: "Merry Christmas" script under a swagged string of C9 bulbs.

Spec:
  object:       holiday lettering for sweatshirts, totes, pillows and tea towels
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      green (wire, sockets, green bulbs), red (red bulbs, lettering), gold,
                sky and pink (bulbs): 5 colours
  must have:    a 1.2 mm satin wire in two swags across the top; nine 6 x 10 mm C9 bulbs
                hanging from it on green sockets, alternating red, gold, green, sky, pink;
                "Merry" and "Christmas" in bold script, 16 mm cap height, 0.35 mm rows
  font:         Segoe Script Bold (Windows `segoescb.ttf`), as in `winter_merry_bright`
  density:      sockets sit on the wire (2.7 layers); bulbs knock out their sockets
"""
from pathlib import Path

import numpy as np

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Merry Christmas script under a string of coloured C9 Christmas lights"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Christmas Lights Merry Christmas Embroidery Design",
    "\"Merry Christmas\" in red script under a string of colourful vintage bulbs",
    ["christmas lights", "merry christmas", "christmas lettering", "vintage christmas bulbs",
     "christmas sweatshirt"],
    "A swagged string of big vintage C9 Christmas bulbs in red, gold, green, blue and pink, "
    "hanging over \"Merry Christmas\" in a bold red script.\n\nGreat on sweatshirts, totes, "
    "pillows and tea towels.",
    mockups=("tshirt", "tote"),
)

FONT = Path("C:/Windows/Fonts/segoescb.ttf")
COLORS = ["red", "gold", "green", "sky", "pink"]


def checks(p):
    return standard_checks(p, 5, 12000)


def _word(s, size, y):
    t = text_shape(s, size, font="Segoe Script", bold=True, font_path=FONT if FONT.exists() else None)
    return move(centered(t), 0, y)


def _bulb(x, y, deg):
    """A C9 bulb hanging from (x, y), turned `deg` from straight down; (bulb, socket)."""
    b = smooth([(-2.5, -1.5), (-3.3, -4.5), (-2.4, -8.0), (0, -11.5), (2.4, -8.0), (3.3, -4.5), (2.5, -1.5)], 8)
    b = b.buffer(0)
    s = rounded_rect(4.2, 3.4, 0.8, 0, -0.6)
    return move(rotate(b, deg), x, y), move(rotate(s, deg), x, y)


def art():
    d = Design()
    wire = spline([(-47, 40), (-24, 27), (0, 36), (24, 27), (47, 40)], samples=16)
    L = np.cumsum(np.r_[0, np.hypot(*np.diff(wire, axis=0).T)])
    bulbs = []
    for k in range(9):
        s = L[-1] * (k + 0.5) / 9
        i = int(np.searchsorted(L, s))
        x, y = wire[i]
        tx, ty = wire[min(i + 1, len(wire) - 1)] - wire[max(i - 1, 0)]
        deg = np.degrees(np.arctan2(ty, tx)) * 0.6 + (8 if k % 2 else -8)
        b, s_ = _bulb(x, y, deg)
        bulbs.append((b, s_, COLORS[k % 5]))
    merry = _word("Merry", 16, 6)
    xmas = _word("Christmas", 16, -16)
    d.satin(wire, 1.2, C_["green"], name="wire", trim_after=True)
    for b, s_, c in bulbs:
        d.fill(knockout(s_, b), C_["green"], angle=0, underlay=False, name="socket")
    for b, s_, c in bulbs:
        if c == "green":
            d.fill(b, C_["green"], angle=80, name="bulb")
    for b, s_, c in bulbs:
        if c == "red":
            d.fill(b, C_["red"], angle=80, name="bulb")
    d.fill(merry, C_["red"], angle=None, spacing=0.35, name="Merry")
    d.fill(xmas, C_["red"], angle=None, spacing=0.35, name="Christmas")
    for c in ("gold", "sky", "pink"):
        for b, s_, bc in bulbs:
            if bc == c:
                d.fill(b, C_[c], angle=80, name="bulb")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
