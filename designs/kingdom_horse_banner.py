"""Horse-Lord Shield: a gold horse at full gallop on a green round shield, a sun above and a
running wave band round the rim.

Spec:
  object:       the round shield of a kingdom of plains horse-riders (original heraldry:
                a gold horse courant and sun on green, a running-wave border) for tees, hoodies,
                totes, saddle-blanket patches and cloaks
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens, canvas and fleece with tear-away
  threads:      green (field), pine (band), brass (far legs, mane), gold (horse, sun, rim,
                wave), bark (eye): 5 colours
  must have:    a 92 mm round shield: a 2.8 mm gold satin rim, a 9 mm deep green band inside
                it with a gold 1.8 mm satin running wave (24 crests) sewn round it, a
                green field; a 64 mm long gold horse in a flying gallop
                facing right, forelegs reaching, hind legs thrown back, a tail streaming
                behind as a tapered satin, its far legs in
                darker brass for depth, four brass mane locks (tapered satins 2.4 -> 1 mm), a bark eye 1.6 mm; a gold sun disk 11 mm with eight rays above the horse's
                back
  density:      the field is knocked out under the horse and sun; the band under the
                wave; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *

from shapely.geometry import LineString as LineString_

from _kingdom import C_, SIZES, fit, hoop_for, product, standard_checks, trim_path, tube, widths_along

DESCRIPTION = "Gold galloping horse and sun on a green round shield with a running-wave border"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Horse-Lord Shield Embroidery Design",
    "A gold horse at full gallop under a gold sun, on a green round shield",
    ["horse", "galloping horse", "horse lords", "horse rider", "equestrian", "round shield",
     "heraldry", "shield", "plains", "renaissance faire", "viking"],
    "The shield of the riders of the golden plains: a horse at full gallop under a rising "
    "sun, gold on deep green, inside a running wave border and a gold rim.\n\n"
    "Great on hoodies, tees, tote bags, saddle pads and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 22000)


R = 46.0
BW = 2.8
R_BAND = (R - BW / 2 - 9.0, R - BW / 2 + 0.6)     # brass band, under the rim's inner half
HX, HY, HK = 3.4, -4.5, 0.88                       # horse placement and scale


def horse():
    """Flying-gallop horse facing right, about 64 x 34 mm, as one silhouette."""
    body = smooth([(-18, 5), (-9, 7.5), (3, 6.8), (10, 8.5), (16, 4), (15, -5), (6, -7.5),
                   (-5, -7.0), (-14, -5.5), (-21, -1)], samples=8)
    rump = circle(-15.5, 1.8, 7.6)
    chest = circle(11.0, 0.2, 7.6)
    neck = smooth([(5, 7.5), (10.5, 13.5), (15.0, 19.0), (19.5, 22.0), (24.0, 20.0),
                   (21.5, 12.5), (18.0, 2.0)], samples=8)
    head = smooth([(17.5, 21.5), (21.0, 24.2), (25.5, 22.8), (31.5, 16.0), (32.6, 13.0),
                   (30.0, 11.2), (25.5, 13.0), (21.5, 14.0)], samples=8)
    ears = [poly([(19.0, 22.6), (18.8, 27.4), (21.6, 23.6)]),
            poly([(20.8, 23.6), (22.2, 27.4), (23.4, 23.2)])]
    legs = [
        # near foreleg reaching forward, far foreleg folded under
        (spline([(12.5, -3.0), (19.0, -7.5), (25.5, -7.0), (31.5, -3.5)], samples=8), [6.0, 3.4, 2.6, 2.8]),
        (spline([(8.5, -5.0), (13.5, -11.5), (19.5, -12.0), (21.5, -16.5)], samples=8), [5.6, 3.2, 2.5, 2.8]),
        # hind legs thrown back
        (spline([(-16.5, -2.5), (-23.0, -8.0), (-29.0, -9.5), (-35.0, -13.0)], samples=8), [8.0, 3.8, 2.6, 2.8]),
        (spline([(-12.0, -4.0), (-15.5, -11.0), (-22.0, -15.5), (-24.5, -20.5)], samples=8), [7.0, 3.4, 2.5, 2.8]),
    ]
    leg_g = [tube(p, w) for p, w in legs]
    near = union(body, rump, chest, neck, head, *ears, leg_g[0], leg_g[2])
    far = union(leg_g[1], leg_g[3])
    T = lambda g: move(scale(g.buffer(0.4).buffer(-0.4), HK), HX, HY)
    return T(near), T(far)


def tail():
    pth = spline([(-20.5, 5.5), (-27.0, 7.0), (-32.5, 4.5), (-36.0, -0.5), (-40.0, -4.0)], samples=8)
    return pth * HK + (HX, HY)


def mane():
    """Brass locks flicking back off the crest of the neck (tapered satins)."""
    out = []
    for (x, y), k in zip([(18.4, 22.2), (15.0, 19.2), (11.8, 15.2), (8.6, 11.0)], (1.0, 1.1, 1.05, 0.9)):
        out.append(spline([(x + 0.8, y - 0.9), (x - 2.0 * k, y + 1.4 * k), (x - 5.2 * k, y + 1.6 * k)],
                          samples=8) * HK + (HX, HY))
    return out


def sun(x, y, r=5.5):
    rays = [poly([(x + (r + 1.2) * math.cos(a - 0.2), y + (r + 1.2) * math.sin(a - 0.2)),
                  (x + (r + 5.0) * math.cos(a), y + (r + 5.0) * math.sin(a)),
                  (x + (r + 1.2) * math.cos(a + 0.2), y + (r + 1.2) * math.sin(a + 0.2))]).buffer(0.35)
            for a in np.radians(np.arange(8) * 45 + 22.5)]
    return circle(x, y, r), rays


def wave_ring(rc, amp, n, res=720):
    t = np.linspace(0, 2 * np.pi, res + 1)
    r = rc + amp * np.sin(n * t)
    return np.c_[r * np.cos(t), r * np.sin(t)]


def art():
    d = Design()
    disc = circle(0, 0, R, res=256)
    band = circle(0, 0, R_BAND[1], res=256) - circle(0, 0, R_BAND[0], res=256)
    field = circle(0, 0, R_BAND[0] + 0.6, res=256)
    h, far = horse()
    far = far - h.buffer(-0.4)
    tl = tail()
    tw = widths_along(tl, 3.4, 2.8, 2.0, 1.3)
    tail_area = tube(tl, tw)
    disk, rays = sun(-6.0, 19.0)
    locks = mane()
    lock_w = [widths_along(m, 2.4, 1.6, 1.0) for m in locks]
    lock_area = union(*[tube(m, w) for m, w in zip(locks, lock_w)])
    wave = wave_ring((R_BAND[0] + R - BW) / 2 + 0.2, 2.6, 24)
    wave_band = LineString_(wave).buffer(1.0)

    d.fill(knockout(field, h, far, tail_area, lock_area, disk, *rays), C_["green"], angle=30, name="field")
    d.fill(knockout(band, wave_band), C_["pine"], angle=0, name="band")
    d.fill(far, C_["brass"], angle=60, name="far legs")
    for m, w in zip(locks, lock_w):
        d.satin(m, w, C_["brass"], taper=True, underlay="center", name="mane", trim_after=True)
    d.fill(h, C_["gold"], angle=100, name="horse")
    d.satin(tl, tw, C_["gold"], taper=True, underlay="center", name="tail")
    d.fill(disk, C_["gold"], angle=45, name="sun")
    for r_ in rays:
        d.fill(r_, C_["gold"], angle=0, name="sun ray")
    d.satin(wave, 1.8, C_["gold"], underlay="center", name="wave band")
    d.outline(disc, C_["gold"], width=BW, name="rim")
    # bark detail: the eye, and a line dividing the tail from the rump
    d.fill(circle(26.2 * HK + HX, 18.2 * HK + HY, 0.8, res=24), C_["bark"], angle=0, name="eye")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))


