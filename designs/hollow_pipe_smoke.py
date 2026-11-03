"""Pipe & Smoke Rings: a long-stemmed clay pipe resting on a sprig of leaves, a curl of
smoke rising from the bowl and three smoke rings drifting up and away.

Spec:
  object:       a long churchwarden-style pipe (generic, cozy-fantasy) for tees, totes,
                hoodies, tea towels, cushions and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      leaf green (leaves), moss (leaf veins), light brown (stem, bowl),
                khaki (bowl highlight), dark brown (bowl rim, stem band, mouthpiece,
                bowl shadow), orange (embers), gray (smoke): 7 colours
  must have:    a pipe ~88 mm from mouthpiece to bowl, a 3.4-5.4 mm stem curving down to
                a 24 x 30 mm bowl with a khaki highlight and dark shadow side, a dark
                2 mm rim ellipse with glowing embers; a tapered satin smoke curl rising
                from the bowl; three satin smoke rings 2.4 mm wide, 13/18/24 mm across,
                drifting up to the left; a fan of three leaves under the stem (the pipe rests on them)
  density:      stem and bowl knocked out under the band, rim and highlight; max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M
from shapely.geometry import LineString

from _hollow import C_, SIZES, backfill, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Long clay pipe with a curl of smoke and drifting smoke rings"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Pipe and Smoke Rings Embroidery Design",
    "A long-stemmed wooden pipe on a sprig of leaves, blowing a curl of smoke and three drifting smoke rings",
    ["smoke rings", "pipe", "churchwarden pipe", "cozy fantasy", "fantasy pipe", "wizard pipe",
     "pipe smoker gift", "fireside", "book lover"],
    "An evening on the bench outside a round front door: a long-stemmed wooden pipe resting on "
    "a sprig of leaves, embers glowing in the bowl, a lazy curl of smoke and three smoke rings "
    "drifting off into the dusk.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tees, hoodies, totes, "
    "cushions and patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 14000)


BOWL_C = (30.0, -20.0)
K = 1.35          # bowl scale


def stem_path():
    return np.asarray(spline([(-50, -12), (-28, -17), (-5, -26), (12, -28), (22, -25)], samples=14))


def bowl():
    cx, cy = BOWL_C
    pts = [(-8.5, 11), (-8.8, 4), (-8.0, -3), (-5.5, -8.5), (-1.5, -11), (2.0, -11), (5.6, -8.4),
           (8.0, -3), (8.8, 4), (8.5, 11)]
    return smooth([(cx + x * K, cy + y * K) for x, y in pts], samples=10)


def art():
    d = Design()
    cx, cy = BOWL_C
    path = stem_path()
    t = np.linspace(0, 1, len(path))
    stem = strip(path, 3.4 + 2.0 * t)                            # thickens toward the bowl
    mouth = strip(path[:9], 3.8)
    cup = bowl()
    b = lambda pts: [(cx + x * K, cy + y * K) for x, y in pts]
    rim = ellipse(cx, cy + 11 * K, 8.6 * K, 2.6 * K)
    rim_band = rim.exterior.buffer(1.2)
    embers = ellipse(cx, cy + 11 * K, 6.0 * K, 1.4 * K)
    high = smooth(b([(-6.6, 7.5), (-7.2, 1), (-6.0, -5), (-3.2, -8.4),
                     (-3.6, -4), (-4.3, 2), (-4.0, 7.5)]), samples=8)
    shade = smooth(b([(4.6, 7.5), (5.2, 1), (4.5, -5), (2.4, -9.0),
                      (5.8, -7.6), (8.0, -2.5), (8.6, 4), (8.2, 7.5)]), samples=8)
    jp = path[-5]
    band = rotate(rect(2.6, 8.0, *jp), 15, origin=tuple(jp))

    # a sprig of three leaves fanning out from under the stem
    leaves = []
    for deg, ln, wd, bend in ((196, 30, 11, 0.12), (250, 24, 10, -0.1), (318, 26, 10, 0.1)):
        g = move(rotate(M.leaf(ln, wd, bend=bend), deg), -2, -31)
        v = move(rotate(np.asarray(M.leaf_vein(ln, bend=bend)), deg), -2, -31)
        leaves.append((g, v, deg))
    pipe_all = union(stem, cup, band, mouth)

    for i, (g, v, deg) in enumerate(leaves):
        above = [pipe_all] + [h for h, _, _ in leaves[:i]]
        d.fill(knockout(g, *above), C_["leaf"], angle=deg + 60, name="leaf")
    for i, (g, v, deg) in enumerate(leaves):
        vis = knockout(g, pipe_all, *[h for h, _, _ in leaves[:i]])
        cut = LineString(v).intersection(shrink(vis, 1.6))
        for s_ in getattr(cut, "geoms", [cut]):
            if s_.geom_type == "LineString" and s_.length > 3:
                d.run(list(s_.coords), C_["moss"], bean=1, name="leaf vein")
    d.fill(knockout(stem, cup, band, mouth), C_["wood"], angle=0, name="stem")
    d.fill(knockout(cup, high, shade, rim_band, embers), C_["wood"], angle=80, name="bowl")
    d.fill(knockout(high, rim_band), C_["khaki"], angle=80, name="bowl highlight")
    d.fill(embers, C_["flame"], angle=0, name="embers")
    d.fill(knockout(shade, rim_band), C_["bark"], angle=100, name="bowl shadow")
    d.fill(band, C_["bark"], angle=105, name="stem band")
    d.fill(mouth, C_["bark"], angle=-10, name="mouthpiece")
    d.outline(rim, C_["bark"], width=2.0, name="bowl rim")

    # smoke: a tapered curl, then three rings drifting up-left
    top = cy + 11 * K + 4.4
    curl = np.asarray(spline([(cx - 1, top), (cx + 5, top + 7), (cx - 1, top + 15), (cx - 8, top + 20),
                              (cx - 6, top + 27)], samples=10))
    w = np.interp(np.linspace(0, 1, len(curl)), [0, 0.5, 1], [3.6, 3.2, 0.8])
    d.satin(curl, w, C_["gray"], name="smoke curl", taper=True)
    for (x, y, r, deg) in ((10, 24, 6.5, 15), (-10, 33, 9.0, 10), (-35, 40, 12.0, 5)):
        d.outline(rotate(ellipse(x, y, r, r * 0.72), deg, origin=(x, y)), C_["gray"], width=2.4,
                  name="smoke ring")
    backfill(d, C_["bark"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
