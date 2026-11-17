"""Village corner post: the timber that stands on a grid corner where two walls meet.

Spec:
  kind: environment
  size: 0.36 x 3.0 x 0.36 m
  pivot: base centre on Y=0, on the grid corner
  budget: 1500 triangles, one material, 512 px textures
  materials: weathered timber
  use: on every corner of a timber-framed house; it covers the joint of two 0.3 m walls
  engine: body static, auto collider
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village corner post"
PARAMS = dict(side=0.36)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "timber-frame")


def checks(p):
    return piece_checks(p.side, STOREY, p.side, mats=1) + [
        custom("covers the wall joint", lambda ctx: (ctx.params["side"] > POST, "wider than the walls it joins"))]


def build(p):
    return Model((grain_up(block(p.side, STOREY, p.side)), timber()))
