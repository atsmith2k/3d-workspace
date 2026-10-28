"""Monstera leaf polymer-clay cutter set: a split-leaf monstera with its edge slits and a
midrib imprint, a year-round boho earring shape, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, a midrib imprint blade 1.5 mm shorter than the edge so it presses a groove without cutting through, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, monstera leaf with edge slits and a midrib imprint
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    leaf outline with six edge slits; midrib imprint from the stem notch;
                0.45 mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Monstera leaf polymer-clay earring cutter set with slits and midrib, 3 sizes with pushers"

PRODUCT = dict(
    title="Monstera Leaf Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'monstera', 'leaf', 'boho', 'botanical', 'tropical'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    # broad leaf, stem notch at the bottom, tip leaning slightly right
    leaf = smooth_shape([(0, -12.6), (-3.0, -14.6), (-8.8, -13.2), (-13.4, -7.6), (-14.6, 0.0),
                         (-12.6, 7.6), (-7.4, 13.0), (0.6, 15.2), (7.8, 12.6), (12.8, 6.8),
                         (14.6, -0.6), (13.2, -7.8), (8.6, -13.2), (3.0, -14.6)], samples=18)
    slits = CrossSection()
    for side, ys in ((-1, (-6.5, 0.0, 6.5)), (1, (-4.0, 2.8, 9.0))):
        for y in ys:
            slits += stroke([(side * 4.2, y), (side * 18.0, y + 6.0)], 2.6)
    outline = grow(grow(leaf - slits, 0.6), -0.6)
    midrib = [bezier((0, -16.0), (0.8, -2.0), (0.6, 11.0), n=20)]
    return Art(outline=outline, imprints=midrib, bars_y=[-1.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def build(p):
    return cutter_set(art(p), p)
