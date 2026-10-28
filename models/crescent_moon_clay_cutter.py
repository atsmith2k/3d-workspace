"""Crescent moon polymer-clay cutter set: a crescent with a star cut out of it, for
celestial earrings, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, an inner blade that cuts the star out in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, crescent moon with a five-point star cut out
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    crescent outline; five-point star cut through the wide part; 0.45 mm cutting
                edge; finger flange 2 mm
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

DESCRIPTION = "Crescent moon with star cutout polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Crescent Moon and Star Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'moon', 'crescent', 'star', 'celestial', 'boho'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


STAR_AT = (-8.9, -4.7)   # middle of the crescent's widest part


def star(cx, cy, r_out, r_in, n=5):
    a = math.pi / 2 + math.pi * np.arange(2 * n) / n
    r = np.where(np.arange(2 * n) % 2, r_in, r_out)
    return poly(np.c_[cx + r * np.cos(a), cy + r * np.sin(a)])


def art(p):
    outline = circle(0, 0, 15) - circle(6.5, 3.5, 12.6)
    outline = grow(grow(outline, -0.8), 0.8)     # round the horn tips
    return Art(outline=outline, cutouts=[star(*STAR_AT, 4.1, 1.9)], cut_round=0.2,
               bars_x=[STAR_AT[0]], bars_y=[STAR_AT[1]])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def build(p):
    return cutter_set(art(p), p)
