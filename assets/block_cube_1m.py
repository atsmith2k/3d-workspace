"""Building block, 1 m cube: the unit of the sandbox building set.

Spec:
  kind: prop
  size: 1.0 x 1.0 x 1.0 m
  pivot: centre of bounds (dynamic; the box collider is centred on the entity)
  budget: 44 triangles, one material (the shared 512 px sandbox atlas)
  materials: blue panel tile, lighter rim on every face
  features: every edge chamfered 40 mm; the flat faces reach the full 1 m
  use: CinderCore sandbox building set; snaps to the 1 m / 2 m grid and stacks flush with the other blocks
  engine: body dynamic, box collider (matches the mesh)
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "building block, 1 m cube"
PARAMS = dict(size=1.0, bevel=0.04)
BUDGET = dict(tris=200, texture=512, materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["block"])


def checks(p):
    return block_checks(p.size, p.size, p.size)


def build(p):
    return Model((tile(bevel_box(p.size, p.size, p.size, p.bevel), T.BLUE), atlas()))
