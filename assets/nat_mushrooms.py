"""Mushrooms: three red-brown caps on pale stems, a gatherable.

Spec:
  kind: environment
  size: about 0.26 x 0.15 x 0.24 m
  pivot: on Y=0, among the stems
  budget: 800 triangles, two materials, no textures
  materials: pale stems; dark red-brown caps (flat colours)
  features: three mushrooms 0.07 to 0.15 m tall; domed caps wider than their stems, each
            tipped a different way
  use: wilderness sub-pack; a gatherable node (matches a future itm_ ingredient); at the
       foot of trees and logs
  engine: no body (a pickup)
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "three mushrooms, gatherable"
PARAMS = dict(seed=0)
BUDGET = dict(BUDGET_OF["small_prop"], materials=2)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "plant", "mushroom", "gatherable", gameplay=dict(gather="mushroom", count=3))

SHROOMS = [((0.0, 0.0), 0.15, 0.065, (6, "z")), ((0.1, 0.06), 0.1, 0.05, (-12, "x")), ((-0.07, -0.07), 0.07, 0.04, (14, "z"))]


def checks(p):
    def caps(ctx):
        stems, tops = ctx.model.parts[0][0], ctx.model.parts[1][0]
        return np.ptp(tops.v[:, 0]) > np.ptp(stems.v[:, 0]) and tops.v[:, 1].min() > 0.02, \
            "caps are wider than the stems and clear of the ground"
    return [size(x=(0.2, 0.32), y=(0.12, 0.17), z=(0.18, 0.3)), tris(max=BUDGET["tris"]), pivot((None, 0.0, None)),
            materials(2), on_ground(), custom("caps", caps)]


def build(p):
    stems, caps = [], []
    for (x, z), h, r, (deg, axis) in SHROOMS:
        stems.append(merge(cylinder(r * 0.34, h * 0.8, 7, r_top=r * 0.26, caps=False), disc(r * 0.34, 0.0, 7, up=False)).moved(x, 0, z))
        cap = merge(lathe([(r, 0.0), (r * 0.92, r * 0.3), (r * 0.6, r * 0.62), (0.0, r * 0.75)], 9), disc(r, 0.0, 9, up=False))
        caps.append(cap.rotated(deg, axis).moved(x, h * 0.74, z))
    return Model((merge(*stems), flat_material("frp_fungus", "fungus", roughness=0.8)),
                 (merge(*caps), flat_material("frp_fungus_cap", "fungus_cap", roughness=0.6)))
