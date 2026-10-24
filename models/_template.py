"""DESCRIPTION_HERE

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from build123d import *

DESCRIPTION = "DESCRIPTION_HERE"

# Every tunable dimension lives here so it can be changed with --set name=value.
PARAMS = dict(
    width=40.0,
    depth=30.0,
    height=20.0,
    corner_radius=3.0,
)


def build(p):
    part = Box(p.width, p.depth, p.height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = fillet(part.edges().filter_by(Axis.Z), p.corner_radius)
    return part
