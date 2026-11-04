"""Dreidel polymer-clay cutter set: a dreidel with a handle, a square body and a pointed
tip, with a Star of David and a rim line pressed into the face, in three sizes with a
pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, recessed imprint blades that press the star and the rim line in the same press, and
support bars across the back that sit well clear of the clay. No Hebrew letters.
Prints edge-up with no supports.

Spec:
  object:       polymer-clay cutter set, dreidel (handle, square body, pointed tip) with a
                Star of David imprint and a rim line under the handle
  overall:      cut pieces 26, 34 and 42 mm on the longest side (height); cutters 6.7 mm
                larger (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    dreidel outline with handle and pointed tip; Star of David imprint (two
                triangles) on the body; rim line imprint across the top of the body; 0.45
                mm cutting edge; finger flange 2 mm
  tolerances:   cut size +-0.3 mm; blade edge one 0.4 mm-nozzle line

Units: mm. Z is up. Don't scale the STL to resize (it changes blade thickness):
use --set sizes=24,32,40.
"""
import math

import numpy as np
from manifold3d import CrossSection

from cadkit.checks import *
from cadkit.cutter import *
from cadkit.relief import *

DESCRIPTION = "Dreidel polymer-clay earring cutter set with Star of David imprint, 3 sizes with pushers"

PRODUCT = dict(
    title="Dreidel Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings',
          'cutter set', 'hanukkah', 'chanukah', 'judaica', 'dreidel', 'star of david', 'holiday'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(26.0, 34.0, 42.0))

STAR_AT = (0.0, -1.2)    # centre of the body face


def triangle(cx, cy, r, rot):
    pts = [(cx + r * math.cos(math.radians(rot + 120 * k)),
            cy + r * math.sin(math.radians(rot + 120 * k))) for k in range(4)]
    return np.array(pts)


def art(p):
    handle = poly([(-2.4, 7.0), (2.4, 7.0), (2.4, 15.0), (-2.4, 15.0)])
    body = poly([(-9.5, -6.0), (9.5, -6.0), (9.5, 8.0), (-9.5, 8.0)])
    tip = poly([(-9.5, -5.5), (9.5, -5.5), (0, -16.0)])
    outline = grow(grow(grow(grow(handle + body + tip, -1.2), 1.2), 0.7), -0.7)
    rim = [(-11, 4.6), (11, 4.6)]
    star = [triangle(*STAR_AT, 4.6, 90), triangle(*STAR_AT, 4.6, -90)]
    return Art(outline=outline, imprints=[rim] + star, bars_y=[STAR_AT[1], -8.5])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
