"""1 in (25.4 mm) jack-o'-lantern clay cutter for polymer clay sheets, plus a matching pusher.

Three kinds of blade, all sharing the same back plane:
  - outer blade: cuts the pumpkin silhouette (body lobes + curled stem)
  - cut-through inner blades: triangle eyes, nose and toothy grin, removed from the piece
  - imprint blades: pumpkin rib lines and a stem line, `imprint_recess` shorter than the
    cutting edge so they only press a groove into the clay instead of cutting through

Blade profile follows the 0.4 mm nozzle rule (walls at multiples of the 0.45 mm line
width): the outer blade is 1.35 mm at the base, inner and imprint blades 0.9 mm, and all
taper over the top `taper_h` to a 0.45 mm single-line edge. The cutting face is vertical
on the keep side (the piece) and the taper sits on the waste side as a straight bevel
(blades and pusher are built by `cadkit.cutter`).

The inner blades are held by three support bars across the back (`bar_h` tall). They sit
well back from the clay, so they never show in the cut piece, and the back stays open so
the pusher's prongs can pop the piece out between the bars.

Print orientation: back plane and finger flange on the bed, cutting edge up. No overhangs,
no supports. The pusher prints plate-down, prongs up, and slides into the back of the
cutter without flipping.

Don't scale the STL to resize: that changes blade thickness. Use --set size=... instead.
"""
import numpy as np
from manifold3d import JoinType

from cadkit.relief import *
from cadkit.cutter import Art, _cutter

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
    by = [(y - c[1]) * s for y in bar_ys]

    # blades, bars and pusher come from cadkit.cutter (exact ruled bevels); the art is
    # already at final size and centred, so _cutter's own scaling is 1
    art = Art(outline=O, cutouts=[F], imprints=rib_paths, bars_x=[0.0], bars_y=by, cut_round=0)
    cutter, pusher = _cutter(art, max(O.bounds()[2] - O.bounds()[0], O.bounds()[3] - O.bounds()[1]), p)
    if not p.pusher:
        return cutter
    return {"cutter": cutter, "pusher": pusher}
