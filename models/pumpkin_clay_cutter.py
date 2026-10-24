"""1 in (25.4 mm) jack-o'-lantern clay cutter for polymer clay sheets, plus a matching pusher.

Three kinds of blade, all sharing the same back plane:
  - outer blade: cuts the pumpkin silhouette (body lobes + curled stem)
  - cut-through inner blades: triangle eyes, nose and toothy grin, removed from the piece
  - imprint blades: pumpkin rib lines and a stem line, `imprint_recess` shorter than the
    cutting edge so they only press a groove into the clay instead of cutting through

Blade profile follows the 0.4 mm nozzle rule (walls at multiples of the 0.45 mm line
width): the outer blade is 1.35 mm at the base, inner and imprint blades 0.9 mm, and all
taper over the top `taper_h` to a 0.45 mm single-line edge. The cutting face is vertical
on the keep side (the piece) and the taper sits on the waste side.

The inner blades are held by three support bars across the back (`bar_h` tall). They sit
well back from the clay, so they never show in the cut piece, and the back stays open so
the pusher's prongs can pop the piece out between the bars.

Print orientation: back plane and finger flange on the bed, cutting edge up. No overhangs,
no supports. The pusher prints plate-down, prongs up, and slides into the back of the
cutter without flipping.

Don't scale the STL to resize: that changes blade thickness. Use --set size=... instead.
"""
import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

from cadkit.relief import *

DESCRIPTION = "1 in jack-o'-lantern clay cutter with face cutouts, rib imprints and matching pusher"

PARAMS = dict(
    size=25.4,            # longest side of the cut pumpkin (stem tip to base / lobe to lobe)
    height=12.0,          # back plane to cutting edge
    tip=0.45,             # cutting edge thickness (one 0.4 mm-nozzle line)
    outer_base=1.35,      # outer blade thickness below the taper (3 lines)
    inner_base=0.9,       # cut-through and imprint blade thickness below the taper (2 lines)
    taper_h=4.0,          # height of the tapered zone at the top of every blade
    imprint_recess=1.5,   # imprint blades stop this far short of the cutting edge
    flange_w=2.0,         # finger flange outside the outer blade
    flange_t=1.6,
    bar_w=1.8,            # support bars across the back
    bar_h=3.0,
    pusher=True,
    pusher_clearance=0.3,  # per side, between prongs and blades/bars
    pusher_plate=2.4,
)

SEG = 72  # segments per circle for rounded offsets


def off(cs, d):
    return cs.offset(d, JoinType.Round, 2.0, SEG) if d else cs


