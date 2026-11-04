"""Chocolate Gelt: a blue mesh pouch tied with a gold cord, spilling gold foil coins.

Spec:
  object:       Hanukkah gelt for kids' sweatshirts, gift bags, stockings, tea towels
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      blue (pouch), sky (mesh lattice), navy (pouch border), yellow (coin
                faces), gold (cord, bow, coin rims, stamps): 5 colours
  must have:    a 46 x 58 mm mesh pouch lying tipped over, mouth down-right, gathered at the neck with a ruffled
                top, a 3 mm gold cord and 18 mm bow round the neck; a diamond mesh of sky
                running stitch at 5 mm over the blue; a 1.4 mm navy border; seven foil
                coins 15-22 mm across spilling out in front, each with a 1.4 mm gold rim;
                the three biggest stamped, two with a Star of David (two triangle runs),
                one with an inner ring
  density:      front coins knock out what is behind them (borders sit side by side);
                the cord and bow knock out the pouch; max 3.5
"""
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import substring

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Blue mesh pouch tied with a gold cord spilling gold foil chocolate gelt coins"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Chocolate Gelt Hanukkah Embroidery Design",
    "A blue mesh pouch of chocolate gelt spilling shiny gold coins",
    ["gelt", "chocolate gelt", "hanukkah gelt", "kids hanukkah", "hanukkah gift bag",
     "star of david", "festival of lights"],
    "A little blue mesh pouch tied with a gold cord and bow, tipped over and spilling shiny "
    "gold foil chocolate coins, some stamped with a Star of David.\n\nSweet on kids' "
    "sweatshirts, gift bags, stockings and tea towels.",
    mockups=("tshirt", "tote"),
)

B = 1.4          # border / rim width
TILT = -112.0


def checks(p):
    return standard_checks(p, 6, 15000)


def _pouch():
    body = smooth([(-6, 20), (-14, 15), (-21, 4), (-23, -9), (-17, -20), (0, -24), (17, -20),
                   (23, -9), (21, 4), (14, 15), (6, 20)], 10).buffer(0)
    neck = rect(12, 6, 0, 21)
    frill = smooth([(-5, 22), (-12, 27), (-13, 31), (-8, 33.5), (-4, 31.5), (0, 34.5),
                    (4, 31.5), (8, 33.5), (13, 31), (12, 27), (5, 22)], 10).buffer(0)
    bag = union(body, neck, frill).buffer(0.8).buffer(-0.8)
    band = rect(18, 3.2, 0, 21.6)
    bowp = [move(g, 0, 21.6) for g in M.bow(13)]
    T = lambda g: move(rotate(g, TILT, origin=(0, 0)), -24, 10)
    return T(bag), T(body), T(band), [T(g) for g in bowp]


def _ring_walk(ring, a, b):
    """The shorter way round closed `ring` from point a to point b."""
    L = ring.length
    da, db = ring.project(a), ring.project(b)
    fwd = (db - da) % L
    if fwd <= L / 2:
        if da <= db:
            return list(substring(ring, da, db).coords)
        return list(substring(ring, da, L).coords) + list(substring(ring, 0, db).coords)
    if db <= da:
        return list(substring(ring, da, db).coords)
    return list(substring(ring, da, 0).coords) + list(substring(ring, L, db).coords)


def _lattice(shape, gap, inset):
    """One continuous run path: lines at +-45 deg `gap` mm apart across `shape`, joined
    by walking `inset` mm inside its edge (under the border sewn later)."""
    inner = max(polygons_of(shrink(shape, inset)), key=lambda g: g.area)
    ring = LineString(inner.exterior.coords)
    x0, y0, x1, y1 = inner.bounds
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    R = np.hypot(x1 - x0, y1 - y0)
    path = []
    for deg in (45, -45):
        u = np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])
        n = np.array([-u[1], u[0]])
        flip = False
        for k in np.arange(-R / 2, R / 2, gap):
            o = c + n * k
            seg = LineString([o - u * R, o + u * R]).intersection(inner)
            pieces = [g for g in getattr(seg, "geoms", [seg]) if g.length > 1.5]
            for pc in pieces:
                pts = list(pc.coords)
                if flip:
                    pts = pts[::-1]
                if path:
                    path += _ring_walk(ring, Point(path[-1]), Point(pts[0]))[1:-1]
                path += pts
            if pieces:
                flip = not flip
    return np.array(path)


def _coins():
    """(shape, stamp) back to front; stamp is None, 'star' or 'ring'."""
    return [
        (circle(24, -10, 8.5), None),
        (circle(39, -20, 7.5), None),
        (circle(-14, -30, 8.5), None),
        (circle(10, -21, 10.0), "star"),
        (circle(29, -30, 10.0), "ring"),
        (circle(5, -41, 10.5), "star"),
        (circle(-14, -48, 7.5), None),
    ]


def _star_paths(x, y, r):
    tri = lambda a0: [(x + r * np.cos(np.radians(a0 + 120 * i)), y + r * np.sin(np.radians(a0 + 120 * i)))
                      for i in range(4)]
    return tri(90), tri(-90)


def art():
    d = Design()
    bag, body, band, bowp = _pouch()
    coins = _coins()
    tie = union(band, *bowp)
    shapes = [c for c, _ in coins]
    # visible part of each piece: knocked out under every coin in front of it, with a
    # rim's width spare so the rims sit side by side
    vis = []
    for i, s in enumerate(shapes):
        front = [grow(t, B) for t in shapes[i + 1:]]
        vis.append(knockout(s, *front, min_width=2.0) if front else s)
    bag_vis = knockout(bag, *[grow(t, B) for t in shapes], min_width=2.0)
    body_vis = body.intersection(bag_vis)
    d.fill(knockout(tuck(bag_vis, B), grow(tie, 0.25)), C_["blue"], angle=TILT + 90, name="pouch")
    d.run(_lattice(knockout(body_vis, grow(band, 1.0)), 5.0, 0.4), C_["sky"], length=2.5,
          name="mesh")
    d.outline(bag_vis, C_["navy"], width=B, name="pouch border")
    for v, (c, stamp) in zip(vis, coins):
        d.fill(tuck(v, B), C_["yellow"], angle=60 if stamp else 120, name="coin face")
    d.fill(knockout(band, *bowp), C_["gold"], angle=TILT, underlay=False, name="cord")
    lo, ro, knot, lt, rt = bowp
    d.fill(knockout(lt, lo, ro, knot), C_["gold"], angle=TILT + 75, name="bow tail")
    d.fill(knockout(rt, lo, ro, knot), C_["gold"], angle=TILT + 105, name="bow tail")
    d.fill(knockout(lo, knot), C_["gold"], angle=TILT + 150, name="bow loop")
    d.fill(knockout(ro, knot), C_["gold"], angle=TILT + 30, name="bow loop")
    d.fill(knot, C_["gold"], angle=TILT + 100, name="bow knot")
    for v, (c, stamp) in zip(vis, coins):
        d.outline(v, C_["gold"], width=B, name="coin rim")
    for c, stamp in coins:
        x, y = c.centroid.coords[0]
        r = (c.bounds[2] - c.bounds[0]) / 2
        if stamp == "star":
            for t in _star_paths(x, y, r * 0.52):
                d.run(t, C_["ginger"], bean=1, name="star")
        elif stamp == "ring":
            d.run(circle_path(x, y, r * 0.55), C_["ginger"], bean=1, name="ring")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
