"""Coquette Ornament: a blush Christmas bauble with a pink ribbon band, pearls and a bow.

Spec:
  object:       coquette-trend bauble for sweatshirts, totes, stockings and gift bags
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits and sweatshirts with cut-away; wovens with tear-away
  threads:      gold (hanger loop, cap), blush (ball), pink (ribbon band and bow),
                white (pearls, highlight arc), berry (bow knot): 5 colours
  must have:    a 62 mm ball; a gold cap and a bean-stitch hanger loop; a 9 mm pink band
                across the ball with eleven 1.3 mm pearls along its middle; a 44 mm pink
                bow over the cap; a white bean-stitch highlight arc on the upper left
  density:      band, pearls and bow knock out what they cover; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, sew_bow, standard_checks

DESCRIPTION = "Blush bauble with a pink ribbon band, pearls and a coquette bow"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Coquette Bow Ornament Embroidery Design",
    "A blush-pink Christmas bauble with a ribbon band, pearls and a bow",
    ["coquette christmas", "coquette bow", "pink ornament", "christmas bauble", "pearls"],
    "A soft blush Christmas bauble wrapped in a pink ribbon band strung with pearls, topped with "
    "a big coquette bow over its gold cap. Pretty, girly and very on-trend.\n\nGreat on "
    "sweatshirts, totes, stockings and gift bags.",
    mockups=("tshirt", "tote"),
)

R = 31.0


def checks(p):
    return standard_checks(p, 5, 11000)


def art():
    d = Design()
    ball, cap, hook = M.bauble(R, 0, -8)
    band_y = -10.0
    band = rect(2 * R + 4, 9, 0, band_y).intersection(ball)
    pearls = [circle(x, band_y, 1.3) for x in [(k - 5) * 5.2 for k in range(11)]
              if ball.buffer(-2.5).contains(Point(x, band_y))]
    bow = [move(g, 0, -8 + R * 1.02 + 2) for g in M.bow(44)]
    bow_all = union(*bow)
    # the hanger stops at the bow and the cap: a bean run under a fill piles up the thread
    hanger = LineString(hook).difference(union(bow_all, cap).buffer(0.6))
    for part in getattr(hanger, "geoms", [hanger]):
        if part.length > 2:
            d.run(np.asarray(part.coords), C_["gold"], bean=1, name="hanger", trim_after=True)
    d.fill(knockout(cap, bow_all), C_["gold"], angle=0, name="cap")
    d.fill(knockout(ball, band, bow_all, cap), C_["blush"], angle=45, name="ball")
    d.fill(knockout(band, *pearls), C_["pink"], angle=0, name="band")
    sew_bow(d, bow, C_["pink"], C_["berry"])
    for g in pearls:
        d.fill(g, C_["white"], angle=45, underlay=False, name="pearl")
    d.run(arc(0, -8, R - 6, 128, 162), C_["white"], bean=1, name="highlight", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
