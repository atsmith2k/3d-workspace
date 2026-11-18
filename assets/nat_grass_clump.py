"""Grass clump: a fan of dying blades, two-sided geometry.

Spec:
  kind: environment
  size: about 0.6 x 0.5 x 0.6 m
  pivot: on Y=0, at the root
  budget: 800 triangles, one material, no textures
  materials: one flat colour, dead grass (no sampler: clumps are placed by the dozen)
  features: sixteen blades 0.3 to 0.55 m long, leaning outward, each bent once; two-sided,
            so no blade vanishes seen from behind
  use: wilderness sub-pack; scattered on nat_ground to break up the flat
  engine: no body
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "clump of dying grass"
PARAMS = dict(seed=4, blades=16)
BUDGET = dict(BUDGET_OF["small_prop"], materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "plant", "grass")


def checks(p):
    def both_sides(ctx):
        m = ctx.model.parts[0][0]
        fn = np.cross(m.v[m.f[:, 1]] - m.v[m.f[:, 0]], m.v[m.f[:, 2]] - m.v[m.f[:, 0]])
        return abs(fn.sum(0)).max() < 1e-9, "every blade has a front and a back"
    return [size(x=(0.4, 0.8), y=(0.35, 0.6), z=(0.4, 0.8)), tris(max=BUDGET["tris"]), pivot((None, 0.0, None)),
            materials(1), on_ground(), custom("two-sided", both_sides)]


def build(p):
    rng = np.random.default_rng(p.seed)
    blades = []
    for k in range(p.blades):
        a = 2 * np.pi * k / p.blades + rng.uniform(-0.2, 0.2)
        out = np.array([np.cos(a), 0, np.sin(a)])
        root = out * rng.uniform(0.02, 0.1)
        length, lean = rng.uniform(0.3, 0.55), rng.uniform(0.15, 0.5)
        tip = root + out * length * lean + [0, length * (1 - 0.5 * lean), 0]
        blades.append(blade(root, tip, rng.uniform(0.025, 0.04), lean=out * -0.03 + [0, 0.03, 0]))
    return Model((merge(*blades), flat_material("frp_grass_dead", "grass_dead", roughness=0.95)))
