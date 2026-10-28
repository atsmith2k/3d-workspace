"""Butterfly polymer-clay cutter set: a butterfly with a window cut into each upper wing,
in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, inner blades that cut both wing windows in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, butterfly with two upper-wing windows
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    four-wing butterfly outline with body; an oval window cut through each upper wing;
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

DESCRIPTION = "Butterfly polymer-clay earring cutter set with wing windows, 3 sizes with pushers"

PRODUCT = dict(
    title="Butterfly Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'butterfly', 'spring', 'garden'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    wings = (mirror_x(ellipse(0, 0, 8.0, 6.2).rotate(28).translate((7.4, 4.4)))
             + mirror_x(ellipse(0, 0, 5.6, 4.6).rotate(-32).translate((5.6, -6.0))))
    body = ellipse(0, -0.5, 1.9, 9.5)
    outline = grow(grow(wings + body, 0.8), -0.8)
    windows = mirror_x(ellipse(0, 0, 4.3, 2.8).rotate(28).translate((8.2, 5.0)))
    return Art(outline=outline, cutouts=[windows], bars_x=[0], bars_y=[5.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
