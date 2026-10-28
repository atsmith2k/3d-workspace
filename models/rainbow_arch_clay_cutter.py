"""Rainbow arch polymer-clay cutter set: the boho arch earring shape with two imprint
blades that press the rainbow bands into the clay, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, imprint blades 1.5 mm shorter than the edge so they press the bands without cutting through, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, rainbow arch with band imprints
  overall:      cut pieces 20, 28 and 36 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    half-round arch outline with a flat base; two concentric band imprints
                pressed 1.5 mm shallower than the cut; 0.45 mm cutting edge; finger flange 2 mm
  tolerances:   cut size +-0.3 mm; blade edge one 0.4 mm-nozzle line

Units: mm. Z is up. Don't scale the STL to resize (it changes blade thickness):
use --set sizes=18,26,34.
"""
import math

import numpy as np
from manifold3d import CrossSection

from cadkit.checks import *
from cadkit.cutter import *
from cadkit.relief import *

DESCRIPTION = "Rainbow arch polymer-clay earring cutter set with band imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Rainbow Arch Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'rainbow', 'arch', 'boho'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS)


def arc(r, y0=-3.0, n=48):
    t = np.linspace(0, math.pi, n)
    return np.r_[[(r, y0)], np.c_[r * np.cos(t), r * np.sin(t)], [(-r, y0)]]


def art(p):
    outline = circle(0, 0, 15) ^ poly([(-16, 0), (16, 0), (16, 16), (-16, 16)])
    outline = grow(grow(outline, -1.0), 1.0)    # soften the two base corners
    return Art(outline=outline, imprints=[arc(10.3), arc(5.6)])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
