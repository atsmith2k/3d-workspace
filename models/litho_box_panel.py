"""Lithophane side wall for the user's light box ("Litho Box_Bottom_Dimmable Light_With
Slats.stl"): a 100 x 100 mm panel that slides down into the slots of the box's corner
posts. Four of these make the four walls; build one per photo with
`--set image=models/images/<photo> --name litho_box_panel_<n>`, and the lid's top
panel with `--set fit=lid` (measured from models/refs/litho_box_lid.stl).

Fit dimensions measured from the user-supplied box STL (models/refs/litho_box_bottom.stl,
119.15 x 119.15 x 105.82 mm), sliced and ray-probed on 2026-11-07:
  corner posts:   2.18..10.29 mm square at each corner, a slot in each inner face
  slot:           3.03 mm wide (y 4.91..7.94 on the y=0 side), 1.03 mm deep into the post
  slot to slot:   100.63 mm between slot bottoms (post faces 98.57 mm apart)
  slot height:    floor ledge z 2.82 (2.57 further in) to post top z 105.82 (~103 mm)
  outer rim:      covers the panel's outside face up to z 6.5 (4 mm above the floor)

Spec:
  object:       backlit lithophane panel for the light box: 4 walls (fit=wall) and
                1 top panel in the lid (fit=lid)
  overall:      100 x 100 mm, picture 0.8 (white) to 3.2 mm (black) thick
  mates with:   box slots 3.03 x 1.03 mm, 100.63 mm apart: panel edges 2.6 mm thick
                (0.21 mm clearance per side in the slot), width 100 mm (0.31 mm per
                side), height 100 mm (3.0 mm spare under the post tops)
  orientation:  printed upright on its bottom edge, smooth face toward the viewer
                (outside of the box), relief toward the light; supports expected: none
  must have:    2 mm edge band 2.6 mm thick on all four sides (the side bands are what
                slide in the slots); the picture between them may reach 3.2 mm because
                it stays between the posts; chamfer under the top band
  tolerances:   sliding 0.2 mm per side in the slot thickness
  lid panel:    fit=lid: 100 x 100 in the lid's 100.12 x 4.02 mm recess (0.06 mm per
                side as the user asked for exactly 100 mm: a tight fit, sand the edges
                or rebuild at width=99.6 height=99.6 if it binds); frame 3.2 mm, border
                2.5 mm so it rests on the 2.3 mm ledge, smooth face 0.82 mm below the top
  material:     Elegoo Rapid PETG White, sliced with Bambu's Generic PETG preset
                (255 C nozzle, 80 C textured PEI plate, 8 mm3/s); tone mapping uses
                transmittance 0.60/mm (white PETG estimate: no published value; measure
                it with models/lithophane_calibration.py and `cad litho calibrate`)
  print:        0.12 mm layers, walls only (4 loops, 100% infill for any leftover),
                6 mm brim, turned 90 deg on the plate; reprint walls 1, 2, 4 together
                braced on one plate with models/litho_box_plate.py
"""
from pathlib import Path

import numpy as np

from cadkit.checks import *
from cadkit.lithophane import (LITHO_MIN_WALL, LITHO_SLICE, TRANSMITTANCE, litho_build, litho_checks,
                               litho_extras, litho_params)

DESCRIPTION = "100 x 100 mm lithophane wall panel that slides into the light box's corner-post slots"

SLOT_W = 3.03            # measured slot width
SLOT_GAP = 100.63        # slot bottom to slot bottom (user measured 100.68 on the print)
REFS = Path(__file__).resolve().parent / "refs"
BOX = REFS / "litho_box_bottom.stl"
LID = REFS / "litho_box_lid.stl"
# lid (as modelled, top face at z=0): 118.25 square, recess 100.12 square x 4.02 deep
# from the top face, resting on a 2.3 mm ledge round a 95.53 mm window
LID_RECESS, LID_DEPTH, LID_LEDGE = 100.12, 4.02, 2.30

