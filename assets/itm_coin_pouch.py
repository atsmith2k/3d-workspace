"""Coin pouch: a small leather purse, drawn shut with a cord.

Spec:
  kind: prop
  size: 0.12 x 0.13 x 0.12 m
  pivot: base centre on Y=0
  budget: 800 triangles, two materials, no textures
  materials: worn leather; an undyed cord
  features: a slumped, round body widest low down; a gathered neck; a cord tied round the
            neck; a ruffle above it
  use: items sub-pack (valuables): gold as loot; icon frame `coin_pouch`
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "leather coin pouch"
PARAMS = dict(radius=0.06, height=0.13)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("coin_pouch", "valuable", "gold", stack=1)


def checks(p):
    def slumped(ctx):
        v = ctx.model.parts[0][0].v
        r = np.hypot(v[:, 0], v[:, 2])
        return v[r.argmax(), 1] < 0.45 * p.height, f"widest {v[r.argmax(), 1] * 1000:.0f} mm up: the coins sit low"
    return item_checks(2 * p.radius, p.height, 2 * p.radius, 2) + [custom("slumped", slumped)]


def build(p):
    r, h = p.radius, p.height
    body = merge(lathe([(r * 0.7, 0.0), (r, h * 0.2), (r * 0.94, h * 0.42), (r * 0.5, h * 0.68), (r * 0.3, h * 0.76),
                        (r * 0.52, h * 0.92), (r * 0.6, h), (r * 0.4, h * 0.94), (0.0, h * 0.8)], 10),
                 disc(r * 0.7, 0.0, 10, up=False))
    cord = torus(r * 0.34, 0.006, 10, 5).moved(0, h * 0.75, 0)
    return Model((body, flat_material("frp_leather", "leather", roughness=0.8)),
                 (cord, flat_material("frp_cord", "cloth_undyed", roughness=0.95)))
