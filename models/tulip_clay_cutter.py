"""Tulip polymer-clay cutter set: a three-petal tulip head with imprint blades that
mark the petals, for spring and Easter earrings, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, imprint blades 1.5 mm shorter than the edge so they press the petal lines without cutting through, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, three-petal tulip head with petal imprints
  overall:      cut pieces 20, 28 and 36 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    tulip outline with three rounded petal tips; two petal imprint lines; 0.45 mm
                cutting edge; finger flange 2 mm
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

DESCRIPTION = "Tulip polymer-clay earring cutter set with petal imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Tulip Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'tulip', 'flower', 'spring', 'easter'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS)


def art(p):
    outline = smooth_shape([(0, -14.5), (6.5, -12.0), (10.0, -5.0), (10.6, 3.0), (10.2, 13.5),
                            (6.6, 9.0), (4.2, 6.6), (2.2, 10.5), (0, 14.5), (-2.2, 10.5),
                            (-4.2, 6.6), (-6.6, 9.0), (-10.2, 13.5), (-10.6, 3.0),
                            (-10.0, -5.0), (-6.5, -12.0)], samples=18)
    lines = [bezier((0, -16), (s * 1.5, -2), (s * 4.4, 7.6), n=24) for s in (1, -1)]
    return Art(outline=outline, imprints=lines)


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def build(p):
    return cutter_set(art(p), p)
