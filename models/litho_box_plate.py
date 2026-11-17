"""Several light-box wall panels ganged on one plate, braced by snap-off end walls.

Why: a single 100 mm panel stands on a 2.6 x 100 mm footprint (38:1). Its top half is a
floppy cantilever (stiffness falls with height cubed: ~4 N/mm at 60 mm, under 1 N/mm at
100 mm), so nozzle drag and PETG blobs rock it; wall 4 failed with the top 35% unprinted.
Two end walls tie every panel's side edges together with small tabs every 8 mm, so the
panels and walls form a rigid grid in plan: each panel is held on three sides instead of
standing free, and the end walls' flared feet widen the footprint.

Time: alone, each panel layer (~11 s of short relief moves) sits near PETG's 12 s minimum
layer time plus a ~4 s layer change, ~4 h 15 m per panel. Ganged, the layer changes are
shared and each panel cools while the nozzle works on the others: three walls in ~8 h
instead of ~12 h 45 m. Sliced walls-only (4 classic loops = 3.36 mm, thicker than the
3.2 mm picture), every line runs along the panel: no zig-zag infill strokes across the
thin sheet (they shove it sideways and their direction can show when lit), and a third
fewer retractions. G-code resolution 0.1 mm merges the relief's sub-nozzle segments.

Each panel is exactly the litho_box_panel wall (same image, crop and tone settings as
its own build), so the fit and picture checks are the panel's own. Snap the end walls
off after printing (flex them outward, or nip each tab with flush cutters) and sand the
stubs flat: the slots allow 0.31 mm per side past the 100 mm width.

Spec:
  object:       3 lithophane wall panels for the light box (walls 1, 2, 4) on one plate
  overall:      panels 100 x 100 mm, 0.8-3.2 mm, 11.2 mm apart; plate ~105 x 38 x 100 mm
  mates with:   the box slots, through each panel (litho_box_panel's fit check, per panel)
  orientation:  upright on the panels' bottom edges, panels along the bed's Y axis
                (turned 90 deg on the plate), smooth faces all toward -y in the model
  must have:    end walls 0.84 mm thick (one loop), 0.5 mm from the panel edges, tabs 0.8 x 0.6 mm
                at the panel, every 8 mm from z 6, centred on the 2.6 mm side band;
                5 mm wide flared foot under each end wall; 8 mm air gap between panels
  tolerances:   tab stubs must stay under the 0.31 mm side clearance after sanding
  material:     Elegoo Rapid PETG White (Generic PETG preset), as litho_box_panel
  print:        0.12 mm layers, walls only (4 classic loops = 3.36 mm), 6 mm brim,
                G-code resolution 0.1 mm, retract only on travels over 3 mm
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from cadkit.checks import *
from cadkit.lithophane import litho_extras, lithophane_of

DESCRIPTION = "Light-box wall panels ganged on one plate with snap-off bracing end walls"

_spec = importlib.util.spec_from_file_location(
    "litho_box_panel", Path(__file__).resolve().parent / "litho_box_panel.py")
panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(panel)

# the photo and crop each wall was tuned with (output/litho_box_wall_<n>/build.json)
WALLS = {
    1: ("models/images/litho_box_1.webp", (0.0, 0.1, 1.0, 0.85)),
    2: ("models/images/litho_box_2.webp", (0.164, 0.0, 0.831, 1.0)),
    3: ("models/images/litho_box_3.webp", (0.111, -0.08, 0.863, 1.08)),
    4: ("models/images/litho_box_4.webp", (0.015, 0.15, 0.98, 0.8735)),
}

PARAMS = dict(walls="1,2,4", gap=8.0, edge_gap=0.5, wall_t=0.84, foot=5.0, margin=3.0,
              tab_every=8.0, tab_w=0.8, tab_h=0.6,
              simplify=0.025)   # mesh tolerance, mm (the panels' own); the plate STL is ~30 MB:
                                # print it from the 3MF, edit the per-wall STLs

MIN_WALL = panel.MIN_WALL
PRODUCT = dict(panel.PRODUCT)
LICENSE_NOTES = panel.LICENSE_NOTES

# the panel's production setup (litho_box_panel.SLICE: walls only, resolution 0.1,
# retraction over 3 mm), measured on this plate: 8 h 12 m vs 10 h 54 m with the old
# 2-wall + zig-zag setup (arachne gave the same time with 40% more retractions)
SLICE = panel.SLICE


def walls_of(p):
    return [int(w) for w in str(p.walls).replace(" ", "").split(",") if w]


def panel_params(n):
    image, crop = WALLS[n]
    return SimpleNamespace(**dict(panel.PARAMS, image=image, crop=crop, fit="wall"))


def _layout(p):
    pp = panel_params(walls_of(p)[0])
    pitch = pp.max_t + p.gap
    n = len(walls_of(p))
    y0, y1 = -p.margin, (n - 1) * pitch + pp.max_t + p.margin
    xin = pp.width / 2 + p.edge_gap                   # end wall inner face
    return pp, pitch, y0, y1, xin


def _box(x0, x1, y0, y1, z0, z1):
    from manifold3d import Manifold
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def _end_wall(p, side):
    """End wall at x = side * (inner face .. + wall_t), a flared foot, and its tabs."""
    from manifold3d import CrossSection, Manifold
    pp, pitch, y0, y1, xin = _layout(p)
    s = side
    top = pp.height - 2.0
    # profile in (outward distance from the inner face, z): wall_t thick, flaring to
    # wall_t + foot at the bed over 1.6 x foot of height (under 35 deg from vertical)
    prof = CrossSection([[(0, 0), (p.wall_t + p.foot, 0), (p.wall_t, p.foot * 1.6),
                          (p.wall_t, top), (0, top)]])
    wall = Manifold.extrude(prof, y1 - y0)            # along +z: (u, z, y)
    wall = wall.rotate((90, 0, 0)).translate((0, y1, 0))   # (u, y, z) with y y0..y1
    if s < 0:
        wall = wall.mirror((1, 0, 0))
    wall = wall.translate((s * xin, 0, 0))
    tabs = []
    sink = 0.1
    for k in range(len(walls_of(p))):
        yc = k * pitch + pp.frame_t / 2               # middle of the 2.6 mm side band
        z = 6.0
        while z <= top - 3:
            near = _box(-sink, 0.01, yc - p.tab_w / 2, yc + p.tab_w / 2, z - p.tab_h / 2, z + p.tab_h / 2)
            far = _box(p.edge_gap - 0.01, p.edge_gap + 0.2, yc - p.tab_w, yc + p.tab_w,
                       z - p.tab_h, z + p.tab_h)
            t = Manifold.batch_hull([near, far])
            if s < 0:
                t = t.mirror((1, 0, 0))
            tabs.append(t.translate((s * pp.width / 2, 0, 0)))
            z += p.tab_every
    return Manifold.batch_boolean([wall] + tabs, __import__("manifold3d").OpType.Add)


def _panels(p):
    _, pitch, *_ = _layout(p)
    out = []
    for k, n in enumerate(walls_of(p)):
        L = lithophane_of(panel_params(n))
        print(f"  wall {n}: " + "; ".join(L.summary()[:1]))
        out.append(L.solid(simplify=p.simplify).translate((0, k * pitch, 0)))
    return out


def build(p):
    from manifold3d import Manifold, OpType
    parts = _panels(p) + [_end_wall(p, 1), _end_wall(p, -1)]
    return Manifold.batch_boolean(parts, OpType.Add)


def _per_panel(p):
    """Every panel's own checks: thinnest picture wall and the fit in the box's slot."""
    def fn(ctx):
        import trimesh
        from cadkit import mesh as meshmod
        msgs, ok = [], True
        box = panel._man(trimesh.load(panel.BOX)) if panel.BOX.exists() else None
        for n in walls_of(p):
            pp = panel_params(n)
            L = lithophane_of(pp)
            lo = float(L.t_pic.min())
            hit = 0.0
            if box is not None:
                solo = panel._man(meshmod.to_trimesh(L.solid()))
                hit = (box ^ solo.translate(panel._in_box(pp))).volume()
            good = lo >= pp.min_t - 0.01 and hit < 0.05
            ok &= good
            msgs.append(f"wall {n}: picture >= {lo:.2f} mm, {hit:.2f} mm3 in the slot")
        return ok, "; ".join(msgs)
    return fn


def checks(p):
    pp, pitch, y0, y1, xin = _layout(p)
    n = len(walls_of(p))
    x = 2 * (xin + p.wall_t + p.foot)
    out = [single_body(), dims(x=x, y=y1 - y0, z=pp.height),
           custom("each panel fits the box", _per_panel(p)),
           custom("tab stub fits the slot clearance", lambda ctx: (
               (panel.SLOT_GAP - pp.width) / 2 > 0.2,
               f"{(panel.SLOT_GAP - pp.width) / 2:.2f} mm per side past the panel edge"))]
    for k in range(n):                                # each panel solid, air between them
        yk = k * pitch
        out.append(solid((0, yk + pp.frame_t / 2, 1.0), (0, yk + pp.frame_t / 2, pp.height - 1.0)))
        if k < n - 1:
            out.append(empty((0, yk + pp.max_t + p.gap / 2, 50), (30, yk + pp.max_t + p.gap / 2, 90)))
        # the panel edge stands clear of the end wall between tabs
        out.append(empty((xin - p.edge_gap / 2, yk + pp.frame_t / 2, 10.0),
                         (-(xin - p.edge_gap / 2), yk + pp.frame_t / 2, 10.0)))
    return out


def extras(p, out, name):
    files, lines = [], []
    for n in walls_of(p):
        f, l = litho_extras(panel_params(n), out, f"{name}_wall_{n}")
        files += f
        lines += [f"wall {n}: {x}" for x in l]
    return files, lines
