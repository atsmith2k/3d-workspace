"""Cable raceway: an open U-channel swept along an S-curve so cables can be routed
around an obstacle on a desk or wall. Mounting tabs with screw holes at both ends.

Spec:
  object:       surface cable channel for 2-3 cables, open top
  overall:      about 120 x 40 mm footprint, 12 mm wide x 8 mm tall channel
  mates with:   #6 screws through the end tabs
  orientation:  flat bottom on the bed, open side up; no overhangs
  must have:    constant 12 x 8 section along the whole curve, 1.6 mm walls
  tolerances:   none

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from build123d import *

from cadkit.checks import *
from cadkit.hardware import WOOD_SCREW
from cadkit.recipes import swept_channel

DESCRIPTION = "S-curve cable raceway with screw tabs (sweep recipe demo)"

PARAMS = dict(
    length=120.0,
    offset=30.0,       # sideways shift of the S between the ends
    width=12.0,
    height=8.0,
    wall=1.6,
    tab=14.0,          # mounting tab square
    screw="#6",
)


def _path(p):
    L, o = p.length, p.offset
    return [(-L / 2, 0), (-L / 4, 0), (0, o / 2), (L / 4, o), (L / 2, o)]


def checks(p):
    L, o = p.length, p.offset
    return [
        dims(x=L + 2 * p.tab - 2, z=p.height),
        empty((0, o / 2, p.height / 2)),                            # channel is open at the midpoint
        solid((0, o / 2, p.wall / 2)),                              # channel floor at the midpoint
        empty((-L / 4, 0, p.height / 2)),                           # open on the straight too
        thickness_at((-L / 4, p.width / 2 - 0.2, p.height / 2), p.wall - 0.2, direction=(0, 1, 0)),
        hole(WOOD_SCREW[p.screw][0] + 0.2, at=(-L / 2 - p.tab / 2 + 1, 0), span=(0.2, p.wall - 0.2)),
        hole(WOOD_SCREW[p.screw][0] + 0.2, at=(L / 2 + p.tab / 2 - 1, o), span=(0.2, p.wall - 0.2)),
        flat_base(L * p.width * 0.7),
        no_overhang(),
        single_body(),
    ]


def build(p):
    pts = _path(p)
    part = swept_channel(pts, p.width, p.height, p.wall)
    d = WOOD_SCREW[p.screw][0] + 0.2
    for (x, y), sx in ((pts[0], -1), (pts[-1], 1)):
        tab = Box(p.tab, p.tab, p.wall, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x + sx * (p.tab / 2 - 1), y, 0)))
        tab = fillet(tab.edges().filter_by(Axis.Z), 3.0)
        tab -= Cylinder(d / 2, p.wall + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x + sx * (p.tab / 2 - 1), y, -1)))
        part += tab
    return part
