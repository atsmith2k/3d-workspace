"""Pinecones: two pinecones hanging from a pine bough tied with a red bow.

Spec:
  object:       rustic pine bough for napkins, tea towels, pillows and sweatshirts
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (linens) with tear-away; knits with cut-away
  threads:      cocoa (bough, cones), tan (scale scallops), green (needles), red (bow):
                4 colours
  must have:    a 2 mm satin bough 84 mm long; pine needles sewn as one forward zigzag
                bean run per side of the bough (never back over their own holes), kept
                clear of the bow; two 20 x 34 mm cocoa cones hanging below with tan
                bean-stitch scale scallops 4.4 mm apart; a 22 mm red bow in the middle
  density:      runs lie on the fills; the bow sits on the bough only; max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M
from shapely.geometry import LineString, Point

from _hearth import C_, SIZES, fit, hoop_for, product, sew_bow, standard_checks

DESCRIPTION = "Two pinecones hanging from a pine bough tied with a red bow"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Pinecones and Pine Bough Embroidery Design",
    "Two pinecones hanging from a pine bough with a red bow",
    ["pinecone", "pine bough", "rustic christmas", "woodland winter", "christmas napkin",
     "farmhouse christmas"],
    "A rustic pine bough with two hanging pinecones and a red ribbon bow.\n\nA winter design "
    "for napkins, tea towels, pillows and sweatshirts.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 4, 11000)


def _cone(x, y):
    body = smooth([(0, 0), (9, -4), (10, -14), (7, -25), (0, -34), (-7, -25), (-10, -14), (-9, -4)], 10)
    return move(body.buffer(0), x, y)


def _scallops(cone, x, top):
    """Rows of downward scallops across a cone, alternate rows offset half a scale."""
    rows = []
    inner = cone.buffer(-1.6)
    for r, y in enumerate(np.arange(top - 6, top - 32, -4.4)):
        xs = np.linspace(x - 11, x + 11, 89)
        ph = 2.8 * (r % 2)
        ys = y - 1.7 * np.abs(np.sin(np.pi * (xs - x + ph) / 5.6))
        seg = LineString(np.c_[xs, ys]).intersection(inner)
        if seg.is_empty:
            continue
        geoms = getattr(seg, "geoms", [seg])
        rows += [np.array(g.coords) for g in geoms if g.length > 3]
    return rows


def _needles(path, keep_out, side):
    """A forward zigzag along `path`: root, needle tip, next root... on one side."""
    line = LineString(path)
    out = []
    for s in np.arange(1.0, line.length - 1.0, 2.6):
        p = np.array(line.interpolate(s).coords[0])
        q = np.array(line.interpolate(s + 0.5).coords[0])
        t = (q - p) / np.linalg.norm(q - p)
        n = np.array([-t[1], t[0]]) * side
        tip = p + n * 6.5 - t * 3.0
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
    bough = spline([(-42, 26), (-20, 30), (0, 29), (22, 26), (42, 28)], samples=12)
    bow = [move(g, 2, 28.5) for g in M.bow(22)]
    cones = [(_cone(-17, 27), -17), (_cone(21, 25.5), 21)]
    keep = union(*bow).buffer(1.2)
    d.satin(bough, 2.0, C_["cocoa"], name="bough", trim_after=True)
    for c, x in cones:
        d.fill(c, C_["cocoa"], angle=90, name="pinecone")
    for c, x in cones:
        for row in _scallops(c, x, c.bounds[3]):
            d.run(row, C_["tan"], bean=1, name="scales", trim_after=True)
    for side in (1, -1):
        for z in _needles(bough, keep, side):
            d.run(z, C_["green"], bean=1, name="needles", trim_after=True)
    sew_bow(d, bow, C_["red"], C_["red"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
