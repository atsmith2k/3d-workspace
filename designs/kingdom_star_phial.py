"""Starlight Phial: a crystal phial of captured starlight in an elven leaf cradle, its light
breaking out in long rays across a pointed-oval night patch.

Spec:
  object:       an elven star-glass, a light for dark places (an original vessel) for
                tees, hoodies, totes, journal covers and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      navy (night), blue (halo), ice (glass, short rays), white (starlight
                core, long rays, stars), silver (stopper, cradle, border): 5 colours
  must have:    a 64 x 94 mm pointed-oval patch, 2.6 mm silver satin border; a 46 mm
                blue halo; eight long white rays and eight short ice rays, tapered
                satins 2.4 -> 0.6 mm; a 16 x 26 mm round-bellied phial in ice with a
                white four-point star of light inside it, a narrow neck and a silver
                stopper; a silver cradle of two curled leaves round its foot; six small
                white stars in the night
  density:      the night is knocked out under the halo, rays and stars, the halo under
                the phial and rays; rays stop 1.0 mm clear of the phial; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _kingdom import C_, SIZES, fit, hoop_for, product, standard_checks, tube, widths_along

DESCRIPTION = "Crystal phial of starlight in an elven leaf cradle, rays across a night patch"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Starlight Phial Embroidery Design",
    "A crystal phial of captured starlight in a silver leaf cradle, its rays breaking across the night",
    ["star glass", "phial", "starlight", "elven", "light in dark places", "magic potion", "lantern",
     "celestial", "night sky", "fantasy gift"],
    "A light for when all other lights go out: a crystal phial holding a captured star, set "
    "in a silver cradle of curled elven leaves, its light breaking out in long rays across a "
    "pointed oval of night sky.\n\n"
    "Great on hoodies, tees, tote bags, journal covers and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 22000)


HW, HH = 32.0, 47.0       # pointed oval half width / half height
BW = 2.6
PX, PY = 0.0, 2.0         # light centre (inside the phial's belly)


def vesica():
    """Two circular arcs meeting in points at top and bottom, then the points eased."""
    R = (HW ** 2 + HH ** 2) / (2 * HW)
    a = math.asin(HH / R)
    t = np.linspace(-a, a, 80)
    right = np.c_[HW - R + R * np.cos(t), R * np.sin(t)]
    left = np.c_[-right[::-1, 0], right[::-1, 1]]
    g = poly(np.vstack([right, left]))
    return g.buffer(-4.0, join_style="round").buffer(4.0, join_style="round")


def phial():
    belly = circle(PX, PY - 2.5, 8.0)
    shoulder = poly([(PX - 6.0, PY + 2.0), (PX - 2.2, PY + 11.0), (PX + 2.2, PY + 11.0), (PX + 6.0, PY + 2.0)])
    neck = rect(4.2, 5.0, PX, PY + 13.0)
    glass = union(belly, shoulder, neck).buffer(0.8).buffer(-0.8)
    stopper = union(rounded_rect(6.4, 2.6, 0.8, PX, PY + 16.4), circle(PX, PY + 19.4, 2.0))
    return glass, stopper


def cradle():
    """Two silver leaves curling up round the phial's foot, from a small knot below it."""
    out = []
    for s in (-1, 1):
        pth = spline([(PX + s * 1.0, PY - 12.0), (PX + s * 6.5, PY - 12.6), (PX + s * 10.2, PY - 8.0),
                      (PX + s * 10.6, PY - 1.0), (PX + s * 8.6, PY + 4.6)], samples=10)
        out.append((pth, widths_along(pth, 1.6, 3.2, 3.0, 2.0, 1.0)))
    knot = ellipse(PX, PY - 13.2, 2.6, 2.0)
    return out, knot


def art():
    d = Design()
    frame = vesica()
    inner = tuck(frame, BW)
    glass, stopper = phial()
    leaves, knot = cradle()
    leaf_area = union(*[tube(p, w) for p, w in leaves], knot)
    vessel = union(glass, stopper, leaf_area)
    halo = circle(PX, PY, 23.0, res=160)

    rays = []
    for i in range(16):
        a = math.radians(90 + i * 22.5)
        long_ = i % 2 == 0
        r1 = (56.0 if long_ else 30.0)
        u = np.array([math.cos(a), math.sin(a)])
        p0 = np.array([PX, PY]) + u * 6.0
        p1 = np.array([PX, PY]) + u * r1
        seg = LineString([tuple(p0), tuple(p1)]).difference(vessel.buffer(1.0)).intersection(inner.buffer(-2.0))
        segs = [seg] if seg.geom_type == "LineString" else list(getattr(seg, "geoms", []))
        segs = [q for q in segs if q.length > 4.0]
        if not segs:
            continue
        q = max(segs, key=lambda q: q.length)
        pts = np.asarray(q.coords)
        if np.linalg.norm(pts[0] - (PX, PY)) > np.linalg.norm(pts[-1] - (PX, PY)):
            pts = pts[::-1]
        pts = np.array([pts[0] + (pts[-1] - pts[0]) * k / 16 for k in range(17)])
        w0 = 2.4 if long_ else 2.0
        rays.append((pts, widths_along(pts, w0, w0 * 0.7, 0.6), "white" if long_ else "ice"))
    ray_area = union(*[tube(p, w) for p, w, _ in rays])
    # fills give way to the rays only past their flat inner ends (no gap at the end)
    from _kingdom import trim_path
    ray_cut = union(*[tube(trim_path(p, 1.2, 0.0), w[1:]) for p, w, _ in rays])
    stars = [star(4, 2.4, 0.75, x, y, rot=90) for x, y in
             ((-11, 33), (11, 31), (-21, 12), (21, -12), (-15, -30), (13, -36))]
    stars = [g for g in stars if inner.buffer(-1.5).contains(g) and not g.intersects(ray_area.buffer(1.0))]

    d.fill(knockout(inner, halo, ray_cut, *stars), C_["navy"], angle=30, name="night")
    d.fill(knockout(halo & inner, vessel, ray_cut), C_["blue"], angle=120, name="halo")
    core = star(4, 6.5, 1.6, PX, PY - 1.0, rot=90).buffer(0.2)
    d.fill(knockout(glass, core, stopper, leaf_area), C_["ice"], angle=60, name="glass")
    for p, w, col in rays:
        if col == "ice":
            d.satin(p, w, C_["ice"], taper=True, underlay="center", name="short ray", trim_after=True)
    d.fill(core, C_["white"], angle=45, name="starlight")
    for p, w, col in rays:
        if col == "white":
            d.satin(p, w, C_["white"], taper=True, underlay="center", name="long ray", trim_after=True)
    for g in stars:
        d.fill(g, C_["white"], angle=45, name="star")
    d.fill(stopper, C_["silver"], angle=0, name="stopper")
    d.fill(knot, C_["silver"], angle=90, name="cradle knot")
    for p, w in leaves:
        d.satin(p, w, C_["silver"], taper=True, underlay="center", name="cradle leaf", trim_after=True)
    d.outline(frame, C_["silver"], width=BW, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
