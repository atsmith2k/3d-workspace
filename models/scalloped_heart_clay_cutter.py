"""Scalloped heart donut polymer-clay cutter set: a heart with a scalloped edge and a small
heart cut out of the middle, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, an inner blade that cuts the centre heart in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, scalloped-edge heart with a heart window
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    heart outline with a scalloped edge; centre heart cut through (35% of
                the width); 0.45 mm cutting edge; finger flange 2 mm
  tolerances:   cut size +-0.3 mm; blade edge one 0.4 mm-nozzle line

Units: mm. Z is up. Don't scale the STL to resize (it changes blade thickness):
use --set sizes=20,28,36.
"""
import math

import numpy as np
from manifold3d import CrossSection

from cadkit.checks import *
from cadkit.cutter import *
from cadkit.relief import *

DESCRIPTION = "Scalloped heart donut polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Scalloped Heart Donut Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'heart', 'scalloped', 'valentines', 'love', 'donut', 'boho'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def scallop(cs, r, step):
    """Bumps of radius r every `step` along the outer contour of cs."""
    pts = max(cs.to_polygons(), key=len)
    pts = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(6, int(round(s[-1] / step)))
    out = grow(cs, -0.3 * r)
    for d in np.linspace(0, s[-1], n, endpoint=False):
        x = np.interp(d, s, pts[:, 0])
        y = np.interp(d, s, pts[:, 1])
        out += circle(x, y, r)
    return out


def art(p):
    outline = grow(grow(scallop(heart(26), 2.1, 3.7), 0.5), -0.5)
    return Art(outline=outline, cutouts=[heart(9.5).translate((0, 0.8))], bars_x=[0], bars_y=[0.8])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
