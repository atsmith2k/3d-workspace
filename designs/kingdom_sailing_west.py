"""Sailing West: a grey swan-prowed ship under a full sail, heading into the setting sun
over the sea, in a landscape patch.

Spec:
  object:       a ship of the elder folk leaving the shores for the undying west (an
                original ship) for tees, hoodies, totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      purple, wine, rust, flame (sky rings round the sun, outside in), yellow
                (sun and its track on the water), navy (sea), ice (wave lines), pewter
                (hull, mast, swan prow), silver (sail, border): 9 colours
  must have:    a 92 x 72 mm rounded-corner landscape patch (r 10), 2.6 mm silver satin
                border; a half-set sun 22 mm across on the horizon with the sky in rings
                round it; a navy sea with the sun's track in five yellow satin dashes
                shortening toward the viewer and ice bean-stitch wave lines; a 46 mm
                ship sailing right: a low hull rising to a swan-neck prow (tapered
                satin 3 -> 1.4 mm and a head with a beak) and a curled stern, a mast and
                a billowing silver square sail lit against the sun; two gulls
  density:      sky and sea knocked out under the ship and the sun's track; fills tucked
                under the border; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _kingdom import C_, SIZES, fit, hoop_for, pieces, product, standard_checks, tube, widths_along

DESCRIPTION = "Grey swan-prowed ship under full sail heading into the setting sun"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Sailing West Embroidery Design",
    "A grey swan-prowed ship under full sail, heading over the sea into the setting sun",
    ["ship", "sailing ship", "sailing west", "sunset", "ocean", "sea", "voyage", "elven ship",
     "swan ship", "landscape embroidery", "nautical"],
    "The last ship sails west: a grey ship with a swan-necked prow, its silver sail full, "
    "heading over the darkening sea into a setting sun ringed with rose and gold.\n\n"
    "Great on hoodies, tees, tote bags, jackets and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 9, 22000)


W, H, RC = 92.0, 72.0, 10.0
BW = 2.6
HZ = -6.0                     # horizon
SX, SR = 6.0, 11.0            # sun centre x and radius


def hull():
    """Low hull, the bow (right) sweeping up into the prow's base, the stern (left) curling."""
    top = spline([(-25.0, 0.5), (-21.0, -3.5), (-10.0, -4.6), (4.0, -4.6), (14.0, -3.6),
                  (20.5, -0.6), (23.5, 3.5)], samples=8)
    keel = spline([(22.0, 1.0), (17.0, -5.6), (8.0, -9.2), (-8.0, -9.4), (-18.0, -8.0),
                   (-24.0, -3.6), (-26.5, 1.0)], samples=8)
    # the bow ends where the swan neck takes over: past x 20 it was a hairline spike whose
    # fill rows piled 88 penetrations into one spot under the neck
    return (poly(np.vstack([top, keel])) & rect(80, 40, 20.0 - 40, 0)).buffer(0.3).buffer(-0.3)


def prow():
    """Swan neck from the bow, and the head with its beak."""
    neck = spline([(19.6, -2.4), (21.4, 0.2), (25.3, 6.6), (26.5, 13.0), (24.6, 18.4), (21.6, 20.0)], samples=10)
    head = smooth([(19.6, 18.4), (20.6, 21.4), (22.8, 21.8), (24.0, 20.0), (22.6, 18.2)], samples=6)
    beak = poly([(20.2, 20.6), (16.6, 19.4), (20.2, 19.0)])
    return neck, union(head, beak)


def stern():
    return spline([(-25.5, 0.0), (-28.0, 4.0), (-27.2, 8.0), (-24.8, 9.4), (-23.2, 7.8)], samples=10)


def sail():
    """Square sail on a yard, bellied to the right by the wind."""
    left = spline([(-13.0, 30.0), (-11.8, 19.0), (-12.6, 8.0)], samples=8)
    right = spline([(9.0, 8.0), (13.0, 19.0), (9.0, 30.0)], samples=8)
    topc = spline([(9.0, 30.0), (-2.0, 31.0), (-13.0, 30.0)], samples=6)
    foot = spline([(-12.6, 8.0), (-2.0, 5.4), (9.0, 8.0)], samples=6)
    return poly(np.vstack([left, foot[1:], right[1:], topc[1:]]))


