"""Strawberry polymer-clay cutter set: a plump strawberry with a leafy calyx and stem, the
calyx line pressed in, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, a recessed imprint blade that presses the calyx line in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, strawberry with leafy calyx, stem and calyx-line imprint
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    strawberry outline with five-leaf calyx and stem; zigzag calyx line
                imprinted 1.5 mm short of the edge; 0.45 mm cutting edge; finger flange
                2 mm
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

DESCRIPTION = "Strawberry polymer-clay earring cutter set with calyx imprint, 3 sizes with pushers"

PRODUCT = dict(
    title="Strawberry Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'strawberry', 'fruit', 'summer', 'valentines', 'cottagecore'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def art(p):
    berry = smooth_shape([(0, -13), (6.5, -7), (9.8, 1), (8.4, 6.6), (0, 7.6), (-8.4, 6.6),
                          (-9.8, 1), (-6.5, -7)])
    calyx = CrossSection()
    for a in (-70, -35, 0, 35, 70):
        calyx += ellipse(0, 4.0, 1.9, 4.2).rotate(a).translate((0, 6.4))
    stem = stroke([(0, 8), (1.0, 13.2)], 2.0)
    outline = grow(grow(berry + calyx + stem, 0.6), -0.6)
    xs = np.linspace(-11, 11, 13)
    line = np.column_stack([xs, 5.0 - 1.3 * (np.arange(13) % 2)])
    return Art(outline=outline, imprints=[line], bars_x=[0], bars_y=[-3])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
