"""Village door: a boarded door with rusted iron straps, hinged at its edge.

Spec:
  kind: environment
  size: 1.16 x 2.16 x 0.10 m
  pivot: the foot of the hinge edge (X = 0, Y = 0): a game swings it about its origin; it
         extends toward +X
  budget: 800 triangles, two materials, 1024 px textures
  materials: dark vertical boards; rusted iron straps and a ring pull
  features: fits the 1.2 x 2.2 m doorway with 20 mm clearance each side
  use: in vil_wall_door, placed at the left jamb. In a kit world it slides with the `door`
       component; from Mojo it swings on its origin
  engine: body static, auto collider
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village door, boards and iron"
PARAMS = dict(width=1.16, height=2.16, thick=0.06)
BUDGET = BUDGET_OF["small_prop"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "door", gameplay=dict(hinge="origin, vertical axis", opens="about +Y"))


def checks(p):
    return [size(x=p.width, y=p.height, z=(0.08, 0.14)), tris(max=BUDGET["tris"]), pivot((0.0, 0.0, None)),
            materials(2), texture_size(1024),
            custom("fits the doorway", lambda ctx: (
                ctx.params["width"] < DOOR_W and ctx.params["height"] < DOOR_H, "20 mm clear on each side and above"))]


def build(p):
    slab = block(p.width, p.height, p.thick, x=p.width / 2)
    slab = directed_uv(slab, np.c_[slab.v[:, 1] / TILE, slab.v[:, 0] / TILE * 2], "z")   # boards run up the door
    straps = [block(p.width - 0.06, 0.08, p.thick + 0.03, x=(p.width - 0.06) / 2, y=y) for y in (0.3, 1.04, 1.78)]
    ring = torus(0.05, 0.008, 12, 6).rotated(90, "x").moved(p.width - 0.16, 1.0, -(p.thick / 2 + 0.02))
    return Model((slab, timber()), (box_uv(merge(*straps, ring), 3.0), iron_rusted()))
