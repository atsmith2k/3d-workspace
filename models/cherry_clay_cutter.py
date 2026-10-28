"""Cherry pair polymer-clay cutter set: two cherries on joined stems with a leaf, the gap
between the stems cut out, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, an inner blade that cuts the gap between the stems in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, two cherries on joined stems with a leaf
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    two round cherries, two curved stems meeting at the top, one leaf; the
                window between the stems cut through; 0.45 mm cutting edge; finger
                flange 2 mm
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

DESCRIPTION = "Cherry pair polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Cherry Pair Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'cherry', 'cherries', 'fruit', 'valentines', 'summer', 'retro'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    berries = circle(-6.4, -8, 6.0) + circle(6.4, -8, 6.0)
    stems = (stroke(bezier((-6.0, -2.6), (-3.6, 5.0), (0.6, 10.5)), 2.8)
             + stroke(bezier((6.0, -2.6), (3.0, 4.0), (0.6, 10.5)), 2.8))
    leaf = ellipse(0, 0, 6.0, 2.7).rotate(20).translate((5.6, 12.2))
    shape = grow(grow(berries + stems + leaf, 0.7), -0.7)
    outer = poly(max(shape.to_polygons(), key=len))
    window = outer - shape           # the gap the stems enclose
    return Art(outline=outer, cutouts=[window], bars_x=[0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
