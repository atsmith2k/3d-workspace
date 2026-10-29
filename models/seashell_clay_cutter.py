"""Scallop seashell polymer-clay cutter set: a fan shell with a scalloped rim, hinge ears
and radial ribs pressed in, in three sizes with a pusher for each.

Press the cutter into rolled clay (2-3 mm), lift, and push the piece out with the
matching pusher. Each cutter has a flat back with a finger flange, a sharp single-line
edge, recessed imprint blades that press the ribs in the same press, and support bars across the back that sit well clear of the clay.
Prints edge-up with no supports on a Bambu A1 or A1 mini.

Spec:
  object:       polymer-clay cutter set, scallop shell with scalloped rim, hinge ears and rib imprints
  overall:      cut pieces 24, 32 and 40 mm on the longest side; cutters 6.7 mm larger
                (blade + flange), 12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    fan-shaped scallop shell with scalloped rim and hinge ears; seven radial
                rib imprints 1.5 mm short of the edge; 0.45 mm cutting edge; finger
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

DESCRIPTION = "Scallop seashell polymer-clay earring cutter set with rib imprints, 3 sizes with pushers"

PRODUCT = dict(
    title="Scallop Seashell Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=['polymer clay cutter', 'clay cutter', 'earring cutter', 'jewelry making', 'clay earrings', 'cutter set', 'seashell', 'shell', 'beach', 'ocean', 'summer', 'mermaid'],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, sizes=(24.0, 32.0, 40.0))


def art(p):
    c, R = (0.0, -8.0), 17.0
    angs = np.radians(np.linspace(28, 152, 40))
    fan = poly([c] + [(c[0] + R * math.cos(a), c[1] + R * math.sin(a)) for a in angs])
    for a in np.radians(np.linspace(32, 148, 9)):
        fan += circle(c[0] + R * math.cos(a), c[1] + R * math.sin(a), 2.7)
    ears = poly([(-6.5, -11.5), (6.5, -11.5), (5.0, -6.0), (-5.0, -6.0)])
    outline = grow(grow(fan + ears, 0.8), -0.8)
    ribs = [[(c[0] + 5.5 * math.cos(a), c[1] + 5.5 * math.sin(a)),
             (c[0] + 23 * math.cos(a), c[1] + 23 * math.sin(a))]
            for a in np.radians(np.linspace(46, 134, 7))]
    hinge = [(-8, -7.2), (8, -7.2)]
    return Art(outline=outline, imprints=ribs + [hinge])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def display(p):
    return cutter_display(p)


def build(p):
    return cutter_set(art(p), p)
