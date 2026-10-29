"""Mitten polymer-clay cutter set: a winter mitten with a ribbed cuff pressed in, in three
sizes with a pusher for each. Flip one piece over for a matching pair.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, recessed imprint blades that press the cuff seam and ribbing in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, mitten with thumb, cuff seam and cuff ribbing imprints
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    mitten outline with thumb and cuff; cuff seam and three ribbing lines
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

DESCRIPTION = "Mitten polymer-clay earring cutter set with ribbed cuff imprint, 3 sizes with pushers"

PRODUCT = dict(
    title="Winter Mitten Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'mitten', 'winter', 'christmas', 'holiday', 'cozy'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def art(p):
    hand = ellipse(1.5, 3.0, 7.2, 10.0) + poly([(-5.7, -9.5), (8.7, -9.5), (8.7, 2), (-5.7, 2)])
    thumb = ellipse(0, 0, 2.8, 5.2).rotate(32).translate((-6.6, -0.2))
    cuff = poly([(-7.0, -16), (10.0, -16), (10.0, -8.6), (-7.0, -8.6)])
    outline = grow(grow(grow(grow(hand + thumb + cuff, -0.8), 0.8), 0.9), -0.9)
    seam = [(-9, -8.6), (12, -8.6)]
    ribs = [[(x, -8.6), (x, -18)] for x in (-2.5, 1.5, 5.5)]
    return Art(outline=outline, imprints=[seam] + ribs, bars_x=[1.5], bars_y=[-1.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
