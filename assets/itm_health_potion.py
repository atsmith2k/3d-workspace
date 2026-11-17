"""Health potion: a stoppered flask of red draught, the pack's item convention in one asset.

Spec:
  kind: prop
  size: 0.11 x 0.19 x 0.11 m
  pivot: base centre on Y=0 (it stands on tables and shelves)
  budget: 800 triangles, three materials, no textures
  materials: the draught (deep red, faint glow so it reads in a dark room); glass neck and rim
             (Cinder draws no transparency, so the flask shows its contents as its colour);
             cork stopper
  features: round body 110 mm across, narrow neck, flared rim, cork; 12 sides
  use: items sub-pack; its icon is the frame `health_potion` of ui_item_icons, drawn from the
       same shapes and palette
  engine: no body (a pickup); rest_y 0
"""
from _frp import *

KIND = "prop"
DESCRIPTION = "health potion flask"
PARAMS = dict(radius=0.055, height=0.19)
BUDGET = dict(BUDGET_OF["small_prop"], materials=3)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("items", "potion", "consumable", gameplay=dict(icon="ui_item_icons:health_potion", stack=20))


def checks(p):
    return [size(x=2 * p.radius, y=p.height, z=2 * p.radius, tol=0.004), tris(max=BUDGET["tris"]), pivot("base"),
            materials(3)]


def build(p):
    r = p.radius
    body = merge(lathe([(r * 0.6, 0.0), (r, 0.03), (r, 0.075), (r * 0.55, 0.115), (0.02, 0.125)], 12),
                 disc(r * 0.6, 0.0, 12, up=False))
    neck = lathe([(0.02, 0.125), (0.02, 0.155), (0.028, 0.165), (0.028, 0.17), (0.019, 0.17)], 12)
    cork = merge(lathe([(0.019, 0.165), (0.021, p.height)], 8), disc(0.021, p.height, 8))
    draught = flat_material("frp_draught_red", "potion_red", roughness=0.2, emissive="potion_red", strength=0.4)
    return Model((body, draught), (neck, flat_material("frp_glass", "glass", roughness=0.15)),
                 (cork, flat_material("frp_cork", "wood_light", roughness=0.9)))
