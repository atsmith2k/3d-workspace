"""Leaf litter: fallen leaves lying under a tree.

Spec:
  kind: environment
  size: about 3.2 x 0.04 x 3.2 m
  pivot: the centre of the scatter, on Y=0
  budget: 800 triangles, two materials, no textures
  materials: two flat colours, rust and a paler autumn brown (no samplers)
  features: a hundred and seventy leaves 13 to 21 cm long (larger than life: at life size
            they are specks from eye height), densest in the middle and thinning
            outward; each lies 4 to 20 mm above the ground at its own tilt (none flat in the
            ground's own plane); two-sided
  use: wilderness sub-pack: under nat_tree_autumn, along a path, in a doorway. It breaks up a
       flat ground for almost nothing
  engine: no body
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "scatter of fallen leaves"
PARAMS = dict(seed=8, leaves=170, radius=1.6)
BUDGET = dict(BUDGET_OF["small_prop"], materials=2)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "plant", "litter", "autumn")


def checks(p):
    def off_the_ground(ctx):
        lo = min(float(m.v[:, 1].min()) for m, _ in ctx.model.parts)
        return lo >= 0.003, f"the lowest leaf point is {lo * 1000:.0f} mm above the ground: no flicker"

    def thins_out(ctx):
        v = np.vstack([m.v for m, _ in ctx.model.parts])
        r = np.hypot(v[:, 0], v[:, 2])
        inner, outer = (r < p.radius / 2).sum(), (r >= p.radius / 2).sum()
        return inner > outer / 3 * 1.5, f"{inner} leaf corners in the inner half of the radius, {outer} in the outer three quarters of the area"
    return [size(x=(2.6, 3.8), y=(0.01, 0.07), z=(2.6, 3.8)), tris(max=BUDGET["tris"]), pivot((0.5, None, 0.5), tol=0.3),
            materials(2), custom("off the ground", off_the_ground), custom("thins outward", thins_out)]


def build(p):
    rng = np.random.default_rng(p.seed)
    groups = [[], []]
    for i in range(p.leaves):
        r = p.radius * rng.random() ** 0.8
        a = rng.uniform(0, 2 * np.pi)
        length, width = rng.uniform(0.13, 0.21), rng.uniform(0.08, 0.12)
        leaf = Mesh([(-length / 2, 0, 0), (0, 0, width / 2), (length / 2, 0, 0), (0, 0, -width / 2)], [(0, 1, 2), (0, 2, 3)])
        leaf = leaf.rotated(float(rng.uniform(-9, 9)), "x").rotated(float(rng.uniform(-9, 9)), "z").rotated(float(rng.uniform(0, 360)), "y")
        leaf = leaf.moved(r * np.cos(a), 0, r * np.sin(a))
        leaf = leaf.moved(0, 0.004 - leaf.bounds[0][1] + rng.uniform(0, 0.006), 0)
        groups[i % 3 == 0].append(two_sided(leaf))
    return Model((merge(*groups[0]), flat_material("frp_litter_rust", "leaf_rust", roughness=0.95)),
                 (merge(*groups[1]), flat_material("frp_litter_pale", "leaf_autumn", roughness=0.95)))
