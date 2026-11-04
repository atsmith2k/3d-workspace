"""Sufganiyah (jelly doughnut) polymer-clay cutter set: a round doughnut with a wavy
powdered-sugar line pressed across the top and a jam dot, in three sizes with a pusher
for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports.

Spec:
  object:       polymer-clay cutter set, sufganiyah jelly doughnut with sugar-line and jam-dot imprints
  overall:      cut pieces 22, 30 and 38 mm on the longest side; cutters 6.7 mm
                larger (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    rounded doughnut outline (wider than tall); wavy powdered-sugar line
                imprint across the top third; round jam dot imprint; imprints 1.5 mm short of
                the cutting edge; 0.45 mm cutting edge; finger flange 2 mm
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

DESCRIPTION = "Sufganiyah jelly doughnut polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Sufganiyah Jelly Doughnut Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings',
          'cutter set', 'hanukkah', 'chanukah', 'judaica', 'sufganiyah', 'doughnut', 'donut', 'jelly doughnut', 'food', 'holiday'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(22.0, 30.0, 38.0))

JAM = (4.0, -4.0, 2.6)    # jam dot centre and radius


def art(p):
    outline = ellipse(0, 0, 15.0, 12.0) + poly([(-13.0, -11.0), (13.0, -11.0), (13.5, -6.0), (-13.5, -6.0)])
    outline = grow(grow(outline, 1.0), -1.0)
    xs = np.linspace(-17, 17, 49)
    sugar = np.c_[xs, 3.0 + 1.3 * np.sin(xs * math.pi / 4.2)]
    a = np.linspace(0, 2 * math.pi, 25)
    jam = np.c_[JAM[0] + JAM[2] * np.cos(a), JAM[1] + JAM[2] * np.sin(a)]
    return Art(outline=outline, imprints=[sugar, jam], bars_x=[-5.0], bars_y=[JAM[1]])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
