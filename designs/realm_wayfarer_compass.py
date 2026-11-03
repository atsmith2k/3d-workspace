"""Wayfarer's Compass: an eight-point compass rose over a ring, mountains and a trail behind.

Spec:
  object:       adventurer's-map compass rose (original art) for tees, hoodies, backpacks,
                journal covers, map cases and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7), about square
  fabric:       knits with cut-away; canvas, denim and wovens with tear-away
  threads:      pewter (mountains), bone (snow caps), bark (trail dots, X mark, compass
                ring), navy (compass face), wood (shadowed half of every point), gold
                (lit half of every point, ring ticks, centre boss, N): 6 colours
  must have:    a 65 mm ring 5.5 mm wide with eight gold ticks and a 12.5 x 14 mm
                cartouche on its top carrying the N over the north point; a navy face; four main
                points 92 mm tip to tip and four 58 mm diagonal points, each split into a
                lit and a shadowed half for a bevelled look; a 6 mm gold centre boss; an
                8.6 mm "N" in our block lettering on the cartouche; two mountain
                ranges with snow caps behind the ring; a dotted trail from the left
                range round under the ring to an X by the right range
  lettering:    `cadkit.stitch.lettering.block_text` (our own alphabet, no font licence)
  density:      every layer knocked out under the ones in front; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import Polygon

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Gold eight-point compass rose over mountains and a dotted trail"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Wayfarer's Compass Rose Embroidery Design",
    "An ornate gold and bronze compass rose with N lettering, mountain peaks and a dotted trail",
    ["compass rose", "compass", "adventurer", "fantasy map", "wanderlust", "explorer", "travel",
     "mountains", "adventure awaits"],
    "Straight off an old adventurer's map: an eight-point compass rose in bevelled gold and "
    "bronze on a deep navy face, ringed in dark brown with a gold N at the top, set against "
    "snow-capped peaks and a dotted trail that ends at an X.\n\n"
    "Great on backpacks, hoodies, tees, journal covers and map-case patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 20000)


RO, RI = 32.5, 27.0       # compass ring
MAJ, MAJ_S = 46.0, 8.0    # main point length, side vertex radius
MIN, MIN_S = 29.0, 5.6    # diagonal points
BOSS = 3.0


def _u(deg):
    a = math.radians(deg)
    return np.array([math.cos(a), math.sin(a)])


def point_halves(a, L, s):
    """(lit half, shadowed half) of a compass point along angle `a`."""
    tip = _u(a) * L
    lit = Polygon([(0, 0), tuple(_u(a + 45) * s), tuple(tip)])
    dark = Polygon([(0, 0), tuple(tip), tuple(_u(a - 45) * s)])
    return lit, dark


def peaks(pts, base):
    """A mountain range polygon through the peak/valley points, flat base at y=base."""
    xs = [p[0] for p in pts]
    return Polygon([(xs[0], base)] + list(pts) + [(xs[-1], base)])


def snow(peak, left, right, drop):
    """A snow cap on a peak: the triangle above `drop` below the tip, jagged underneath."""
    px, py = peak
    y = py - drop
    t = lambda q: (px + (q[0] - px) * drop / (py - q[1]), y)
    l, r = t(left), t(right)
    m1 = (l[0] + (px - l[0]) * 0.5, y + drop * 0.32)
    m2 = (px, y - drop * 0.12)
    m3 = (px + (r[0] - px) * 0.5, y + drop * 0.32)
    return Polygon([peak, r, m3, m2, m1, l])


def art():
    d = Design()
    left_pts = [(-54, -22), (-47, 10), (-42.5, 3), (-35, 27), (-26, 2)]
    right_pts = [(26, 2), (36, 29), (42.5, 9), (48, 16), (54, -22)]
    rng_l, rng_r = peaks(left_pts, -24), peaks(right_pts, -24)
    caps = [snow(left_pts[1], left_pts[0], left_pts[2], 6.5), snow(left_pts[3], left_pts[2], left_pts[4], 9),
            snow(right_pts[1], right_pts[0], right_pts[2], 9.5), snow(right_pts[3], right_pts[2], right_pts[4], 5)]
    face = circle(0, 0, RI + 0.4)
    band = ring(0, 0, RO, RI)
    halves = []
    for k in range(8):
        a = 90 + 45 * k
        L, s = (MAJ, MAJ_S) if k % 2 == 0 else (MIN, MIN_S)
        halves.append((k % 2 == 0, *point_halves(a, L, s)))
    majors = union(*[g for m, l, r in halves if m for g in (l, r)])
    boss = circle(0, 0, BOSS)
    rose = union(*[g for m, l, r in halves for g in (l, r)], boss)
    ticks = [circle(*(_u(22.5 + 45 * k) * (RO + RI) / 2), 1.2, res=32) for k in range(8)]
    # a gold N on a dark cartouche set on the ring top, over the north point
    cart = rounded_rect(12.5, 14.0, 2.6, 0, RO + 4.2)
    nl = block_text("N", cap=8.6, stroke=2.3)
    x0, y0, x1, y1 = nl.bounds
    nl = move(nl, -(x0 + x1) / 2, RO + 4.6 - (y0 + y1) / 2)
    # a dotted trail from the left mountains' foot, round under the ring, to the X by the right range
    trail_p = spline([(-50, -26.5), (-38, -29), (-27, -36), (-12, -41.5), (2, -42), (16, -40), (27, -35), (35, -30.5)],
                     samples=16)
    xc = np.array([40.5, -28.8])

    def dots_on(path, step=3.2, r=0.85):
        seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
        s = np.r_[0, np.cumsum(seg)]
        out = []
        for t in np.arange(0.6, s[-1], step):
            out.append(circle(np.interp(t, s, path[:, 0]), np.interp(t, s, path[:, 1]), r, res=24))
        return out

    rose = rose.difference(cart)
    halves = [(m, l.difference(cart), r.difference(cart)) for m, l, r in halves]
    majors = majors.difference(cart)
    front = union(band, face, rose, cart)
    trail = [g for g in dots_on(trail_p) if g.distance(front) > 1.2]
    mount = union(rng_l, rng_r)
    d.fill(knockout(mount, *caps, band, face, cart, rose.buffer(-0.5)), C_["pewter"], angle=60, name="mountains")
    for c in caps:
        d.fill(knockout(c, front), C_["bone"], angle=-30, underlay=False, name="snow cap")
    for g in trail:
        d.fill(g, C_["bark"], angle=0, underlay=False, name="trail dot")
    d.satin(line(tuple(xc + (-2.4, -2.4)), tuple(xc + (2.4, 2.4))), 1.4, C_["bark"], underlay="center", name="X")
    d.satin(line(tuple(xc + (-2.4, 2.4)), tuple(xc + (2.4, -2.4))), 1.4, C_["bark"], underlay="center", name="X")
    def a_of(g):                            # rows along the point's axis
        c = g.centroid
        return math.degrees(math.atan2(c.y, c.x))

    d.fill(knockout(union(band, cart), rose.buffer(-0.4), *ticks, nl), C_["bark"], angle=0, name="ring")
    d.fill(knockout(face, rose.buffer(-0.4)), C_["navy"], angle=45, name="face")
    for major, lit, dark in halves:         # diagonals first, the main points over them
        if not major:
            d.fill(knockout(dark, majors, boss), C_["wood"], angle=a_of(dark), name="diagonal shade")
    for major, lit, dark in halves:
        if major:
            d.fill(knockout(dark, boss), C_["wood"], angle=a_of(dark), name="point shade")
    for major, lit, dark in halves:
        if not major:
            d.fill(knockout(lit, majors, boss), C_["gold"], angle=a_of(lit), name="diagonal light")
    for major, lit, dark in halves:
        if major:
            d.fill(knockout(lit, boss), C_["gold"], angle=a_of(lit), name="point light")
    d.fill(boss, C_["gold"], angle=45, name="boss")
    for g in ticks:
        d.fill(g, C_["gold"], angle=0, underlay=False, name="tick")
    d.fill(nl, C_["gold"], angle=0, spacing=0.35, name="N")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
