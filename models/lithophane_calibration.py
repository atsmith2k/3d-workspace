"""Lithophane calibration wedge: measure how much light your filament lets through.

Print it in the filament you will use for lithophanes, hold it flat on a light box (or
a phone showing a white screen) in a dark room, photograph it straight on with the
exposure locked so the thinnest step is bright but not clipped, crop the photo to the
row of steps, then:

    cad litho calibrate wedge.jpg            (or --crop x0,y0,x1,y1)

It fits Beer-Lambert to the step brightnesses and prints the transmittance per mm to
put in a lithophane model (`--set transmittance=0.47`). The steps read left to right
thinnest to thickest when the smooth face looks at the camera (the step thicknesses are
engraved underneath each step on the bottom frame, mirrored on the back so they read
from the front with the light behind).

Spec:
  object:       step wedge, 8 steps of known wall thickness in one frame
  overall:      104 x 34 x 4 mm, printed upright like a lithophane
  mates with:   nothing
  orientation:  upright on its bottom frame edge, smooth face at y=0, steps toward +y;
                supports expected: none (top band chamfered 1:1.5 underneath)
  must have:    steps 0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4 mm thick, 12 x 20 mm each;
                frame 4 mm thick; step numbers engraved 0.4 mm into the bottom band
  tolerances:   step thickness +-0.05 mm (it is the measurement)
  print:        same settings as the lithophanes it calibrates (100% infill, 0.12 mm)
"""
import numpy as np
from manifold3d import CrossSection, Manifold

from cadkit.checks import *
from cadkit.lithophane import LITHO_MIN_WALL, LITHO_SLICE
from cadkit.relief import text

DESCRIPTION = "Lithophane calibration wedge: 8 steps 0.6-3.4 mm to measure filament transmittance"

PARAMS = dict(steps=(0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0, 3.4), step_w=12.0, step_h=20.0,
              frame=4.0, frame_t=4.0, bottom=10.0)

SLICE = LITHO_SLICE
MIN_WALL = LITHO_MIN_WALL

PRODUCT = dict(category="parts", tags=["lithophane", "calibration"], printers=["a1", "a1mini"],
               sellable=False)


def _size(p):
    w = len(p.steps) * p.step_w + 2 * p.frame
    h = p.bottom + p.step_h + p.frame
    return w, h


def checks(p):
    w, h = _size(p)
    x0 = -w / 2 + p.frame
    out = [dims(x=w, y=p.frame_t, z=h), single_body(), no_overhang()]
    z = p.bottom + p.step_h / 2
    for i, t in enumerate(p.steps):
        x = x0 + (i + 0.5) * p.step_w
        out += [solid((x, t - 0.08, z)), empty((x, t + 0.08, z))]
    return out


def build(p):
    w, h = _size(p)
    zt = p.bottom + p.step_h                     # top of the steps
    body = Manifold.cube((w, p.frame_t, h)).translate((-w / 2, 0, 0))
    x0 = -w / 2 + p.frame
    win = Manifold.cube((len(p.steps) * p.step_w, p.frame_t + 1, p.step_h)) \
        .translate((x0, -0.5, p.bottom))
    body = body - win
    for i, t in enumerate(p.steps):
        # each step 0.05 mm wider each side so neighbours fuse (no coplanar faces)
        step = Manifold.cube((p.step_w + 0.1, t, p.step_h + 0.2)) \
            .translate((x0 + i * p.step_w - 0.05, 0, p.bottom - 0.1))
        body = body + step
    # chamfer under the top band: its underside faces down when printed upright
    # polygon in (y, z); rotate (0, 90, 0) maps a section point (-z, y) extruded along
    # +z to (x, y, z), so feed it (-z, y) and extrude across the window's width
    yz = np.array([(0.0, zt + 0.05), (p.frame_t, zt + 0.05), (p.frame_t, zt),
                   (0.0, zt - p.frame_t * 1.5)])
    pts = np.c_[-yz[:, 1], yz[:, 0]]
    x, y = pts[:, 0], pts[:, 1]
    if np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)) < 0:     # clockwise
        pts = pts[::-1]
    wedge = Manifold.extrude(CrossSection([pts]), len(p.steps) * p.step_w) \
        .rotate((0, 90, 0)).translate((x0, 0, 0))
    body = body + (wedge ^ Manifold.cube((w, p.frame_t, h)).translate((-w / 2, 0, 0)))
    # step thickness numbers engraved into the back (y=0) of the bottom band, mirrored
    for i, t in enumerate(p.steps):
        label = text(f"{t:.1f}", 5.0, bold=True, mirror=True)
        (lx0, ly0, lx1, ly1) = label.bounds()
        label = label.translate((-(lx0 + lx1) / 2, -(ly0 + ly1) / 2))
        cut = Manifold.extrude(label, 0.5).rotate((90, 0, 0)) \
            .translate((x0 + (i + 0.5) * p.step_w, 0.4, p.bottom / 2))
        body = body - cut
    return body
