"""Snowflake polymer-clay cutter set: a six-armed snowflake with branched arms and a
hexagon window cut out of the centre, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, an inner blade that cuts the centre window in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, six-armed branched snowflake with a hexagon centre window
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    six arms with two side branches each; hexagon centre cut through; 0.45
                mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Snowflake polymer-clay earring cutter set with hexagon centre window, 3 sizes with pushers"

PRODUCT = dict(
    title="Snowflake Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'snowflake', 'winter', 'christmas', 'holiday', 'frozen'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def hexagon(r, rot=0.0):
    return poly([(r * math.cos(math.radians(rot + 60 * k)), r * math.sin(math.radians(rot + 60 * k)))
                 for k in range(6)])


def art(p):
    flake = hexagon(6.0, 30)
    for k in range(6):
        a = math.radians(90 + 60 * k)
        u = np.array([math.cos(a), math.sin(a)])
        flake += stroke([(0, 0), tuple(14.5 * u)], 4.0)
        for side in (-1, 1):
            b = a + side * math.radians(48)
            root = 8.0 * u
            flake += stroke([tuple(root), tuple(root + 5.2 * np.array([math.cos(b), math.sin(b)]))], 3.0)
    outline = grow(grow(flake, 0.7), -0.7)
    return Art(outline=outline, cutouts=[hexagon(2.6, 30)], bars_x=[0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
