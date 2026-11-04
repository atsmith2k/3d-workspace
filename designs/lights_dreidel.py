"""Spinning Dreidel: a blue and white dreidel tilted mid-spin with a Star of David on its
front face, spin swooshes and gold gelt coins and sparkles.

Spec:
  object:       Hanukkah dreidel for kids' tees, sweatshirts, bibs, totes and tea towels
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      navy (side faces, handle), blue (front face), white (edge highlights,
                Star of David), sky (top face, swooshes), yellow (gelt), gold (gelt rims,
                sparkles): 6 colours
  must have:    a three-quarter dreidel 30 mm wide, 60 mm tall with its handle, tilted
                15 deg: a blue front face with a pointed bottom, navy side faces, a sky
                top face and a navy handle; 1.4 mm white satin highlights on the front
                edges; a white Star of David (two triangles as 2.2 mm bands, 19 mm tip to
                tip) on the front face; no Hebrew letters; two tapered sky spin swooshes
                under the point and three motion lines beside it; two gold-rimmed yellow
                gelt coins (6.5 mm radius) and three four-point gold sparkles
  density:      faces meet with 0.4 mm overlap (knockout); the star and highlights knock
                the faces out; coins knock out under their rims; max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Blue and white spinning dreidel with a Star of David, swooshes and gold gelt"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Spinning Dreidel Hanukkah Embroidery Design",
    "A blue and white dreidel spinning on its point, with a Star of David, gold gelt and sparkles",
    ["dreidel", "spinning dreidel", "star of david", "gelt", "hanukkah gelt", "kids hanukkah",
     "festival of lights", "hanukkah game", "blue and white"],
    "A blue and white dreidel caught mid-spin: tilted on its point with a white Star of David on "
    "the front, sky-blue swooshes whirling round it, two gold gelt coins and a few sparkles.\n\n"
    "Sweet on kids' tees and sweatshirts, bibs and totes, and on Hanukkah tea towels and "
    "napkins.",
    mockups=("tshirt", "tote"),
)

TILT = -15.0                       # degrees; the dreidel leans right as it spins


def checks(p):
    return standard_checks(p, 6, 14000)


def _band_triangle(r, w, rot, x, y):
    outer = regular_polygon(3, r, x, y, rot=rot)
    inner = regular_polygon(3, r - 2 * w, x, y, rot=rot)     # inradius shrinks by w
    return outer.difference(inner)


def _sparkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


def _tapered(pts, w_max):
    n = len(pts)
    t = np.linspace(0, 1, n)
    w = 0.5 + (w_max - 0.5) * np.sin(np.pi * t) ** 0.8
    return [tuple(p) for p in pts], list(np.maximum(w, 0.5))


def dreidel():
    front = poly([(-13, -6), (11, -6), (11, 18), (-13, 18)])
    point = poly([(-13, -6), (11, -6), (1, -27)])
    side = poly([(11, -6), (17, -2), (17, 22), (11, 18)])
    side_pt = poly([(11, -6), (17, -2), (1, -27)])
    top = poly([(-13, 18), (11, 18), (17, 22), (-7, 22)])
    handle = union(rect(5.0, 10.0, 2.0, 25.0), circle(2.0, 30.0, 2.5))
    star_ = union(_band_triangle(10.0, 2.2, 90, -1, 7), _band_triangle(10.0, 2.2, -90, -1, 7))
    hi_bottom = [(-12.2, -6.0), (10.2, -6.0)]
    hi_right = [(11.0, -5.0), (11.0, 17.2)]
    hi_top = [(-12.2, 18.0), (10.2, 18.0)]
    return dict(front=union(front, point), side=union(side, side_pt), top=top, handle=handle,
                star=star_, highlights=[hi_bottom, hi_right, hi_top])


def art():
    d = Design()
    g = dreidel()
    rot = lambda s: rotate(s, TILT, origin=(0, 0))
    rotp = lambda pts: [tuple(c) for c in rotate(LineString(pts), TILT, origin=(0, 0)).coords]
    front, side, top, handle, star_ = (rot(g[k]) for k in ("front", "side", "top", "handle", "star"))
    highs = [rotp(h) for h in g["highlights"]]
    high_bands = [LineString(h).buffer(0.7, cap_style="flat") for h in highs]

    # spin swooshes under the point, motion lines to the left
    swooshes = []
    for cx, cy, rx, ry, a0, a1, w in ((-6, -24.5, 15, 3.6, 195, 345, 1.9), (-6, -26.0, 24, 6.0, 210, 335, 1.7)):
        t = np.radians(np.linspace(a0, a1, 14))
        swooshes.append(_tapered(np.c_[cx + rx * np.cos(t), cy + ry * np.sin(t)], w))
    for k, (y, L) in enumerate(((8, 11), (0, 15), (-8, 10))):
        x1 = -24.0 + 2.5 * k * (k - 1) / 2
        pts = np.c_[np.linspace(x1 - L, x1, 8), y + 0.5 * np.sin(np.linspace(0, np.pi, 8))]
        swooshes.append(_tapered(pts, 1.7))

    coins = [(27.0, -20.0, 6.5), (-29.0, -22.0, 5.5)]
    sparkles = [_sparkle(-26, 26, 4.6), _sparkle(26, 18, 4.0), _sparkle(31, -4, 3.2)]

    # navy: side faces and handle
    d.fill(knockout(side, front, top, *high_bands), C_["navy"], angle=60, name="side faces")
    d.fill(handle, C_["navy"], angle=75, name="handle")
    # blue front face (star and highlights knocked out)
    d.fill(knockout(front, star_, *high_bands), C_["blue"], angle=-15, name="front face")
    # sky top face (the handle sewn before it is knocked out) and swooshes
    d.fill(knockout(top, handle, *high_bands), C_["sky"], angle=10, name="top face")
    # sky swooshes
    for pts, w in swooshes:
        d.satin(pts, w, C_["sky"], name="swoosh", taper=True)
    # white: star and edge highlights
    d.fill(star_, C_["white"], angle=TILT, name="Star of David")
    for h in highs:
        d.satin(h, 1.4, C_["white"], name="highlight")
    # gelt: yellow faces, gold rims and sparkles
    for x, y, r in coins:
        d.fill(knockout(circle(x, y, r), ring(x, y, r + 0.6, r - 0.9)), C_["yellow"], angle=30, name="gelt")
    for x, y, r in coins:
        d.outline(circle(x, y, r - 0.1), C_["gold"], width=1.4, name="gelt rim")
        d.run(circle_path(x, y, r * 0.55), C_["gold"], bean=1, length=1.3, name="gelt ring")
    for s in sparkles:
        d.fill(s, C_["gold"], angle=45, name="sparkle")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
