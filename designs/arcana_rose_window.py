"""Cathedral Rose Window: a round stained-glass rose with a golden sun at its heart.

Spec:
  object:       a round gothic rose window in stained-glass style: a sun medallion in the
                centre, a ring of eight petals, an outer ring of sixteen jewelled panes,
                for tees, totes, hoodies, cushions and patches
  overall:      `size` mm across (round: 90 mm in the 4x4 hoop, 120 mm in the 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      navy, blue (spandrels), purple, teal (petals, alternating), red (outer
                panes, sun ground), gold (jewels, sun), orange (sun's eye), black
                (leading): 8 colours
  must have:    centre medallion (r 16) with an eight-point gold sun and a round orange
                eye, its red ground a contour fill following the sun; 8 lancet
                petals (r 19-31, round foot, pointed equilateral arch outward) alternating purple and teal; 16 outer panes (r 34-48) alternating red and blue, each holding a
                round gold jewel; black satin leading 1.9 mm wide (nominal) on every joint,
                a 2.8 mm black frame ring; rows of every pane turn with the window (tangent
                rows outside, radial rows in the petals)
  leading:      every circle and shape is one continuous satin ring (`outline`); spokes
                are open satins that stop at the edge of the ring they meet; inner and
                outer spokes are offset by 11.25 deg so no ring point gets a spoke from
                both sides
  density:      every pane is knocked out under every lead (0.4 mm overlap); max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Round gothic rose window in jewel-tone stained glass with a golden sun"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Cathedral Rose Window Embroidery Design",
    "A round gothic rose window in jewel-tone stained glass around a golden sun medallion",
    ["rose window", "stained glass", "gothic", "cathedral window", "mandala", "sun",
     "medieval", "high fantasy", "jewel tones", "celestial"],
    "A round cathedral rose window in jewel-tone glass: a golden eight-point sun glows at the "
    "centre, ringed by purple and teal petals and sixteen red and blue panes set with gold "
    "jewels, every pane stitched at its own angle and held in bold black leading.\n\n"
    "Great on tees, hoodies, tote bags, cushions and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 24000)


LW = 1.9
FW = 2.8
R0, R1, R2 = 16.0, 34.0, 48.0      # medallion ring, middle ring, frame
NP = 8                             # petals
NO = 16                            # outer panes


def _pol(r, deg):
    a = math.radians(deg)
    return np.array([r * math.cos(a), r * math.sin(a)])


def petal(deg, r0=18.9, r1=31.1, w=9.0):
    """A lancet petal along the radius at `deg`: round foot towards the centre, sides,
    and an equilateral pointed arch at the outer end (gothic tracery)."""
    h = w / 2
    arch = w * math.sin(math.radians(60))            # equilateral arch height
    xs = r1 - arch                                    # springing line of the arch
    base = r0 + h
    pts = []
    for a in np.linspace(90, 270, 19):                # the round foot
        pts.append((base + h * math.cos(math.radians(a)), h * math.sin(math.radians(a))))
    pts.append((xs, -h))
    for a in np.linspace(0, 60, 13):                  # right arch: centred on the left springing
        pts.append((xs + w * math.sin(math.radians(a)), h - w * math.cos(math.radians(a))))
    for a in np.linspace(60, 0, 13)[1:]:              # left arch: centred on the right springing
        pts.append((xs + w * math.sin(math.radians(a)), -h + w * math.cos(math.radians(a))))
    pts.append((xs, h))
    g = poly(pts)
    return rotate(g, deg, (0, 0)).buffer(-0.3).buffer(0.3)


def _trim(path, blockers, w=LW, gap=0.1):
    """Shorten an open lead at both ends until its square end clears the leads it meets."""
    path = np.asarray(path, float)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    s = np.arange(0, L[-1], 0.1)
    P = np.c_[np.interp(s, L, path[:, 0]), np.interp(s, L, path[:, 1])]
    B = blockers.buffer(gap)

    def clear(i):
        j = i + 1 if i + 1 < len(P) else i - 1
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


def art():
    d = Design()
    frame = circle(0, 0, R2, res=192)
    mid = circle(0, 0, R1, res=192)
    med = circle(0, 0, R0, res=128)
    sun = star(8, 12.3, 7.4, 0, 0, rot=90).buffer(-0.7).buffer(0.7)
    eye = circle(0, 0, 3.6, res=64)
    petals = [petal(22.5 + 45 * i) for i in range(NP)]
    jewels = [circle(*_pol(41.0, 22.5 * i), 2.7, res=48) for i in range(NO)]
    rings = [mid, med, sun, eye, *petals, *jewels]

    spokes = [np.array([_pol(R0 + 0.4, 45 * i), _pol(R1 - 0.4, 45 * i)]) for i in range(NP)]
    spokes += [np.array([_pol(R1 + 0.4, 11.25 + 22.5 * i), _pol(R2 - 0.4, 11.25 + 22.5 * i)])
               for i in range(NO)]

    cuts = [np.array([_pol(R0 - 1.5, 45 * i), _pol(R1 + 1.5, 45 * i)]) for i in range(NP)]
    cuts += [np.array([_pol(R1 - 1.5, 11.25 + 22.5 * i), _pol(R2 + 1.5, 11.25 + 22.5 * i)])
             for i in range(NO)]
    edges = [frame.exterior] + [g.exterior for g in rings] + [LineString(s) for s in cuts]
    panes = [g for g in polygonize(unary_union(edges)) if g.area > 1.0 and frame.contains(g.representative_point())]

    block = union(frame.exterior.buffer(FW / 2), *[g.exterior.buffer(LW / 2) for g in rings])
    leads = []
    for s in spokes:
        q = _trim(s, block)
        leads.append(q)
        block = union(block, LineString(q).buffer(LW / 2, cap_style="flat"))
    bands = block

    def role(g):
        c = g.representative_point()
        r = math.hypot(c.x, c.y)
        th = math.degrees(math.atan2(c.y, c.x)) % 360
        if eye.contains(c):
            return "flame", 90, None
        if sun.contains(c):
            return "gold", 45, None
        if med.contains(c):
            return "red", 0, "contour_fill"
        for i, pt in enumerate(petals):
            if pt.contains(c):
                return ("purple" if i % 2 == 0 else "teal"), 22.5 + 45 * i, None
        for j in jewels:
            if j.contains(c):
                return "gold", th + 45, None
        if r < R1:
            return ("navy" if int(th // 45) % 2 == 0 else "blue"), th + 90, None
        k = int(((th - 11.25) % 360) // 22.5)
        return ("red" if k % 2 == 0 else "blue"), th + 90, None

    fills = {}
    for g in panes:
        col, ang, meth = role(g)
        fills.setdefault(col, []).append((g, ang, meth))
    for col in ("navy", "blue", "purple", "teal", "red", "gold", "flame"):
        for g, ang, meth in fills.get(col, []):
            k = knockout(g, bands)
            if k.is_empty:
                continue
            if meth:
                d.fill(k, C_[col], angle=ang % 180, method=meth, name=f"{col} pane")
            else:
                d.fill(k, C_[col], angle=ang % 180, name=f"{col} pane")
    for q in leads:
        d.satin(q, LW, C_["black"], name="spoke", underlay="center")
    for g in rings:
        d.outline(g, C_["black"], width=LW, name="lead ring")
    d.outline(frame, C_["black"], width=FW, name="frame")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
