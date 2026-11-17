"""DESCRIPTION_HERE

Lithophane from IMAGE_HERE. Built by cadkit.lithophane (Cura's ImageReader tone model,
Beer-Lambert light transmittance, plus print-ready shapes and a backlit simulation).

Spec:
  object:       backlit lithophane of IMAGE_HERE
  overall:      width x height from PARAMS (height 0 = from the photo's aspect ratio)
  mates with:   nothing; flat panels sit on a light box / LED stand, arcs stand alone,
                cylinders drop over an LED tea light (diameter = width / pi)
  orientation:  printed upright (image vertical, smooth face toward the viewer): the
                outer wall traces the relief at nozzle resolution; supports expected: none
  must have:    picture wall min_t (white) to max_t (black); frame `border` mm wide and
                frame_t (default max_t + 1) thick with a chamfer under the top band
  tolerances:   none (no fits)
  print:        100% infill, 0.12 mm layers, brim (SLICE below); white PLA

Workflow: `cad build models/NAME_HERE.py` writes the STL, the preview and
NAME_HERE_backlit.png (target tones vs simulated light box). Tune with --set:
contrast range `min_t`/`max_t`, `gamma`, `sharpen`, `transmittance` (measure it with
models/lithophane_calibration.py + `cad litho calibrate`), `shape=arc|cylinder`,
`outline=oval|heart|rounded|hexagon`, `stand=30` for a foot.
"""
from cadkit.checks import *
from cadkit.lithophane import LITHO_MIN_WALL, LITHO_SLICE, litho_build, litho_checks, litho_extras, litho_params

DESCRIPTION = "DESCRIPTION_HERE"

PARAMS = litho_params("IMAGE_HERE", PARAMS_HERE)

SLICE = LITHO_SLICE
MIN_WALL = LITHO_MIN_WALL      # 0.6 mm white areas are intentional

PRODUCT = dict(category="parts", tags=["lithophane"], printers=["a1", "a1mini"],
               sellable=False)   # a customer's photo: never list it on the shop


def checks(p):
    return litho_checks(p)


def build(p):
    return litho_build(p)


def extras(p, out, name):
    return litho_extras(p, out, name)
