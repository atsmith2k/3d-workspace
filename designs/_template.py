"""DESCRIPTION_HERE

Spec (fill this in before writing design(); it is the contract the checks enforce):
  object:       what it is and where it goes (cap front, tote bag, patch, towel corner...)
  overall:      W x H mm stitched, hoop
  fabric:       what it sews on and the stabiliser (cut-away for knits, tear-away for wovens)
  threads:      the colours in sewing order
  must have:    the features asked for, each with a size (lettering cap height >= 6 mm
                for fills, satin columns 1-7 mm wide, no detail under 1 mm)
  density:      max thread layers (3.5), stitch count budget

Units: mm, Y up, design centred on the origin. Elements sew in the order added.
"""
from cadkit.stitch import *

DESCRIPTION = "DESCRIPTION_HERE"
HOOP = "4x4"                      # 4x4, 5x7, 6x10, 8x8, 8x12...

PARAMS = dict(
    width=80.0,                   # overall stitched width, mm
    color="#c8102e",
)


def checks(p):
    return [
        size(w=p.width, tol=2.0),
        hoop(),
        colors(2),
        max_density(3.5),
        long_stitches(7.0),
        min_feature(1.0),
        stitches(max=20000),
    ]


def design(p):
    d = Design()
    body = heart(p.width)
    d.fill(body, p.color, angle=30, name="heart")
    d.outline(body, "black", width=1.6, name="border")
    return d
