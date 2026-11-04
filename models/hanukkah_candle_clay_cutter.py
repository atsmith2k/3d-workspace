"""Hanukkah candle polymer-clay cutter set: a single candle with a teardrop flame on top
(one outline) and a wavy wax-drip line pressed across the top of the candle, for dangle
earrings, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports.

Spec:
  object:       polymer-clay cutter set, candle with teardrop flame, wax-drip imprint
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm
                larger (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    candle with a teardrop flame in one outline; wavy drip line imprint
                1.5 mm short of the cutting edge; 0.45 mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Hanukkah candle with flame polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Hanukkah Candle Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings',
          'cutter set', 'hanukkah', 'chanukah', 'judaica', 'candle', 'flame', 'menorah', 'festival of lights', 'holiday'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    wax = poly([(-4.5, -16.0), (4.5, -16.0), (4.5, 3.0), (-4.5, 3.0)])
    flame = CrossSection.batch_hull([circle(0, 6.4, 3.2), circle(0, 13.5, 0.4)])
    outline = grow(grow(grow(grow(wax + flame, -0.6), 0.6), 0.8), -0.8)
    xs = np.linspace(-6, 6, 25)
    drip = np.c_[xs, 0.2 - 1.1 * (1 + np.cos(xs * math.pi / 3.0)) / 2 - 0.9 * (np.abs(xs) < 1.5)]
    return Art(outline=outline, imprints=[drip], bars_x=[0], bars_y=[-8.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
