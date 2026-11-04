"""Star of David Olive Wreath: an interlaced blue and gold Star of David framed by two
olive branches with small dark olives.

Spec:
  object:       elegant Hanukkah motif for napkins, challah covers, pillows, table runners
                and tea towels
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7), round
  fabric:       wovens and linens with tear-away (cut-away on knits)
  threads:      olive (stems, dark leaves), leaf (light leaves), charcoal (olives), blue
                (down triangle), gold (up triangle): 5 colours
  must have:    a Star of David 50 mm tip to tip made of two triangles drawn as 3.6 mm
                filled bands, interlaced: the bands alternate over and under at the six
                crossings; two olive branches rising from the bottom around a 37 mm radius,
                open at the top, each on a 1.4 mm satin stem with 11 slim leaves
                (12 x 4.4 mm) in two greens and 5 oval olives (2.0 x 3.0 mm)
  density:      the under band is knocked out at each crossing (0.4 mm overlap); leaves
                overlap only the stem; olives knock out the leaves; max 3.5
"""
import math

import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Interlaced blue and gold Star of David in an olive branch wreath"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Star of David Olive Wreath Hanukkah Embroidery Design",
    "An interlaced blue and gold Star of David framed by an olive branch wreath",
    ["star of david", "olive branch", "olive wreath", "magen david", "challah cover",
     "hanukkah napkin", "jewish embroidery", "judaica", "festival of lights", "blue and gold"],
    "A Star of David woven from a blue and a gold triangle, the bands passing over and under "
    "each other, framed by two olive branches with slim leaves in two greens and small dark "
    "olives.\n\n"
    "An elegant piece for napkins, challah covers, pillows, table runners and tea towels, for "
    "Hanukkah and all year round.",
    mockups=("tote", "tshirt"),
)

R_STAR = 25.0          # triangle circumradius
BAND = 3.6
R_WREATH = 37.0


def checks(p):
    return standard_checks(p, 5, 14000)


def _band_triangle(r, w, rot):
    return regular_polygon(3, r, 0, 0, rot=rot).difference(regular_polygon(3, r - 2 * w, 0, 0, rot=rot))


def star_bands():
    """The up (gold) and down (blue) bands and the six crossings, alternating which is on top."""
    up = _band_triangle(R_STAR, BAND, 90)
    down = _band_triangle(R_STAR, BAND, -90)
    crossings = polygons_of(up.intersection(down))
    up_top, down_top = [], []
    for c in crossings:
        a = math.degrees(math.atan2(c.centroid.y, c.centroid.x)) % 360
        k = int(round(a / 60.0)) % 6
        (up_top if k % 2 == 0 else down_top).append(c)
    return up, down, up_top, down_top


def _place(g, x, y, deg):
    return move(rotate(g, deg, origin=(0, 0)), x, y)


def branch(side):
    """One olive branch from the bottom up one side; side -1 left, +1 right."""
    if side > 0:
        ts = np.radians(np.linspace(278.0, 412.0, 60))
    else:
        ts = np.radians(np.linspace(262.0, 128.0, 60))
    stem = np.c_[R_WREATH * np.cos(ts), R_WREATH * np.sin(ts)]
    leaves, olives = [], []
    n = 11
    for i in range(n):
        f = 0.06 + 0.9 * i / (n - 1)
        t = ts[0] + (ts[-1] - ts[0]) * f
        x, y = R_WREATH * math.cos(t), R_WREATH * math.sin(t)
        tangent = math.degrees(t) + (90 if side > 0 else -90)        # direction of growth
        out = 1 if i % 2 == 0 else -1                                 # alternate outside / inside
        lean = 38 * out * (-side)
        L = 12.0 - 2.5 * (i / (n - 1)) ** 2
        g = M.leaf(L, 4.4)
        g = rotate(g, -90, origin=(0, 0))                             # leaf now points +x
        leaves.append((_place(g, x, y, tangent + lean), i % 2))
    for j in range(5):
        f = 0.13 + 0.18 * j
        t = ts[0] + (ts[-1] - ts[0]) * f
        out = 1 if j % 2 else -1
        rr = R_WREATH + out * 3.4
        x, y = rr * math.cos(t), rr * math.sin(t)
        olives.append(rotate(ellipse(x, y, 1.5, 2.1), math.degrees(t), origin=(x, y)))
    return stem, leaves, olives


def art():
    d = Design()
    up, down, up_top, down_top = star_bands()
    stems, dark, light, olives = [], [], [], []
    for side in (-1, 1):
        s, lv, ol = branch(side)
        stems.append(s)
        dark += [g for g, k in lv if k == 0]
        light += [g for g, k in lv if k == 1]
        olives += ol
    all_olives = union(*olives)
    light_all = union(*light)

    # olive: stems, then the dark leaves
    for s in stems:
        d.satin([tuple(p) for p in s], 1.4, C_["olive"], name="stem")
    for g in dark:
        d.fill(knockout(g, light_all, all_olives), C_["olive"], angle=None, name="dark leaf")
    for g in light:
        d.fill(knockout(g, all_olives), C_["leaf"], angle=None, name="light leaf")
    for g in olives:
        d.fill(g, C_["charcoal"], angle=60, underlay=False, name="olive")
    # the star: blue down-triangle under the gold where gold is on top, then gold
    d.fill(knockout(down, *up_top), C_["blue"], angle=-30, name="down triangle")
    d.fill(knockout(up, *down_top), C_["gold"], angle=30, name="up triangle")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
