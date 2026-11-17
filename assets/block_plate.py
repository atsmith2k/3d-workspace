"""Building plate, 2 x 0.2 x 2 m: floors, roofs and platforms.

Spec:
  kind: prop
  size: 2.0 x 0.2 x 2.0 m
  pivot: centre of bounds (dynamic)
  budget: 44 triangles, one material (the shared 512 px sandbox atlas)
  materials: green panel tile, lighter rim on every face
  features: every edge chamfered 30 mm
  use: CinderCore sandbox building set; snaps to the 1 m / 2 m grid and stacks flush with the other blocks
  engine: body dynamic, box collider (matches the mesh)
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "building plate, 2 x 0.2 x 2 m"
PARAMS = dict(size=2.0, thick=0.2, bevel=0.03)
BUDGET = dict(tris=200, texture=512, materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["block"])


def checks(p):
    return block_checks(p.size, p.thick, p.size)


def build(p):
    return Model((tile(bevel_box(p.size, p.thick, p.size, p.bevel), T.GREEN), atlas()))
