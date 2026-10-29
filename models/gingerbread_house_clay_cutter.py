"""Gingerbread house polymer-clay cutter set: a house with a chimney, two windows and a
round attic window cut out, with an icing line under the eaves and a door pressed in, in
three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, inner blades that cut the three windows and recessed imprint blades that press the icing and door in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, gingerbread house with chimney, three windows, icing and door imprints
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    house outline with pitched roof and chimney; two square windows and a
                round attic window cut through; scalloped icing line and arched door
                imprinted 1.5 mm short of the edge; 0.45 mm cutting edge; finger flange
                2 mm
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

DESCRIPTION = "Gingerbread house polymer-clay earring cutter set with windows and icing, 3 sizes with pushers"

PRODUCT = dict(
    title="Gingerbread House Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'gingerbread', 'gingerbread house', 'christmas', 'holiday', 'winter'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    walls = poly([(-10, -12), (10, -12), (10, 4), (-10, 4)])
    roof = poly([(-13.5, 2.5), (13.5, 2.5), (0, 15)])
    chimney = poly([(5, 6), (8.6, 6), (8.6, 14), (5, 14)])
    outline = grow(grow(grow(grow(walls + roof + chimney, -0.6), 0.6), 0.4), -0.4)
    windows = (poly([(-7.4, -3.4), (-2.8, -3.4), (-2.8, 1.2), (-7.4, 1.2)])
               + poly([(2.8, -3.4), (7.4, -3.4), (7.4, 1.2), (2.8, 1.2)])
               + circle(0, 7.6, 2.1))
    # scalloped icing just under the eaves, both slopes
    t = np.linspace(0, 1, 60)
    icing = []
    for x0, x1 in ((-14.5, 0.0), (0.0, 14.5)):
        x = x0 + (x1 - x0) * t
        y = 15 - 12.5 * np.abs(x) / 13.5 - 2.3 - 0.55 * np.abs(np.sin(np.pi * 5 * t))
        icing.append(np.column_stack([x, y]))
    door = [(-2.8, -13), (-2.8, -7.5)] + [(2.8 * math.cos(a), -7.5 + 2.8 * math.sin(a))
                                          for a in np.linspace(math.pi, 0, 12)] + [(2.8, -13)]
    return Art(outline=outline, cutouts=[windows], imprints=icing + [door],
               bars_x=[0], bars_y=[-1.1])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
