"""Bumblebee polymer-clay cutter set: a round bee with two wings, a window in each wing and
body stripes pressed in, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, inner blades that cut the wing windows and recessed imprint blades that press the stripes in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, bumblebee with two wings, wing windows and stripe imprints
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    oval body with head and stinger, two upper wings; a window cut through
                each wing; two stripe imprints 1.5 mm short of the edge; 0.45 mm cutting
                edge; finger flange 2 mm
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

DESCRIPTION = "Bumblebee polymer-clay earring cutter set with wing windows and stripes, 3 sizes with pushers"

PRODUCT = dict(
    title="Bumblebee Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'bee', 'bumblebee', 'honey', 'spring', 'summer', 'garden'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def art(p):
    body = ellipse(0, -2.0, 6.4, 8.6) + circle(0, 7.2, 3.8)
    sting = poly([(-2.2, -9.6), (2.2, -9.6), (0, -12.6)])
    wings = mirror_x(ellipse(0, 0, 5.6, 3.9).rotate(28).translate((6.4, 6.0)))
    outline = grow(grow(grow(grow(body + sting + wings, -0.4), 0.4), 0.9), -0.9)
    windows = mirror_x(ellipse(0, 0, 3.2, 1.9).rotate(28).translate((7.0, 6.3)))
    stripes = [[(-8, y), (8, y)] for y in (-0.6, -5.0)]
    return Art(outline=outline, cutouts=[windows], imprints=stripes, bars_y=[6.2])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
