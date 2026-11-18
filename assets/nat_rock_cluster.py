"""Rock cluster: three field stones of different sizes, set close, sculpted and baked as one.

Spec:
  kind: environment
  size: about 2.1 x 0.65 x 1.7 m
  pivot: on Y=0, near the middle of the group
  budget: 800 triangles, one material, 1024 px textures (three maps)
  high poly: at least 100,000 triangles before baking
  materials: the pack's field stone, painted from the bake; moss in drifts on the tops and
             in the damp creases where the stones meet
  features: one large stone (1.2 m), one middling (0.75 m), one small (0.45 m), fused where
            they touch so the joins hold dirt and shadow; cut flat at the ground
  use: wilderness sub-pack; edges of paths and clearings. One draw call and three textures
       for three stones
  engine: body static, auto collider
  needs: Blender 5.x (cached after the first build)
"""
from _frp_nature import *
from nat_rock import rough_stone, stone_checks, centred

KIND = "environment"
DESCRIPTION = "cluster of three field stones, sculpted and baked"
PARAMS = dict(seed=5, tris=800, texture=1024)
BUDGET = dict(BUDGET_OF["small_prop"], materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("wilderness", "rock", "cluster", "baked")


def checks(p):
    return plant_checks((1.6, 2.6), (0.4, 0.9), (1.2, 2.2), "small_prop", 1, anchor=(None, 0.0, None)) + stone_checks(p)


def build(p):
    shape = merge(rough_stone(p.seed, 1.0, (-0.35, 0, 0.0)), rough_stone(p.seed + 1, 0.62, (0.6, 0, 0.35)),
                  rough_stone(p.seed + 2, 0.38, (0.45, 0, -0.5)))
    low, r = sculpt(shape, p.tris, p.texture, lumps=(0.35, 0.12), facets=(0.13, 0.04), fuse=0.02)
    low = centred(low)
    mat, facts = paint_rock(low, r, p.texture, p.seed, name="frp_fieldstones")
    model = Model((low, mat))
    model.meta = dict(facts, high_tris=r.step("modify", 0)["triangles"])
    return model
