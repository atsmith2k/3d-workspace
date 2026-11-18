"""Field stone: a boulder half sunk in the ground, sculpted and baked, with nothing generated.

Spec:
  kind: environment
  size: about 1.2 x 0.6 x 1.0 m (seed 2); `--set scale=` for other sizes
  pivot: on Y=0, under the middle
  budget: 800 triangles, one material, 1024 px textures (three maps)
  high poly: at least 100,000 triangles before baking
  materials: cold grey field stone painted in world space from the bake: dark in the crevices,
             worn pale on the edges, moss on 5-40 % of it and mostly on faces that look up
  features: lumps of 0.4 m and facets of 0.15 m sculpted, grain in the normal map; wider than
            it is tall; cut flat where it meets the ground; `seed` gives a different stone
  use: wilderness sub-pack. The partner of nat_boulder_mossy that needs nobody's clearing:
       that one waits on two generated surfaces
  engine: body static, auto collider
  needs: Blender 5.x (cached after the first build)
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "field stone, sculpted and baked"
PARAMS = dict(seed=2, scale=1.0, tris=600, texture=1024)
BUDGET = dict(BUDGET_OF["small_prop"], materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("wilderness", "rock", "boulder", "baked")


def rough_stone(seed, scale=1.0, at=(0, 0, 0), sink=0.3):
    """The shape a stone is sculpted from: a ball, squashed and turned by `seed`, sunk in the ground."""
    rng = np.random.default_rng(seed)
    r = 0.6 * scale
    m = ball(r, 12, 8).scaled(1.0 + 0.25 * rng.random(), 0.6 + 0.12 * rng.random(), 0.8 + 0.2 * rng.random())
    m = m.rotated(float(rng.uniform(0, 360)), "y")
    return m.moved(at[0], -m.bounds[0][1] - sink * r, at[2])


def stone_checks(p, moss=(0.05, 0.4)):
    def squat(ctx):
        lo, hi = ctx.model.bounds
        return (hi[1] - lo[1]) < 0.8 * min(hi[0] - lo[0], hi[2] - lo[2]), "wider than it is tall"

    def mossy(ctx):
        f = ctx.model.meta
        ok = moss[0] < f["moss_share"] < moss[1] and 2 * f["moss_side"] < f["moss_up"] < 0.8      # in drifts, not a cap
        return ok, f"moss on {f['moss_share']:.0%} of the stone: {f['moss_up']:.0%} of upward texels, {f['moss_side']:.0%} of steep ones"

    def dark(ctx):
        m = ctx.model.meta["mean"]
        return 0.1 < m < 0.36, f"mean base colour {m:.2f}: dark-fantasy stone, not washed out and not black"
    def no_underside(ctx):
        m = ctx.model.parts[0][0]
        flat_down = ((m.v[m.f][:, :, 1] < 2e-3).all(1)).sum()
        return flat_down == 0, "the face it stands on is not drawn"
    return [on_ground(0.01), custom("squat", squat), custom("moss lies on top", mossy), custom("palette", dark),
            custom("no underside", no_underside)] + baked_checks(100_000)


def checks(p):
    s = p.scale
    return plant_checks((0.95 * s, 1.6 * s), (0.4 * s, 0.8 * s), (0.8 * s, 1.4 * s), "small_prop", 1, anchor=(None, 0.0, None)) + stone_checks(p)


def centred(low):
    lo, hi = low.bounds
    return low.moved(-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2)


def build(p):
    k = p.scale
    low, r = sculpt(rough_stone(p.seed, k), p.tris, p.texture, lumps=(0.4 * k, 0.16 * k), facets=(0.15 * k, 0.045 * k))
    low = centred(low)
    mat, facts = paint_rock(low, r, p.texture, p.seed)
    model = Model((low, mat))
    model.meta = dict(facts, high_tris=r.step("modify", 0)["triangles"])
    return model
