"""Wanderer's Pack: a leather rucksack with a rolled bedroll strapped on top, a walking
stick with a lantern hanging from its crook, in two-colour vintage line art.

Spec:
  object:       a traveller's pack (cozy fantasy, "off on an adventure") drawn like a
                vintage brownwork/redwork sampler, for tea towels, quilt blocks, tees,
                totes and pillowcases
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (linen, flour-sack towels, cotton) with tear-away; knits cut-away
  threads:      dark brown (everything drawn), moss green (leaf sprig, grass): 2 colours
  must have:    a 44 x 54 mm pack with a rounded flap, two buckled straps, a front
                pocket with its own flap and button, dashed saddle stitching inside the
                flap and pocket edges; a tin mug hung off the side; a 56 x 13 mm bedroll with a rolled spiral end
                and two ties; a walking stick 85 mm long with a crook, a lantern hung
                from it; a grass line with a leaf sprig at the foot
  technique:    no fills: bean-stitch (triple run) outlines, single-run saddle stitching;
                every back line stops 0.9 mm short of the line in front of it (no
                crossings, no doubled holes)
  density:      runs only, max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hollow import C_, SIZES, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Rucksack, bedroll and walking stick with a lantern, in vintage line art"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Wanderer's Pack Line Art Embroidery Design",
    "A leather rucksack with a bedroll, a walking stick and a hanging lantern, drawn in two-colour vintage line art",
    ["adventure", "backpack", "rucksack", "walking stick", "lantern", "hiking", "wanderer",
     "line art embroidery", "redwork", "brownwork", "quilt block", "tea towel", "journey"],
    "Packed for the long road: a buckled leather rucksack with a bedroll strapped on top, "
    "a walking stick leaning beside it with a lantern swinging from the crook, all drawn in "
    "bold brown bean-stitch lines like a vintage sampler, with a little green sprig at its feet.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Light and quick to sew: great on "
    "flour-sack tea towels, quilt blocks, pillowcases, tees and totes.",
    mockups=("tshirt", "tote"),
)

INK = C_["bark"]
GAP = 0.9


def checks(p):
    return standard_checks(p, 2, 9000)


def _lines(g, min_len=1.2):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [list(g.coords)] if g.length > min_len else []
    out = []
    for s in getattr(g, "geoms", []):
        out += _lines(s, min_len)
    return out


class Dash(LineString):
    """A saddle-stitch line: sewn as a single run (reads dashed), not a bean run."""
    __slots__ = ()


def _ring_lines(shape):
    return [LineString(r) for r in outline_paths(shape)]


def drawing():
    """[(shape, inner lines)] front to back. Each shape's outline and inner lines are
    clipped where a shape in front of it covers them."""
    L = []
    # lantern on the crook
    lx, ly = 31.0, 15.0
    lantern = union(rounded_rect(9.5, 12.5, 1.4, lx, ly), poly([(lx - 6, ly + 6.2), (lx, ly + 10.5), (lx + 6, ly + 6.2)]),
                    rect(11, 2.2, lx, ly - 7.0))
    bars = [LineString([(lx - 1.6, ly - 5.4), (lx - 1.6, ly + 5.6)]), LineString([(lx + 1.6, ly - 5.4), (lx + 1.6, ly + 5.6)])]
    flame = smooth([(lx, ly - 2.6), (lx + 1.6, ly + 0.2), (lx, ly + 3.4), (lx - 1.6, ly + 0.2)], samples=5)
    L.append((lantern, bars + _ring_lines(flame)))
    bail = LineString(arc(lx, ly + 11.5, 2.4, 0, 180))
    L.append((Point(lx, ly + 13.5).buffer(0.01), [bail, LineString([(lx, ly + 13.9), (lx, ly + 18.2)])]))
    # front pocket, its flap and button
    pflap = smooth([(-19, -14), (-19, -20.5), (-6, -24.5), (7, -20.5), (7, -14)], samples=6)
    button = circle(-6, -21.2, 1.6)
    L.append((button, []))
    L.append((pflap, [Dash(outline_paths(shrink(pflap, 1.6))[0])]))
    pocket = rounded_rect(28, 20, 3.0, -6, -25)
    L.append((pocket, [Dash(outline_paths(shrink(pocket, 1.6))[0])]))
    # straps and buckles on the main flap
    straps = []
    for x in (-16.0, 4.0):
        buckle = rect(6.4, 5.0, x, -5.5)
        L.append((buckle, [LineString([(x - 1.6, -5.5), (x + 1.6, -5.5)])]))
        straps.append(rect(3.6, 24, x, 2.0))
    for s in straps:
        L.append((s, [LineString([(s.centroid.x, -10.5), (s.centroid.x, -14.0)])]))
    flap = smooth([(-28, 14), (-28.5, 2), (-24, -5), (-6, -8.5), (12, -5), (16.5, 2), (16, 14)], samples=6)
    L.append((flap, [Dash(outline_paths(shrink(flap, 1.8))[0])]))
    # bedroll on top, rolled end showing a spiral
    roll = union(rect(52, 13, -6, 20.5), ellipse(-32, 20.5, 2.6, 6.5), ellipse(20, 20.5, 2.6, 6.5))
    ties = [LineString([(x, 14.0), (x + 1.2, 27.0)]) for x in (-21.0, 7.5)]
    sp = M.spiral(0.8, 5.0, turns=1.6, start=1.0)
    spiral = LineString(np.asarray(sp) * [0.52, 1.0] + [20, 20.5])
    L.append((roll, ties + [spiral]))
    # a tin mug hanging off the right side by its handle
    mug = rounded_rect(8.5, 9.5, 1.2, 19.0, -27.0)
    L.append((mug, [LineString([(15.6, -23.4), (22.4, -23.4)])]))
    L.append((ring(19.0, -20.6, 3.0, 1.2).difference(mug), []))
    # the pack body and a shoulder strap loop on the left
    body = rounded_rect(44, 52, 6.0, -6, -12)
    L.append((body, []))
    loop = LineString(spline([(-28, 8), (-35, -2), (-36, -18), (-28, -30)], samples=10))
    L.append((loop.buffer(1.6, cap_style="flat"), []))
    # walking stick with a crook (behind the pack)
    sp = np.asarray(spline([(23, -43), (26, -10), (29, 18), (31.5, 33), (35, 38), (39, 36), (39.5, 31)], samples=10))
    stick = strip(sp, np.r_[np.full(len(sp) - 12, 3.0), np.linspace(3.0, 2.4, 12)])
    knots = [LineString([(25.3, -20), (27.4, -19.2)]), LineString([(28.0, 4.0), (30.0, 4.6)])]
    L.append((stick, knots))
    return L


def art():
    d = Design()
    L = drawing()
    drawn = []
    front = None
    for shape, inner in L:
        lines = _ring_lines(shape) + inner
        if shape.area < 0.1:                          # just lines (the lantern bail)
            lines = inner
        for ln in lines:
            g = ln if front is None else ln.difference(grow(front, GAP))
            drawn += [(p, isinstance(ln, Dash)) for p in _lines(g)]
        front = shape if front is None else union(front, shape)
    for path, dash in drawn:
        if dash:
            d.run(path, INK, length=1.8, name="saddle stitching")
        else:
            d.run(path, INK, bean=1, name="line")
    # ground and a sprig in moss green
    ground = LineString(spline([(-38, -41), (-10, -42.2), (20, -41.6), (42, -40.4)], samples=10))
    gfront = grow(front, GAP)
    for g in _lines(ground.difference(gfront)):
        d.run(g, C_["moss"], bean=1, name="ground")
    stem = np.asarray(spline([(-34, -40.6), (-37, -33), (-36, -25)], samples=8))
    d.run(stem, C_["moss"], bean=1, name="sprig stem")
    for (x, y, deg, ln) in ((-36.6, -31.5, 150, 8.0), (-36.4, -28.0, 35, 7.5), (-36.2, -25.4, 95, 6.5)):
        leaf = move(rotate(M.leaf(ln, ln * 0.42, bend=0.1), deg), x, y)
        for r in outline_paths(leaf):
            d.run(r, C_["moss"], bean=1, name="sprig leaf")
    for x in (-24, 30, 38):
        for blade in ((x, -41.2, x - 1.6, -36.5), (x + 1.2, -41.2, x + 2.6, -37.0)):
            g = LineString([blade[:2], blade[2:]]).difference(gfront)
            for s in _lines(g):
                d.run(s, C_["moss"], bean=1, name="grass")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
