"""Village chimney: a stone stack built against the outside of a wall, behind a hearth.

Spec:
  kind: environment
  size: 1.30 x 6.00 x 0.70 m
  pivot: base centre in X, on Y=0, at the face that stands against the wall (Z=0); the stack
         reaches toward -Z, away from the house
  budget: 1500 triangles, two materials, 1024 px textures
  materials: the pack's soot-stained stone; a soot-black flue mouth
  features: a breast 1.3 m wide to 2.2 m; shoulders stepping in twice to a flue 0.7 m wide;
            a projecting cap course and an open flue mouth at 6.0 m, 0.7 m above a thatched
            ridge (5.3 m); every edge eased
  use: village sub-pack: outside the wall int_hearth stands against. It passes through the
       eave of the roof, as built chimneys do
  engine: body static, auto collider
"""
from _frp_village import *
from _frp_interior import block as eased

KIND = "environment"
DESCRIPTION = "village chimney, stone stack against a wall"
PARAMS = dict(width=1.30, height=6.00, depth=0.70)
BUDGET = dict(BUDGET_OF["building"], materials=2)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("village", "building", "chimney", gameplay=dict(pairs_with="int_hearth", against="+z face"))
RIDGE = STOREY + PITCH_RISE + THATCH_T


def checks(p):
    def tops_the_ridge(ctx):
        top = float(ctx.model.bounds[1][1])
        return top > RIDGE + 0.5, f"the flue mouth is {top - RIDGE:.2f} m above a thatched ridge"

    def steps_in(ctx):
        m = ctx.model.parts[0][0]
        t = m.v[m.f]                                               # width where triangles cross a height
        widths = [float(np.ptp(t[(t[:, :, 1].min(1) < y) & (t[:, :, 1].max(1) > y)][:, :, 0])) for y in (1.0, 2.8, 4.5)]
        return widths[0] > widths[1] > widths[2], "width at 1.0, 2.8 and 4.5 m: " + ", ".join(f"{w:.2f}" for w in widths)
    return [size(x=p.width, y=p.height, z=p.depth, tol=0.004), tris(max=BUDGET["tris"]), pivot((0.5, 0.0, 1.0)), materials(2),
            texture_size(1024), custom("tops the ridge", tops_the_ridge), custom("steps in", steps_in)]


def build(p):
    w, h, d = p.width, p.height, p.depth
    e = 0.012
    parts = [eased(w, 2.2, d, 0, 0, -d / 2, e),                               # breast
             eased(w - 0.2, 0.35, d - 0.06, 0, 2.2 - 0.002, -(d - 0.06) / 2, e),  # first shoulder
             eased(w - 0.42, 0.35, d - 0.1, 0, 2.55 - 0.004, -(d - 0.1) / 2, e),  # second shoulder
             eased(0.7, h - 2.9 - 0.2 + 0.006, d - 0.14, 0, 2.9 - 0.006, -(d - 0.14) / 2, e),   # flue
             eased(0.86, 0.12, d, 0, h - 0.2, -d / 2, e),                          # cap course
             eased(0.74, 0.08, d - 0.08, 0, h - 0.08, -(d - 0.08) / 2, e)]         # rim
    mouth = block(0.42, 0.006, d - 0.38, 0, h - 0.004, -(d - 0.08) / 2)
    return Model((tiled(merge(*parts)), stone()), (mouth, flat_material("frp_soot", "soot", roughness=0.95)))
