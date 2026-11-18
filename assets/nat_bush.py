"""Bush: a low thicket, sculpted as one mass of leaf clumps and baked.

Spec:
  kind: environment
  size: about 1.8 x 0.9 x 1.6 m
  pivot: on Y=0, near the middle
  budget: 800 triangles, one material, 1024 px textures (three maps)
  high poly: at least 100,000 triangles before baking
  materials: foliage painted from the bake: dark green with about a third turned to rust, each
             clump lit on top and dark inside
  features: five masses fused into one thicket, the largest in the middle; leaf clumps of
            0.1 m in the normal map; cut flat at the ground; under 1 m, so a 1.8 m person
            sees over it
  use: wilderness sub-pack; undergrowth round a clearing. Solid because Cinder 0.1.1 draws
       alpha-masked leaves opaque. One draw call; it costs a scene three texture samplers a
       copy, so dress with a handful, not dozens
  engine: no body (walked through, or give it a box from Mojo)
  needs: Blender 5.x (cached after the first build)
"""
from _frp_nature import *
from nat_rock import centred

KIND = "environment"
DESCRIPTION = "low bush, sculpted and baked"
PARAMS = dict(seed=11, tris=780, texture=1024, turned=0.35)
BUDGET = dict(BUDGET_OF["small_prop"], materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "plant", "bush", "baked")

MASSES = [((0, 0.38, 0), 0.55), ((0.55, 0.26, 0.2), 0.4), ((-0.5, 0.28, 0.25), 0.42), ((0.15, 0.26, -0.45), 0.38), ((-0.25, 0.24, 0.5), 0.32)]


def checks(p):
    def colours(ctx):
        t = ctx.model.meta["turned"]
        return 0.1 < t < 0.6, f"{t:.0%} of the leaves have turned: both colours show"

    def dark(ctx):
        m = ctx.model.meta["mean"]
        return 0.04 < m < 0.25, f"mean base colour {m:.2f}"
    return [size(x=(1.4, 2.2), y=(0.7, 1.0), z=(1.2, 2.0)), tris(max=BUDGET["tris"]), pivot((None, 0.0, None)),
            materials(1), texture_size(1024), on_ground(0.01), custom("two colours", colours), custom("palette", dark)] + baked_checks(100_000)


def build(p):
    shape = clumps(MASSES, p.seed, sub=6, squash=0.8)
    low, r = sculpt(shape, p.tris, p.texture, lumps=(0.25, 0.06), facets=(0.09, 0.04), grain=(0.03, 0.012), fuse=0.02)
    low = centred(low)
    mat, facts = paint_foliage(low, r, p.texture, p.seed, name="frp_bush", turned=p.turned)
    model = Model((low, mat))
    model.meta = dict(facts, high_tris=r.step("modify", 0)["triangles"])
    return model
