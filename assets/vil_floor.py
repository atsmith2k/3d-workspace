"""Village floor: one 2 m cell of worn boards, walking surface at Y=0.

Spec:
  kind: environment
  size: 2.0 x 0.15 x 2.0 m
  pivot: centre of the top face (the walking surface is the piece's Y=0)
  budget: 1500 triangles, one material, 1024 px textures
  materials: floor boards, eight to the cell, running along X
  use: ground floors (on the ground tiles) and upper storeys (at Y = 3 m per storey)
  engine: body static, auto collider
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village floor, boards"
PARAMS = dict(thick=0.15)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "floor")


def checks(p):
    return piece_checks(GRID, p.thick, GRID, anchor="top", mats=1)


def build(p):
    return Model((tiled(block(GRID, p.thick, GRID, y=-p.thick)), boards()))
