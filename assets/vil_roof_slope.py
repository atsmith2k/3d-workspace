"""Village roof slope: 2 m of old thatch rising 45 degrees from the wall line to the ridge.

Spec:
  kind: environment
  size: 2.0 x 2.7 x 2.4 m
  pivot: on the wall line at wall-top height: the piece is placed at the top of a wall (Y = 3 m
         per storey) and rises toward its +Z; the eave hangs 0.4 m outside and below
  budget: 1500 triangles, one material, 1024 px textures
  materials: straw thatch, strands and bundles running down the slope
  features: four courses of thatch, each 0.3 m thick at its butts and thinning to 0.2 m where
            the next covers it, so the slope steps and each course shadows the one below; covers one 2 m cell of a 4 m deep house up to the ridge; two rows back
            to back make a roof
  use: one per 2 m of eave, as its own entity so a top-down game can hide the roof
  engine: body static, auto collider
"""
from _frp_village import *

KIND = "environment"
DESCRIPTION = "village roof slope, thatch"
PARAMS = dict(width=GRID)
BUDGET = BUDGET_OF["building"]
ENGINE = dict(body="static", collider="auto", rest_y=STOREY)
PRODUCT = product("village", "building", "roof", "thatch")


def checks(p):
    height, depth = PITCH_RISE + THATCH_T + EAVE, PITCH_RISE + EAVE
    return [size(x=p.width, y=height, z=depth, tol=0.002), tris(max=BUDGET["tris"]),
            pivot((0.5, EAVE / height, EAVE / depth)), materials(1), texture_size(1024),
            custom("sheds water", lambda ctx: (
                bool((ctx.model.parts[0][0].n[:, 1] > 0.6).any()), "the top faces tilt 45 degrees, not flat")),
            custom("laid in courses", lambda ctx: (
                len(np.unique(np.round(ctx.model.parts[0][0].v[ctx.model.parts[0][0].n[:, 2] < -0.9][:, 2], 3))) >= COURSES - 1,
                f"{COURSES} courses: the butt of each stands proud of the one below"))]


def build(p):
    return Model((roof_slope(p.width), thatch()))
