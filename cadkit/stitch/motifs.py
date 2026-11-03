"""Reusable botanical and seasonal motifs for embroidery designs (shapely, mm, Y up).

Every motif returns plain shapes and paths so a design decides colours, angles and
sewing order. Shapes come in at a nominal size and are placed with `move`, `rotate`
and `scale` from `shapes`.

    maple_leaf(h)          5-lobed maple with teeth; maple_veins(h) its vein paths and
                           maple_sectors(h) the leaf cut into one wedge per lobe
    oak_leaf(l, lobes)     rounded-lobe oak leaf along a midrib; oak_veins(l, lobes)
    leaf(l, w, bend)       pointed ellipse leaf, optionally curved; leaf_vein(l, bend)
    acorn(h)               (nut, cap, stem path)
    pumpkin(w, h, n)       rib segments back to front, plus the stem
    spiral(r0, r1, turns)  tendril path
    wheat(l, grains)       (stem path, grain shapes)
    petal_ring(...)        petals around a centre (sunflower, daisy)
    scallop(r, n, depth)   closed wavy ring path for decorative borders
    dots(...)              small round dots in a ring or along a path (seed, berry)
    blade(...)             tapered grass blade centreline + widths
"""
import math

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from . import shapes as S


def _poly(pts):
    p = Polygon(pts)
    return p if p.is_valid else p.buffer(0)


# ---------- maple ----------

# right half of a sugar-maple outline, unit height, tip at the top; mirrored for the left
_MAPLE_HALF = [
    (0.00, 1.00), (0.07, 0.84), (0.15, 0.89), (0.13, 0.72), (0.15, 0.60), (0.28, 0.66),
    (0.33, 0.77), (0.38, 0.70), (0.53, 0.81), (0.47, 0.64), (0.57, 0.61), (0.44, 0.52),
    (0.31, 0.43), (0.41, 0.39), (0.49, 0.42), (0.48, 0.33), (0.61, 0.25), (0.43, 0.20),
    (0.39, 0.12), (0.25, 0.15), (0.10, 0.08), (0.03, 0.11), (0.00, 0.11),
]
_MAPLE_CENTRE = (0.0, 0.40)
_MAPLE_TIPS = [(0.00, 1.00), (0.53, 0.81), (-0.53, 0.81), (0.61, 0.25), (-0.61, 0.25)]


def _maple_xy(u, h):
    """Unit leaf coords -> mm, the vein centre at the origin."""
    return ((u[0] - _MAPLE_CENTRE[0]) * h, (u[1] - _MAPLE_CENTRE[1]) * h)


def maple_leaf(h=60.0):
    """A sugar-maple leaf `h` mm from base to top tip (about 1.2 h wide), its vein
    centre at the origin. Sinuses are rounded, lobe points kept."""
    half = [_maple_xy(u, h) for u in _MAPLE_HALF]
    left = [(-x, y) for x, y in reversed(half[1:-1])]
    leaf = _poly(half + left)
    k = h * 0.012
    return leaf.buffer(k, join_style="round").buffer(-k, join_style="round")


def maple_veins(h=60.0):
    """Paths from the leaf centre to each lobe tip (85% of the way)."""
    out = []
    for u in _MAPLE_TIPS:
        tx, ty = _maple_xy(u, h)
        out.append(np.array([[0.0, 0.0], [tx * 0.45, ty * 0.45], [tx * 0.85, ty * 0.85]]))
    return out


def maple_stem(h=60.0, bend=0.15):
    y0 = (0.11 - _MAPLE_CENTRE[1]) * h
    return S.bezier((0, 0), (0, y0 * 0.8), (bend * h * 0.3, y0 * 1.2), (bend * h, y0 * 1.6), 24)


def maple_sectors(h=60.0):
    """The leaf cut into one wedge per lobe (boundaries halfway between lobes), for
    multi-tone fills: [(lobe angle, shape), ...]."""
    leaf = maple_leaf(h)
    angs = sorted(math.degrees(math.atan2(*_maple_xy(u, 1.0))) for u in _MAPLE_TIPS)
    out = []
    R = h * 2
    for i, a in enumerate(angs):
        lo = (angs[i - 1] + a) / 2 if i else -180
        hi = (a + angs[i + 1]) / 2 if i + 1 < len(angs) else 180
        ts = np.radians(np.linspace(lo, hi, 40))
        wedge = _poly([(0, 0)] + [(R * math.sin(t), R * math.cos(t)) for t in ts])
        out.append((a, leaf.intersection(wedge)))
    return out


# ---------- oak ----------

