"""Desk-edge cable clip: a strip of C-clips that USB cables press into, with a flat
base for adhesive tape (or a screw hole with --set mount=screw).

Spec:
  object:       holder for three ~5 mm cables at a desk edge
  overall:      about 33 x 9 x 8 mm, flat base
  mates with:   5 mm cables (snap mouth 3.8 mm); optional #6 screw
  orientation:  base on the bed, clips as vertical walls; no overhangs
  must have:    cables held by the snap, mouth opens upward, 1.6 mm clip walls
  tolerances:   cable bore +0.2 mm

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from build123d import *

from cadkit.checks import *
from cadkit.hardware import WOOD_SCREW
from cadkit.recipes import cable_clip

DESCRIPTION = "Press-in clip strip for three cables, adhesive or screw mount"

PARAMS = dict(
    cable_d=5.0,
    count=3,
    wall=1.6,
    base_t=2.0,
    grip=1.2,
    mount="tape",     # tape | screw
    screw="#6",
)


def _geom(p):
    pitch = p.cable_d + 2 * p.wall + 2
    width = p.cable_d + 2 * p.wall + 1
    return pitch, width


def checks(p):
    from math import asin, cos
    pitch, width = _geom(p)
    ro = p.cable_d / 2 + p.wall
    cz = p.base_t + ro - 0.1
    half = min(asin((p.cable_d - p.grip) / (2 * (p.cable_d / 2 + 0.1))), 1.2)   # mouth half-angle
    top = cz + ro * cos(half)                                                     # crown after the mouth cut
    xs = [(k - (p.count - 1) / 2) * pitch for k in range(p.count)]
    out = [dims(x=pitch * p.count, y=width, z=(top - 0.5, top + 0.5)),
           flat_base(pitch * p.count * width * 0.8), no_overhang(), single_body()]
    ri = p.cable_d / 2 + 0.1
    for x in xs:
        out += [empty((x, 0, cz)),                                          # cable bore
                solid((x + ro - p.wall / 2, 0, cz)),                        # clip wall beside it
                empty((x, 0, cz + ro - 0.3)),                               # mouth open at the crown
                solid((x + (ri + p.wall / 2) * 0.76, 0, cz + (ri + p.wall / 2) * 0.65))]  # lip beside the mouth (40 deg)
    return out


def build(p):
    part = cable_clip(p.cable_d, p.count, p.wall, p.base_t, grip=p.grip)
    if p.mount == "screw":
        pitch, width = _geom(p)
        d = WOOD_SCREW[p.screw][0] + 0.2
        part -= Cylinder(d / 2, p.base_t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((pitch * (p.count - 1) / 2 + pitch / 2 - 0.1, 0, -1)))
    return part
