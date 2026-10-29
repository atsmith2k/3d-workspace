"""Christmas bauble polymer-clay cutter set: a round ornament with a cap and hanging loop,
a pin that punches the jump-ring hole, and two zigzag bands pressed across it, in three
sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, a pin that punches the jump-ring hole and recessed imprint blades that press the zigzag bands in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, round Christmas bauble with cap, punched hanging hole and two zigzag band imprints
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    round bauble outline with cap and loop; jump-ring hole punched through
                the loop; two zigzag band imprints 1.5 mm short of the edge; 0.45 mm
                cutting edge; finger flange 2 mm
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

DESCRIPTION = "Christmas bauble polymer-clay earring cutter set with hole punch and band imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Christmas Bauble Ornament Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'christmas', 'ornament', 'bauble', 'holiday', 'winter'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def art(p):
    cap = poly([(-3.8, 10.5), (3.8, 10.5), (3.8, 14.6), (-3.8, 14.6)])
    outline = grow(grow(circle(0, 0, 12) + cap + circle(0, 16.6, 3.9), 0.8), -0.8)
    zigs = []
    for yc in (3.4, -3.4):
        xs = np.linspace(-14, 14, 15)
        zigs.append(np.column_stack([xs, yc + 1.1 * (-1) ** np.arange(15)]))
    return Art(outline=outline, cutouts=[circle(0, 16.6, 1.7)], imprints=zigs, bars_x=[0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
