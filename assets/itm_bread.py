"""Bread: a round country loaf, scored with a cross.

Spec:
  kind: prop
  size: 0.22 x 0.10 x 0.22 m
  pivot: base centre on Y=0
  budget: 800 triangles, two materials, no textures
  materials: dark crust; pale crumb showing in the scoring
  features: a domed round loaf, flat underneath; a cross cut in the top, 12 mm wide,
            showing the crumb
  use: items sub-pack (food); on a table or shelf; icon frame `bread`
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "round loaf of bread"
PARAMS = dict(radius=0.11, height=0.10)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("bread", "food", "consumable", stack=10, restores="health")


def checks(p):
    def scored(ctx):
        cut = ctx.model.parts[1][0]
        return cut.v[:, 1].max() > p.height - 0.004 and np.ptp(cut.v[:, 0]) > p.radius and np.ptp(cut.v[:, 2]) > p.radius, "the cross shows on top of the loaf"
    return item_checks(2 * p.radius, p.height, 2 * p.radius, 2) + [custom("scored", scored)]


def build(p):
    r, h = p.radius, p.height
    loaf = merge(lathe([(r * 0.82, 0.0), (r, h * 0.3), (r * 0.9, h * 0.62), (r * 0.6, h * 0.88), (0.0, h - 0.003)], 12),
                 disc(r * 0.82, 0.0, 12, up=False))
    rho = np.linspace(-0.6, 0.6, 7) * r                             # the scoring follows the dome, 1.5 mm proud of it
    y = np.interp(np.abs(rho), [0.0, 0.6 * r], [h - 0.003, h * 0.88]) + 0.0015
    v = np.array([(x, yy, s * 0.006) for x, yy in zip(rho, y) for s in (-1, 1)])
    f = [t for i in range(len(rho) - 1) for t in ((2 * i, 2 * i + 1, 2 * i + 3), (2 * i, 2 * i + 3, 2 * i + 2))]
    strip = flat(Mesh(v, f))
    if strip.n[:, 1].mean() < 0:
        strip = flat(Mesh(v, np.array(f)[:, ::-1]))
    cut = merge(strip, strip.rotated(90, "y"))
    return Model((loaf, flat_material("frp_crust", "crust", roughness=0.85)),
                 (cut, flat_material("frp_crumb", "plaster_light", roughness=0.95)))
