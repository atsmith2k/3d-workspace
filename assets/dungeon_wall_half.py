"""Dungeon half wall: a 1 m run, to close gaps the 2 m wall cannot.

Spec:
  kind: environment
  size: 1.0 x 3.0 x 0.52 m
  pivot: base centre on Y=0
  budget: 24 triangles, one material, 1024 px textures
  materials: stone blocks, as dungeon_wall
  use: fill a half cell beside a doorway or at the end of a run
  engine: body static, auto collider
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon wall, 1 m run"
PARAMS = dict(width=GRID / 2)
BUDGET = dict(tris=24, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    return kit_checks(p.width, WALL_H, WALL_T + 2 * PLINTH_OUT, 24)


def build(p):
    return Model((stoned(wall_run(p.width)), stone()))
