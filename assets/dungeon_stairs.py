"""Dungeon stairs: five stone steps rising 1 m over one 2 m cell, climbing toward -Z.

Spec:
  kind: environment
  size: 2.0 x 1.0 x 2.0 m
  pivot: base centre on Y=0
  budget: 60 triangles, one material, 1024 px textures
  materials: flagstones
  features: 5 steps, 0.2 m rise, 0.4 m going
  use: joins a floor at Y=0 to one at Y=1; turn it to change direction
  engine: body static, auto collider (triangle mesh)
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon stairs, 1 m rise"
PARAMS = dict(steps=5, rise=0.2)
BUDGET = dict(tris=60, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    return kit_checks(GRID, p.steps * p.rise, GRID, 60)


def build(p):
    going = GRID / p.steps
    steps = [block(GRID, p.rise * (i + 1), going, z=GRID / 2 - going / 2 - going * i) for i in range(p.steps)]
    return Model((stoned(merge(*steps)), paving()))
