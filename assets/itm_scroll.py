"""Scroll: a roll of parchment tied with a red ribbon.

Spec:
  kind: prop
  size: 0.26 x 0.05 x 0.05 m
  pivot: on Y=0, at the middle of its length; it lies along X
  budget: 800 triangles, two materials, no textures
  materials: old parchment; a dull red ribbon
  features: a roll 46 mm thick with the ends rolled a little tighter (it reads as a roll,
            not a rod); a ribbon 20 mm wide round the middle with a knot on top
  use: items sub-pack (scrolls and books): a spell scroll, a letter, a map; icon frame `scroll`
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "rolled parchment scroll"
PARAMS = dict(length=0.26, radius=0.023)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("scroll", "scroll", "readable", stack=10)


def checks(p):
    def ribbon(ctx):
        roll, band = ctx.model.parts[0][0], ctx.model.parts[1][0]
        return np.ptp(band.v[:, 0]) < 0.05 and band.v[:, 1].max() > roll.v[:, 1].max(), "a narrow ribbon with its knot on top"
    return item_checks(p.length, (0.046, 0.058), (0.046, 0.052), 2) + [custom("ribbon", ribbon)]


def build(p):
    L, r = p.length, p.radius
    prof = [(r * 0.55, -L / 2), (r * 0.9, -L / 2), (r, -L / 2 + 0.02), (r, L / 2 - 0.02), (r * 0.9, L / 2), (r * 0.55, L / 2)]
    roll = merge(lathe(prof, 10), disc(r * 0.55, -L / 2, 10, up=False), disc(r * 0.55, L / 2, 10))
    band = lathe([(r + 0.002, -0.01), (r + 0.002, 0.01)], 10, smooth=False)
    knot = bevel_box(0.010, 0.018, 0.022, 0.003).moved(r + 0.004, 0, 0)

    def lay(m):                                                   # built along Y, laid along X, resting on Y=0
        return m.rotated(90, "z").moved(0, r, 0)
    return Model((lay(roll), flat_material("frp_parchment", "plaster", roughness=0.9)),
                 (lay(merge(band, knot)), flat_material("frp_ribbon", "cloth_red", roughness=0.85)))
