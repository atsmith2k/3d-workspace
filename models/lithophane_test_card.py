"""Lithophane of the generated test card: the reference model for cadkit.lithophane.

The card (scripts/make_litho_test_card.py, all generated, no photo) has a gradient,
11 grey steps, a shaded sphere, a Siemens star, line pairs and lettering, so one print
shows tone response, contrast range and resolution. Also the selftest entry that keeps
the lithophane pipeline from drifting.

Spec:
  object:       backlit test-card lithophane, 100 mm wide flat panel
  overall:      100 x 76.4 x 4 mm (frame 3 mm wide, 4 mm thick), picture 94 x 70.4 (4:3)
  mates with:   nothing (light box, window, LED stand)
  orientation:  printed upright on its bottom frame edge, smooth face at y=0 toward the
                viewer, relief toward +y; supports expected: none
  must have:    picture wall 0.6 mm (white) to 3.0 mm (black), Beer-Lambert mapping at
                tau 0.50/mm; frame 3 mm x 4 mm with a chamfer under the top band
  tolerances:   none (no fits)
  print:        100% infill, 0.12 mm layers, 6 mm brim, white PLA
"""
from cadkit.checks import *
from cadkit.lithophane import LITHO_MIN_WALL, LITHO_SLICE, litho_build, litho_checks, litho_extras, litho_params

DESCRIPTION = "Test-card lithophane, 100 mm flat panel (tone, contrast and resolution check)"

PARAMS = litho_params("models/images/litho_test_card.png", width=100.0)

SLICE = LITHO_SLICE
MIN_WALL = LITHO_MIN_WALL      # 0.6 mm white areas are intentional

PRODUCT = dict(category="parts", tags=["lithophane", "calibration"], printers=["a1", "a1mini"],
               sellable=False)


def checks(p):
    return litho_checks(p) + [
        empty((0, 3.5, 38.0)),                   # picture area is thinner than the frame
    ]


def build(p):
    return litho_build(p)


def extras(p, out, name):
    return litho_extras(p, out, name)
