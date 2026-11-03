"""Silver Tree Banner: a heraldic flowering silver tree under a crescent moon, on a navy
swallowtail banner hung from a gold rod.

Spec:
  object:       a kingdom's war banner (original arms: no stars, no crown) for tees,
                hoodies, cloaks, totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens, canvas and cloaks with tear-away
  threads:      navy (field), silver (tree), white (blossoms, moon), gold (border, rod,
                finials): 4 colours
  must have:    a 58 x 76 mm navy banner with a swallowtail foot, 2.4 mm gold satin
                border; a 62 mm gold rod with ball finials above it; a silver tree with
                spreading roots, a trunk and two fork limbs in a fill (rows along the
                grain), nine branches as tapered satins 2.4 -> 1.1 mm; fifteen white
                five-petal blossoms 5 mm across at the branch tips; a white crescent moon
                over the crown
  density:      the field is knocked out under the tree, blossoms and moon; branches
                stop under their blossoms; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *

from _kingdom import C_, SIZES, band, fit, hoop_for, product, standard_checks, tube, widths_along

DESCRIPTION = "Heraldic flowering silver tree under a crescent moon on a navy swallowtail banner"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Silver Tree Banner Embroidery Design",
    "A heraldic silver tree in white blossom under a crescent moon, on a navy banner bordered in gold",
    ["white tree", "silver tree", "heraldic tree", "kingdom banner", "war banner", "heraldry",
     "tree of life", "crescent moon", "elven", "renaissance faire"],
    "The banner of an old and noble kingdom: a silver tree with spreading roots, its "
    "branches in white blossom beneath a crescent moon, on a deep navy swallowtail banner "
    "edged in gold and hung from a gold rod.\n\n"
    "Great on cloaks, hoodies, tees, tote bags and sew-on patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 4, 18000)


BW = 2.4
HW, TOP, FOOT, NOTCH = 29.0, 36.0, -44.0, -32.0


def banner():
    rc = 3.0
    pts = [(-HW, TOP - rc), (-HW, FOOT), (0.0, NOTCH), (HW, FOOT), (HW, TOP - rc)]
    for a in np.radians(np.linspace(0, 90, 6)):
        pts.append((HW - rc + rc * math.cos(a), TOP - rc + rc * math.sin(a)))
    for a in np.radians(np.linspace(90, 180, 6)):
        pts.append((-HW + rc + rc * math.cos(a), TOP - rc + rc * math.sin(a)))
    # the foot's points rounded (r 3): a sharp satin corner sews 7+ mm stitches at 5x7
    return poly(pts).buffer(-3.0, join_style="round").buffer(3.0, join_style="round")


def trunk():
    """Trunk, two fork limbs and four roots as one silhouette (filled)."""
    body = tube(spline([(0, -21), (0.4, -12), (-0.4, -4), (0, 2)], samples=10), [7.5, 5.6, 5.0, 4.6])
    forks = [tube(spline([(0, 0), (-4.5, 6.5), (-9.5, 10.5)], samples=10), [4.6, 3.6, 3.0]),
             tube(spline([(0, 0), (4.5, 6.5), (9.5, 10.5)], samples=10), [4.6, 3.6, 3.0]),
             tube(spline([(0, 1), (0.3, 8), (0, 13)], samples=10), [3.8, 3.2, 2.8])]
    roots = [tube(spline([(-1.5, -19), (-7, -23.5), (-14, -24.5), (-19, -27)], samples=10), [3.6, 2.6, 1.9, 1.5]),
             tube(spline([(-0.8, -20), (-3.5, -25), (-6, -29)], samples=10), [3.2, 2.2, 1.6]),
             tube(spline([(0.8, -20), (3.5, -25), (6, -29)], samples=10), [3.2, 2.2, 1.6]),
             tube(spline([(1.5, -19), (7, -23.5), (14, -24.5), (19, -27)], samples=10), [3.6, 2.6, 1.9, 1.5])]
    return union(body, *forks, *roots)


# branches: (path from inside a fork end outward, tip), mirrored left/right + centre
_B = [   # each starts at its own spot on the fork limb, 0.6 mm inside its edge
    [(-9.0, 9.4), (-13.5, 11.6), (-18.5, 12.2), (-23.0, 15.0)],
    [(-9.6, 11.0), (-12.0, 15.5), (-16.0, 19.0), (-18.5, 24.0)],
    [(-6.2, 8.6), (-7.4, 14.0), (-9.0, 20.0), (-8.5, 26.5)],
    [(-4.2, 4.6), (-9.0, 4.8), (-14.0, 3.2), (-18.5, 5.0)],
]
BRANCHES = _B + [[(-x, y) for x, y in b] for b in _B] + [[(0, 12.2), (-0.8, 16.5), (0.4, 20.5), (0, 23.5)]]
TWIGS = [  # short side twigs, starting off a branch and clear of it
    [(-15.0, 13.6), (-17.0, 17.0), (-21.5, 19.5)],
    [(15.0, 13.6), (17.0, 17.0), (21.5, 19.5)],
]


def blossom(x, y, r=1.25):
    """Five round petals round a centre: about 5 mm across."""
    return union(circle(x, y, r * 0.9),
                 *[circle(x + r * 1.05 * math.cos(a), y + r * 1.05 * math.sin(a), r, res=32)
                   for a in np.radians(np.arange(5) * 72 + 90)])


def art():
    d = Design()
    ban = banner()
    tr = trunk()
    br = [spline(b, samples=8) for b in BRANCHES]
    tw = [spline(t, samples=8) for t in TWIGS]
    tips = [b[-1] for b in br] + [t[-1] for t in tw]
    flowers = [blossom(*t) for t in tips]
    # a few more blossoms along the larger branches
    extra = [(-13.0, 15.8), (13.0, 15.8), (-12.0, 8.6), (12.0, 8.6), (-3.6, 19.0), (3.6, 19.0)]
    flowers += [blossom(x, y, 1.1) for x, y in extra]
    moon = (circle(0, 31.6, 5.2) - circle(0, 34.4, 4.6)).buffer(-0.6).buffer(0.6)
    flower_all = union(*flowers)

    widths = [widths_along(b, 2.4, 1.1) for b in br] + [widths_along(t, 1.6, 1.1) for t in tw]
    paths = br + tw
    sat_area = union(*[tube(p, w) for p, w in zip(paths, widths)])
    # under the trunk the branches' flat starts would leave a gap: knock the trunk out
    # only past the first 1.5 mm of each branch
    from _kingdom import trim_path
    sat_tail = union(*[tube(trim_path(p, 1.5, 0.0), w) for p, w in zip(paths, widths)])

    field = tuck(ban, BW)
    d.fill(knockout(field, tr, sat_area, flower_all, moon), C_["navy"], angle=0, name="field")
    d.fill(knockout(tr, flower_all, sat_tail), C_["silver"], angle=90, spacing=0.42, name="trunk")
    for p, w in zip(paths, widths):
        d.satin(p, w, C_["silver"], taper=True, underlay="center", name="branch", trim_after=True)
    for f in flowers:
        d.fill(f, C_["white"], angle=45, name="blossom")
    d.fill(moon, C_["white"], angle=30, name="moon")
    d.outline(ban, C_["gold"], width=BW, name="border")
    # rod with finials, and two cords from its ends
    d.satin(line((-31.0, TOP + 2.6), (31.0, TOP + 2.6)), 2.6, C_["gold"], underlay="center", name="rod")
    for s in (-1, 1):
        d.fill(circle(s * 34.2, TOP + 2.6, 2.6), C_["gold"], angle=0, name="finial")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
