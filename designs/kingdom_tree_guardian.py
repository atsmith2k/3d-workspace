"""Tree Guardian: an ancient forest guardian, a wise old face grown into the bark of a great
tree, amber eyes under heavy brows and a beard of moss, its branches leafing into a crown.

Spec:
  object:       a walking-tree giant / spirit of the old forest (an original face, no
                film creature) for tees, hoodies, totes, journal covers and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      green (back canopy), wood (trunk), bark (outline, bark grain, brows,
                mouth, pupils), leaf (front leaf clusters), yellow (eyes), moss (beard):
                6 colours
  must have:    a 94 mm tall tree: flared roots, a 42 mm wide trunk splitting into three
                limbs; a lumpy green canopy behind the limbs and nine leaf clusters over
                their ends; in the trunk a face: two narrow amber eyes 7 x 2.7 mm with
                round bark pupils, sunk in two bean-stitch socket rings, under heavy bark
                brows (fills), a long knotted nose
                drawn in bark bean stitch, a gnarled bark mouth, a moss beard of eleven
                tapered satin strands 12-23 mm long hanging from a V-shaped jaw; two
                bark furrows across the brow; bark grain in bean stitch flowing round the face;
                the trunk filled with vertical rows like the grain
  density:      the canopy is knocked out under the tree and clusters, the trunk under
                the brows, eyes, mouth and beard; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _kingdom import C_, SIZES, fit, hoop_for, pieces, product, standard_checks, trim_path, tube, widths_along

DESCRIPTION = "Ancient tree guardian: a wise old face in the bark, amber eyes and a moss beard"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Tree Guardian Embroidery Design",
    "A wise old face grown into the bark of a great tree, with amber eyes, a moss beard and a leafy crown",
    ["tree guardian", "tree spirit", "tree giant", "forest guardian", "green man", "ancient tree",
     "tree face", "forest", "druid", "nature spirit", "woodland"],
    "The oldest thing in the forest is watching: a great tree with a wise old face grown into "
    "its bark, amber eyes under heavy brows, a beard of hanging moss, and limbs that leaf "
    "into a green crown.\n\n"
    "Great on hoodies, tees, tote bags, journal covers and woodland patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 26000)


def trunk():
    left = spline([(-34.0, -47.0), (-24.0, -41.0), (-20.5, -30.0), (-21.0, -12.0), (-20.0, 4.0),
                   (-17.0, 14.0)], samples=10)
    right = spline([(17.0, 14.0), (20.0, 4.0), (21.0, -12.0), (20.5, -30.0), (24.0, -41.0),
                    (34.0, -47.0)], samples=10)
    foot = spline([(34.0, -47.0), (18.0, -45.0), (8.0, -47.5), (0.0, -44.5), (-8.0, -47.5),
                   (-18.0, -45.0), (-34.0, -47.0)], samples=6)
    body = poly(np.vstack([left, [(0.0, 18.0)], right, foot[1:-1]]))
    limbs = [(spline([(-12.0, 12.0), (-20.0, 22.0), (-30.0, 30.0), (-36.0, 37.0)], samples=10), [11.0, 8.0, 5.5, 3.5]),
             (spline([(0.0, 14.0), (1.5, 26.0), (-1.0, 36.0), (0.5, 44.0)], samples=10), [11.0, 7.0, 5.0, 3.5]),
             (spline([(12.0, 12.0), (20.0, 21.0), (29.0, 27.0), (36.0, 35.0)], samples=10), [11.0, 8.0, 5.5, 3.5])]
    g = union(body, *[tube(p, w) for p, w in limbs])
    return g.buffer(0.6).buffer(-0.6), limbs


CANOPY = [(-34, 33, 9), (-24, 38, 9), (-12, 41, 9), (0, 43, 9), (12, 41, 9), (24, 37, 9), (34, 32, 9),
          (-40, 24, 6.5), (40, 23, 6.5), (-18, 31, 7), (18, 30, 7)]
CLUSTERS = [(-37, 37, 5.2), (-28, 42, 4.6), (-16, 46.5, 4.4), (1, 47, 5.2), (14, 45.5, 4.6),
            (27, 40.5, 4.8), (37, 34.5, 5.0), (-41, 27, 4.0), (42, 26, 4.0)]


def cluster(x, y, r):
    """A clump of leaves: five lobes round a centre."""
    return union(circle(x, y, r * 0.7),
                 *[circle(x + r * 0.55 * np.cos(a), y + r * 0.55 * np.sin(a), r * 0.5) for a in
                   np.radians(np.arange(5) * 72 + 18)]).buffer(0.3).buffer(-0.3)


def face():
    eyes = [smooth([(-14.2, 5.4), (-11.0, 6.6), (-7.2, 5.6), (-8.2, 3.9), (-11.6, 3.9)], samples=8),
            smooth([(14.2, 5.4), (11.0, 6.6), (7.2, 5.6), (8.2, 3.9), (11.6, 3.9)], samples=8)]
    pupils = [circle(-10.2, 5.1, 1.0), circle(10.2, 5.1, 1.0)]
    brows = [smooth([(-18.0, 7.6), (-14.0, 12.4), (-7.0, 12.8), (-2.4, 9.6), (-5.6, 8.6), (-10.5, 8.8),
                     (-15.2, 6.4)], samples=8),
             smooth([(18.0, 7.6), (14.0, 12.4), (7.0, 12.8), (2.4, 9.6), (5.6, 8.6), (10.5, 8.8),
                     (15.2, 6.4)], samples=8)]
    nose = smooth([(-1.6, 8.0), (-2.2, 2.0), (-3.4, -4.0), (-2.6, -7.0), (0.0, -7.8), (2.6, -7.0),
                   (3.4, -4.0), (2.2, 2.0), (1.6, 8.0)], samples=6)
    mouth = smooth([(-7.0, -12.6), (-3.5, -11.6), (0.0, -12.2), (3.5, -11.5), (7.0, -12.4),
                    (3.5, -13.8), (0.0, -14.2), (-3.5, -13.8)], samples=6)
    return eyes, pupils, brows, nose, mouth


def beard():
    """Moss hanging from the chin in strands of different lengths, fanning out a little."""
    out = []
    xs = np.linspace(-14.0, 14.0, 11)
    drops = [12.0, 16.0, 13.0, 20.0, 17.0, 23.0, 18.0, 21.0, 14.0, 17.0, 12.5]
    for k, (x, drop) in enumerate(zip(xs, drops)):
        sway = 1.4 * np.sin(k * 1.7)
        y0 = -14.4 - 4.0 * (1 - abs(x) / 14.0)
        pth = spline([(x * 0.8, y0), (x * 0.95 + sway * 0.5, y0 - drop * 0.5), (x * 1.1 + sway, y0 - drop)],
                     samples=8)
        out.append((pth, widths_along(pth, 2.3, 1.7, 0.7)))
    return out


WRINKLES = [  # furrows across the brow, like old bark
    [(-12.0, 15.2), (-6.0, 16.6), (0.0, 15.6), (6.0, 16.6), (12.0, 15.2)],
    [(-8.0, 19.0), (-3.0, 20.0), (3.0, 20.0), (8.0, 19.0)],
]

GRAIN = [  # bark grain, flowing round the face: drawn per side and mirrored
    [(-17.5, -40.0), (-17.0, -28.0), (-18.0, -12.0), (-17.6, 0.0), (-19.0, 8.0)],
    [(-13.5, -42.0), (-14.0, -30.0), (-13.0, -20.0), (-15.5, -10.0), (-16.5, -2.0)],
    [(-10.0, -44.0), (-10.5, -34.0), (-12.0, -24.0)],
    [(-5.0, -44.5), (-6.0, -36.0), (-4.5, -30.0)],
    [(-4.0, 15.5), (-6.5, 18.0), (-10.0, 18.5)],
    [(-13.0, 15.0), (-16.0, 20.0), (-22.0, 25.0), (-28.5, 30.5)],
]


def art():
    d = Design()
    tr, limbs = trunk()
    eyes, pupils, brows, nose, mouth = face()
    bd = beard()
    bd_area = union(*[tube(p, w) for p, w in bd])
    # the strands' roots (first 2.5 mm) sew over the trunk fill: knocking the trunk out
    # between roots this close leaves slivers too thin to sew
    bd_cut = union(*[tube(trim_path(p, 2.5, 0.0), w[2:]) for p, w in bd])
    clusters = [cluster(*c) for c in CLUSTERS]
    canopy = union(*[circle(x, y, r) for x, y, r in CANOPY]).buffer(0.5).buffer(-0.5)
    inner_face = union(*eyes, *brows, mouth)

    d.fill(knockout(canopy, tr, *clusters), C_["green"], angle=45, name="canopy")
    d.fill(knockout(tr, inner_face, bd_cut, *clusters), C_["wood"], angle=90, spacing=0.42, name="trunk")
    # bark: outline, grain, brows, mouth, pupils and the nose line
    for ring_pts in outline_paths(tr):
        seg = LineString(np.asarray(ring_pts)).difference(union(*clusters).buffer(0.4))
        for q in pieces(seg, 2.0):
            d.run(q, C_["bark"], bean=1, length=1.8, name="outline", trim_after=True)
    keep_out = union(inner_face.buffer(1.6), *[e.buffer(5.2) for e in eyes], bd_area.buffer(1.4), *[c.buffer(1.0) for c in clusters],
                     nose.buffer(1.4))
    inside = tr.buffer(-1.6)
    for g in GRAIN + [[(-x, y) for x, y in g] for g in GRAIN] + WRINKLES:
        ln = LineString(spline(g, samples=8)).intersection(inside).difference(keep_out)
        for q in pieces(ln, 2.5):
            d.run(q, C_["bark"], bean=1, length=1.6, name="grain", trim_after=True)
    # deep sockets: bark rings round each eye, like knots in the wood
    for e in eyes:
        for off in (1.7, 3.4):
            ring_ = LineString(np.asarray(e.buffer(off).exterior.coords))
            ring_ = ring_.difference(union(*brows).buffer(1.2)).difference(nose.buffer(1.2)).intersection(inside)
            for q in pieces(ring_, 2.0):
                d.run(q, C_["bark"], bean=1, length=1.4, name="socket", trim_after=True)
    for b in brows:
        d.fill(b, C_["bark"], angle=0, name="brow")
    d.fill(mouth, C_["bark"], angle=0, name="mouth")
    for pu in pupils:
        d.fill(pu, C_["bark"], angle=45, name="pupil")
    for ring_pts in outline_paths(nose):
        top = LineString(np.asarray(ring_pts)).difference(brows[0].buffer(1.0)).difference(brows[1].buffer(1.0))
        for q in pieces(top, 2.0):
            d.run(q, C_["bark"], bean=1, length=1.4, name="nose", trim_after=True)
    for c in clusters:
        d.fill(c, C_["leaf"], angle=135, name="leaves")
    for e, pu in zip(eyes, pupils):
        d.fill(knockout(e, pu), C_["yellow"], angle=0, name="eye")
    for p, w in bd:
        d.satin(p, w, C_["moss"], taper=True, underlay="center", name="beard", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
