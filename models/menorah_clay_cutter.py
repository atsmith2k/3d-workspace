"""Menorah polymer-clay cutter set: a nine-branch menorah with the shamash raised in the
middle, a flame on every candle, a branch bar, stem and foot, in three sizes with a
pusher for each. Simplified so every candle is at least 2 mm wide at the smallest size.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports.

Spec:
  object:       polymer-clay cutter set, nine-branch menorah silhouette with flames, shamash raised
  overall:      cut pieces 35, 45 and 55 mm on the longest side; cutters 6.7 mm
                larger (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    nine candles with teardrop flames on a branch bar, the centre (shamash)
                raised 3 mm; candles >= 2 mm wide at 35 mm; stem and foot; 0.45 mm cutting
                edge; finger flange 2 mm
  tolerances:   cut size +-0.3 mm; blade edge one 0.4 mm-nozzle line

Units: mm. Z is up. Don't scale the STL to resize (it changes blade thickness):
use --set sizes=40,50,60.
"""
import math

import numpy as np
from manifold3d import CrossSection

from cadkit.checks import *
from cadkit.cutter import *
from cadkit.relief import *

DESCRIPTION = "Nine-branch menorah polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Menorah Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings',
          'cutter set', 'hanukkah', 'chanukah', 'judaica', 'menorah', 'hanukkiah', 'candles', 'holiday'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(35.0, 45.0, 55.0))

PITCH = 4.1     # candle spacing (art units = mm at the 35 mm size)
CANDLE = 2.2    # candle width
FLAME = 1.4     # flame radius


def candle(x, top):
    body = poly([(x - CANDLE / 2, -0.5), (x + CANDLE / 2, -0.5), (x + CANDLE / 2, top), (x - CANDLE / 2, top)])
    flame = CrossSection.batch_hull([circle(x, top + 1.1, FLAME), circle(x, top + 3.9, 0.25)])
    return body + flame


def art(p):
    shape = CrossSection()
    for k in range(-4, 5):
        shape += candle(k * PITCH, 9.0 if k == 0 else 6.0)
    bar = poly([(-4 * PITCH - CANDLE / 2, -3.0), (4 * PITCH + CANDLE / 2, -3.0),
                (4 * PITCH + CANDLE / 2, 0.0), (-4 * PITCH - CANDLE / 2, 0.0)])
    stem = poly([(-1.8, -12.0), (1.8, -12.0), (1.8, -2.5), (-1.8, -2.5)])
    foot = poly([(-8.0, -15.0), (8.0, -15.0), (5.5, -11.5), (-5.5, -11.5)])
    outline = grow(grow(grow(grow(shape + bar + stem + foot, -0.5), 0.5), 0.6), -0.6)
    return Art(outline=outline, bars_y=[3.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
