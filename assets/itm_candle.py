"""Candle: a tallow candle burning in an iron dish.

Spec:
  kind: prop
  size: 0.11 x 0.17 x 0.11 m
  pivot: base centre on Y=0
  budget: 800 triangles, three materials, no textures
  materials: dark iron dish with a ring handle; yellowed tallow; a flame (emissive, strength
             1.2: a point light beside it does the lighting)
  features: a shallow dish 0.11 m across; a candle 28 mm thick burnt down unevenly; a flame
            25 mm tall above the wick
  use: items sub-pack (tools) and room dressing: on int_table and the hearth's mantel; icon
       frame `candle`. Place a small warm point light at the flame (intensity about 6, range 3)
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "tallow candle in an iron dish"
PARAMS = dict(dish=0.055, height=0.17)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("candle", "tool", "light", stack=5,
               light=dict(kind="point", at=(0.0, 0.16, 0.0), color=(1.0, 0.6, 0.25), intensity=6, range=3))


def checks(p):
    def flame(ctx):
        mesh, mat = ctx.model.parts[2]
        return mat.emissive_strength <= 1.5 and mesh.v[:, 1].min() > 0.12, f"the flame glows at strength {mat.emissive_strength}, above the candle"
    return item_checks(2 * p.dish, p.height, 2 * p.dish, 3) + [custom("flame", flame)]


def build(p):
    d, h = p.dish, p.height
    dish = merge(lathe([(d * 0.6, 0.0), (d, 0.012), (d, 0.018)], 12), lathe([(d, 0.018), (d * 0.9, 0.012), (d * 0.3, 0.006)], 12),
                 disc(d * 0.6, 0.0, 12, up=False), disc(d * 0.3, 0.006, 12))
    top = h - 0.03
    wax = merge(lathe([(0.014, 0.005), (0.014, top - 0.012), (0.012, top)], 9, smooth=False), disc(0.012, top, 9),
                lathe([(0.02, 0.006), (0.016, 0.014), (0.014, 0.02)], 9))                       # a pool of drips at the foot
    wick = cylinder(0.0015, 0.008, 4).moved(0, top, 0)
    flame = lathe([(0.0, top + 0.004), (0.006, top + 0.011), (0.004, top + 0.02), (0.0, h)], 6)
    return Model((dish, flat_material("frp_dish_iron", "iron", roughness=0.6, metallic=1.0)),
                 (merge(wax, wick), flat_material("frp_tallow", "bone", roughness=0.6)),
                 (flame, flat_material("frp_flame", "ember", roughness=0.9, emissive="ember", strength=1.2)))
