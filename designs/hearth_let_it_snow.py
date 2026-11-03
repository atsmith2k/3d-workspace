"""Let It Snow: script lettering in two blues with three satin snowflakes.

Spec:
  object:       winter lettering for sweatshirts, totes, pillows and towels (December to
                March, not only Christmas)
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away; towels add a topper
  threads:      navy ("Let it"), sky ("snow"), ice (snowflakes): 3 colours
  must have:    "Let it" at 15 mm and "snow" at 27 mm cap height in bold script, filled at
                0.35 mm rows; three six-arm snowflakes (radius 9, 7 and 6 mm) with 1.3 mm
                satin arms, 1.0 mm satin side branches and a filled hexagon centre
  font:         Segoe Script Bold (Windows `segoescb.ttf`), as in `winter_merry_bright`
  density:      the lettering does not overlap; branch roots lie under their arms (2.7)
"""
import math
from pathlib import Path

import numpy as np

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Let It Snow script lettering with three satin snowflakes"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Let It Snow Embroidery Design",
    "\"Let it snow\" in blue script with three sparkling snowflakes",
    ["let it snow", "winter lettering", "snowflake", "winter quote", "snow day", "winter sweatshirt"],
    "\"Let it snow\" in a bold navy and sky-blue script, with three stitched snowflakes "
    "drifting around it. A winter saying that sews all season.\n\nGreat on sweatshirts, totes, "
    "pillows and towels.",
    mockups=("tshirt", "tote"),
    base=["winter embroidery design", "machine embroidery", "winter", "holiday"],
)

FONT = Path("C:/Windows/Fonts/segoescb.ttf")


def checks(p):
    return standard_checks(p, 3, 11000)


def _word(s, size, x, y):
    t = text_shape(s, size, font="Segoe Script", bold=True, font_path=FONT if FONT.exists() else None)
    return move(centered(t), x, y)


def sew_flake(d, x, y, r, color):
    """A six-arm satin snowflake: side branches first (roots under the arms), then the
    arms, then the hexagon centre."""
    for i in range(6):
        a = math.radians(90 + 60 * i)
        u = np.array([math.cos(a), math.sin(a)])
        base = np.array([x, y]) + u * r * 0.55
        for side in (1, -1):
            b = a + side * math.radians(50)
            tip = base + np.array([math.cos(b), math.sin(b)]) * r * 0.32
            d.satin(np.array([base, tip]), 1.0, color, name="branch", underlay="none", trim_after=True)
    for i in range(6):
        a = math.radians(90 + 60 * i)
        u = np.array([math.cos(a), math.sin(a)])
        d.satin(np.array([np.array([x, y]) + u * r * 0.14, np.array([x, y]) + u * r]), 1.3, color,
                name="arm", underlay="none", trim_after=True)
    d.fill(regular_polygon(6, max(1.3, r * 0.17), x, y, rot=90), color, angle=0, underlay=False, name="centre")


def art():
    d = Design()
    let = _word("Let it", 15, -14, 16)
    snow = _word("snow", 27, 4, -8)
    d.fill(let, C_["navy"], angle=None, spacing=0.35, name="Let it")
    d.fill(snow, C_["sky"], angle=None, spacing=0.35, name="snow")
    sew_flake(d, 28, 22, 9.0, C_["ice"])
    sew_flake(d, -37, -27, 7.0, C_["ice"])
    sew_flake(d, 36, -24, 6.0, C_["ice"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
