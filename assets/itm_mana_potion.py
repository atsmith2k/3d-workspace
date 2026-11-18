"""Mana potion: a tall, narrow flask of blue draught.

Spec:
  kind: prop
  size: 0.09 x 0.22 x 0.09 m
  pivot: base centre on Y=0
  budget: 800 triangles, three materials, no textures
  materials: the draught (deep blue, faint glow); glass neck and rim; cork stopper
  features: the health potion's flask drawn taller and narrower, so the two are told apart
            by silhouette as well as colour (the icon keeps the difference)
  use: items sub-pack; icon frame `mana_potion` of ui_item_icons
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "mana potion flask"
PARAMS = dict(radius=0.045, height=0.22)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("mana_potion", "potion", "consumable", stack=20)


def checks(p):
    return item_checks(2 * p.radius, p.height, 2 * p.radius, 3) + [
        custom("narrower than the health potion", lambda ctx: (p.radius < 0.055 and p.height > 0.19, "taller and narrower: read by outline"))]


def build(p):
    return flask(p.radius, p.height, "potion_blue", "potion_blue")
