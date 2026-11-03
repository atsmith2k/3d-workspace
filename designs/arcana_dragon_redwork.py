"""Redwork Dragon: a coiled dragon in bold red bean-stitch line art, vintage sampler style.

Spec:
  object:       one coherent serpentine dragon: head at the top right on a curved neck
                that rises from the chest; the body runs from the chest down, round the
                bottom, up the left and over the top, and the tail curls into the middle
                of the coil ending in a spade; a bat wing raised behind from the shoulder;
                a clawed foreleg reaching forward from the chest and a clawed hind leg
                gripping below the coil; for tea towels, quilt blocks, tees and totes
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (linen, cotton, flour-sack towels) with tear-away; knits cut-away
  threads:      red (everything): 1 colour, the classic redwork look
  must have:    the whole dragon as bean-stitch (triple run) lines: one continuous outline
                of head, horns, neck, body, legs, spine ridge and tail spade; spine ridge
                spikes every ~5.5 mm from behind the head to the tail; a wing (arm bone
                as leading edge, four finger tips, scalloped membrane) whose lines stop
                at the body, three finger bones; one row of scale scallops on the back
                only where the body is over 7.5 mm wide; a belly line; mouth, nostril
                curl, brow, almond eye and a tiny satin pupil
  technique:    no fills; every line runs forward only (no out-and-back over its own
                holes); lines start 0.8 mm clear of the lines they meet; no crossings
  density:      runs only, max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Coiled dragon in bold red bean-stitch redwork line art"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Redwork Dragon Embroidery Design",
    "A coiled dragon with a raised wing, clawed feet and curling tail, drawn in bold red bean-stitch redwork lines",
    ["redwork", "line art embroidery", "dragon", "bean stitch", "vintage embroidery",
     "quilt block", "tea towel", "one color embroidery", "serpent"],
    "A serpentine dragon coiled round on itself, head raised on a curving neck, wing "
    "lifted behind, claws out and tail curling into a spade, drawn entirely in bold "
    "triple-run lines in one red thread, the way vintage redwork samplers were "
    "stitched. Light, soft and quick to sew.\n\n"
    "Great on flour-sack tea towels, quilt blocks, pillowcases, tees and tote bags.",
    mockups=("tshirt", "tote"),
)

RED = C_["red"]
LEN = 2.0     # bean stitch length, mm


def checks(p):
    return standard_checks(p, 1, 9000)


# ---------- geometry helpers ----------

def _normals(path):
    d = np.gradient(path, axis=0)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    return np.c_[-d[:, 1], d[:, 0]]


def _resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.c_[np.interp(t, s, path[:, 0]), np.interp(t, s, path[:, 1])]


def _arclen(c):
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]


def tube(path, widths):
    """A tapered tube along a path: union of discs (radius width/2) every 0.4 mm."""
    path = _resample(np.asarray(path, float), 0.12)
    w = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(widths)), widths)
    return union(*[Point(*q).buffer(r / 2, quad_segs=12) for q, r in zip(path, w)]).simplify(0.05)


def offset_path(path, w, k):
    """The path moved sideways by k x local width (k > 0 to the left)."""
    return path + _normals(path) * (np.asarray(w)[:, None] * k)


def _pieces(g, min_len=1.5):
    """Every LineString piece of a shapely geometry as arrays, dropping crumbs."""
    if g.is_empty:
        return []
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "LineString" and p.length > min_len:
            out.append(np.asarray(p.coords))
        elif hasattr(p, "geoms"):
            out += _pieces(p, min_len)
    return out


# ---------- the dragon ----------

T = np.linspace(0, 1, 420)
HEAD_K = 1.45
HEAD_AT = dict(x=30.5, y=39.5, deg=6.0)


def spine():
    """Centreline head -> tail and its width. The neck rises from the chest at the right
    up to the head; the body runs clockwise from the chest (down, round the bottom, up
    the left, over the top) and the tail curls into the middle. Walking head -> tail,
    the left-hand side (+normal) is the back (the outside of the coil)."""
    th = np.radians(20 - 420 * T)
    r = 30 - 18 * T ** 0.9
    body = np.c_[r * np.cos(th), r * np.sin(th)]
    w = 10.5 * (1 - T) ** 0.7 + 1.8
    neck = spline([(29.5, 36.5), (25.5, 29.0), (25.0, 21.0), tuple(body[0])], samples=16)[:-1]
    neck_w = np.interp(np.linspace(0, 1, len(neck)), [0, 0.5, 1], [8.0, 8.6, w[0]])
    return np.vstack([neck, body]), np.r_[neck_w, w], len(neck)


def place(g, x=0.0, y=0.0, deg=0.0, k=HEAD_K):
    """Head space -> art space: scaled, mirrored to face left, turned, moved."""
    g = g * (-k, k) if isinstance(g, np.ndarray) else scale(g, -k, k)
    return move(rotate(g, deg), x, y)


def head():
    """Head in profile facing right (local: skull back at the origin), horns, jaw frill."""
    skull = smooth([(-2.0, 3.0), (3.0, 5.6), (8.5, 6.2), (12.5, 4.6), (17.5, 3.6), (20.5, 2.6),
                    (21.0, 0.6), (19.0, -0.4), (14.0, -1.6), (9.0, -4.6), (3.0, -5.6),
                    (-2.5, -3.5)], samples=10)
    horn1 = tube(spline([(2.0, 4.2), (-3.0, 8.0), (-8.0, 9.0), (-11.5, 7.0)], samples=12),
                 [3.0, 2.2, 1.3, 0.3])
    horn2 = tube(spline([(6.5, 5.6), (4.5, 9.5), (1.5, 11.5), (-2.0, 11.5)], samples=12),
                 [2.6, 1.9, 1.1, 0.3])
    frill = [poly([(0.5, -4.2), (-4.0, -7.0), (3.5, -5.4)]),
             poly([(4.5, -5.3), (2.5, -8.5), (8.0, -4.9)])]
    return union(skull, horn1, horn2, *frill)


def leg(hip, knee, ankle, toes):
    """A clawed leg: tapered tubes hip -> knee -> ankle, three hooked toes."""
    limb = tube(spline([hip, knee, ankle], samples=10), [5.0, 3.4, 2.6])
    claws = []
    a = np.asarray(ankle, float)
    for tx, ty in toes:
        tip = np.array([tx, ty])
        v = tip - a
        mid = a + v * 0.55 + np.array([-v[1], v[0]]) * 0.12
        claws.append(tube(np.array([a, mid, tip]), [2.0, 1.4, 0.3]))
    return union(limb, *claws)


WING_ROOT = (29.5, 20.0)


def back_spikes(c, w, n):
    """Spine ridge along the back from behind the head to near the tail tip: spikes
    every ~5.5 mm leaning toward the tail, skipped at the wing root."""
    s = _arclen(c)
    out = []
    for pos in np.arange(5.0, s[-1] - 6.0, 5.5):
        i = int(np.searchsorted(s, pos))
        base = c[i] + n[i] * w[i] * 0.3
        if np.hypot(*(base - WING_ROOT)) < 6.0:
            continue
        tang = c[min(i + 2, len(c) - 1)] - c[max(i - 2, 0)]
        tang /= np.linalg.norm(tang)
        h = 1.4 + 0.36 * w[i]
        out.append(poly([base - tang * h * 0.5, base + n[i] * h + tang * h * 0.45,
                         base + tang * h * 0.55]))
    return out


def body_shape():
    c, w, _ = spine()
    n = _normals(c)
    body = tube(c, w)
    tip, d = c[-1], c[-1] - c[-8]
    d /= np.linalg.norm(d)
    nn = np.r_[-d[1], d[0]]
    spade = poly([tip - d * 0.5, tip + nn * 3.2 - d * 0.4, tip + d * 5.5, tip - nn * 3.2 - d * 0.4])
    # a foreleg reaches forward from the chest, the hind leg grips below the coil
    fore = leg((23.0, 12.0), (17.5, 15.0), (15.0, 20.5), [(10.8, 22.5), (10.3, 20.0), (11.8, 17.6)])
    hind = leg((4.0, -26.0), (10.0, -32.5), (17.0, -33.5), [(21.0, -31.0), (22.0, -34.5), (19.5, -37.5)])
    return union(body, *back_spikes(c, w, n), spade, fore, hind, place(head(), **HEAD_AT))


WRIST = (52.0, 40.0)


def wing():
    """Bat wing raised behind the coil from the shoulder: the arm bone (root -> elbow ->
    wrist) is the leading edge, then the scalloped membrane runs between four finger
    tips back down to the body; three finger bones fan from the wrist."""
    elbow = (40.0, 28.0)
    tips = [(63.0, 54.0), (72.0, 38.0), (70.0, 20.0), (60.0, 6.0)]
    edge = [WING_ROOT, elbow, WRIST, tips[0]]
    prev = tips[0]
    for b in tips[1:] + [(36.0, 2.0)]:
        m = (np.asarray(prev) + b) / 2
        edge.append(tuple(m + (np.asarray(WRIST) - m) * 0.2))
        edge.append(b)
        prev = b
    outline = spline(edge, samples=10)
    bones = [spline([WRIST, tuple((np.asarray(WRIST) + t) / 2 + (0.0, 1.0)), t], samples=10)
             for t in tips[1:]]
    return outline, bones


def _scallops(c, w, k, phase):
    """A continuous row of arcs bulging toward the back, along a path at k x width."""
    base = offset_path(c, w, k)
    s = _arclen(base)
    n = _normals(base)
    out, pos = [], phase * 4.5
    while pos < s[-1] - 1:
        i0 = np.searchsorted(s, pos)
        step = max(3.0, 0.5 * w[min(i0, len(w) - 1)])
        a, b = pos, min(pos + step, s[-1])
        for u in np.linspace(0, 1, 13)[(1 if out else 0):]:
            q = a + (b - a) * u
            j = min(np.searchsorted(s, q), len(base) - 1)
            out.append(base[j] + n[j] * np.sin(np.pi * u) * step * 0.34)
        pos = b
    return np.array(out)


def art():
    d = Design()
    body = body_shape()
    keep = body.buffer(0.8)            # wing lines stop this far from the body outline

    w_edge, bones = wing()
    edge_keep = LineString(w_edge).buffer(0.8)
    for seg in _pieces(LineString(w_edge).difference(keep)):
        d.run(seg, RED, bean=1, length=LEN, name="wing edge", trim_after=True)
    for b in bones:
        for seg in _pieces(LineString(b).difference(keep).difference(edge_keep)):
            d.run(seg, RED, bean=1, length=LEN, name="wing bone", trim_after=True)

    # the dragon: one continuous ring round head, horns, neck, body, legs, spikes, spade
    for ring_pts in outline_paths(body):
        d.run(ring_pts, RED, bean=1, length=LEN, name="dragon outline", trim_after=True)

    c, w, n0 = spine()
    inside = body.buffer(-0.9)
    core = tube(c, w).buffer(-1.0)     # scales stay off the spikes and legs
    # scale scallops on the back, only where the body is wide enough for them
    wide = int(np.argmax(w[n0:] < 7.5)) + n0
    sc = _scallops(c[n0 + 24:wide], w[n0 + 24:wide], 0.12, 0.0)
    for seg in _pieces(LineString(sc).intersection(core), min_len=4.0):
        d.run(seg, RED, bean=1, length=1.2, name="scales", trim_after=True)
    # belly line from under the jaw to the tail
    belly = offset_path(c, w, -0.28)[8:n0 + int(0.88 * (len(c) - n0))]
    for seg in _pieces(LineString(belly).intersection(inside), min_len=4.0):
        d.run(seg, RED, bean=1, length=LEN, name="belly line", trim_after=True)

    # face: mouth with a curl at the corner, nostril curl, brow, almond eye, satin pupil
    mouth = spline([(20.0, 0.9), (16.0, 0.1), (11.5, -1.6), (9.3, -1.2), (9.4, 0.0)], samples=10)
    nostril = spline([(16.4, 2.0), (17.6, 2.9), (18.6, 2.1)], samples=8)
    brow = spline([(5.5, 2.6), (8.5, 4.6), (12.4, 3.6)], samples=8)
    eye = spline([(6.8, 2.0), (8.6, 3.1), (10.6, 2.4), (8.6, 1.3), (6.8, 2.0)], samples=8)
    for nm, pth in (("mouth", mouth), ("nostril", nostril), ("brow", brow), ("eye", eye)):
        d.run(place(pth, **HEAD_AT), RED, bean=1, length=1.2, name=nm, trim_after=True)
    d.satin(place(line((8.7, 1.65), (8.7, 2.75)), **HEAD_AT), 1.4, RED, name="pupil")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
