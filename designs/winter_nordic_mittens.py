"""Nordic Mittens: a pair of red knitted mittens with white folk stars, on a string.

Spec:
  object:       cosy winter mittens for sweatshirts, beanies, kids' wear and stockings
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits and fleece with cut-away; wovens with tear-away
  threads:      red (hands and the string), white (cuffs, folk stars, dot band), green
                (cuff stripe): 3 colours
  must have:    two 52 mm mittens, thumbs inward, tilted 8 deg outward; ribbed white
                cuffs (fill rows along the ribs); an eight-point white star on each
                back; a band of seven white dots above each cuff; a green 1.6 mm satin
                stripe across each cuff; a bean-stitch string looping below the cuffs
  density:      stars and dots knock out the red; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Pair of red Nordic mittens with white folk stars, joined by a string"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Nordic Mittens Embroidery Design",
    "A pair of red knitted mittens with white folk stars, joined by a string",
    ["mittens", "nordic knit", "cozy winter", "kids winter", "scandi christmas"],
    "A pair of cosy red mittens with ribbed white cuffs, a white folk star on each and a row of "
    "dots, joined by their string. Wintry rather than strictly Christmas, so it sews up all "
    "season.\n\nGreat on sweatshirts, beanies, kids' wear and stockings.",
    mockups=("tshirt", "cap"),
)

H = 52.0


def checks(p):
    return standard_checks(p, 3, 10000)


def _pose(g, sign):
    """sign -1: the left mitten (as drawn, thumb on the right); +1: the right one."""
    g = scale(g, -1, 1) if sign > 0 else g
    return move(rotate(g, -sign * 8, origin=(0, 0)), sign * 25, 0)


def art():
    d = Design()
    parts = []
    for sign in (-1, 1):
        hand, cuff = M.mitten(H)
        star = move(M.folk_star(8.0, 4.0), -0.02 * H, 0.57 * H)
        dots = [circle(-0.02 * H + (k - 3) * 4.2, 0.31 * H, 1.05) for k in range(7)]
        parts.append(dict(hand=_pose(hand, sign), cuff=_pose(cuff, sign), star=_pose(star, sign),
                          dots=[_pose(g, sign) for g in dots], sign=sign))
    for m in parts:
        top = union(m["cuff"], m["star"], *m["dots"])
        d.fill(knockout(m["hand"], top), C_["red"], angle=80 - 20 * m["sign"], name="mitten")
    # the string: from one cuff's outer bottom corner, in a loop below, into the other
    a, b = parts[0]["cuff"].bounds, parts[1]["cuff"].bounds
    p0 = (a[0] + 3.5, a[1] + 1.5)
    p1 = (b[2] - 3.5, b[1] + 1.5)
    string = bezier(p0, (p0[0] - 6, p0[1] - 24), (p1[0] + 6, p1[1] - 24), p1, 40)
    d.run(string, C_["red"], bean=1, name="string", trim_after=True)
    for m in parts:
        d.fill(knockout(m["cuff"], m["star"]), C_["white"], angle=90 - 8 * m["sign"], name="cuff")
        d.fill(m["star"], C_["white"], angle=45, name="star")
        for g in m["dots"]:
            d.fill(g, C_["white"], angle=0, underlay=False, name="dot")
    for m in parts:
        cx0, _, cx1, _ = m["cuff"].bounds
        c = np.array(m["cuff"].centroid.coords[0])
        r = math.radians(-m["sign"] * 8)
        u = np.array([math.cos(r), math.sin(r)])
        half = (cx1 - cx0) / 2 - 3.2
        d.satin(np.array([c - u * half, c + u * half]), 1.6, C_["green"], name="cuff stripe", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
