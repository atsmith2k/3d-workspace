"""Dungeon corner pier: a square post that closes the corner where two walls meet.

Spec:
  kind: environment
  size: 0.62 x 3.1 x 0.62 m (pier 0.5 m square, plinth and cap 60 mm proud, 0.1 m above the walls)
  pivot: base centre on Y=0, on the grid corner
  budget: 36 triangles, one material, 1024 px textures
  materials: stone blocks, as dungeon_wall
  use: on every grid corner where walls end or turn; hides the joint
  engine: body static, auto collider
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon corner pier"
PARAMS = dict(pier=0.5, cap=0.25)
BUDGET = dict(tris=36, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    return kit_checks(p.pier + 2 * PLINTH_OUT, WALL_H + 0.1, p.pier + 2 * PLINTH_OUT, 36)


def build(p):
    out = p.pier + 2 * PLINTH_OUT
    top = WALL_H + 0.1
    parts = [block(out, PLINTH_H, out), block(p.pier, top - PLINTH_H - p.cap, p.pier, y=PLINTH_H),
             block(out, p.cap, out, y=top - p.cap)]
    return Model((stoned(merge(*parts)), stone()))
