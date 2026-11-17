"""Dungeon wall: a 2 m run of dressed stone on a plinth course.

Spec:
  kind: environment
  size: 2.0 x 3.0 x 0.52 m (wall 0.4 m thick, plinth 60 mm proud each side)
  pivot: base centre on Y=0; the wall is centred on the cell edge and runs along X
  budget: 24 triangles, one material, 1024 px textures
  materials: stone blocks 1.0 x 0.5 m, 512 px per metre, courses continuous across pieces
  use: line the edges of 2 m cells; turn 90 degrees for walls along Z
  engine: body static, auto collider
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon wall, 2 m run"
PARAMS = dict(width=GRID)
BUDGET = dict(tris=24, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    return kit_checks(p.width, WALL_H, WALL_T + 2 * PLINTH_OUT, 24)


def build(p):
    return Model((stoned(wall_run(p.width)), stone()))
