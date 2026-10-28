"""Toadstool mushroom polymer-clay cutter set: a domed cap on a flared stem with three
round spots cut out and the gill line pressed in, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, inner blades that cut the three spots and a recessed imprint blade for the gill line in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, toadstool mushroom with three spot windows and a gill-line imprint
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    domed cap on a flared stem; three round spots cut through the cap; gill
                line imprinted 1.5 mm short of the edge; 0.45 mm cutting edge; finger
                flange 2 mm
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

DESCRIPTION = "Toadstool mushroom polymer-clay earring cutter set with spot windows, 3 sizes with pushers"

PRODUCT = dict(
    title="Toadstool Mushroom Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'mushroom', 'toadstool', 'cottagecore', 'woodland', 'fall', 'botanical'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def art(p):
    cap = ellipse(0, 0, 13.0, 10.5) ^ poly([(-14, -1.5), (14, -1.5), (14, 11), (-14, 11)])
    stem = smooth_shape([(-3.6, -1), (3.6, -1), (4.2, -8), (5.2, -13), (0, -14.2), (-5.2, -13), (-4.2, -8)])
    outline = grow(grow(grow(grow(cap + stem, -0.8), 0.8), 0.8), -0.8)
    spots = circle(-6.0, 4.6, 2.3) + circle(1.8, 6.3, 2.1) + circle(7.6, 4.0, 2.0)
    gills = [(-15, -0.2), (15, -0.2)]
    return Art(outline=outline, cutouts=[spots], imprints=[gills], bars_y=[5.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
