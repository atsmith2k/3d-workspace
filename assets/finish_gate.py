"""Finish gate: two gold posts under a checkered banner, the end of a level.

Spec:
  kind: prop
  size: 3.0 x 2.5 x 0.5 m
  pivot: base centre on Y=0, centred on the opening; the player walks through along Z
  budget: 800 triangles, one material (sandbox atlas)
  materials: gold posts on dark plinths; black-and-white checkered banner
  features: posts 0.36 m square on 0.4 m plinths, 2.5 m tall, centres 2.6 m apart; opening 2.2 m wide x 2.0 m high
            (the dungeon doorway is 1.2 x 2.2, so a player carrying a prop fits); banner 0.5 m deep
            in four panels so the checks stay square
  use: the goal of a builder course; pair it with a world-kit `goal`
  engine: body static, auto collider (triangle mesh, so the opening is open)
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "finish gate, gold posts and a checkered banner"
PARAMS = dict(width=3.0, height=2.5, post=0.4, banner=0.5)
BUDGET = dict(tris=800, texture=512, materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["goal", "finish", "gate"],
               gameplay=dict(goal=True, opening_m=[2.2, 2.0]))


def checks(p):
    def opening(ctx):
        v = np.vstack([m.v for m, _ in ctx.model.parts])
        inside = v[(np.abs(v[:, 0]) < 1.09) & (v[:, 1] < 1.99)]
        return len(inside) == 0, "nothing stands in the 2.2 x 2.0 m opening"
    return [size(x=p.width, y=p.height, z=(0.45, 0.55)), tris(max=800), pivot("base"), materials(1),
            texture_size(512), custom("opening", opening)]


def build(p):
    x = p.width / 2 - p.post / 2
    parts = []
    for s in (-1, 1):
        parts.append(tile(bevel_box(p.post, 0.16, p.post + 0.1, 0.02).moved(s * x, 0.08, 0), T.DARK))
        parts.append(tile(bevel_box(p.post - 0.04, p.height - 0.16, p.post - 0.04, 0.03)
                          .moved(s * x, 0.16 + (p.height - 0.16) / 2, 0), T.GOLD))
    span = p.width - 2 * p.post + 0.08                      # reaches 20 mm into each post
    panel = span / 4
    for i in range(4):
        cx = -span / 2 + panel * (i + 0.5)
        parts.append(tile(box(panel, p.banner, 0.12).moved(cx, p.height - p.banner / 2, 0), T.CHECKER))
    return Model((merge(*parts), atlas()))
