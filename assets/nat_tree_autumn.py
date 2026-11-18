"""Autumn tree: a leaning broadleaf holding the last of its leaves, built without leaf cards.

Spec:
  kind: environment
  size: about 5.0 x 6.0 x 4.4 m
  pivot: the foot of the trunk on Y=0 (the canopy is not centred on it: the tree leans)
  budget: 3000 triangles, two materials; bark 512 px, canopy 2048 px (it is the largest thing
          in a clearing and is seen from underneath: 1024 px would be 120 px per metre)
  high poly: the canopy is at least 150,000 triangles before baking
  materials: furrowed bark (tiling); a canopy painted from its bake: drifts of dark green and
             rust, each leaf clump lit on top and dark underneath and inside
  features: a flared foot; a trunk 0.21 m in radius at chest height that bends twice; four
            boughs; nine canopy masses fused into one crown with leaf clumps of 0.2 m, sparse
            enough that sky shows between them; nothing of the canopy below 2.3 m, so a 1.8 m
            person walks under it
  use: wilderness sub-pack, temperate forest. Solid geometry because Cinder 0.1.1 draws
       alpha-masked leaves opaque
  engine: no body in a kit world (a kit collider would make the canopy solid); wants a
          capsule on the trunk, radius 0.25 m, height 2.5 m
  needs: Blender 5.x (cached after the first build)
"""
from _frp_nature import *
from nat_stump import grounded

KIND = "environment"
DESCRIPTION = "autumn broadleaf tree, solid canopy"
PARAMS = dict(seed=3, tris=2400, texture=2048, turned=0.65)
BUDGET = dict(BUDGET_OF["tree"], materials=2, texture=2048)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "tree", "forest", "autumn", "baked", gameplay=dict(
    collider_wanted=dict(kind="capsule", radius=0.25, height=2.5, on="trunk"), walk_under_m=2.3))

TRUNK = [(0, -0.03, 0), (0.0, 0.35, 0), (0.1, 1.5, 0.04), (0.02, 2.7, -0.06), (-0.14, 3.7, 0.0), (-0.2, 4.5, 0.08)]
TRUNK_R = [0.45, 0.25, 0.21, 0.17, 0.12, 0.06]
BOUGHS = [([(0.08, 2.0, 0.02), (0.9, 2.8, 0.3), (1.5, 3.5, 0.45)], [0.09, 0.06, 0.03]),
          ([(0.04, 2.5, -0.04), (-0.7, 3.2, -0.7), (-1.1, 3.9, -1.2)], [0.085, 0.055, 0.03]),
          ([(0.0, 3.0, -0.03), (0.3, 3.7, -0.9), (0.5, 4.3, -1.4)], [0.07, 0.05, 0.025]),
          ([(-0.1, 3.4, 0.0), (-0.9, 3.9, 0.6), (-1.5, 4.4, 1.0)], [0.07, 0.045, 0.025])]
CANOPY = [((1.35, 3.9, 0.5), 1.05, 0), ((-1.2, 4.3, -1.2), 1.1, 1), ((0.5, 4.7, -1.4), 0.95, 0),
          ((-1.35, 4.8, 1.0), 1.0, 1), ((-0.2, 5.2, 0.1), 1.2, 0), ((0.6, 5.0, 0.9), 0.8, 1),
          ((0.3, 4.3, -0.2), 1.0, 1), ((-0.6, 4.1, 0.2), 0.85, 0), ((0.9, 4.5, -0.5), 0.8, 1)]


def checks(p):
    def under(ctx):
        low = float(ctx.model.parts[1][0].v[:, 1].min())
        return low > 2.3, f"the canopy starts {low:.2f} m up"

    def sparse(ctx):
        crown = ctx.model.parts[1][0]
        lo, hi = crown.bounds
        share = abs(volume(crown)) / float(np.prod(hi - lo))
        return share < 0.5, f"the canopy masses fill {share:.0%} of the space they span"
    return [size(x=(4.4, 5.4), y=(5.6, 6.4), z=(3.9, 4.9)), tris(max=BUDGET["tris"]), pivot((None, 0.0, None)),
            materials(2), texture_size(2048), custom("walk under it", under), custom("sparse canopy", sparse),
            custom("two colours", lambda ctx: (0.2 < ctx.model.meta["turned"] < 0.85, f"{ctx.model.meta['turned']:.0%} of the leaves have turned")),
            custom("palette", lambda ctx: (0.04 < ctx.model.meta["mean"] < 0.25, f"mean canopy colour {ctx.model.meta['mean']:.2f}"))
            ] + baked_checks(150_000, part=1)


def build(p):
    wood = [stem(TRUNK, TRUNK_R, 12, u_repeat=2.0)] + [stem(pts, r, 7) for pts, r in BOUGHS]
    shape = clumps([(at, r) for at, r, _ in CANOPY], p.seed, squash=0.72)
    crown, r = sculpt(shape, p.tris, p.texture, lumps=(0.5, 0.14), facets=(0.16, 0.07), grain=(0.05, 0.02), fuse=0.05, ground=False)
    mat, facts = paint_foliage(crown, r, p.texture, p.seed, name="frp_canopy_autumn", turned=p.turned)
    model = Model((grounded(merge(*wood)), bark()), (crown, mat))
    model.meta = dict(facts, high_tris=r.step("modify", 0)["triangles"])
    return model
