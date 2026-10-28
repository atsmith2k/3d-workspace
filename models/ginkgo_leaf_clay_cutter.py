"""Ginkgo leaf polymer-clay cutter set: a fan-shaped ginkgo leaf with its centre notch,
stem and radial veins pressed in, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, recessed imprint blades that press the veins in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, ginkgo fan leaf with centre notch, stem and vein imprints
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    fan leaf with a wavy rim and a centre notch, curved stem; seven radial
                vein imprints 1.5 mm short of the edge; 0.45 mm cutting edge; finger
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

DESCRIPTION = "Ginkgo leaf polymer-clay earring cutter set with vein imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Ginkgo Leaf Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'ginkgo', 'leaf', 'botanical', 'boho', 'fall', 'nature'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    c, R = (0.0, -5.0), 15.5
    angs = np.radians(np.linspace(22, 158, 48))
    rim = [(c[0] + (R + 0.7 * math.sin(6 * a)) * math.cos(a), c[1] + (R + 0.7 * math.sin(6 * a)) * math.sin(a))
           for a in angs]
    fan = poly([c] + rim)
    notch = poly([(0, 2.5), (3.2, 12), (-3.2, 12)])
    stem = stroke(bezier((0, -4), (0.4, -11), (2.6, -16)), 2.3)
    outline = grow(grow(grow(grow(fan - notch, -0.5), 0.5), 0.6), -0.6) + stem
    outline = grow(grow(outline, 0.6), -0.6)
    veins = []
    for a in np.radians((36, 54, 72, 108, 126, 144)):
        veins.append([(c[0] + 5.5 * math.cos(a), c[1] + 5.5 * math.sin(a)),
                      (c[0] + 20 * math.cos(a), c[1] + 20 * math.sin(a))])
    veins.append([(0, -6), (0, 10)])
    return Art(outline=outline, imprints=veins)


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
