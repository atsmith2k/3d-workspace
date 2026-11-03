"""Ancient Rune Oak: a gnarled oak in line-art style inside a ring of Elder Futhark runes.

Spec:
  object:       an old, gnarled oak: a flared trunk with spreading roots in a light
                wood fill with dark bark outline and grain lines, crooked dark limbs as
                tapered satins reaching into a rounded canopy, a few gold acorns; round
                it a band of Elder Futhark runes between two gold rings; for tees,
                totes, journals covers and wall hangings
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens and canvas with tear-away; knits with cut-away
  threads:      green (canopy), light brown (trunk fill), dark brown (bark outline,
                grain, limbs), gold (acorns, rings, runes): 4 colours
  must have:    a 72 mm wide lumpy canopy in a contour fill (concentric ripples, a
                foliage texture unlike flat tatami); five crooked limbs, tapered satins
                3.0 -> 1.2 mm; trunk and roots filled (rows along the grain), one
                continuous bean-stitch outline, four grain lines and a knot on top; two gold bean rings r 46.5 and 37.5 mm;
                26 runes 6 mm tall, each one continuous stroke (no retraced line)
  runes:        genuine Elder Futhark letter shapes, those that draw in one stroke
                (uruz, thurisaz, raido, kaunan, wunjo, isa, eihwaz, sowilo, berkanan,
                ehwaz, laguz, ingwaz, dagaz); decorative, they spell nothing
  density:      the canopy is knocked out under every limb, acorn and the trunk; the
                limbs sew over the top of the trunk fill (about 2.9 layers); max 3.5
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Gnarled oak tree inside a ring of Elder Futhark runes"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Ancient Rune Oak Embroidery Design",
    "A gnarled old oak with a rippled green canopy and bark-lined trunk, ringed by a band of gold runes",
    ["rune", "runes", "elder futhark", "oak tree", "tree of life", "line art embroidery",
     "blackwork", "nordic", "celtic", "pagan", "druid"],
    "An ancient, gnarled oak: its trunk and spreading roots in warm wood tones lined "
    "with dark bean-stitch bark, grain and a knot, crooked limbs reaching into a rippled green "
    "canopy hung with gold acorns, all inside a ring of Elder Futhark runes.\n\n"
    "Great on tees, tote bags, journal covers, cushions and wall hangings.",
    mockups=("tshirt", "tote"),
)

GREEN, WOOD, BARK, GOLD = C_["moss"], C_["wood"], C_["bark"], C_["gold"]


def checks(p):
    return standard_checks(p, 4, 20000)


# ---------- helpers ----------

def _resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.c_[np.interp(t, s, path[:, 0]), np.interp(t, s, path[:, 1])]


def tube(path, widths):
    path = _resample(path, 0.4)
    w = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(widths)), widths)
    return union(*[Point(*q).buffer(r / 2, quad_segs=12) for q, r in zip(path, w)]).simplify(0.05)


def _pieces(g, min_len=1.5):
    if g.is_empty:
        return []
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "LineString" and p.length > min_len:
            out.append(np.asarray(p.coords))
        elif hasattr(p, "geoms"):
            out += _pieces(p, min_len)
    return out


# ---------- the tree ----------

def canopy():
    blobs = [(0, 24, 14), (-14, 22, 12), (14, 23, 12), (-24, 14, 9), (24, 13, 9.5),
             (-8, 32, 9), (9, 32, 9), (-18, 8, 7.5), (18, 7, 7.5), (0, 14, 12)]
    return union(*[circle(x, y, r) for x, y, r in blobs]).simplify(0.05)


def trunk():
    """Trunk with flared base and four roots: one silhouette for the line-art outline."""
    left = spline([(-4.0, 10.0), (-4.5, 2.0), (-3.2, -6.0), (-4.8, -13.0), (-8.0, -18.0)], samples=10)
    right = spline([(8.0, -18.0), (5.0, -12.5), (3.6, -5.0), (4.8, 3.0), (4.5, 10.0)], samples=10)
    body = poly(np.vstack([left, right, [(0.0, 12.0)]]))
    roots = [tube(spline([(-5.0, -16.0), (-12.0, -20.5), (-18.5, -21.0), (-24.0, -22.5)], samples=12),
                  [4.0, 2.8, 2.0, 1.5]),
             tube(spline([(-2.5, -17.0), (-5.0, -23.0), (-9.0, -27.5)], samples=12), [3.6, 2.4, 1.5]),
             tube(spline([(3.0, -17.0), (6.0, -23.5), (11.0, -27.0)], samples=12), [3.6, 2.4, 1.5]),
             tube(spline([(5.5, -16.0), (13.0, -19.5), (19.0, -19.5), (25.0, -21.5)], samples=12),
                  [4.0, 2.6, 1.6, 0.6])]
    return union(body, *roots)


LIMBS = [  # crooked limbs: centreline from the trunk top outwards
    [(-3.0, 5.5), (-8.0, 10.0), (-12.0, 10.5), (-17.5, 14.5), (-26.0, 16.0)],
    [(-2.2, 9.5), (-4.5, 15.5), (-9.5, 19.0), (-12.0, 27.0)],
    [(0.5, 11.5), (1.5, 18.0), (-0.5, 24.0), (1.5, 33.0)],
    [(3.0, 9.5), (6.5, 15.0), (12.0, 18.0), (13.0, 27.0)],
    [(3.4, 5.0), (8.5, 8.5), (13.0, 9.0), (18.5, 12.5), (26.0, 13.0)],
]
TWIGS = [  # side twigs, starting clear of their limb
    [(-15.5, 16.2), (-17.5, 22.5), (-21.0, 25.0)],
    [(14.6, 19.5), (17.5, 22.0), (21.0, 21.0)],
    [(-7.0, 20.8), (-6.8, 25.5), (-4.5, 29.0)],
]
ACORNS = [(-20.0, 9.5), (-8.0, 30.5), (8.0, 33.0), (21.5, 8.0), (19.0, 26.0)]


def acorn(x, y, s=1.0):
    """Acorn hanging from (x, y): a rounded cap over a nut with a blunt point."""
    nut = smooth([(x - 1.9 * s, y - 1.0 * s), (x - 1.6 * s, y - 3.0 * s), (x, y - 4.6 * s),
                  (x + 1.6 * s, y - 3.0 * s), (x + 1.9 * s, y - 1.0 * s)], samples=8)
    cap = ellipse(x, y - 0.6 * s, 2.6 * s, 1.5 * s)
    return union(nut, cap)


def _width(path, w0, w1):
    return np.linspace(w0, w1, len(path))


# ---------- runes ----------

RUNES = {  # one-stroke Elder Futhark letters in a 0.6 x 1 box (x, y)
    "uruz": [(0, 0), (0, 1), (0.55, 0.72), (0.55, 0)],
    "thurisaz": [(0, 0), (0, 0.28), (0.45, 0.5), (0, 0.72), (0, 1)],
    "raido": [(0, 0), (0, 1), (0.45, 0.8), (0, 0.56), (0.5, 0)],
    "kaunan": [(0.4, 0.9), (0, 0.6), (0.4, 0.3)],
    "wunjo": [(0, 0), (0, 1), (0.45, 0.8), (0, 0.58)],
    "isa": [(0, 0), (0, 1)],
    "eihwaz": [(0.5, 0.78), (0.25, 1), (0.25, 0), (0, 0.22)],
    "sowilo": [(0.45, 1), (0, 0.66), (0.45, 0.34), (0, 0)],
    "berkanan": [(0, 0), (0, 1), (0.42, 0.76), (0, 0.5), (0.42, 0.24), (0.04, 0.02)],
    "ehwaz": [(0, 0), (0, 1), (0.3, 0.66), (0.6, 1), (0.6, 0)],
    "laguz": [(0, 0), (0, 1), (0.45, 0.72)],
    "ingwaz": [(0.3, 0.05), (0.6, 0.5), (0.3, 0.95), (0, 0.5), (0.3, 0.05)],
    "dagaz": [(0, 0), (0, 1), (0.7, 0), (0.7, 1), (0, 0)],
}
ORDER = ["raido", "uruz", "ehwaz", "sowilo", "laguz", "ingwaz", "berkanan", "thurisaz", "dagaz",
         "kaunan", "wunjo", "eihwaz", "isa"]
R_OUT, R_IN, RUNE_H = 46.5, 37.5, 6.0


def rune_ring():
    """26 runes round the band, feet toward the centre, read clockwise from the top."""
    seq = ORDER + ORDER[::-1]
    out = []
    rc = (R_OUT + R_IN) / 2
    for i, name in enumerate(seq):
        g = np.asarray(RUNES[name], float)
        g[:, 0] -= (g[:, 0].min() + g[:, 0].max()) / 2
        g[:, 1] -= 0.5
        g *= RUNE_H
        a = np.radians(90 - i * 360 / len(seq))
        # local x along the tangent (clockwise), local y outward
        radial = np.array([np.cos(a), np.sin(a)])
        tang = np.array([np.sin(a), -np.cos(a)])
        pts = radial * rc + g[:, :1] * tang + g[:, 1:] * radial
        out.append((name, _resample_poly(pts)))
    return out


def _resample_poly(pts):
    """Keep corners exactly; add points on long sides so the bean stitch follows them."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / 1.2)))
        out += [a + (b - a) * k / n for k in range(1, n + 1)]
    return np.array(out)


