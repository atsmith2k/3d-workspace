"""Cardinal on Holly: a red cardinal perched on a branch with holly leaves and berries.

Spec:
  object:       winter songbird motif (cardinals are a memorial / "visitor from heaven"
                favourite) for sweatshirts, towels, pillows and framed hoops
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and towels with tear-away (+ topper on towels)
  threads:      cocoa (branch), green (holly), red (body, berries), berry (wing and
                tail shading), black (face mask), carrot (beak): 6 colours
  must have:    a cardinal facing left with a pointed crest; a darker wing with three
                red feather runs kept 2 mm inside it; a long tail; a black mask round the
                eye and beak; an orange cone beak; a 3 mm satin branch it sits on; two
                holly sprigs with three berries each on the branch
  density:      every part knocks out what it covers; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *

from _winter import C_, SIZES, fit, holly_sprig, product, standard_checks

DESCRIPTION = "Red cardinal perched on a holly branch"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Cardinal on Holly Embroidery Design",
    "A red cardinal perched on a branch of holly and berries",
    ["cardinal", "cardinal embroidery", "winter bird", "memorial cardinal", "holly branch"],
    "A bright red cardinal perched on a winter branch with sprigs of holly and red berries. A "
    "darker wing, a long tail and the black mask round its orange beak make it unmistakable.\n\n"
    "Great on sweatshirts, tea towels, pillows and framed hoops.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    # the slot left between the berries, the branch and the tail is open on purpose
    return standard_checks(p, 6, 12000, between_mm2=4.0)


def art():
    d = Design()
    body = smooth([(-22, 17), (-19, 24), (-13, 29), (-7, 39), (-5, 31), (1, 26), (10, 19), (17, 10),
                   (19, 2), (14, -10), (4, -12.5), (-8, -11.5), (-17, -2), (-21, 8)], 10).buffer(0)
    tail = smooth([(12, 2), (26, -8), (40, -19), (37, -24), (22, -15), (8, -6)], 6).buffer(0)
    wing = smooth([(-5, 13), (6, 17), (15, 10), (22, -3), (12, -4), (0, 1)], 8).buffer(0)
    mask = smooth([(-24, 20.5), (-18, 25), (-12.5, 21), (-13, 14), (-21, 12.5)], 6).buffer(0)
    beak = poly([(-20.5, 21.5), (-30, 17.5), (-20.5, 13.5)])
    branch = spline(np.array([(-40, -13), (-10, -11), (20, -13), (42, -10)]), 10)
    feathers = [spline(np.array(p), 6) for p in (
        [(1, 4), (9, 8), (16, 5)], [(4, 0), (11, 2), (17, -1)], [(-1, 9), (7, 13), (12, 12)])]
    sprigs = [holly_sprig(-32, -14, deg=-90, length=14), holly_sprig(14, -14.5, deg=-90, length=12)]
    leaves = [g for s in sprigs for g in s[0]]
    berries = [g for s in sprigs for g in s[2]]
    bird = union(body, tail)
    d.satin(branch, 3.0, C_["cocoa"], name="branch")
    for g in leaves:
        d.fill(knockout(g, bird, *berries), C_["green"], name="holly leaf")
    d.fill(knockout(tail, body), C_["berry"], angle=-35, name="tail")
    d.fill(wing, C_["berry"], angle=20, name="wing")
    d.fill(knockout(body, wing, mask, beak), C_["red"], angle=60, name="body")
    for b in berries:
        d.fill(knockout(b, bird), C_["red"], angle=45, underlay=False, name="berry")
    for f in feathers:
        d.run(f, C_["red"], bean=1, name="feather", trim_after=True)
    d.fill(knockout(mask, beak), C_["black"], angle=0, name="mask")
    d.fill(beak, C_["carrot"], angle=0, name="beak")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
