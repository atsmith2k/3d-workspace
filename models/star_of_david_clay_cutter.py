"""Star of David polymer-clay cutter set: a six-point star with a smaller star cut out
of the centre, so it makes an open star earring, in three sizes with a pusher for each.
An inner blade cuts the window in the same press.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports.

Spec:
  object:       polymer-clay cutter set, open Star of David (hexagram outline, star window cut through)
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm
                larger (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    hexagram outline with softly rounded points; star window cut through
                leaving an even rim (~2.4 mm at 24 mm); 0.45 mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Open Star of David polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Star of David Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings',
          'cutter set', 'hanukkah', 'chanukah', 'judaica', 'star of david', 'magen david', 'star', 'holiday'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0), rim=3.0)   # rim in art units (star ~30 wide)


def triangle(r, rot):
    return poly([(r * math.cos(math.radians(rot + 120 * k)), r * math.sin(math.radians(rot + 120 * k)))
                 for k in range(3)])


def art(p):
    star = triangle(15.0, 90) + triangle(15.0, -90)
    outline = grow(grow(star, -0.9), 0.9)              # round the six points
    k = 1 - 2 * p.rim / 15.0                          # homothetic star: every edge moves in by rim
    window = triangle(15.0 * k, 90) + triangle(15.0 * k, -90)
    return Art(outline=outline, cutouts=[window], cut_round=0.3, bars_x=[0], bars_y=[0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
