"""Scalloped circle donut polymer-clay cutter set: a twelve-scallop round with its centre
cut out, an evergreen statement-earring shape, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, an inner blade that cuts the centre out in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, twelve-scallop circle with a round centre cut out
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    twelve-scallop round outline; centre hole cut through (40% of the
                width); 0.45 mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Scalloped circle donut polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Scalloped Circle Donut Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'scalloped', 'circle', 'donut', 'hoop', 'minimal', 'boho', 'geometric'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def art(p):
    ring = circle(0, 0, 11.0)
    for k in range(12):
        a = math.radians(30 * k)
        ring += circle(11.0 * math.cos(a), 11.0 * math.sin(a), 3.1)
    outline = grow(grow(ring, 0.5), -0.5)
    return Art(outline=outline, cutouts=[circle(0, 0, 5.6)], bars_x=[0], bars_y=[0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
