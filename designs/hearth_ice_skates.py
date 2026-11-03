"""Ice Skates: a pair of white figure skates hanging from a red bow by their laces.

Spec:
  object:       vintage hanging ice skates for sweatshirts, pillows, totes and stockings
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      white (boots), silver (1.2 mm boot outline, blades, stanchions), red
                (cross laces, hanging laces, pompoms, bow): 3 colours
  must have:    two 30 mm white boots tilted +-12 deg, each with a silver satin edge, a
                red criss-cross lace run up the front, a 5 mm red pompom, two stanchions
                and a 1.4 mm satin blade curling up at the toe; laces rising from both
                cuffs to a 30 mm red bow
  density:      laces and pompoms lie on the boots (2 layers); max 3.5
"""
import numpy as np
from shapely.affinity import rotate as _rot, scale as _scl, translate as _tr
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hearth import C_, SIZES, fit, hoop_for, product, sew_bow, standard_checks

DESCRIPTION = "Pair of white figure skates hanging from a red bow"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Hanging Ice Skates Embroidery Design",
    "A pair of vintage white ice skates hanging from a red bow",
    ["ice skates", "figure skates", "vintage ice skates", "skating", "winter sports", "cozy winter"],
    "A pair of vintage white figure skates with red laces and pompoms and silver blades, "
    "hanging from a red ribbon bow.\n\nA winter design that sews from December to March: "
    "sweatshirts, pillows, totes and stockings.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.2


def checks(p):
    return standard_checks(p, 3, 11000)


def _skate():
    """One skate pointing right, cuff top at the origin: (boot, lace path, pompom,
    stanchions, blade path, lace top point)."""
    boot = smooth([(-9, 0), (4, 0), (4.5, -13), (12, -18), (17, -21), (17.5, -26), (-10, -26), (-11, -13)], 8)
    boot = boot.buffer(0)
    lace = np.array([(1.5, -2), (-2.5, -5), (2, -8), (-2, -11), (3, -14), (-1, -17), (5, -19)])
    pom = circle(5.5, -1.5, 2.7)
    stanchions = [rect(2.6, 6.5, -6, -29), rect(2.6, 6.5, 12, -29)]
    blade = np.array([(-11, -32), (16, -32), (19.5, -30.5), (20.5, -28)])
    return boot, lace, pom, stanchions, blade, (-2.5, 0)


def _place(obj, deg, dx, dy, flip):
    def t(g):
        if isinstance(g, np.ndarray):
            g = LineString(g)
            out = _tr(_rot(_scl(g, -1 if flip else 1, 1, origin=(0, 0)), deg, origin=(0, 0)), dx, dy)
            return np.array(out.coords)
        return _tr(_rot(_scl(g, -1 if flip else 1, 1, origin=(0, 0)), deg, origin=(0, 0)), dx, dy)
    return t(obj)


def art():
    d = Design()
    skates = []
    for flip, deg, dx in ((True, -12, -14), (False, 12, 14)):
        boot, lace, pom, st, blade, top = _skate()
        f = lambda g: _place(g, deg, dx, 6, flip)
        top_pt = f(np.array([top, top]))[0]
        skates.append(dict(boot=f(boot), lace=f(lace), pom=f(pom), st=[f(g) for g in st],
                           blade=f(blade), top=top_pt))
    bow = [move(g, 0, 34) for g in M.bow(30)]
    hang = [np.array([s["top"], (s["top"][0] * 0.35, 28.0), (0, 33.0)]) for s in skates]
    for s in skates:
        d.fill(tuck(s["boot"], BORDER), C_["white"], angle=80 if s["top"][0] < 0 else 100, name="boot")
    for s in skates:
        d.outline(knockout(s["boot"], s["pom"].buffer(BORDER / 2)), C_["silver"], width=BORDER, name="boot edge")
        for g in s["st"]:
            d.fill(g, C_["silver"], angle=90, name="stanchion")
        d.satin(s["blade"], 1.4, C_["silver"], name="blade", trim_after=True)
    for s in skates:
        d.run(s["lace"], C_["red"], bean=1, name="laces", trim_after=True)
        d.fill(s["pom"], C_["red"], angle=45, name="pompom")
    for h in hang:
        d.run(h, C_["red"], bean=1, name="hanging lace", trim_after=True)
    sew_bow(d, bow, C_["red"], C_["red"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
