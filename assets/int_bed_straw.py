"""Straw bed: a low box frame, a straw-stuffed tick, a blanket and a bolster.

Spec:
  kind: prop
  size: 0.95 x 0.62 x 2.00 m (head board the highest point)
  pivot: base centre on Y=0; the head is at -Z
  budget: 3000 triangles, four materials, 1024 px textures
  materials: dark timber frame; straw tick (undyed cloth); a muted blue blanket; a bolster
  features: sleeping surface 1.9 m long (a 1.8 m person lies on it) at about 0.4 m; a head
            board 0.62 m high and a lower foot board; the blanket covers the foot two thirds
            and hangs over both sides; four corner posts
  use: interiors sub-pack; against a wall of the cottage
  engine: body static, auto collider
"""
from _frp_interior import *

KIND = "prop"
DESCRIPTION = "straw bed with a blanket"
PARAMS = dict(width=0.95, length=2.00, head=0.62)
BUDGET = dict(BUDGET_OF["large_prop"], materials=4)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("interiors", "furniture", "bed", gameplay=dict(lie_y=0.40, head="-z"))


def checks(p):
    def lies(ctx):
        tick = ctx.model.parts[1][0]
        lo, hi = tick.bounds
        return hi[2] - lo[2] >= 1.85 and 0.34 < hi[1] < 0.46, f"the tick is {hi[2] - lo[2]:.2f} m long, its top {hi[1]:.2f} m up"

    def covered(ctx):
        tick, blanket = ctx.model.parts[1][0], ctx.model.parts[2][0]
        share = (blanket.bounds[1][2] - blanket.bounds[0][2]) / (tick.bounds[1][2] - tick.bounds[0][2])
        over = blanket.bounds[1][0] - tick.bounds[1][0]
        return 0.55 < share < 0.8 and over > 0.01 and blanket.bounds[1][1] > tick.bounds[1][1], \
            f"the blanket covers {share:.0%} of the length and lies over the tick"
    return furniture_checks(p.width, p.head, p.length, BUDGET["tris"], 4) + [custom("long enough to lie on", lies),
                                                                             custom("blanket", covered)]


def build(p):
    w, l = p.width, p.length
    post = 0.08
    px, pz = w / 2 - post / 2, l / 2 - post / 2
    posts = upright(merge(*[block(post, p.head if z < 0 else 0.48, post, x, 0, z) for x in (-px, px) for z in (-pz, pz)]))
    sides = boards_z(merge(*[block(0.035, 0.2, 2 * pz, s * px, 0.14) for s in (-1, 1)]))
    head = boards_x(block(2 * px, 0.34, 0.035, 0, 0.24, -pz))
    foot = boards_x(block(2 * px, 0.22, 0.035, 0, 0.2, pz))
    slats = boards_x(block(2 * px, 0.03, 2 * pz, 0, 0.2))
    inner_w, inner_l = 2 * px - 0.05, 2 * pz - 0.06
    tick = bevel_box(inner_w, 0.19, inner_l, 0.05).moved(0, 0.225 + 0.095, 0)
    b_len = inner_l * 0.66
    blanket = bevel_box(inner_w + 0.035, 0.2, b_len, 0.05).moved(0, 0.332, inner_l / 2 - b_len / 2 + 0.01)
    bolster = bevel_box(inner_w - 0.14, 0.11, 0.3, 0.045).moved(0, 0.46, -inner_l / 2 + 0.2)
    return Model((merge(posts, sides, head, foot, slats), timber()),
                 (tick, flat_material("frp_tick", "cloth_undyed", roughness=0.95)),
                 (blanket, flat_material("frp_blanket", "cloth_blue", roughness=0.95)),
                 (bolster, flat_material("frp_bolster", "plaster", roughness=0.95)))
