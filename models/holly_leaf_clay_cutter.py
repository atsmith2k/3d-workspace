"""Holly leaf polymer-clay cutter set: a spiky holly leaf with a midrib and veins pressed
in, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, recessed imprint blades that press the midrib and veins in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, spiky holly leaf with stem, midrib and vein imprints
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    holly-leaf outline with three spikes per side and a stem; midrib and six
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

DESCRIPTION = "Holly leaf polymer-clay earring cutter set with vein imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Holly Leaf Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'holly', 'leaf', 'christmas', 'holiday', 'winter', 'botanical'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    L, W = 15.0, 8.5
    w = lambda t: W * math.sin(math.pi * t) ** 0.8
    y = lambda t: -L + 2 * L * t
    right, spikes = [(0, -L)], []
    for k in range(4):
        ts, t1 = k / 4 + 0.125, (k + 1) / 4
        if k < 3:
            right.append((0.68 * w(ts), y(ts)))                 # notch
            s = (w(t1) + 1.6, y(t1) - 0.6)
            right.append(s)                                     # spike
            spikes.append(s)
        else:
            right.append((0.68 * w(ts), y(ts)))
    right.append((0, L + 1.5))
    pts = right + [(-x, yy) for x, yy in reversed(right[1:-1])]
    outline = grow(grow(poly(pts) + stroke([(0, -L + 1), (0, -L - 4.5)], 2.4), -0.45), 0.45)
    veins = [[(0, -L - 6), (0, L + 3)]]
    for sx, sy in spikes:
        for m in (1, -1):
            veins.append([(0, sy - 4.0), (m * (sx + 1), sy + 0.4)])
    return Art(outline=outline, imprints=veins)


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