def oak_leaf(length=60.0, lobes=4, width=None):
    """Rounded-lobed oak leaf: base at the origin, tip at (0, length)."""
    w = width or length * 0.55
    core = S.ellipse(0, length * 0.52, w * 0.16, length * 0.46)
    parts = [core]
    for i in range(lobes):
        f = (i + 0.8) / (lobes + 0.6)                 # position along the midrib
        y = length * (0.14 + 0.78 * f)
        prof = math.sin(math.pi * (0.25 + 0.65 * f))  # widest past the middle
        r = w * 0.17 * (0.65 + 0.5 * prof)
        x = w * 0.30 * prof + r * 0.3
        for sgn, dy in ((1, 0.0), (-1, length * 0.05)):
            parts.append(S.ellipse(sgn * x, y + dy, r * 1.05, r * 0.9))
    parts.append(S.ellipse(0, length * 0.96, w * 0.11, length * 0.07))
    leaf = unary_union(parts)
    k = w * 0.05
    return leaf.buffer(k, join_style="round").buffer(-k * 1.6, join_style="round").buffer(k * 0.6)


def oak_veins(length=60.0, lobes=4, width=None):
    w = width or length * 0.55
    out = [np.array([[0, 0], [0, length * 0.9]])]
    for i in range(lobes):
        f = (i + 0.8) / (lobes + 0.6)
        y = length * (0.14 + 0.78 * f)
        prof = math.sin(math.pi * (0.25 + 0.65 * f))
        x = w * 0.30 * prof
        for sgn, dy in ((1, 0.0), (-1, length * 0.05)):
            out.append(np.array([[0, y - length * 0.06 + dy], [sgn * x * 0.95, y + dy]]))
    return out


# ---------- simple leaf ----------

def _leaf_axis(length, bend, n=40):
    t = np.linspace(0, 1, n)
    return np.c_[bend * length * np.sin(np.pi * t) * 0.5 * t, t * length]


def leaf(length=20.0, width=8.0, bend=0.0, n=40):
    """Pointed leaf from the origin (stem end) to (0, length); `bend` curves it."""
    t = np.linspace(0, 1, n)
    half = width / 2 * np.sin(np.pi * t) ** 0.85 * (1 - 0.25 * t)
    ax = _leaf_axis(length, bend, n)
    left = ax + np.c_[-half, 0 * t]
    right = ax + np.c_[half, 0 * t]
    return _poly(np.vstack([left, right[::-1]]))


def leaf_vein(length=20.0, bend=0.0):
    ax = _leaf_axis(length, bend)
    return ax[2:-4]


# ---------- acorn ----------

def acorn(h=24.0):
    """(nut, cap, stem): the nut's tip at (0, -h/2), cap on top; stem is a path."""
    nw = h * 0.31
    t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    # an egg pointed at the bottom
    x = nw * np.sin(t)
    y = h * 0.30 * np.cos(t)
    y = np.where(y < 0, y * (1.55 + 0.25 * (1 - np.abs(np.sin(t)))), y)
    nut = _poly(np.c_[x, y - h * 0.02])
    tip = S.ellipse(0, -h * 0.49, h * 0.035, h * 0.05)
    nut = unary_union([nut, tip])
    cw = nw * 1.18
    cap_top = S.ellipse(0, h * 0.16, cw, h * 0.20)
    cap = cap_top.intersection(S.rect(cw * 2.2, h * 0.3, 0, h * 0.27))
    # scalloped lower rim
    rim = unary_union([S.circle(x0, h * 0.13, h * 0.055) for x0 in np.linspace(-cw * 0.85, cw * 0.85, 7)])
    cap = unary_union([cap, rim.intersection(S.ellipse(0, h * 0.16, cw * 1.02, h * 0.21))])
    stem = S.bezier((0, h * 0.34), (0, h * 0.42), (h * 0.05, h * 0.47), (h * 0.12, h * 0.50), 12)
    return nut, cap, stem


# ---------- pumpkin ----------

def pumpkin(w=60.0, h=44.0, n=2):
    """Rib segments (back to front: outermost first, centre last) and the stem.
    Returns ([(rank, shape), ...], stem). rank 0 is the centre segment."""
    segs = []
    count = 2 * n + 1
    for i in range(-n, n + 1):
        cx = i * w / count * 0.70
        rx = w / count * (1.30 if i == 0 else 1.18) - abs(i) * w * 0.01
        ry = h / 2 * (1 - 0.05 * abs(i))
        e = S.ellipse(cx, -abs(i) * h * 0.015, rx, ry)
        # pumpkins dip at the top where the ribs meet the stem
        e = e.difference(S.ellipse(cx * 0.6, h * 0.56, rx * 0.55, h * 0.10))
        segs.append((abs(i), e))
    segs.sort(key=lambda s: -s[0])
    stem_path = np.array([[0, h * 0.40], [w * 0.02, h * 0.52], [w * 0.07, h * 0.60]])
    stem = unary_union([S.ellipse(0, h * 0.44, w * 0.06, h * 0.07),
                        _poly([(-w * 0.045, h * 0.44), (w * 0.045, h * 0.44), (w * 0.10, h * 0.62), (w * 0.04, h * 0.64)])])
    return segs, stem, stem_path


