"""Village gable: the triangular end wall that closes a thatched roof over a 4 m deep house.

Spec:
  kind: environment
  size: 4.0 x 2.0 x 0.32 m
  pivot: base centre on Y=0 (placed at wall-top height)
  budget: 1500 triangles, two materials, 1024 px textures
  materials: stained plaster; a timber tie beam along the base, a king post to the apex, a collar
             half way up and two queen posts
  use: one at each end of a roof; turn it 90 degrees for a ridge that runs along Z
  engine: body static, auto collider
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village gable end"
PARAMS = dict(depth=2 * GRID)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=STOREY)
PRODUCT = product("village", "building", "roof")


def checks(p):
    return piece_checks(p.depth, p.depth / 2, POST, mats=2)


def build(p):
    plaster_mesh, timber_mesh = gable(p.depth)
    return Model((plaster_mesh, plaster()), (timber_mesh, timber()))
