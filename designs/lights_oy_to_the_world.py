"""Oy to the World: three lines of block lettering, a big "OY" with a drop shadow, a small
gold Star of David and sparkles.

Spec:
  object:       Hanukkah pun lettering for sweatshirts, tees and totes
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      sky (OY shadow), blue (OY), navy (WORLD), gold ("TO THE", the star,
                sparkles, rules): 4 colours
  must have:    "OY" in our block lettering, 30 mm cap, blue with a sky offset shadow;
                "TO THE" 8 mm cap in gold between two 1.6 mm gold satin rules; "WORLD"
                16 mm cap in navy; a gold Star of David (two triangles as 1.8 mm bands,
                16 mm tip to tip) beside OY; three four-point gold sparkles
  lettering:    `cadkit.stitch.lettering.block_text` (our own alphabet, no font licence);
                rows 0.35 mm; at 4x4 the smallest cap is >= 6.5 mm
  density:      the shadow is knocked out under OY; nothing else overlaps; max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "OY TO THE WORLD block lettering with a gold Star of David and sparkles"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Oy to the World Hanukkah Embroidery Design",
    "\"OY TO THE WORLD\" in bold blue and gold block letters with a Star of David",
    ["oy to the world", "oy vey", "funny hanukkah", "hanukkah pun", "star of david",
     "hanukkah sweatshirt", "jewish humor", "chrismukkah", "holiday lettering"],
    "A big blue \"OY\" with a sky-blue drop shadow over \"TO THE WORLD\" in gold and navy "
    "block letters, with a little gold Star of David and a few sparkles. The holiday pun every "
    "Hanukkah party needs.\n\n"
    "Made for sweatshirts and tees, and great on totes, pillows and gift bags.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 4, 14000)


def _centred(t, cx, y_base):
    x0, y0, x1, y1 = t.bounds
    return move(t, cx - (x0 + x1) / 2, y_base - y0)


def _solid(t):
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(t)])


def _band_triangle(r, w, rot, x, y):
    return regular_polygon(3, r, x, y, rot=rot).difference(regular_polygon(3, r - 2 * w, x, y, rot=rot))


def _sparkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


def art():
    d = Design()
    oy = _centred(block_text("OY", cap=30, stroke=2.5, tracking=1.6), -7, 12)
    shadow = knockout(move(oy, 2.0, -2.0), _solid(oy))
    to_the = _centred(block_text("TO THE", cap=8, stroke=2.5, tracking=1.4), 0, 0)
    world = _centred(block_text("WORLD", cap=16, stroke=2.5, tracking=1.3), 0, -20)
    x0, _, x1, _ = to_the.bounds
    wx0, _, wx1, _ = world.bounds
    rules = [[(wx0, 4.0), (x0 - 3.0, 4.0)], [(x1 + 3.0, 4.0), (wx1, 4.0)]]
    ox1 = oy.bounds[2]
    sx, sy = ox1 + 11.0, 32.0
    star_ = union(_band_triangle(9.0, 1.8, 90, sx, sy), _band_triangle(9.0, 1.8, -90, sx, sy))
    sparkles = [_sparkle(oy.bounds[0] - 8, 36, 4.6), _sparkle(sx + 2, 16.5, 3.4),
                _sparkle(wx1 + 4, -24, 3.8)]

    d.fill(shadow, C_["sky"], angle=45, name="OY shadow")
    d.fill(oy, C_["blue"], angle=0, spacing=0.35, name="OY")
    d.fill(world, C_["navy"], angle=0, spacing=0.35, name="WORLD")
    for r in rules:
        d.satin(r, 1.6, C_["gold"], name="rule")
    d.fill(to_the, C_["gold"], angle=0, spacing=0.35, name="TO THE")
    d.fill(star_, C_["gold"], angle=30, name="Star of David")
    for s in sparkles:
        d.fill(s, C_["gold"], angle=45, name="sparkle")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