# ---------- paths ----------

def spiral(r0=1.0, r1=6.0, turns=1.6, start=0.0, n=120, cw=False):
    """A tendril curl from radius r1 (outside) in to r0, centred on the origin."""
    t = np.linspace(0, 1, n)
    a = math.radians(start) + (-1 if cw else 1) * t * turns * 2 * math.pi
    r = r1 + (r0 - r1) * t
    return np.c_[r * np.cos(a), r * np.sin(a)]


def tendril(p0, p1, curl=4.0, turns=1.4, cw=False):
    """A vine tendril from p0 heading to p1, ending in a curl of radius `curl`."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    ang = math.degrees(math.atan2(d[1], d[0]))
    sp = spiral(curl * 0.25, curl, turns, start=ang + (90 if cw else -90), cw=cw)
    sp = sp - sp[0] + p1
    mid = p0 + d * 0.5 + np.array([-d[1], d[0]]) * 0.15 * (1 if cw else -1)
    lead = S.bezier(tuple(p0), tuple(p0 + (mid - p0) * 0.9), tuple(mid), tuple(p1), 20)
    return np.vstack([lead, sp[1:]])


def wheat(length=50.0, grains=7, grain=5.0, lean=0.12):
    """(stem path, [grain shapes]): a wheat ear on a gently curved stem, base at origin."""
    stem = S.bezier((0, 0), (0, length * 0.4), (lean * length, length * 0.7), (lean * length * 1.4, length), 30)
    out = []
    top = length * 0.42
    for i in range(grains):
        f = i / max(1, grains - 1)
        idx = int((0.58 + 0.42 * f) * (len(stem) - 1))
        p = stem[idx]
        q = stem[min(idx + 1, len(stem) - 1)]
        ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) - 90
        for side in (1, -1) if i < grains - 1 else (0,):
            g = leaf(grain * (1 - 0.25 * f), grain * 0.48, 0.0)
            g = S.rotate(g, ang + side * 32, origin=(0, 0))
            out.append(S.move(g, p[0], p[1]))
    del top
    return stem, out


def petal_ring(n=16, r_in=8.0, length=12.0, width=5.0, jitter=0.0, start=0.0, seed=3):
    """Petals around the origin, each a leaf shape pointing outward."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a = start + 360 * i / n + (rng.uniform(-jitter, jitter) if jitter else 0)
        L = length * (1 + (rng.uniform(-0.12, 0.12) if jitter else 0))
        p = leaf(L, width, bend=(rng.uniform(-0.2, 0.2) if jitter else 0))
        p = S.move(p, 0, r_in)
        out.append(S.rotate(p, a - 0, origin=(0, 0)))
    return out


def scallop(r=40.0, n=24, depth=1.5, x=0.0, y=0.0, res=720):
    t = np.linspace(0, 2 * np.pi, res + 1)
    rr = r + depth * np.abs(np.sin(n * t / 2))
    return np.c_[x + rr * np.cos(t), y + rr * np.sin(t)]


def dots(points, r=0.9):
    """Small round dots (fills) at the given points."""
    return unary_union([S.circle(px, py, r, res=24) for px, py in points])


def ring_points(r, n, x=0.0, y=0.0, start=0.0):
    return [(x + r * math.cos(math.radians(start + 360 * i / n)), y + r * math.sin(math.radians(start + 360 * i / n)))
            for i in range(n)]


def blade(p0, height, lean=0.3, width=1.6):
    """(path, widths) for a tapered grass blade from p0, for Design.satin."""
    x0, y0 = p0
    path = S.bezier((x0, y0), (x0, y0 + height * 0.45), (x0 + lean * height * 0.6, y0 + height * 0.8),
                    (x0 + lean * height, y0 + height), 14)
    w = np.linspace(width, 0.35, len(path))
    return path, w


def taper(path, w0, w1):
    """Widths for a satin that tapers from w0 to w1 along `path`."""
    return np.linspace(w0, w1, len(path))


# ---------- winter / Christmas ----------

