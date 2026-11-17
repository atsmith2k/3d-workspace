"""Building ramp, 2 x 1 x 2 m: rises 1 m over one grid cell, climbing toward -Z.

Spec:
  kind: prop
  size: 2.0 x 1.0 x 2.0 m
  pivot: base centre on Y=0 (it is placed, not thrown)
  budget: 8 triangles, one material (the shared 512 px sandbox atlas)
  materials: grey panel tile, lighter rim on every face
  features: a clean wedge: slope 26.6 degrees, walkable by the character controller
  use: CinderCore sandbox building set; snaps to the 1 m / 2 m grid and stacks flush with the other blocks
  engine: body kinematic, mesh collider (matches the mesh; the builder moves it). A dynamic body cannot have a mesh collider in Cinder, and a box would not match a wedge
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "building ramp, 1 m rise over 2 m"
PARAMS = dict(width=2.0, rise=1.0, run=2.0)
BUDGET = dict(tris=200, texture=512, materials=1)
ENGINE = dict(body="kinematic", collider="mesh", rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["block"],
               gameplay=dict(collider_wanted="convex hull, dynamic"),
               notes="Delivered kinematic with a triangle-mesh collider, which matches the wedge and "
                     "lets a builder move it. For a dynamic ramp, give it a convex hull from Mojo "
                     "(physics.convex_hull of its six corners).")


def checks(p):
    return block_checks(p.width, p.rise, p.run, tris_max=200, anchor="base")


def build(p):
    return Model((tile(wedge(p.width, p.rise, p.run), T.GREY), atlas()))