def art():
    d = Design()
    frame = rounded_rect(W, H, RC, 0, 0)
    inner = tuck(frame, BW)
    hl = hull()
    neck, head = prow()
    neck_w = widths_along(neck, 3.0, 2.4, 2.0, 1.6, 1.4)
    st = stern()
    st_w = widths_along(st, 2.6, 2.2, 1.8, 1.4, 1.2)
    sl = sail()
    mast = np.array([(-1.8, -5.0), (-1.8, 31.0)])     # ends under the yard
    yard = np.array([(-14.4, 30.6), (10.4, 30.6)])
    ship = union(hl, tube(neck, neck_w), head, tube(st, st_w), sl,
                 LineString(mast).buffer(0.9), LineString(yard).buffer(0.9))

    sky = inner & rect(200, 100, 0, HZ + 50)
    sea = inner & rect(200, 100, 0, HZ - 50)
    sun = circle(SX, HZ, SR) & rect(200, 100, 0, HZ + 50 - 0.0)
    rings = [("flame", SR, 19.0), ("rust", 19.0, 28.0), ("wine", 28.0, 39.0), ("purple", 39.0, 200.0)]
    sky_cover = union(ship, sun)
    for i, (col, r0, r1) in enumerate(rings):
        g = sky & (circle(SX, HZ, r1 + (0.4 if i < 3 else 0), res=200) - circle(SX, HZ, r0, res=200))
        g = knockout(g, ship)
        if not g.is_empty:
            d.fill(g, C_[col], angle=0, spacing=0.42, name=f"{col} sky")
    # sea, with the sun's track on the water
    track = []
    for k, (y, half) in enumerate([(-15.5, 6.5), (-19.5, 9.0), (-23.5, 6.0), (-27.5, 10.0), (-31.0, 5.0)]):
        track.append(np.array([(SX - half, y), (SX + half, y)]))
    track_band = union(*[LineString(t).buffer(1.0, cap_style="flat") for t in track])
    # the hull's reflection is dark water: the track starts below it
    # the sea runs on under the sun's track (fill + satin, 2.7 layers): cutting the
    # dashes out splits it into strips whose travel piles up along the keel
    d.fill(knockout(sea, ship), C_["navy"], angle=0, spacing=0.42, name="sea")
    d.fill(knockout(sun, ship), C_["yellow"], angle=0, name="sun")
    for t in track:
        d.satin(t, 2.0, C_["yellow"], underlay="center", name="sun track", trim_after=True)
    waves = [spline([(-38, -16), (-33, -15), (-28, -16.5), (-22, -15.5)], samples=6),
             spline([(-30, -24), (-24, -23), (-18, -24.5), (-12, -23.5)], samples=6),
             spline([(22, -18), (28, -17), (34, -18.5), (40, -17.5)], samples=6),
             spline([(18, -28), (24, -27), (30, -28.5), (36, -27.5)], samples=6),
             spline([(-40, -30), (-34, -29), (-28, -30.5)], samples=6)]
    for wv in waves:
        for q in pieces(LineString(wv).intersection(inner.buffer(-1.6)), 3.0):
            d.run(q, C_["ice"], bean=1, length=1.6, name="wave", trim_after=True)
    # ship: hull, prow, stern and mast in pewter, the sail in silver
    d.fill(hl, C_["pewter"], angle=0, name="hull")
    d.satin(neck, neck_w, C_["pewter"], taper=True, underlay="center", name="swan neck")
    d.fill(head, C_["pewter"], angle=60, name="swan head")
    d.satin(st, st_w, C_["pewter"], taper=True, underlay="center", name="stern")
    d.satin(np.array([(-1.8, -6.0), (-1.8, 30.0)]), 1.6, C_["pewter"], underlay="center", name="mast")
    d.satin(yard, 1.8, C_["pewter"], underlay="center", name="yard")
    d.fill(knockout(sl, LineString(mast).buffer(0.8), LineString(yard).buffer(0.9)), C_["silver"], angle=80,
           name="sail")
    # gulls: small silver bean-stitch V's
    for x, y, s_ in ((-30.0, 22.0, 1.0), (-22.0, 26.5, 0.8)):
        g = np.array([(x - 3.0 * s_, y + 1.2 * s_), (x - 1.4 * s_, y + 1.0 * s_), (x, y),
                      (x + 1.4 * s_, y + 1.0 * s_), (x + 3.0 * s_, y + 1.2 * s_)])
        d.run(g, C_["silver"], bean=1, length=1.6, name="gull", trim_after=True)
    d.outline(frame, C_["silver"], width=BW, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
