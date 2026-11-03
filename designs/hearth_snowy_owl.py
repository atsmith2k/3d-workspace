"""Snowy Owl: a white snowy owl with gold eyes perched on a pine branch.

Spec:
  object:       snowy owl for sweatshirts, pillows, totes and woodland winter decor
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      cocoa (branch), green (needles), white (owl), silver (1.2 mm outline and
                wing lines), gold (eyes), black (pupils, flecks), charcoal (beak, talons):
                7 colours
  must have:    a 44 x 67 mm round-headed owl; a 1.2 mm satin wing line down each side; 10.4 mm
                gold eyes with black pupils; a charcoal beak; fourteen 1.1 mm black V
                flecks; a 2.4 mm satin branch either side of the owl with zigzag bean-run
                needles kept clear of the owl; charcoal talons on the branch
  density:      the branch stops at the owl; wing lines lie on the white (2.7); max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "White snowy owl with gold eyes perched on a pine branch"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Snowy Owl Embroidery Design",
    "A white snowy owl with gold eyes perched on a pine branch",
    ["snowy owl", "owl", "winter bird", "woodland winter", "winter animal", "cozy winter"],
    "A snowy owl with golden eyes and dark speckled feathers, perched on a pine branch. A "
    "winter design that sews all season.\n\nGreat on sweatshirts, pillows, totes and woodland "
    "decor.",
    mockups=("tshirt", "tote"),
    base=["winter embroidery design", "machine embroidery", "winter", "holiday"],
)

BORDER = 1.2
FLECKS = [(-16, -4), (-3, -6), (5, -3), (6, -9), (-16, -14), (-5, -15), (3, -12), (16, -18),
          (-8, -22), (1, -21), (8, -25), (-15, 4), (15, 2), (0, 1)]


def checks(p):
    return standard_checks(p, 7, 13000)


def _v(x, y):
    return LineString([(x - 1.8, y + 1.0), (x, y - 0.6), (x + 1.8, y + 1.0)]).buffer(0.55)


def _needles(path, keep_out):
    line = LineString(path)
    for side in (1, -1):
        out = []
        for s in np.arange(1.0, line.length - 1.0, 2.6):
            p = np.array(line.interpolate(s).coords[0])
            q = np.array(line.interpolate(min(s + 0.5, line.length)).coords[0])
            t = (q - p) / max(np.linalg.norm(q - p), 1e-6)
            n = np.array([-t[1], t[0]]) * side
            tip = p + n * 6.0 - t * 2.6
            if keep_out.intersects(LineString([p, tip])):
                if len(out) > 1:
                    yield np.array(out)
                out = []
                continue
            out += [p, tip]
        if len(out) > 1:
            yield np.array(out)


def art():
    d = Design()
    body = smooth([(0, 34), (12, 32), (19, 24), (21, 10), (22, -6), (18, -22), (10, -31), (0, -33), (-10, -31),
                   (-18, -22), (-22, -6), (-21, 10), (-19, 24), (-12, 32)], 10).buffer(0)
    inner = body.buffer(-2.5)
    wings = [spline([(-18.5, 9), (-13, 4), (-10.5, -8), (-12.5, -23)], samples=10),
             spline([(18.5, 9), (13, 4), (10.5, -8), (12.5, -23)], samples=10)]
    eyes = [circle(-7.5, 17, 5.2), circle(7.5, 17, 5.2)]
    pupils = [circle(-7.5, 17, 2.5), circle(7.5, 17, 2.5)]
    beak = poly([(-2.6, 12.0), (2.6, 12.0), (0, 7.0)]).buffer(0.5)
    flecks = [_v(x, y) for x, y in FLECKS]
    talons = [ellipse(x, -33, 1.6, 2.4) for x in (-9, -5.5, 5.5, 9)]
    branch = np.array([(-46, -34), (-20, -33.5), (0, -33), (22, -32.5), (46, -31.5)])
    keep = body.buffer(1.2)
    pieces = LineString(branch).difference(keep)
    pieces = [np.array(g.coords) for g in getattr(pieces, "geoms", [pieces]) if g.length > 3]
    for b in pieces:
        d.satin(b, 2.4, C_["cocoa"], name="branch", trim_after=True)
    for b in pieces:
        for z in _needles(b, keep):
            d.run(z, C_["green"], bean=1, name="needles", trim_after=True)
    d.fill(knockout(tuck(body, BORDER), *eyes, beak, *flecks, *talons), C_["white"], angle=80, name="owl")
    d.outline(body, C_["silver"], width=BORDER, name="outline")
    for w in wings:
        d.satin(w, 1.2, C_["silver"], name="wing line", trim_after=True)
    for g in eyes:
        d.fill(knockout(g, *pupils), C_["gold"], angle=45, name="eye")
    for g in pupils + flecks:
        d.fill(g, C_["black"], angle=45, underlay=False, name="pupil / fleck")
    d.fill(beak, C_["charcoal"], angle=90, underlay=False, name="beak")
    for g in talons:
        d.fill(g, C_["charcoal"], angle=90, underlay=False, name="talon")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
