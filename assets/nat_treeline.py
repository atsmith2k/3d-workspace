"""Treeline: a ring of dark forest that closes the view round a clearing.

Spec:
  kind: environment
  size: about 54 x 14 x 54 m
  pivot: the centre of the ring, on Y=0
  budget: 3000 triangles, two materials, no textures
  materials: two flat colours, a dark green for the near rank and a darker, colder one for the
             far rank (no samplers: it is the cheapest thing in a scene and the largest)
  features: two ranks of conifer shapes on circles of 20 m and 25 m, each tree a stack of
            three cones 7 to 13 m tall with its own lean and width; ranks are staggered so
            no sky shows between the trunks at eye height; nothing nearer the centre than 16 m
  use: wilderness sub-pack: stands on the rim of nat_ground_clearing. A backdrop: it is never
       walked up to, so it has no bark, no detail and no collider
  engine: no body
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "ring of dark forest, a backdrop for a clearing"
PARAMS = dict(radius=20.0, seed=9, near=46, far=54)
BUDGET = dict(BUDGET_OF["tree"], materials=2)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "tree", "backdrop", "forest", gameplay=dict(inner_radius=16.0, role="backdrop"))


def conifer(rng, h, w):
    """Three cones stacked, a little off true: the outline of a fir at a distance."""
    lean = rng.normal(0, 0.03, 2) * h
    parts = []
    for k, (y0, y1, r) in enumerate(((0.0, 0.5, 1.0), (0.3, 0.78, 0.74), (0.58, 1.0, 0.48))):
        cone = lathe([(w * r, y0 * h), (0.0, y1 * h)], 6, phase=float(rng.uniform(0, 60)))
        parts.append(cone.moved(lean[0] * y0, 0, lean[1] * y0))
    return flat(merge(*parts))


def rank(p, rng, count, radius, tall, base):
    out = []
    for k in range(count):
        a = 2 * np.pi * (k + rng.uniform(-0.3, 0.3)) / count
        r = radius + rng.uniform(-1.2, 1.2)
        h = rng.uniform(*tall)
        out.append(conifer(rng, h, h * rng.uniform(0.2, 0.27)).moved(r * np.cos(a), base, r * np.sin(a)))
    return merge(*out)


def checks(p):
    def closed(ctx):
        v = np.vstack([m.v for m, _ in ctx.model.parts])
        ang = np.degrees(np.arctan2(v[:, 2], v[:, 0]))
        low = v[v[:, 1] < 4.0]
        gaps = np.diff(np.sort(np.degrees(np.arctan2(low[:, 2], low[:, 0]))))
        return gaps.max() < 6.0 and np.ptp(ang) > 350, f"widest gap in the lower trees, seen from the centre: {gaps.max():.1f} degrees"

    def clear_middle(ctx):
        v = np.vstack([m.v for m, _ in ctx.model.parts])
        return np.hypot(v[:, 0], v[:, 2]).min() > 16.0, f"nothing within {np.hypot(v[:, 0], v[:, 2]).min():.1f} m of the centre"
    return [size(x=(48, 60), y=(11, 16), z=(48, 60)), tris(max=BUDGET["tris"]), pivot((0.5, None, 0.5), tol=1.5), materials(2),
            custom("closes the view", closed), custom("clear middle", clear_middle)]


def build(p):
    rng = np.random.default_rng(p.seed)
    near = rank(p, rng, p.near, p.radius, (7.0, 10.5), 0.6)
    far = rank(p, rng, p.far, p.radius + 5.0, (10.0, 13.5), 0.0)
    return Model((near, flat_material("frp_forest_near", "forest_near", roughness=1.0)),
                 (far, flat_material("frp_forest_far", "forest_far", roughness=1.0)))
