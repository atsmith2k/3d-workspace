"""Elven Leaf Brooch: a slender two-tone green leaf with silver filigree and a jewelled clasp.

Spec:
  object:       fantasy cloak-pin leaf brooch (original art) for cloaks, tees, totes,
                journals and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7), the leaf
                hanging tip-down under its clasp, about 0.5 as wide as tall
  fabric:       knits with cut-away; wovens, felt and wool with tear-away
  threads:      leaf (lit half), green (shadowed half), teal (clasp jewel), ice (jewel
                glint), silver (rim, midrib, veins, stem, jewel setting, swirls): 5 colours
  must have:    an 80 x 42 mm pointed leaf with a slight curve, split along the midrib into a
                light and a dark half; a 1.6 mm silver satin rim and a tapered silver
                midrib; five pairs of curved silver veins as bean runs; a 12 mm round
                teal jewel in a silver setting at the top with a glint; two filigree
                swirls curling out from the clasp; a short silver stem to the leaf
  density:      fills tucked under the rim and knocked out under midrib and jewel; max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Two-tone green leaf brooch with silver filigree and a jewelled clasp"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Elven Leaf Brooch Embroidery Design",
    "An elegant two-tone green leaf with a silver filigree rim and veins and a jewelled clasp",
    ["elven leaf", "leaf brooch", "cloak pin", "high fantasy", "fantasy jewelry", "elegant leaf",
     "forest fantasy", "cosplay", "fantasy embroidery"],
    "A cloak pin fit for a forest wanderer: a slender leaf in two shades of green, edged and "
    "veined in silver filigree, hanging from a jewelled clasp with a teal stone and two "
    "delicate silver swirls.\n\n"
    "Great on cloaks, tees, hoodies, totes, journal covers and cosplay patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 16000)


TOP, TIP = 34.0, -46.0     # leaf stem end and tip
W = 42.0                   # widest
RIM = 1.6
GX, GY, GR = 0.0, 47.5, 6.0   # jewel


def axis(t):
    """Midrib point at t (0 stem end, 1 tip): a gentle S curve."""
    y = TOP + (TIP - TOP) * t
    x = 3.2 * np.sin(np.pi * t) - 1.6 * np.sin(2 * np.pi * t)
    return np.c_[x, y]


def halfwidth(t):
    return W / 2 * np.sin(np.pi * np.clip(t, 0, 1) ** 0.85) ** 0.9 * (1 - 0.15 * t)


def halves():
    t = np.linspace(0, 1, 120)
    ax = axis(t)
    hw = halfwidth(t)
    # offsets perpendicular to the midrib
    dl = np.gradient(ax, axis=0)
    nrm = np.c_[-dl[:, 1], dl[:, 0]] / np.linalg.norm(dl, axis=1, keepdims=True)   # points to +x side... (dy<0)
    side_a = ax + nrm * hw[:, None]
    side_b = ax - nrm * hw[:, None]
    a = Polygon(np.vstack([ax, side_a[::-1]])).buffer(0)
    b = Polygon(np.vstack([ax, side_b[::-1]])).buffer(0)
    left, right = (a, b) if a.centroid.x < b.centroid.x else (b, a)
    return left, right, ax, nrm, hw


def art():
    d = Design()
    left, right, ax, nrm, hw = halves()
    leaf_shape = union(left, right).buffer(0.01).buffer(-0.01)
    # midrib: tapered satin from the stem end to near the tip
    i0, i1 = 9, 100
    rib = ax[i0:i1]
    rib_w = np.linspace(2.4, 1.0, len(rib))
    rib_band = LineString(rib).buffer(1.0, cap_style="flat")
    # veins: curved bean runs leaving the midrib toward the tip, five per side
    veins = []
    t = np.linspace(0, 1, 120)
    for k, tv in enumerate((0.16, 0.30, 0.44, 0.58, 0.72)):
        i = int(tv * 119)
        for s in (1, -1):
            p0 = ax[i] + s * nrm[i] * 1.8
            j = min(i + 14, 119)
            reach = 0.72 * hw[i]
            p2 = ax[j] + s * nrm[j] * min(reach, hw[j] - 3.0)
            p1 = ax[i] + s * nrm[i] * reach * 0.6 + (ax[j] - ax[i]) * 0.25
            veins.append(bezier(tuple(p0), tuple(p1), tuple(p1 + (p2 - p1) * 0.5), tuple(p2), 16))
    gem = circle(GX, GY, GR)
    glint = circle(GX - 1.6, GY + 1.6, 1.2, res=32)
    stem = line((ax[0][0], TOP + 0.9), (GX, GY - GR - 1.4))
    stem_band = LineString(stem).buffer(1.1, cap_style="flat")
    swirls = []
    for s in (1, -1):
        sw = M.tendril((GX + s * (GR + 1.4), GY - 0.5), (GX + s * 19, GY - 6.5), curl=4.4, turns=1.15, cw=(s < 0))
        swirls.append(sw)

    body = tuck(leaf_shape, RIM)
    body = body.buffer(-1.3).buffer(1.3)     # no fill sliver into the tip, where the rim satin fans
    d.fill(knockout(body.intersection(left.buffer(0.3)), rib_band, stem_band), C_["leaf"], angle=60, name="lit half")
    d.fill(knockout(body.intersection(right.buffer(0.3)), rib_band, stem_band, left.buffer(-0.1)), C_["green"],
           angle=120, name="shadow half")
    d.fill(knockout(tuck(gem, RIM), glint), C_["teal"], angle=45, name="jewel")
    d.fill(glint, C_["ice"], angle=0, underlay=False, name="glint")
    for v in veins:
        d.run(v, C_["silver"], length=1.6, bean=1, name="vein", trim_after=True)
    d.satin(rib, rib_w, C_["silver"], taper=True, underlay="center", name="midrib")
    d.outline(leaf_shape, C_["silver"], width=RIM, name="rim")
    d.satin(stem, 2.0, C_["silver"], underlay="center", name="stem")
    d.outline(gem, C_["silver"], width=RIM, name="setting")
    for sw in swirls:
        d.satin(sw, np.linspace(1.8, 1.3, len(sw)), C_["silver"], underlay="center", name="swirl")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
