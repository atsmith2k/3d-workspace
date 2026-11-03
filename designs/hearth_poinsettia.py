"""Poinsettia: a red Christmas poinsettia with two-tone bracts and green leaves.

Spec:
  object:       poinsettia flower for napkins, tea towels, table runners, sweatshirts
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (linens) with tear-away; knits with cut-away
  threads:      green (leaves), pine (leaf veins), red (outer bracts), berry (bract veins,
                inner bracts), gold (flower buds): 5 colours
  must have:    five 30 x 13 mm red outer bracts; five 20 x 9 mm berry inner bracts
                between them; five 36 mm green leaves peeking out behind; bean-stitch veins
                on the leaves and outer bracts, clear of everything sewn on top; a cluster
                of seven 3.4 mm gold buds in the centre
  density:      every layer knocks out the one under it; max 3.5
"""
import math

import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Red Christmas poinsettia with two-tone bracts, green leaves and gold buds"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Poinsettia Embroidery Design",
    "A red Christmas poinsettia with green leaves and a gold centre",
    ["poinsettia", "christmas flower", "christmas floral", "christmas napkin",
     "christmas table runner"],
    "A full Christmas poinsettia: red and deep rose bracts with stitched veins, green leaves "
    "peeking out behind and a cluster of gold buds in the middle.\n\nGreat on napkins, tea "
    "towels, table runners and sweatshirts.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 13000, between_mm2=4.0)


def _turn(g, deg):
    """A `motifs.leaf` (stem at the origin, pointing +Y) turned to point at `deg`."""
    return rotate(g, deg - 90, origin=(0, 0))


def _vein(length, deg, f0, f1):
    a = math.radians(deg)
    u = np.array([math.cos(a), math.sin(a)])
    return np.array([u * length * f0, u * length * f1])


def art():
    d = Design()
    outer_a = [90 + 72 * k for k in range(5)]
    inner_a = [a + 36 for a in outer_a]
    leaves = [_turn(M.leaf(40, 15), a) for a in inner_a]
    outer = [_turn(M.leaf(32, 13), a) for a in outer_a]
    inner = [_turn(M.leaf(21, 9.5), a) for a in inner_a]
    buds = [circle(0, 0, 1.7)] + [circle(3.6 * math.cos(math.radians(60 * k + 30)),
                                         3.6 * math.sin(math.radians(60 * k + 30)), 1.7) for k in range(6)]
    centre = union(*buds).buffer(0.3)
    all_outer, all_inner = union(*outer), union(*inner)
    d.fill(knockout(union(*leaves), all_outer, all_inner), C_["green"], angle=None, name="leaves")
    for a in inner_a:
        d.run(_vein(40, a, 0.66, 0.9), C_["pine"], bean=1, name="leaf vein", trim_after=True)
    for g, a in zip(outer, outer_a):
        d.fill(knockout(g, all_inner, centre), C_["red"], angle=a, name="outer bract")
    for a in outer_a:
        d.run(_vein(32, a, 0.48, 0.86), C_["berry"], bean=1, name="bract vein", trim_after=True)
    for g, a in zip(inner, inner_a):
        d.fill(knockout(g, centre), C_["berry"], angle=a, name="inner bract")
    for b in buds:
        d.fill(b, C_["gold"], angle=45, underlay=False, name="bud")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
