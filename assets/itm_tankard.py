"""Tankard: a coopered wooden mug with iron bands.

Spec:
  kind: prop
  size: about 0.14 x 0.14 x 0.10 m (handle included)
  pivot: on Y=0, under the cup
  budget: 800 triangles, three materials, no textures
  materials: wood; dark iron bands and handle; ale (dark, a little below the rim)
  features: a straight-sided cup 0.10 m across, slightly wider at the foot; two iron bands;
            a handle on +X big enough for three fingers; the inside is modelled (a
            first-person camera looks down into it) and holds ale 15 mm below the rim
  use: items sub-pack (food and drink) and tavern dressing; icon frame `tankard`
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "wooden tankard with iron bands"
PARAMS = dict(radius=0.05, height=0.14)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("tankard", "drink", "consumable", stack=1)


def checks(p):
    def hollow(ctx):
        ale = ctx.model.parts[2][0]
        y = float(ale.v[:, 1].max())
        return p.height - 0.03 < y < p.height - 0.008, f"the ale stands {1000 * (p.height - y):.0f} mm below the rim: the cup is hollow"

    def grip(ctx):
        v = ctx.model.parts[1][0].v
        reach = float(v[:, 0].max()) - p.radius
        return reach > 0.03, f"the handle stands {reach * 1000:.0f} mm off the cup"
    return item_checks((0.13, 0.15), p.height, (0.1, 0.11), 3) + [custom("hollow", hollow), custom("handle", grip)]


def build(p):
    r, h = p.radius, p.height
    cup = merge(lathe([(r * 1.04, 0.0), (r, h)], 12), lathe([(r, h), (r - 0.008, h)], 12),
                lathe([(r - 0.008, h), (r - 0.008, h - 0.03)], 12), disc(r * 1.04, 0.0, 12, up=False))
    bands = merge(*[lathe([(r * (1.04 - 0.04 * y / h) + 0.002, y), (r * (1.04 - 0.04 * (y + 0.014) / h) + 0.002, y + 0.014)], 12,
                          smooth=False) for y in (0.018, h - 0.04)])
    handle = merge(*[block(0.04 + 0.006, 0.012, 0.016, r + 0.018, y) for y in (0.03, h - 0.045)],
                   block(0.012, h - 0.063, 0.016, r + 0.036, 0.03))
    ale = disc(r - 0.008, h - 0.015, 12)
    return Model((cup, flat_material("frp_tankard_wood", "wood_mid", roughness=0.8)),
                 (merge(bands, handle), flat_material("frp_tankard_iron", "iron", roughness=0.6, metallic=1.0)),
                 (ale, flat_material("frp_ale", "wood_rot", roughness=0.15)))
