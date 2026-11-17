"""Village wall with a window: 0.8 x 1.0 m opening, sill at 1.1 m.

Spec:
  kind: environment
  size: 2.0 x 3.0 x 0.32 m
  pivot: base centre on Y=0; the wall is centred on its cell edge and runs along X
  budget: 1500 triangles, two materials (plaster, timber), 1024 px textures
  materials: stained lime plaster panels; weathered dark timbers 30-40 mm proud on both faces
  features: opening 0.8 x 1.0 m with its sill 1.1 m above the floor; a proud sill board; a lattice of bars in place of glass (Cinder draws no transparency yet)
  use: village sub-pack: one storey of a timber-framed house; both faces finished, so it works
       from the street, from inside (first person) and from above (top-down, roof hidden)
  engine: body static, auto collider (triangle mesh)
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village wall with a latticed window"
PARAMS = dict(width=GRID)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "timber-frame", "wall")


def checks(p):
    return piece_checks(p.width, STOREY, POST + 0.06, mats=2) + [
        custom("window looks out at eye level", lambda ctx: (
            WINDOW_SILL < 1.6 < WINDOW_SILL + WINDOW_H, "a standing person's eye line (1.6 m) is inside the opening"))]


def build(p):
    plaster_mesh, timber_mesh = timber_wall(p.width, "window")
    return Model((plaster_mesh, plaster()), (timber_mesh, timber()))
