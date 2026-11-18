"""Standing shelf: open shelves between two plank sides, boarded at the back.

Spec:
  kind: prop
  size: 1.00 x 1.80 x 0.34 m
  pivot: base centre on Y=0; the open front faces +Z, the back stands against a wall
  budget: 3000 triangles, one material, 1024 px textures
  materials: dark weathered timber
  features: four shelves at 0.10, 0.52, 0.94 and 1.36 m, each 30 mm thick and at least 0.38 m
            clear above (a 0.19 m potion or a jar stands on any of them); the top one within
            reach of a 1.8 m person; a top board; a back of boards
  use: interiors sub-pack; against a cottage wall, stocked with itm_ pieces in a world
  engine: body static, auto collider
"""
from _frp_interior import *

KIND = "prop"
DESCRIPTION = "standing shelf, four shelves"
PARAMS = dict(width=1.00, height=1.80, depth=0.34)
SHELVES = (0.10, 0.52, 0.94, 1.36)
BUDGET = dict(BUDGET_OF["large_prop"], materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("interiors", "furniture", "storage",
                  gameplay=dict(shelf_tops=[round(y + 0.03, 3) for y in SHELVES], front="+z", usable_depth=0.28))


def checks(p):
    def clear(ctx):
        gaps = [b - a - 0.03 for a, b in zip(SHELVES, SHELVES[1:] + (p.height - 0.03,))]
        return min(gaps) >= 0.38 - 1e-9, f"clear height above each shelf: {', '.join(f'{g:.2f}' for g in gaps)} m"

    def open_front(ctx):
        v = ctx.model.parts[0][0].v
        tops = SHELVES + (p.height - 0.03,)
        blocked = [a for a, b in zip(tops, tops[1:])
                   if len(v[(np.abs(v[:, 0]) < p.width / 2 - 0.06) & (v[:, 1] > a + 0.05) & (v[:, 1] < b - 0.02) & (v[:, 2] > -p.depth / 2 + 0.06)])]
        return not blocked, "the front is open between the shelves"
    return furniture_checks(p.width, p.height, p.depth, BUDGET["tris"], 1) + [custom("shelf spacing", clear),
                                                                              custom("open front", open_front)]


def build(p):
    w, h, d = p.width, p.height, p.depth
    sides = upright(merge(*[block(0.035, h, d, s * (w / 2 - 0.0175)) for s in (-1, 1)]))
    inner = w - 0.07 + 2 * SINK
    shelves = boards_x(merge(*[block(inner, 0.03, d - 0.03, 0, y, 0.01) for y in SHELVES],
                             block(inner, 0.03, d - 0.01, 0, h - 0.03, 0.0)))
    back = upright(block(inner, h - 0.06, 0.02, 0, 0.04, -d / 2 + 0.012))
    return Model((merge(sides, shelves, back), timber()))