def snowflake(r=40.0, arms=6, branches=((0.42, 0.30), (0.70, 0.22)), start=90.0):
    """Arm and branch centrelines of a dendrite snowflake: [(path, w_root, w_tip)].
    Each arm runs from 0.12 r out to r; `branches` are (position along the arm,
    branch length) pairs, both as fractions of r, sprouting at 55 deg either side."""
    out = []
    for i in range(arms):
        a = math.radians(start + 360 * i / arms)
        u = np.array([math.cos(a), math.sin(a)])
        out.append((np.array([u * r * 0.12, u * r]), 2.2, 1.2))
        for pos, length in branches:
            base = u * r * pos
            for side in (1, -1):
                b = a + side * math.radians(55)
                tip = base + np.array([math.cos(b), math.sin(b)]) * r * length
                out.append((np.array([base, tip]), 1.6, 1.0))
    return out


def folk_star(r_out=40.0, r_in=None, points=8, start=90.0):
    """A pointed folk star (8 points by default), the Scandinavian kind."""
    return S.star(points, r_out, r_in or r_out * 0.52, rot=start)


def bow(w=60.0, h=None):
    """A ribbon bow `w` mm across: (left loop, right loop, knot, left tail, right tail),
    the knot at the origin, tails hanging below with V-cut ends."""
    h = h or w * 0.5
    knot = S.ellipse(0, 0, w * 0.075, h * 0.2)

    def loop(sign):
        pts = [(0.03, 0.10), (0.18, 0.46), (0.38, 0.58), (0.50, 0.40), (0.48, 0.05),
               (0.36, -0.20), (0.18, -0.24), (0.03, -0.10)]
        return S.smooth([(sign * x * w, y * h) for x, y in pts], 10).buffer(0)

    def tail(sign):
        pts = [(0.03, -0.12), (0.12, -0.30), (0.24, -0.78), (0.30, -1.02), (0.24, -0.93),
               (0.17, -1.06), (0.12, -0.80), (0.02, -0.30)]
        return _poly([(sign * x * w, y * h) for x, y in pts])

    return loop(-1), loop(1), knot, tail(-1), tail(1)


def bauble(r=14.0, x=0.0, y=0.0):
    """A round Christmas ornament: (ball, cap, hanger loop path), ball centred at (x, y)."""
    ball = S.circle(x, y, r)
    cap = S.rounded_rect(r * 0.62, r * 0.36, r * 0.08, x, y + r * 1.02)
    hook = S.arc(x, y + r * 1.42, r * 0.22, -60, 240)
    return ball, cap, hook


def holly_leaf(length=26.0, width=None, spikes=3):
    """A holly leaf along +X from the origin: spiky edges, `spikes` points a side."""
    width = width or length * 0.42
    n = spikes * 2 + 1
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        env = math.sin(math.pi * t) ** 0.7 * width / 2
        dip = 1.0 if i % 2 == 0 else 0.62           # alternate points and scallops
        x = t * length
        top.append((x, env * (dip if 0 < i < n else 0)))
        bot.append((x, -env * (dip if 0 < i < n else 0)))
    return _poly(top + bot[::-1][1:-1])


def holly_vein(length=26.0):
    return np.array([(length * 0.08, 0.0), (length * 0.88, 0.0)])


def mitten(h=50.0):
    """A mitten `h` mm tall, cuff at the bottom, thumb on the right: (hand, cuff)."""
    hand = S.smooth([(-0.30, 0.10), (-0.33, 0.55), (-0.22, 0.86), (0.00, 0.95), (0.20, 0.86),
                     (0.27, 0.62), (0.30, 0.48), (0.44, 0.56), (0.52, 0.48), (0.46, 0.30),
                     (0.32, 0.16), (0.30, 0.10)], 10)
    hand = S.scale(hand, h, h).buffer(0)
    cuff = S.rounded_rect(0.68 * h, 0.22 * h, 0.05 * h, -0.005 * h, 0.0)
    return hand, cuff


def candy_cane(h=70.0, hook=None):
    """Centreline of a candy cane `h` mm tall, the hook curling left at the top."""
    hook = hook or h * 0.2
    straight = np.array([(0.0, -h / 2), (0.0, h / 2 - hook)])
    arc = S.arc(-hook, h / 2 - hook, hook, 0, 180, res_deg=6)
    return np.vstack([straight, arc[1:]])


def gingerbread(h=70.0):
    """A gingerbread figure `h` mm tall, centred on the origin."""
    head = S.circle(0, h * 0.30, h * 0.17)
    body = S.smooth([(-0.15, 0.13), (-0.45, 0.10), (-0.48, 0.00), (-0.18, -0.02), (-0.16, -0.18),
                     (-0.32, -0.45), (-0.24, -0.50), (0.00, -0.24), (0.24, -0.50), (0.32, -0.45),
                     (0.16, -0.18), (0.18, -0.02), (0.48, 0.00), (0.45, 0.10), (0.15, 0.13)], 10)
    return unary_union([head, S.scale(body, h, h).buffer(0)]).buffer(h * 0.02).buffer(-h * 0.02)
