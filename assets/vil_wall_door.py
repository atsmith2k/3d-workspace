"""Village wall with a doorway: 1.2 x 2.2 m opening in a 2 m run.

Spec:
  kind: environment
  size: 2.0 x 3.0 x 0.32 m
  pivot: base centre on Y=0; the wall is centred on its cell edge and runs along X
  budget: 1500 triangles, two materials (plaster, timber), 1024 px textures
  materials: stained lime plaster panels; weathered dark timbers 30-40 mm proud on both faces
  features: opening 1.2 m wide x 2.2 m high, centred; jambs and a lintel standing proud; no sill across the opening
  use: village sub-pack: one storey of a timber-framed house; both faces finished, so it works
       from the street, from inside (first person) and from above (top-down, roof hidden)
  engine: body static, auto collider (triangle mesh, so the doorway is open)
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village wall with a doorway"
PARAMS = dict(width=GRID)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "timber-frame", "wall")


def checks(p):
    return piece_checks(p.width, STOREY, POST, mats=2) + [
        custom("doorway is open", lambda ctx: (
            not any(((np.abs(m.v[:, 0]) < DOOR_W / 2 - 0.01) & (m.v[:, 1] < DOOR_H - 0.01)).any() for m, _ in ctx.model.parts),
            "nothing stands in the 1.2 x 2.2 m opening"))]


def build(p):
    plaster_mesh, timber_mesh = timber_wall(p.width, "door")
    return Model((plaster_mesh, plaster()), (timber_mesh, timber()))
