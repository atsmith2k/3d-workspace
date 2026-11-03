"""Raven Skull & Moon: a bone-white bird skull in profile in front of a pale crescent moon,
with three black raven feathers fanned behind it and a few stars.

Spec:
  object:       dark-fantasy / witchy night motif (a corvid skull, no branding) for tees,
                hoodies, tote bags, jackets and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      lavender (moon, stars), black (feather vanes), pewter (feather lit
                halves), bone (feather shafts, skull), khaki (bone shading), charcoal
                (eye socket, nostril, sutures, skull border): 6 colours
  must have:    a 90 mm crescent moon opening to the upper right; three 50-60 mm
                feathers fanned below the skull, each split into a black and a pewter half
                with a tapered bone shaft and a notch in the vane; a raven skull facing
                right, about 75 mm long, with a domed cranium, a 14 mm eye socket filled
                dark, a long slightly hooked beak with a nostril slot and the jaw line; a
                1.2 mm charcoal satin border round the skull so it reads on light fabric;
                three four-point stars
  density:      everything knocked out under what sews on top; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Raven skull in profile with black feathers against a crescent moon"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Raven Skull & Moon Embroidery Design",
    "A bone-white raven skull with black feathers in front of a pale crescent moon",
    ["raven skull", "raven", "crow skull", "dark fantasy", "gothic", "witchy", "crescent moon",
     "raven feathers", "occult", "halloween embroidery"],
    "A raven skull in profile, bone white with soft khaki shading, a dark hollow eye and a long "
    "hooked beak, set against a pale crescent moon. Three black raven feathers with pewter "
    "highlights fan out behind it, and a few stars glint in the night.\n\n"
    "Great on hoodies, tees, denim jackets, tote bags and witchy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 16000)


# ---------- pieces ----------

def _place(g, x, y, deg):
    return move(rotate(g, deg, origin=(0, 0)), x, y)


def _place_path(pts, x, y, deg):
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return np.asarray(pts) @ R.T + (x, y)


def feather(length, width, notch_l=0.55, notch_r=0.38):
    """A feather along +Y from its quill end (origin): (left vane, right vane, shaft path,
    shaft widths), in local coordinates. One notch is cut in each vane."""
    q = 5.0                                   # bare quill below the vane
    L = length - q
    t = np.linspace(0, 1, 48)
    half = width / 2 * np.sin(np.pi * np.clip(t * 1.08, 0, 1) ** 0.75) ** 0.6 * (1 - 0.35 * t ** 2)
    half[-1] = 0
    y = q + t * L
    lean = 0.04 * L * np.sin(np.pi * t)       # a slight curve
    left = np.c_[lean - half, y]
    right = np.c_[lean + half * 0.85, y]
    vane = poly(np.vstack([left, right[::-1]]))
    cuts = []
    for tn, side in ((notch_l, -1), (notch_r, 1)):
        i = int(tn * 47)
        ex = lean[i] + side * half[i] * (0.85 if side > 0 else 1)
        cut = Polygon([(ex + side * 1.0, y[i] + 1.2), (ex + side * 1.0, y[i] - 1.6),
                       (lean[i] + side * 1.6, y[i] - 3.6)])
        cuts.append(cut)
    axis = np.c_[lean, y]
    shaft = np.vstack([[0, 0.5], axis[:-6]])
    gap = LineString(shaft).buffer(0.35)
    lefth = vane.intersection(Polygon([(-50, 0), (0, 0)] + [tuple(p) for p in axis] + [(-50, length + 5)])) - gap
    righth = (vane - lefth) - gap
    widths = np.linspace(1.4, 0.9, len(shaft))
    return lefth.buffer(0), righth.buffer(0), shaft, widths, cuts


def skull_shape():
    pts = [(43, -1.0), (34, 2.5), (24, 6.5), (14, 10.5), (5, 15.5), (0, 20.5), (-6, 24.5),
           (-15, 26), (-24, 23.5), (-31, 16.5), (-34, 7), (-33, -2.5), (-28, -10), (-19, -14.5),
           (-9, -13.5), (0, -9.5), (10, -7.2), (22, -5.8), (34, -4.6), (42, -3.9), (44.6, -2.5)]
    return smooth(pts, 10).buffer(0).buffer(-1.3).buffer(1.3)


def sparkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


# ---------- art ----------

def art():
    d = Design()
    moon = circle(-6, 4, 44, res=200) - circle(12, 16, 38, res=200)
    skull = skull_shape()
    socket = ellipse(-10, 9, 8.0, 7.8)
    nostril = smooth([(12, 6.8), (20, 4.6), (21.5, 3.4), (13.5, 4.3), (10.5, 5.5)], 6).buffer(0)
    temporal = smooth([(-23.5, 4), (-20.5, -1), (-22, -6.5), (-25.5, -2)], 6).buffer(0)
    # bone shading: a band along the underside of the cranium and beak
    shade = (skull - move(skull, 2.2, 3.0)).buffer(-0.3).buffer(0.3)

    feathers = []
    for (x, y, deg, L, W) in ((-22, 0, 128, 54, 19), (-20, -4, 150, 62, 21), (-15, -6, 174, 54, 19)):
        lh, rh, sh, wd, cuts = feather(L, W)
        feathers.append([_place(lh, x, y, deg), _place(rh, x, y, deg), _place_path(sh, x, y, deg), wd,
                         [_place(c, x, y, deg) for c in cuts]])
    # a notch only where the vane edge is open fabric: one cut into a neighbour's
    # overlap would leave a tiny bare pocket between two feathers
    for k, f in enumerate(feathers):
        others = union(skull, *[union(g[0], g[1]) for j, g in enumerate(feathers) if j != k]).buffer(1.5)
        for c in f[4]:
            if not c.intersects(others):
                f[0], f[1] = f[0] - c, f[1] - c
    feathers = [tuple(f[:4]) for f in feathers]
    stars = [sparkle(32, 30, 6.5), sparkle(42, 16, 3.8), sparkle(20, 40, 3.5)]

    vanes = union(*[union(a, b) for a, b, _, _ in feathers])
    front_of_moon = union(vanes, skull.buffer(0.6))
    d.fill(knockout(moon, front_of_moon), C_["lavender"], angle=-30, spacing=0.45, name="moon")
    for s in stars:
        d.fill(s, C_["lavender"], angle=45, name="star")
    # feathers back to front so each lies on the one before
    order = [1, 0, 2]
    for c, key in ((0, "black"), (1, "pewter")):
        for k in order:
            later = [union(*feathers[j][:2]) for j in order[order.index(k) + 1:]]
            g = knockout(feathers[k][c], skull.buffer(1.0), *later)
            if not g.is_empty:
                d.fill(g, C_[key], angle=None, name=f"feather {key}")
    for k in order:
        a, b, sh, wd = feathers[k]
        line_ = LineString(sh)
        covered = union(skull.buffer(1.8), *[union(*feathers[j][:2]).buffer(0.8) for j in order[order.index(k) + 1:]])
        vis = line_.difference(covered)
        parts = [g for g in getattr(vis, "geoms", [vis]) if g.geom_type == "LineString" and g.length > 4]
        for g in parts:
            pts = np.asarray(g.coords)
            d.satin(pts, np.linspace(1.4, 0.9, len(pts)), C_["bone"], name="shaft", taper=True)

    bone = tuck(skull, 1.2)
    d.fill(knockout(bone, socket, nostril, temporal, shade), C_["bone"], angle=20, name="skull")
    d.fill(knockout(shade & bone, socket, temporal), C_["khaki"], angle=-20, name="bone shade")
    d.fill(socket, C_["charcoal"], angle=45, name="socket")
    d.fill(nostril, C_["charcoal"], angle=0, underlay=False, name="nostril")
    d.fill(temporal, C_["charcoal"], angle=80, underlay=False, name="temporal")
    d.run(spline(np.array([(4, -4.5), (16, -3.3), (28, -2.4), (36, -1.2)]), 8), C_["charcoal"],
          bean=1, name="jaw line", trim_after=True)
    d.run(spline(np.array([(-2, 19), (1, 12), (0, 4)]), 8), C_["charcoal"], bean=1,
          name="suture", trim_after=True)
    d.outline(skull, C_["charcoal"], width=1.2, name="skull border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
