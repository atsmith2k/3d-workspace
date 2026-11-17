"""Building cylinder, 1 m across and 1 m tall: columns, rollers and wheels.

Spec:
  kind: prop
  size: 1.0 x 1.0 x 1.0 m (radius 0.5, height 1.0)
  pivot: centre of bounds (dynamic)
  budget: 128 triangles, one material (the shared 512 px sandbox atlas)
  materials: purple panel tile, lighter rim on every face
  features: 16 sides; rims chamfered 40 mm; stands upright
  use: CinderCore sandbox building set; snaps to the 1 m / 2 m grid and stacks flush with the other blocks
  engine: body dynamic, box collider: the world kit has no cylinder collider, so it stacks and pushes like a 1 m box and does not roll
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "building cylinder, 1 m"
PARAMS = dict(radius=0.5, height=1.0, bevel=0.04, sides=16)
BUDGET = dict(tris=200, texture=512, materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["block"],
               gameplay=dict(collider_wanted="cylinder", radius=0.5, height=1.0),
               notes="Cinder 0.1.1's world kit offers box, sphere and mesh colliders only; a dynamic "
                     "body cannot use a mesh. From Mojo, give it a cylinder shape of radius 0.5 and "
                     "half-height 0.5.")


def checks(p):
    return block_checks(2 * p.radius, p.height, 2 * p.radius)


def cyl(p):
    r, h, b = p.radius, p.height / 2, p.bevel
    side = lathe([(r - b, -h), (r, -h + b), (r, h - b), (r - b, h)], p.sides, smooth=False)
    return merge(side, disc(r - b, -h, p.sides, up=False), disc(r - b, h, p.sides))


def build(p):
    return Model((tile(cyl(p), T.PURPLE), atlas()))
