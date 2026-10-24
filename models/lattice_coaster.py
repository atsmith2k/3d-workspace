"""Drink coaster: a rounded square slab with a solid skin and a gyroid lattice inside
(light, uses little filament, no infill needed), with raised text on top. Built as a
signed-distance field (cadkit.sdf), meshed with manifold's level set, then unioned
with text from cadkit.relief. Demonstrates the SDF kernel and mesh text together.

Spec:
  object:       coaster for a mug
  overall:      size x size x thickness, corners rounded, flat top and bottom
  must have:    closed 1.6 mm skin all round, gyroid lattice inside, label on top
  orientation:  flat on the bed; no overhangs, no supports
  tolerances:   none

Units: mm. Z is up, the coaster sits on Z=0.
"""
from cadkit.checks import *
from cadkit.relief import extrude, text
from cadkit.sdf import *

DESCRIPTION = "Lattice-filled coaster with raised text (SDF kernel + mesh text demo)"

PARAMS = dict(
    size=90.0,
    thickness=8.0,
    corner=10.0,       # corner radius in plan
    skin=1.6,          # solid skin all round
    cell=7.0,          # gyroid cell
    strut=1.6,         # lattice wall thickness
    label="A1",
    label_size=22.0,
    label_height=0.6,
    edge=0.6,          # SDF grid spacing (0.5 is finer but the STL passes 25 MB)
)


def checks(p):
    return [
        dims(x=p.size, y=p.size, z=p.thickness + p.label_height),
        solid((0, 0, p.skin / 2), (0, 0, p.thickness - p.skin / 2),
              (p.size / 2 - p.skin / 2, 0, p.thickness / 2)),      # skin top, bottom, side
        thickness_at((0, p.size / 4, p.thickness - 0.2), p.skin - 0.3),
        flat_base(p.size * p.size * 0.8),
        no_overhang(),
        single_body(),
    ]


def build(p):
    # plan-rounded corners: a box rounded by `corner` then cut flat top and bottom
    slab = intersect(box(p.size, p.size, p.thickness + 2 * p.corner, c=(0, 0, p.thickness / 2), r=p.corner),
                     plane((0, 0, 1), p.thickness), plane((0, 0, -1), 0))
    body = lattice_fill(slab, cell=p.cell, wall=p.strut, skin=p.skin)
    m = build_sdf(body, (-p.size / 2 - 1, -p.size / 2 - 1, -0.5, p.size / 2 + 1, p.size / 2 + 1, p.thickness + 0.5),
                  edge=p.edge)
    label = extrude(text(p.label, p.label_size, bold=True), p.label_height + 0.1, z=p.thickness - 0.1)
    return m + label