TK, TY = 0.9, 6.75     # the tree is drawn larger, then scaled to sit inside the rune band


def tf(g):
    """Tree drawing space -> art space."""
    if isinstance(g, np.ndarray):
        return (g - (0.0, TY)) * TK
    return scale(move(g, 0.0, -TY), TK)


def art():
    d = Design()
    tr = tf(trunk())
    limbs = []
    for pts in LIMBS:
        pth = tf(spline(pts, samples=10))
        limbs.append((pth, _width(pth, 3.0, 1.2)))
    for pts in TWIGS:
        pth = tf(spline(pts, samples=10))
        limbs.append((pth, _width(pth, 1.8, 1.1)))
    limb_area = union(*[tube(p, w) for p, w in limbs])
    acorns = [tf(acorn(x, y)) for x, y in ACORNS]

    leaves = knockout(tf(canopy()), limb_area, *acorns, tr.buffer(-0.6))
    d.fill(leaves, GREEN, spacing=0.45, method="contour_fill", name="canopy")

    # trunk and roots: a wood fill, one continuous bark outline, grain lines and a knot
    wood = tr.buffer(-0.25)          # limbs sew over its top (fill + satin, ~2.9 layers)
    d.fill(wood, WOOD, angle=88, spacing=0.42, name="trunk")
    for ring_pts in outline_paths(tr):
        d.run(ring_pts, BARK, bean=1, length=1.8, name="trunk outline", trim_after=True)
    inner = tr.buffer(-0.9)
    grain = [spline([(-2.6, -14.0), (-2.0, -6.0), (-2.6, 2.0), (-1.8, 8.0)], samples=10),
             spline([(-0.2, -16.0), (0.4, -9.0), (-0.4, -3.5)], samples=10),
             spline([(1.2, 2.5), (0.8, 6.0), (1.5, 9.5)], samples=10),
             spline([(2.6, -15.0), (2.2, -9.0), (3.0, -2.0), (2.6, 5.0)], samples=10)]
    knot = spline([(0.5, -1.0), (1.2, -0.1), (0.7, 1.0), (-0.3, 0.6), (-0.4, -0.6), (0.6, -1.4)], samples=6)
    for g in [tf(g) for g in grain + [knot]]:
        for seg in _pieces(LineString(g).intersection(inner)):
            d.run(seg, BARK, bean=1, length=1.4, name="bark grain", trim_after=True)
    for pth, w in limbs:
        d.satin(pth, w, BARK, name="limb", taper=True, trim_after=True)

    for g in acorns:
        d.fill(g, GOLD, angle=70, name="acorn")
    d.run(circle_path(0, 0, R_IN, res=200), GOLD, bean=1, length=2.0, name="inner ring", trim_after=True)
    for name, pts in rune_ring():
        d.run(pts, GOLD, bean=1, length=1.2, name=f"rune {name}", trim_after=True)
    d.run(circle_path(0, 0, R_OUT, res=220), GOLD, bean=1, length=2.0, name="outer ring")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