def rect(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def rounded(cs, r):
    """Round convex then concave corners by r."""
    return off(off(off(off(cs, -r), r), r), -r)


def slices(make, z0, z1, steps, top_extra=0.0):
    """Stack of extruded slices from z0 to z1. make(f) gives the section, f in (0, 1],
    f = 1 being the top slice. Slices overlap 0.05 mm so they fuse; the top slice can
    run past z1 by top_extra (for cutting tools)."""
    out = Manifold()
    h = (z1 - z0) / steps
    for k in range(steps):
        cs = make((k + 1) / steps).simplify(0.002)
        if cs.is_empty():
            continue
        top = z0 + (k + 1) * h + (0.05 if k < steps - 1 else top_extra)
        out += Manifold.extrude(cs, top - (z0 + k * h)).translate((0, 0, z0 + k * h))
    return out


def prism(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate((0, 0, z0))


# ---- artwork, drawn in a ~26 mm frame and scaled to `size` ----

def pumpkin_art():
    body = (ellipse(0, 0, 5.6, 9.6)
            + mirror_x(ellipse(4.8, -0.2, 6.2, 9.2))
            + mirror_x(ellipse(8.0, -0.6, 5.0, 8.0)))
    stem = smooth_shape([(-1.7, 7.6), (-1.6, 10.8), (-1.0, 13.0), (0.2, 14.5), (1.9, 15.0),
                         (2.6, 14.4), (1.5, 13.2), (1.3, 11.0), (1.8, 7.6)], samples=16)
    outline = body + stem

    eye = poly([(-7.6, 1.2), (-1.6, 1.2), (-4.9, 5.8)])
    eyes = eye + eye.mirror((1, 0))
    nose = poly([(-1.9, -1.8), (1.9, -1.8), (0, 1.0)])
    xs = np.linspace(-8.2, 8.2, 60)
    mouth = poly(np.r_[np.c_[xs, -3.7 + 0.03 * xs ** 2],
                       np.c_[xs[::-1], -7.4 + 0.05 * xs[::-1] ** 2]])
    mouth = mouth - rect(-3.4, -5.4, -1.3, -2.0) - rect(1.3, -9.0, 3.4, -5.7)
    face = [eyes, nose, mouth]

    ribs = [bezier((s * 9.0, 6.6), (s * 11.6, -0.6), (s * 9.0, -7.2), n=24) for s in (1, -1)]
    ribs.append(bezier((0.05, 9.4), (0.15, 11.4), (0.3, 13.2), n=10))
    bar_ys = [3.2, -5.6]  # through the eyes and the mouth; plus a vertical bar at x=0
    return outline, face, ribs, bar_ys


def build(p):
    outline, face, ribs, bar_ys = pumpkin_art()
    outline = off(off(outline, 0.7), -0.7)  # soften the notches between lobes and stem
    x0, y0, x1, y1 = outline.bounds()
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    s = p.size / max(x1 - x0, y1 - y0)
    xf = lambda cs: cs.translate((-c[0], -c[1])).scale((s, s))

    O = xf(outline)
    F = rounded(xf(face[0]), 0.4) + rounded(xf(face[1]), 0.35) + rounded(xf(face[2]), 0.3)
    rib_paths = [(np.asarray(r) - c) * s for r in ribs]
    H, T = p.height, p.taper_h
    zt = H - T
    steps = max(4, int(round(T / 0.2)))
    lerp = lambda a, b, f: a + (b - a) * f

    # outer blade + finger flange, inner face exactly on the outline
    outer = (prism(off(O, p.outer_base + p.flange_w), 0, p.flange_t)
             + prism(off(O, p.outer_base), p.flange_t - 0.1, zt + 0.05)  # starts inside the flange
             + slices(lambda f: off(O, lerp(p.outer_base, p.tip, f)), zt, H, steps))
    outer -= prism(O, -1, H + 1)

    # cut-through blades for the face, growing inward (waste side)
    inner = prism(F, 0, H)
    inner -= prism(off(F, -p.inner_base), -1, zt + 0.05)
    inner -= slices(lambda f: off(F, -lerp(p.inner_base, p.tip, f)), zt, H, steps, top_extra=1.0)

    # imprint blades: symmetric taper, stopping imprint_recess short of the edge
    Hr = H - p.imprint_recess
    imprint = Manifold()
    for path in rib_paths:
        imprint += prism(stroke(path, p.inner_base), 0, Hr - T + 0.05)
        imprint += slices(lambda f, path=path: stroke(path, lerp(p.inner_base, p.tip, f)),
                          Hr - T, Hr, steps)

    # support bars, ends buried mid-way into the outer blade wall
    by = [(y - c[1]) * s for y in bar_ys]
    big = p.size
    strips = rect(-p.bar_w / 2, -big, p.bar_w / 2, big)
    for y in by:
        strips += rect(-big, y - p.bar_w / 2, big, y + p.bar_w / 2)
    bars_cs = strips ^ off(O, p.outer_base / 2)
    bars = prism(bars_cs, 0, p.bar_h)

    cutter = outer + inner + imprint + bars
    if not p.pusher:
        return cutter

    # pusher: prongs fill every open gap in the back, clear of blades and bars
    clr = p.pusher_clearance
    ribs_cs = CrossSection()
    for path in rib_paths:
        ribs_cs += stroke(path, p.inner_base)
    blocked = off(F + ribs_cs + bars_cs, clr)
    room = (off(O, -clr) - blocked) + (off(F, -p.inner_base - clr) - off(bars_cs, clr))
    room = off(off(room, -0.6), 0.6)  # drop slivers too thin to print as a 12 mm prong
    prongs = CrossSection()
    for piece in room.decompose():
        if piece.area() >= 3.0:
            prongs += piece
    plate = off(O, p.outer_base + p.flange_w)
    pusher = (prism(plate, 0, p.pusher_plate)
              + prism(prongs, p.pusher_plate - 0.1, p.pusher_plate + H - 0.2))
    return {"cutter": cutter, "pusher": pusher}
