"""Christmas Stocking: a red knit stocking with a blank white cuff for a name.

Spec:
  object:       Christmas stocking motif for stockings, sweatshirts, tea towels; the cuff
                is left plain so buyers can add a name in their embroidery software
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       felt / wovens with tear-away; knits with cut-away
  threads:      red (stocking, hanging loop), green (heel, toe, knit stripes, holly
                leaves), white (cuff), silver (1.2 mm cuff edge), berry (berries): 5 colours
  must have:    a 60 mm stocking with the toe to the right; green heel and toe patches
                and two 2.4 mm green stripes across the leg; a 32 x 13 mm white cuff with a
                silver satin edge; a holly sprig with three berries on the cuff's corner;
                a 1.4 mm satin hanging loop
  density:      patches knock out the stocking; the cuff tucks under its edge; max 3.5
"""
import numpy as np

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, holly_sprig, hoop_for, product, standard_checks

DESCRIPTION = "Red knit Christmas stocking with a blank cuff for a name and a holly sprig"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Christmas Stocking Embroidery Design",
    "A red Christmas stocking with a blank white cuff, ready for a name",
    ["christmas stocking", "personalized stocking", "stocking name", "holly",
     "kids christmas", "christmas decor"],
    "A classic red knit Christmas stocking with green heel, toe and stripes and a sprig of "
    "holly. The white cuff is left plain so you can add a name in your embroidery software.\n\n"
    "Great on stockings, sweatshirts, gift bags and tea towels.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.2


def checks(p):
    return standard_checks(p, 5, 12000, between_mm2=3.0)


def art():
    d = Design()
    sock = smooth([(-12, 26), (12, 26), (12, -3), (23, -9), (31, -17), (28, -28), (14, -31), (-3, -27),
                   (-13, -15)], 10).buffer(0)
    cuff = rounded_rect(32, 13, 3.0, 0, 30)
    heel = circle(-13, -27, 12).intersection(sock)
    toe = circle(33, -21, 10).intersection(sock)
    stripes = union(rect(30, 2.4, 0, 10), rect(30, 2.4, 0, 4)).intersection(sock)
    loop = spline([(-13.5, 36.8), (-16.5, 41.5), (-15.5, 46.5), (-12, 47), (-10.5, 42), (-10.5, 36.8)], samples=8)
    leaves, veins, berries = holly_sprig(12, 36, deg=10, length=11)
    holly = union(*leaves, *berries)
    d.satin(loop, 1.4, C_["red"], name="hanging loop", trim_after=True)
    d.fill(knockout(sock, heel, toe, stripes, cuff), C_["red"], angle=80, name="stocking")
    d.fill(knockout(tuck(cuff, BORDER), holly), C_["white"], angle=0, name="cuff")
    d.outline(cuff, C_["silver"], width=BORDER, name="cuff edge")
    for g in (heel, toe, stripes):
        d.fill(g, C_["green"], angle=30, name="knit patch")
    for g in leaves:
        d.fill(knockout(g, *berries), C_["green"], angle=None, name="holly leaf")
    for b in berries:
        d.fill(b, C_["berry"], angle=45, underlay=False, name="berry")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
