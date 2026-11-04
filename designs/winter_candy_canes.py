"""Candy Canes: two striped candy canes crossed, tied with a green bow.

Spec:
  object:       Christmas candy canes for kids' sweatshirts, stockings, gift bags, towels
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and towels with tear-away (+ topper on towels)
  threads:      white (cane body), red (diagonal stripes and a continuous 1.4 mm border),
                green (bow), pine (bow knot): 4 colours
  must have:    two 8 mm wide canes, hooks curling outward, crossed in a shallow X;
                3.2 mm red stripes at 3.2 mm gaps running diagonally across each cane;
                a 46 mm green bow, its knot right over the crossing
  density:      the front cane knocks out the back one, the stripes and bow knock out the
                white; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Two crossed red-and-white candy canes tied with a green bow"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Crossed Candy Canes Embroidery Design",
    "Two striped candy canes crossed and tied with a green bow",
    ["candy cane", "peppermint", "kids christmas", "christmas stocking", "sweet treats"],
    "Two peppermint candy canes, crossed and tied with a green bow. Red stripes run diagonally "
    "across each cane and a red satin border keeps the white crisp on any fabric colour.\n\n"
    "Great on kids' sweatshirts, stockings, gift bags and tea towels.",
    mockups=("tshirt", "tote"),
)

W = 8.0          # cane width
BORDER = 1.4
PIVOT = (0, -41)


def checks(p):
    # the bow leaves a small open notch where the canes cross
    return standard_checks(p, 4, 15000, between_mm2=2.0)


def _cane(sign, deg, dx):
    path = M.candy_cane(82, 15) * np.array([sign, 1.0])     # hook curls outward
    body = LineString(path).buffer(W / 2, cap_style="round", quad_segs=12)
    return move(rotate(body, deg, origin=PIVOT), dx, 0)


def _stripes(body, sign, deg, dx):
    # bands across the cane at 40 deg to its shaft, laid out in the cane's own frame
    bands = [rotate(rect(60, 3.2, 0, k * 6.4), sign * 40, origin=(0, k * 6.4)) for k in range(-20, 21)]
    s = move(rotate(union(*bands), deg, origin=PIVOT), dx, 0).intersection(body)
    return s.buffer(-0.6).buffer(0.6)          # drop the slivers where a band grazes the edge


def _bow(d, bow, main, knot_color):
    lo, ro, knot, lt, rt = bow
    d.fill(knockout(lt, lo, ro, knot), main, angle=75, name="tail")
    d.fill(knockout(rt, lo, ro, knot), main, angle=105, name="tail")
    d.fill(knockout(lo, knot), main, angle=150, name="loop")
    d.fill(knockout(ro, knot), main, angle=30, name="loop")
    d.fill(knot, knot_color, angle=100, name="knot")


def art():
    d = Design()
    back = _cane(-1, -20, -16)
    front = _cane(1, 20, 16)
    back_st = _stripes(back, -1, -20, -16)
    front_st = _stripes(front, 1, 20, 16)
    bow = [move(g, 0, 1.0) for g in M.bow(46)]
    bow_all = union(*bow)
    under_bow = grow(bow_all, BORDER * 0.35)      # cane borders mostly outside the bow
    # min_width 3: drop the slivers left between the bow and the crossing (their
    # borders would pile up into a knot of satin)
    back_vis = knockout(back, grow(front, BORDER * 1.1), under_bow, min_width=3.0)  # borders side by side
    front_vis = knockout(front, under_bow, min_width=3.0)
    d.fill(knockout(tuck(back_vis, BORDER), back_st), C_["white"], angle=120, name="back cane")
    d.fill(knockout(tuck(front_vis, BORDER), front_st), C_["white"], angle=60, name="front cane")
    # stripes stop under the border like the white does (a stripe running under the whole
    # satin stacks three layers where the border fans round a corner)
    for st, vis, ang, nm in ((back_st, back_vis, 120, "back"), (front_st, front_vis, 60, "front")):
        d.fill(st.intersection(tuck(vis, BORDER)).buffer(-0.5).buffer(0.5), C_["red"], angle=ang,
               name=f"{nm} stripes")
        d.outline(vis, C_["red"], width=BORDER, name=f"{nm} border")
    # the notches left between the two borders and the bow (where min_width dropped the
    # slivers) would open once the fabric pulls: the loops reach over them
    sewn = union(grow(back_vis, BORDER / 2), grow(front_vis, BORDER / 2), bow_all)
    notches = [g for g in polygons_of(sewn.buffer(1.5).buffer(-1.5).difference(sewn))
               if g.area < 30 and g.distance(bow_all) < 0.3]
    lo, ro, *rest = bow
    for g in notches:
        if g.distance(lo) <= g.distance(ro):
            lo = union(lo, grow(g, 0.5))
        else:
            ro = union(ro, grow(g, 0.5))
    _bow(d, [lo, ro, *rest], C_["green"], C_["pine"])
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
