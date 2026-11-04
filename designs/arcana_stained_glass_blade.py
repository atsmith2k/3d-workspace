"""Stained Glass Sword Window: a gothic arched window with a sword, moon, stars and leaves.

Spec:
  object:       a pointed-arch church window in stained-glass style: a sword point-down
                in the centre, a crescent moon and two four-point stars in the arch above,
                two leaves either side of the blade, for tees, totes, hoodies and patches
  overall:      `size` mm on the long side (90 mm tall in the 4x4 hoop, 160 in the 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      navy, blue, purple (background glass), green (leaves), silver (blade),
                red (grip), gold (guard, pommel, moon, stars), black (leading): 8 colours
  must have:    every pane a jewel-tone fill with its own row angle; black satin
                "leading" 1.9 mm wide (nominal) on every pane joint, sewn last; a 2.8 mm
                black arch frame; the blade split down its middle into two silver panes
                at different angles (a bevelled look); each leaf a single pane
  leading:      every shape's lead is one continuous satin ring (`outline`); straight
                leads are open satins that stop at the edge of the lead they meet
                (a T, 0.2 mm overlap at most), so no point gets more than two columns
  density:      every pane is knocked out under every lead (0.4 mm overlap); max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import polygonize, unary_union

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Gothic stained-glass window with a sword, crescent moon, stars and leaves"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Stained Glass Sword Window Embroidery Design",
    "A gothic arched stained-glass window: a silver sword under a gold crescent moon and stars",
    ["stained glass", "gothic window", "sword", "crescent moon", "cathedral window",
     "medieval", "knight", "high fantasy", "jewel tones", "celestial"],
    "A pointed gothic window in jewel-tone glass: a silver sword hangs point-down beneath a "
    "golden crescent moon and two stars, with green leaves either side, every pane sewn at "
    "its own angle so it catches the light, all held in bold black leading.\n\n"
    "Great on tees, hoodies, tote bags, jackets and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 22000)


LW = 1.9          # leading
FW = 2.8          # frame
HW = 30.0         # window half width
Y0, YS = -45.0, 0.0   # sill, springing line


def window():
    R = 2 * HW
    a = np.radians(np.linspace(0, 60, 40))
    right = np.c_[-HW + R * np.cos(a), YS + R * np.sin(a)]     # centred on the left springing
    left = np.c_[-right[::-1, 0], right[::-1, 1]]
    pts = [(-HW, Y0), (HW, Y0)] + [tuple(p) for p in right] + [tuple(p) for p in left[1:]]
    return poly(pts).buffer(-4.5).buffer(4.5)        # rounded sill corners


def sword():
    blade = poly([(-5.8, 0.4), (5.8, 0.4), (4.6, -30), (0, -40), (-4.6, -30)])
    guard = rounded_rect(36, 5.6, 2.2, 0, 2.8)
    grip = rect(6, 11, 0, 10)
    pommel = circle(0, 19.5, 4.8)
    return union(blade, guard, grip, pommel).buffer(-1.0).buffer(1.0)   # blunt tip


def leaf(x, y, ang, L=14.0, W=7.0):
    t = np.linspace(0, np.pi, 30)
    up = np.c_[L / 2 * np.cos(t), W / 2 * np.sin(t) ** 1.2]
    lo = up[::-1] * [1, -1]
    g = poly([tuple(p) for p in np.vstack([up, lo[1:-1]])])
    return move(rotate(g, ang, (0, 0)), x, y).buffer(-0.9).buffer(0.9)   # blunt tips


def leaf_axis(x, y, ang, L=14.0):
    a = math.radians(ang)
    u = np.array([math.cos(a), math.sin(a)]) * L / 2
    return np.array([[x, y] - u, [x, y] + u])


def moon():
    return (circle(0, 36.5, 8.5) - circle(0, 40.5, 7.0)).buffer(-1.5).buffer(1.5)   # a rising crescent


STARS = [(-18.0, 15.0), (18.0, 15.0)]
LEAVES = [(-17.0, -9.5, 120), (-15.0, -31.5, 120), (17.0, -9.5, 60), (15.0, -31.5, 60)]


def _trim(path, blockers, w=LW, gap=-0.2):
    """Shorten an open lead at both ends until its square end clears the leads it meets."""
    path = np.asarray(path, float)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    s = np.arange(0, L[-1], 0.1)
    P = np.c_[np.interp(s, L, path[:, 0]), np.interp(s, L, path[:, 1])]
    B = blockers.buffer(gap)

    def clear(i):
        j = min(i + 1, len(P) - 1) if i + 1 < len(P) else i - 1
        t = P[j] - P[i] if j > i else P[i] - P[j]
        t = t / np.linalg.norm(t)
        n = np.array([-t[1], t[0]]) * w / 2
        return not LineString([P[i] - n, P[i] + n]).intersects(B)
    i = 0
    while i < len(P) - 1 and not clear(i):
        i += 1
    j = len(P) - 1
    while j > i and not clear(j):
        j -= 1
    return P[i:j + 1]


def _ext(path, mm=1.5):
    path = np.asarray(path, float)
    a = path[0] - (path[1] - path[0]) / np.linalg.norm(path[1] - path[0]) * mm
    b = path[-1] + (path[-1] - path[-2]) / np.linalg.norm(path[-1] - path[-2]) * mm
    return np.vstack([a, path, b])


def art():
    d = Design()
    win = window()
    sw = sword()
    mn = moon()
    stars = [star(4, 6.8, 2.8, x, y, rot=90).buffer(-0.8).buffer(0.8) for x, y in STARS]
    leaves = [leaf(*lv) for lv in LEAVES]
    rings = [sw, mn, *stars, *leaves]

    # open leads in priority order: each stops at the leads before it and at the rings
    lines = [
        np.array([[-5.0, 0.0], [5.0, 0.0]]),                  # blade | guard
        np.array([[-3.0, 5.6], [3.0, 5.6]]),                  # guard | grip
        np.array([[-3.0, 15.5], [3.0, 15.5]]),                # grip | pommel
        np.array([[0.0, 0.0], [0.0, -41.0]]),                 # blade bevel
        np.array([[17.0, 2.8], [40, 2.8]]),                   # transoms
        np.array([[-17.0, 2.8], [-40, 2.8]]),
        np.array([[-4.6, -20.5], [-40, -20.5]]),              # lower panes
        np.array([[4.6, -20.5], [40, -20.5]]),
        np.array([[-7.73, 34.43], [-40, 25.78]]),               # sky rays from the moon
        np.array([[7.73, 34.43], [40, 25.78]]),
    ]
    lines = [np.asarray(LineString(_ext(p, 0.01)).intersection(win).coords) for p in lines]

    # panes: the window cut by every lead's centreline
    edges = [win.exterior] + [g.exterior for g in rings] + [LineString(_ext(p)) for p in lines]
    panes = [g for g in polygonize(unary_union(edges)) if g.area > 1.0 and win.contains(g.representative_point())]

    # leads as stitched
    frame_band = win.exterior.buffer(FW / 2, join_style="mitre", mitre_limit=2.0)
    ring_bands = [g.exterior.buffer(LW / 2, join_style="mitre", mitre_limit=2.0) for g in rings]
    block = union(frame_band, *ring_bands)
    leads = []
    for i, p in enumerate(lines):
        q = _trim(p, block, gap=0.1)
        if i == 3:                                 # the bevel lead stops where the point starts
            q = q[q[:, 1] > -28.5]
        leads.append(q)
        block = union(block, LineString(q).buffer(LW / 2, cap_style="flat"))
    bands = block

    def role(g):
        c = g.representative_point()
        m = g.centroid
        for i, s in enumerate(stars):
            if s.contains(c):
                return "gold", 45 + 90 * i
        if mn.contains(c):
            return "gold", 30
        for i, lf in enumerate(leaves):
            if lf.contains(c):
                return "green", LEAVES[i][2] + 45
        if sw.contains(c):
            if m.y < 0.0:
                return "silver", 60 if c.x < 0 else 120
            if m.y < 5.6:
                return "gold", 0
            if m.y < 15.5:
                return "red", 90
            return "gold", 135
        # background glass
        if c.y > 30:
            return "navy", 20
        if c.y > 2.8:
            return "purple", 110 if c.x < 0 else 70
        if c.y > -22:
            return "blue", 160 if c.x < 0 else 20
        return "navy", 130 if c.x < 0 else 50

    fills = {}
    for g in panes:
        col, ang = role(g)
        fills.setdefault(col, []).append((g, ang))
    for col in ("navy", "blue", "purple", "green", "silver", "red", "gold"):
        for g, ang in fills.get(col, []):
            k = knockout(g, bands)
            if not k.is_empty:
                d.fill(k, C_[col], angle=ang, name=f"{col} pane")
    for q in leads:
        d.satin(q, LW, C_["black"], name="lead", underlay="center")
    for g in rings:
        # the small four-point stars pile satin at their points: open their leads a little
        sp = dict(spacing=0.46) if any(g is s for s in stars) else {}
        d.outline(g, C_["black"], width=LW, name="lead ring", **sp)
    d.outline(win, C_["black"], width=FW, name="frame")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
