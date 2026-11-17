"""Dungeon floor tile: one 2 m cell of worn flagstones, walking surface at Y=0.

Spec:
  kind: environment
  size: 2.0 x 0.2 x 2.0 m
  pivot: centre of the top face (the walking surface is Y=0, so walls and props stand at Y=0)
  budget: 12 triangles, one material, 1024 px textures
  materials: flagstones, 0.5 m flags, 512 px per metre
  use: tile on the 2 m grid under every cell of a dungeon
  engine: body static, auto collider
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon floor tile, 2 m flagstones"
PARAMS = dict(thick=0.2)
BUDGET = dict(tris=12, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    return kit_checks(GRID, p.thick, GRID, 12, anchor="top")


def build(p):
    return Model((stoned(block(GRID, p.thick, GRID, y=-p.thick)), paving()))
