"""Grip knob for a 6 mm D-shaft (potentiometer, encoder, valve), scalloped sides,
rounded top edge. Prints on its flat shaft face.

Spec:
  object:       control knob, finger grip
  overall:      30 mm diameter, 18 mm tall
  mates with:   6 mm D-shaft with a 5.5 mm flat, 12 mm deep; or --set style=bolt for
                an M4 bolt with a captive nut in the base
  orientation:  shaft face on the bed, dome up; scallops are vertical; no overhangs
  must have:    scallops deep enough to feel (2.5 mm), shaft socket a light press fit
  tolerances:   shaft socket +0.3 mm on diameter; flat +0.1

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from cadkit.checks import *
from cadkit.hardware import HEX_NUT, clearance
from cadkit.recipes import knob

DESCRIPTION = "Scalloped grip knob for a 6 mm D-shaft or an M4 bolt"

PARAMS = dict(
    style="dshaft",      # dshaft | bolt
    diameter=30.0,
    height=18.0,
    lobes=6,
    lobe_depth=2.5,
    top_radius=3.0,
    shaft_d=6.0,
    shaft_flat=5.5,
    shaft_depth=12.0,
    bolt="M4",
)


def checks(p):
    from math import cos, pi, sin
    a = pi / p.lobes                                                             # halfway between two scallops
    out = [dims(x=(p.diameter - p.lobe_depth - 0.5, p.diameter + 0.5), y=(p.diameter - 0.5, p.diameter + 0.5), z=p.height),
           flat_base(3.14 * (p.diameter / 2) ** 2 * 0.5), no_overhang(), single_body(),
           empty((0, 0, 1.0)),                                                   # socket or bore open at the base
           solid(((p.diameter / 2 - 0.6) * cos(a), (p.diameter / 2 - 0.6) * sin(a), p.height / 2)),  # rim between scallops
           empty(((p.diameter / 2 - 0.3), 0, p.height / 2))]                     # scallop at angle 0 is cut
    if p.style == "dshaft":
        out += [solid((0, 0, p.height - 2)),                                     # blind: top is solid
                empty((0, p.shaft_flat - p.shaft_d / 2 - 0.3, p.shaft_depth / 2)),  # inside the round side
                solid((0, p.shaft_flat - p.shaft_d / 2 + 0.4, p.shaft_depth / 2))]  # the flat
    else:
        af, nt = HEX_NUT[p.bolt]
        out += [hole(clearance(p.bolt), at=(0, 0), span=(nt + 1, p.height - 0.3)),
                empty((af / 2 - 0.3, 0, nt / 2))]                                 # nut pocket
    return out


def build(p):
    if p.style == "dshaft":
        return knob(p.diameter, p.height, p.lobes, p.lobe_depth, p.top_radius,
                    shaft_d=p.shaft_d, shaft_flat=p.shaft_flat, shaft_depth=p.shaft_depth)
    return knob(p.diameter, p.height, p.lobes, p.lobe_depth, p.top_radius, bolt=p.bolt)
