"""Bench: a plank on two slab ends, for the long side of a table.

Spec:
  kind: prop
  size: 1.20 x 0.45 x 0.30 m
  pivot: base centre on Y=0
  budget: 800 triangles, one material, 1024 px textures
  materials: dark weathered timber
  features: seat plank 45 mm thick at 0.45 m; two slab ends set in 0.12 m with a notch cut
            from the foot of each (two feet, so it does not rock); one rail under the seat
  use: interiors sub-pack; along int_table, against a wall, outside a door
  engine: body static, auto collider
"""
from _frp_interior import *

KIND = "prop"
DESCRIPTION = "plank bench on slab ends"
PARAMS = dict(length=1.20, depth=0.30, height=SEAT_H)
BUDGET = dict(BUDGET_OF["small_prop"], materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("interiors", "furniture", "seat", gameplay=dict(seat_y=SEAT_H, seats=2))


def checks(p):
    def notch(ctx):
        v = ctx.model.parts[0][0].v
        under = v[(v[:, 1] < 0.005) & (np.abs(v[:, 2]) < 0.04)]
        return len(under) == 0, "each end stands on two feet: nothing touches the floor under its middle"
    return furniture_checks(p.length, p.height, p.depth, BUDGET["tris"], 1) + [custom("notched feet", notch)]


def build(p):
    h = p.height - 0.045
    seat = planked(p.length, 0.045, p.depth, h, boards=2, seed=3)
    ex = p.length / 2 - 0.12 - 0.02
    ends = []
    for s in (-1, 1):
        for z in (-1, 1):                                          # two feet a side, joined above the notch
            ends.append(block(0.04, h + SINK, 0.09, s * ex, 0, z * (p.depth / 2 - 0.045 - 0.01)))
        ends.append(block(0.04, h - 0.1 + SINK, p.depth - 0.2 + 2 * SINK, s * ex, 0.1))
    rail = boards_x(block(2 * ex, 0.07, 0.03, 0, h - 0.068))
    return Model((merge(seat, upright(merge(*ends)), rail), timber()))
