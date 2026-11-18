"""Cottage table: a trestle-legged board table for a poor house.

Spec:
  kind: prop
  size: 1.40 x 0.75 x 0.78 m
  pivot: base centre on Y=0
  budget: 3000 triangles, one material, 1024 px textures
  materials: dark weathered timber
  features: top of five separate boards 50 mm thick, every edge eased, 0.75 m off the floor (0.30 m above a 0.45 m seat);
            four square legs set in from the corners; a stretcher low on each end and one
            down the middle, so a first-person camera sees joinery, not a box;
            at least 0.60 m clear under the top for knees
  use: interiors sub-pack; stands on vil_floor with int_stool and int_bench
  engine: body static, auto collider
"""
from _frp_interior import *

KIND = "prop"
DESCRIPTION = "cottage table, boards on four legs"
PARAMS = dict(length=1.40, depth=0.78, height=TABLE_H, top=0.05)
BUDGET = dict(BUDGET_OF["large_prop"], materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("interiors", "furniture", "table", gameplay=dict(surface_y=TABLE_H, seats="int_stool, int_bench"))


def checks(p):
    def knees(ctx):
        m = ctx.model.parts[0][0]
        c = m.v[m.f].mean(1)                                       # triangle centres
        mid = c[(np.abs(c[:, 0]) < p.length / 2 - 0.2) & (np.abs(c[:, 2]) > 0.12)]     # between the legs, off the centre rail
        low = float(mid[:, 1].min())
        return low > 0.6, f"lowest timber between the legs is {low:.2f} m up: knees go under"
    return furniture_checks(p.length, p.height, p.depth, BUDGET["tris"], 1) + [
        custom("top at table height", lambda ctx: (abs(top_height()(ctx) - TABLE_H) < 0.005, f"{top_height()(ctx):.3f} m")),
        custom("room for knees", knees)]


def build(p):
    h = p.height - p.top
    top = planked(p.length, p.top, p.depth, h, boards=5, seed=7)
    leg = legs(p.length, p.depth, h + SINK)
    lx, lz = p.length / 2 - 0.075, p.depth / 2 - 0.075
    ends = boards_z(merge(*[block(0.05, 0.07, 2 * lz, s * lx, 0.12) for s in (-1, 1)]))
    spine = boards_x(block(2 * lx, 0.07, 0.05, 0, 0.125))
    apron = boards_x(merge(*[block(2 * lx, 0.08, 0.03, 0, h - 0.078, s * lz) for s in (-1, 1)]))
    return Model((merge(top, leg, ends, spine, apron), timber()))
