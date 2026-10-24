"""Coat hook: a J profile extruded to a width, with two countersunk screw holes
through the back plate. Prints lying on its side (the J flat on the bed).

Spec:
  object:       wall coat hook for a jacket or bag
  overall:      50 mm drop x 35 mm reach, 20 mm wide, 5 mm thick
  mates with:   two #6 wood screws through the back plate, 82 deg countersunk
  orientation:  lying on its side, J profile on the bed; no overhangs
  must have:    lip at least 14 mm so a strap cannot slip off; inner corners rounded
  tolerances:   screw holes include the print allowance

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
In print pose the back plate runs up +Y, the arm out +X; mounted, +Y is up.
"""
from build123d import *

from cadkit.checks import *
from cadkit.hardware import WOOD_SCREW
from cadkit.recipes import j_hook

DESCRIPTION = "Coat hook (J profile) with countersunk screw holes, prints on its side"

PARAMS = dict(
    drop=50.0,
    arm=35.0,
    lip=14.0,
    t=5.0,
    width=20.0,
    corner=3.0,
    screw="#6",
    screw_y=(14.0, 38.0),   # hole centres up the back plate
)


def checks(p):
    screw_d = WOOD_SCREW[p.screw][0] + 0.2
    return [
        dims(x=p.arm, y=p.drop, z=p.width),
        *[hole(screw_d, at=(y, p.width / 2), axis="x", span=(0.3, p.t - 2.0)) for y in p.screw_y],
        solid((p.arm - p.t / 2, p.lip - 1, p.width / 2)),          # lip reaches its height
        solid((p.arm / 2, p.t / 2, p.width / 2)),                   # arm is solid
        empty((p.arm / 2, p.t + 3, p.width / 2)),                   # open above the arm
        flat_base(p.arm * p.t + p.drop * p.t - p.t * p.t),
        no_overhang(),
        single_body(),
    ]


def build(p):
    part = j_hook(p.drop, p.arm, p.lip, p.t, p.width, p.corner)
    screw_d = WOOD_SCREW[p.screw][0] + 0.2
    head_d = WOOD_SCREW[p.screw][1] + 0.4
    csk_depth = (head_d - screw_d) / 2 / 0.87
    for y in p.screw_y:
        # through the back plate along X, countersunk on the x = t face (away from the wall)
        part -= Cylinder(screw_d / 2, p.t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .rotate(Axis.Y, 90).moved(Location((-1, y, p.width / 2)))
        cone = Cone(screw_d / 2, head_d / 2 + 0.01, csk_depth + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        part -= cone.rotate(Axis.Y, 90).moved(Location((p.t - csk_depth, y, p.width / 2)))
    return part
