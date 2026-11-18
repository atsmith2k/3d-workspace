"""Dead tree: a bare, forked trunk, bark only.

Spec:
  kind: environment
  size: about 3.2 x 5.0 x 2.8 m
  pivot: the foot of the trunk on Y=0
  budget: 3000 triangles, one material, 1024 px textures
  materials: furrowed bark
  features: a flared foot; the trunk forks at 2.2 m into two leaders; six bare branches
            ending in points; no branch below 1.9 m
  use: wilderness sub-pack: blighted ground, graveyards, the edge of a clearing
  engine: no body in a kit world; wants a capsule on the trunk, radius 0.22 m, height 2.2 m
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "dead tree, bare forked trunk"
PARAMS = dict(seed=1)
BUDGET = dict(BUDGET_OF["tree"], materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "tree", "dead", "blight", gameplay=dict(
    collider_wanted=dict(kind="capsule", radius=0.22, height=2.2, on="trunk")))

LIMBS = [([(0, 0, 0), (0.0, 0.3, 0), (-0.06, 1.2, 0.03), (0.0, 2.2, 0.0)], [0.32, 0.18, 0.15, 0.13], 8),
         ([(0.0, 2.15, 0.0), (0.45, 3.0, 0.1), (0.5, 4.0, -0.1), (0.75, 5.0, -0.2)], [0.11, 0.085, 0.05, 0.008], 6),
         ([(0.0, 2.15, 0.0), (-0.5, 2.9, -0.15), (-0.9, 3.9, 0.1), (-0.8, 4.6, 0.3)], [0.1, 0.075, 0.045, 0.008], 6),
         ([(0.46, 3.1, 0.1), (1.1, 3.4, 0.6), (1.6, 3.9, 0.9)], [0.05, 0.03, 0.006], 5),
         ([(-0.6, 3.1, -0.1), (-1.2, 3.3, -0.7), (-1.5, 3.2, -1.2)], [0.045, 0.028, 0.006], 5),
         ([(-0.9, 3.9, 0.1), (-1.3, 4.3, 0.6)], [0.03, 0.006], 5),
         ([(0.5, 4.0, -0.1), (0.2, 4.5, -0.6)], [0.03, 0.006], 5),
         ([(-0.03, 1.95, 0.02), (0.1, 2.1, 0.75), (0.05, 2.45, 1.2)], [0.05, 0.03, 0.006], 5)]


def checks(p):
    def clear(ctx):
        v = ctx.model.parts[0][0].v
        far = v[np.hypot(v[:, 0], v[:, 2]) > 0.4]
        return far[:, 1].min() > 1.9, f"nothing reaches out below {far[:, 1].min():.2f} m"
    return [size(x=(2.8, 3.6), y=(4.8, 5.2), z=(2.2, 3.0)), tris(max=BUDGET["tris"]), pivot((None, 0.0, None)),
            materials(1), texture_size(1024), custom("clear trunk", clear)]


def build(p):
    return Model((merge(*[stem(pts, r, s, u_repeat=2.0 if s > 6 else 1.0) for pts, r, s in LIMBS]), bark()))
