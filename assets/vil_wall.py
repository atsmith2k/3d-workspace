"""Village wall: a 2 m run of timber frame and plaster.

Spec:
  kind: environment
  size: 2.0 x 3.0 x 0.32 m
  pivot: base centre on Y=0; the wall is centred on its cell edge and runs along X
  budget: 1500 triangles, two materials (plaster, timber), 1024 px textures
  materials: stained lime plaster panels; weathered dark timbers 30-40 mm proud on both faces
  features: half posts at both ends (two neighbours make one post), sill beam, mid rail at 1.44 m, top plate
  use: village sub-pack: one storey of a timber-framed house; both faces finished, so it works
       from the street, from inside (first person) and from above (top-down, roof hidden)
  engine: body static, auto collider (triangle mesh)
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village wall, timber frame and plaster"
PARAMS = dict(width=GRID)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "timber-frame", "wall")


def checks(p):
    return piece_checks(p.width, STOREY, POST, mats=2)


def build(p):
    plaster_mesh, timber_mesh = timber_wall(p.width, None)
    return Model((plaster_mesh, plaster()), (timber_mesh, timber()))