# fit="wall": slides into the box's post slots (edges 2.6 mm thick for the 3.03 slot)
# fit="lid":  drops into the lid's recess, smooth face up, frame resting on the ledge
#             (frame = max_t so the relief never hangs below it; border covers the ledge)
PARAMS = litho_params("models/images/litho_test_card.png", width=100.0, height=100.0,
                      min_t=0.8, max_t=3.2, frame_t=2.6, border=2.0, fit="wall",
                      transmittance=TRANSMITTANCE["elegoo_rapid_petg_white"],
                      detail="soft")   # keep sub-nozzle facial detail (rounded, not deleted)
LID_OVERRIDES = dict(frame_t=3.2, border=2.5)

# Elegoo Rapid PETG White: no Elegoo preset for Bambu printers, so Bambu's Generic PETG
# for the A1 (255 C nozzle, 80 C plate, 8 mm3/s), inside Elegoo's 230-260 C / 70-90 C
SLICE = dict(LITHO_SLICE, filament="Generic PETG")
# detail="soft" keeps sub-nozzle bumps (rounded) for likeness on small faces; the wall
# sampler reads their tips ~0.2 mm, measured on wall 4 as 0.2 mm crests on a 1.7-3.0 mm
# wall. `picture wall >= min_t` still enforces the real 0.8 mm minimum.
MIN_WALL = 0.15

PRODUCT = dict(category="parts", tags=["lithophane"], printers=["a1", "a1mini"], sellable=False)
LICENSE_NOTES = ("Fits a light box supplied by the user as an STL (Litho Box_Bottom_Dimmable "
                 "Light_With Slats); slot dimensions measured from that file. Personal photos: "
                 "not for sale.")


def _in_box(p):
    """Panel moved from print pose into the y=0 side's slot of the box."""
    clear = (SLOT_W - p.frame_t) / 2
    return (119.15 / 2, 4.91 + clear, 2.82)          # rests on the 2.82 mm ledge


def _resolved(p):
    """Params with the lid's frame settings laid over them for fit="lid"."""
    from types import SimpleNamespace
    d = dict(vars(p))
    if p.fit == "lid":
        d.update(LID_OVERRIDES)
    elif p.fit != "wall":
        raise ValueError(f"fit must be 'wall' or 'lid', got {p.fit!r}")
    return SimpleNamespace(**d)


def _man(tm):
    from manifold3d import Manifold, Mesh
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                         tri_verts=np.asarray(tm.faces, np.uint32)))


def _fit(p):
    def fn(ctx):
        import trimesh
        ref = BOX if p.fit == "wall" else LID
        if not ref.exists():
            return True, f"{ref.name} not found; fit not checked"
        panel = _man(ctx.tm)
        if p.fit == "wall":
            panel = panel.translate(_in_box(p))
            where = "in the box's slot"
        else:
            # lay it in the recess: thickness (y) -> lid z, smooth face toward the top face
            panel = panel.rotate((90, 0, 0)).translate(
                (118.25 / 2, 118.25 / 2 + p.height / 2, LID_DEPTH - p.frame_t))
            where = "in the lid's recess"
        hit = (_man(trimesh.load(ref)) ^ panel).volume()
        return hit < 0.05, f"{where}: {hit:.2f} mm3 interference"
    return fn


def checks(p):
    p = _resolved(p)
    edge = p.width / 2 - 0.5                          # inside the part that enters the slot
    out = litho_checks(p) + [
        dims(x=p.width, y=(p.max_t - 0.05, p.max_t + 0.05), z=p.height),
        solid((edge, p.frame_t - 0.1, 50), (-edge, p.frame_t - 0.1, 50)),
        custom("fits the " + ("box" if p.fit == "wall" else "lid"), _fit(p)),
    ]
    if p.fit == "wall":                               # edges thin enough for the slot
        out.append(empty((edge, p.frame_t + 0.1, 50), (-edge, p.frame_t + 0.1, 50)))
    else:                                             # frame wide enough to sit on the ledge
        out.append(custom("frame covers the ledge", lambda ctx: (
            p.border >= (p.width - (LID_RECESS - 2 * LID_LEDGE)) / 2,
            f"border {p.border} mm vs ledge reach {(p.width - (LID_RECESS - 2 * LID_LEDGE)) / 2:.2f} mm")))
    return out


def build(p):
    return litho_build(_resolved(p))


def extras(p, out, name):
    return litho_extras(_resolved(p), out, name)
