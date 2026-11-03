"""Reforged Blade: a broken longsword, point down, its shards hanging apart in a forge glow.

Spec:
  object:       the broken sword of an old line of kings, waiting to be forged anew
                (an original sword, no film prop) for tees, hoodies, totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      ember, flame, yellow (forge glow, outside in), silver and pewter (blade
                lit and shadow halves), gray (fuller), bark (grip, line-art edges), gold (crossguard,
                pommel): 8 colours
  must have:    an 11 mm wide blade, hilt to point 92 mm, broken across in a jagged break
                at the middle: the lower blade hangs 7 mm below the stub, tilted 5 deg,
                with two shards between; each piece split down its axis into a silver
                lit half and a gray shadow half, a 1.6 mm gray fuller; every piece edged
                in a dark bean-stitch line; a 38 mm gold crossguard bowed toward the
                blade, a satin-wrapped grip, a gold pommel with a bark ring; a forge glow
                behind the break: a 34 mm yellow twelve-point burst, twelve short
                flame rays and twelve long ember rays (to 41 and 36 mm, alternately);
                five yellow sparks
  density:      the glow is knocked out under every blade piece and spark; max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString
from shapely.ops import split

from cadkit.stitch import *

from _kingdom import C_, SIZES, fit, hoop_for, pieces, product, standard_checks

DESCRIPTION = "Broken longsword with its shards hanging apart in a glowing forge fire"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Reforged Blade Embroidery Design",
    "A broken silver longsword, its shards hanging apart in the glow of the forge",
    ["broken sword", "reforged sword", "sword", "longsword", "forge", "blacksmith",
     "heir of kings", "knight", "sword embroidery", "renaissance faire"],
    "The sword that was broken, waiting for the forge: a silver longsword with a gold "
    "crossguard, its blade snapped clean in two and the shards hanging apart in a "
    "blazing ring of forge fire, sparks flying.\n\n"
    "Great on hoodies, tees, tote bags, jackets and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 20000)


GY = 3.0          # glow centre (the break)
BHW = 5.4         # blade half width


def blade():
    return poly([(-BHW, 27.0), (BHW, 27.0), (BHW, -28.0), (BHW * 0.8, -36.0), (0.7, -46.0), (-0.7, -46.0), (-BHW * 0.8, -36.0), (-BHW, -28.0)])


def zig(y, amp, n=6, seed=0):
    rng = np.random.default_rng(seed)
    xs = np.linspace(-8, 8, n)
    ys = y + amp * np.array([(-1) ** i for i in range(n)]) + rng.uniform(-0.6, 0.6, n)
    return np.c_[xs, ys]


def broken():
    """Stub (with hilt end), three shards and the lower blade, in place."""
    b = blade()
    top_cut = zig(10.0, 1.6, 7, 1)
    low_cut = zig(-3.0, 1.6, 7, 2)
    above = poly([(-8, 40)] + [tuple(q) for q in top_cut] + [(8, 40)])
    below = poly([(-8, -60)] + [tuple(q) for q in low_cut] + [(8, -60)])
    stub = b & above
    lower = b & below
    mid = b - above - below
    # the middle splits into three shards along two cracks
    c1 = LineString([(-8, 1.0), (1.0, 4.5), (8, 9.0)])

    shards = []
    for g in polygons_of(mid):
        parts = [g]
        for c in (c1,):
            nxt = []
            for q in parts:
                nxt += [r for r in split(q, c).geoms]
            parts = nxt
        shards += [q for q in parts if q.area > 6]
    shards = sorted(shards, key=lambda q: -q.centroid.y)[:2]
    # pull the pieces apart: shards drift out and turn, the lower blade drops and tilts
    moved = []
    for i, q in enumerate(shards):
        c = q.centroid
        dx = (1.6, 3.0)[i]
        dy = (-1.4, -3.4)[i]
        moved.append(rotate(move(q, dx, dy), (-9, 7)[i], (c.x + dx, c.y + dy)).buffer(-0.7).buffer(0.2))
    lower = rotate(move(lower, 0.8, -5.0), 5.0, (0, -8.0))
    stub = stub.buffer(-0.2)
    return stub, moved, lower


def halves(g, ang, cx):
    """Split a blade piece down its axis (rotated by ang about the break) into lit/shadow."""
    ax = rotate(LineString([(cx, 60), (cx, -60)]), ang, (0, -8.0))
    parts = list(split(g, ax).geoms)
    lit = [q for q in parts if q.centroid.x < ax.interpolate(ax.project(q.centroid)).x]
    sh = [q for q in parts if q not in lit]
    return union(*lit), union(*sh), ax


def art():
    d = Design()
    stub, shards, lower = broken()
    pieces_ = [stub] + shards + [lower]
    # forge glow: long ember rays and short flame rays round a yellow core
    def ray(a, r1, bw, r0=8.0):
        tip = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
        nrm = np.array([-tip[1], tip[0]])
        c = np.array([0, GY])
        return poly([tuple(c + tip * r0 + nrm * bw), tuple(c + tip * r1 + nrm * 0.7),
                     tuple(c + tip * r1 - nrm * 0.7), tuple(c + tip * r0 - nrm * bw)])
    long_rays = [ray(a, 42.0 if i % 2 == 0 else 36.0, 4.2) for i, a in enumerate(np.arange(12) * 30 + 15)]
    short_rays = [ray(a, 28.0, 3.4) for a in np.arange(12) * 30]
    core = star(12, 17.0, 11.0, 0, GY, rot=97.5).buffer(-1.0).buffer(1.0)
    sparks = [star(4, 3.2, 1.0, x, y, rot=90 + a) for x, y, a in
              ((-17, 31, 10), (24, 23, -12), (-28, -6, 20), (21, -22, 0), (-14, -27, 8))]
    blades = union(*pieces_)

    # hilt
    guard_y = 28.2
    tt = np.linspace(-1, 1, 25)
    gpath = np.c_[19.0 * tt, guard_y - 1.8 * tt ** 2]
    gw = 2.4 + 1.4 * (1 - np.abs(tt)) ** 0.7
    grip = line((0, guard_y + 1.4), (0, 40.6))
    pommel = circle(0, 44.6, 4.2)
    hilt = union(LineString(gpath).buffer(2.0), LineString(grip).buffer(2.8), pommel)

    cover = union(blades, *sparks, hilt)
    sr = union(*short_rays)
    for i, g in enumerate(long_rays):
        a = 15 + 30 * i
        g = knockout(g, cover, sr, core)
        if not g.is_empty:
            d.fill(g, C_["ember"], angle=a + 90, name="ember ray")
    for i, g in enumerate(short_rays):
        g = knockout(g, cover, core)
        if not g.is_empty:
            d.fill(g, C_["flame"], angle=30 * i + 90, name="flame ray")
    d.fill(knockout(core, cover), C_["yellow"], angle=75, name="glow core")
    for s in sparks:
        d.fill(s, C_["yellow"], angle=45, name="spark")

    lit_all, sh_all, axes = [], [], []
    for i, g in enumerate(pieces_):
        if i == 0:
            lit, sh, ax = halves(g, 0, 0)
        elif i == len(pieces_) - 1:
            lit, sh, ax = halves(g, 5.0, 0.8)
        else:
            c = g.centroid
            lit, sh = g & poly([(c.x - 20, -60), (c.x, -60), (c.x, 60), (c.x - 20, 60)]), \
                g - poly([(c.x - 20, -60), (c.x, -60), (c.x, 60), (c.x - 20, 60)])
            ax = None
        lit_all.append(lit)
        sh_all.append(sh)
        axes.append(ax)
    for i, g in enumerate(lit_all):
        if not g.is_empty:
            d.fill(g.buffer(0.2) & pieces_[i], C_["silver"], angle=(0, 81, 97, 5)[i], name="blade lit")
    for i, g in enumerate(sh_all):
        if not g.is_empty:
            d.fill(knockout(g & pieces_[i], lit_all[i].buffer(0.2) & pieces_[i]) if False else g,
                   C_["pewter"], angle=(0, 81, 97, 5)[i] + 30, name="blade shadow")
    # fuller on the stub and the lower blade, clear of the break and the guard
    for i, g in ((0, pieces_[0]), (len(pieces_) - 1, pieces_[-1])):
        ax = axes[i]
        seg = ax.intersection(g.buffer(-2.2))
        for q in pieces(seg, 3.0):
            if i == 0:
                q = q[q[:, 1] < guard_y - 3.4] if q[0, 1] > q[-1, 1] else q[q[:, 1] < guard_y - 3.4]
            if len(q) < 2:
                continue
            from shapely.geometry import LineString as LS
            L = LS(q)
            if i == len(pieces_) - 1:
                # stop well short of the point
                from shapely.ops import substring
                L = substring(L, 0, L.length - 10.0) if q[0, 1] > q[-1, 1] else substring(L, 10.0, L.length)
            if L.length > 3:
                d.satin(np.asarray(L.coords), 1.6, C_["gray"], underlay="center", name="fuller",
                        trim_after=True)

    d.satin(grip, 4.0, C_["bark"], underlay="center", name="grip")
    for g in pieces_:
        for ring_pts in outline_paths(g):
            d.run(ring_pts, C_["bark"], bean=1, length=1.5, name="blade edge", trim_after=True)
    d.satin(gpath, gw, C_["gold"], underlay="center", name="crossguard")
    d.fill(knockout(pommel, circle(0, 44.6, 1.6)), C_["gold"], angle=90, name="pommel")
    d.run(circle_path(0, 44.6, 1.6, res=24), C_["gold"], bean=1, length=1.0, name="pommel boss")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
