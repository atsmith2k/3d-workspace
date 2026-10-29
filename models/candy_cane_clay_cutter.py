"""Candy cane polymer-clay cutter set: a hooked cane with diagonal stripes pressed in, in
three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, recessed imprint blades that press the stripes in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, hooked candy cane with diagonal stripe imprints
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    candy-cane outline (straight stem, round hook); diagonal stripe imprints
                along the stem and radial stripes round the hook, 1.5 mm short of the
                edge; 0.45 mm cutting edge; finger flange 2 mm
  tolerances:   cut size +-0.3 mm; blade edge one 0.4 mm-nozzle line

Units: mm. Z is up. Don't scale the STL to resize (it changes blade thickness):
use --set sizes=22,30,38.
"""
import math

import numpy as np
from manifold3d import CrossSection

from cadkit.checks import *
from cadkit.cutter import *
from cadkit.relief import *

DESCRIPTION = "Candy cane polymer-clay earring cutter set with stripe imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Candy Cane Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'candy cane', 'christmas', 'holiday', 'winter', 'peppermint'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    R = 5.0
    arc = [(R + R * math.cos(a), 6 + R * math.sin(a)) for a in np.linspace(math.pi, 0, 24)]
    path = [(0, -16)] + arc + [(2 * R, 2.5)]
    outline = stroke(path, 5.4)
    stripes = [[(-4, y - 2.4), (4, y + 2.4)] for y in (-13.0, -8.4, -3.8, 0.8)]
    stripes += [[(R + 1.0 * math.cos(a), 6 + 1.0 * math.sin(a)), (R + 9 * math.cos(a), 6 + 9 * math.sin(a))]
                for a in np.radians((150, 90, 30))]
    return Art(outline=outline, imprints=stripes, bars_y=[-6.1])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
