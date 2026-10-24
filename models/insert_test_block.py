"""Fastener test block: one column per screw size with a heat-set insert pocket, a
clearance hole and a captive hex-nut pocket over a clearance hole, each column
labelled with raised text. Print one on a new printer or filament to confirm the
hardware table (cadkit/hardware.py) fits before designing around it.

Spec:
  object:       calibration block for M2 / M3 / M4 / M5 hardware (set with --set sizes=)
  overall:      pitch x columns wide, 3 rows + label strip deep, 10 mm thick, flat
  mates with:   McMaster/ruthex heat-set inserts, ISO clearance holes, ISO 4032 nuts
  orientation:  flat on its back, pockets opening upward; no overhangs, no supports
  must have:    insert pocket (hole, depth from table), through clearance hole,
                nut pocket (across flats + 0.3) over a clearance hole, bold labels
  tolerances:   holes include the 0.2 mm print allowance from the hardware table

Units: mm. Z is up, the block sits on Z=0.
"""
from math import sqrt

from build123d import *

from cadkit.cad import emboss_text
from cadkit.checks import *
from cadkit.hardware import clearance, insert, nut_pocket

DESCRIPTION = "Heat-set insert, clearance hole and nut pocket test block with labels"

PARAMS = dict(
    sizes="M2,M3,M4,M5",   # comma-separated metric sizes, one column each
    pitch=16.0,            # column spacing
    thickness=12.0,          # deeper than the longest insert pocket (M5: 10 mm)
    label_height=0.6,      # raised text, 3 layers
    label_size=6.0,        # cap height; strokes come out ~1 mm
    corner_radius=2.0,
)

LABEL_STRIP = 8.0


def _layout(p):
    sizes = [s.strip() for s in p.sizes.split(",")]
    width = len(sizes) * p.pitch
    depth = 3 * p.pitch + LABEL_STRIP
    return sizes, width, depth


def checks(p):
    sizes, width, depth = _layout(p)
    out = [dims(x=width, y=depth, z=p.thickness + p.label_height),
           flat_base(width * depth * 0.9), no_overhang(), single_body()]
    for i, s in enumerate(sizes):
        x = (i + 0.5) * p.pitch
        ins = insert(s)
        out.append(hole(ins["hole"], at=(x, 0.5 * p.pitch), span=(p.thickness - ins["depth"] + 0.3, p.thickness - 0.3)))
        out.append(hole(clearance(s), at=(x, 1.5 * p.pitch)))
        out.append(solid((x, 0.5 * p.pitch, 1.0)))     # insert pocket is blind
    return out


def build(p):
    sizes, width, depth = _layout(p)
    block = Box(width, depth, p.thickness, align=(Align.MIN, Align.MIN, Align.MIN))
    block = fillet(block.edges().filter_by(Axis.Z), p.corner_radius)
    top = p.thickness
    for i, s in enumerate(sizes):
        x = (i + 0.5) * p.pitch
        # row 1: heat-set insert pocket, blind
        ins = insert(s)
        block -= Cylinder(ins["hole"] / 2, ins["depth"], align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x, 0.5 * p.pitch, top - ins["depth"])))
        # row 2: through clearance hole
        block -= Cylinder(clearance(s) / 2, p.thickness + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x, 1.5 * p.pitch, -1)))
        # row 3: captive nut pocket over a clearance hole
        af, t = nut_pocket(s)
        hexagon = extrude(RegularPolygon(af / sqrt(3), 6), amount=t + 1)
        block -= hexagon.moved(Location((x, 2.5 * p.pitch, top - t)))
        block -= Cylinder(clearance(s) / 2, p.thickness + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x, 2.5 * p.pitch, -1)))
        # label
        block = emboss_text(block, s, p.label_size, p.label_height, at=(x, 3 * p.pitch + LABEL_STRIP / 2, top), bold=True)
    return block
