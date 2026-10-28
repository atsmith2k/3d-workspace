"""Easter egg polymer-clay cutter set: an egg with a zigzag band pressed across it, in
three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, imprint blades 1.5 mm shorter than the edge so they press the band without cutting through, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, egg with a zigzag band imprint
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    egg outline (narrow end up); two band lines and a zigzag imprinted between them;
                0.45 mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Easter egg polymer-clay earring cutter set with zigzag band imprint, 3 sizes with pushers"

PRODUCT = dict(
    title="Easter Egg Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'easter', 'egg', 'spring', 'zigzag'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))


def egg(rx=11.0, ry=15.0, k=0.16, n=200):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return poly(np.c_[rx * np.cos(t) * (1 - k * np.sin(t)), ry * np.sin(t)])


def art(p):
    lo, hi = -3.6, 2.4
    xs = np.arange(-13.5, 13.6, 3.0)
    zig = np.c_[xs, np.where(np.arange(len(xs)) % 2, hi, lo)]
    band = [np.array([(-14, lo), (14, lo)]), np.array([(-14, hi), (14, hi)]), zig]
    return Art(outline=egg(), imprints=band)


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def build(p):
    return cutter_set(art(p), p)
