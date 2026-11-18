"""Tree stump: a felled trunk with three root spurs.

Spec:
  kind: environment
  size: about 0.95 x 0.48 x 0.95 m
  pivot: on Y=0, under the trunk
  budget: 800 triangles, two materials, 1024 px textures
  materials: furrowed bark; pale cut wood on top
  features: cut face 0.46 m up and 0.5 m across, tilted a few degrees (felled with an
            axe, not a saw); three roots running out into the ground
  use: wilderness sub-pack; a seat in a clearing (0.46 m, about a stool's height)
  engine: body static, auto collider
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "tree stump with roots"
PARAMS = dict(radius=0.25, height=0.46)
BUDGET = BUDGET_OF["small_prop"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("wilderness", "tree", "stump", gameplay=dict(seat_y=0.46))


def grounded(m):
    """Nothing under the ground: vertices below Y=0 are brought up to it."""
    return Mesh(np.c_[m.v[:, 0], np.maximum(m.v[:, 1], 0.0), m.v[:, 2]], m.f, None, m.uv)


def checks(p):
    def face(ctx):
        top = ctx.model.parts[1][0]
        tilt = float(np.ptp(top.v[:, 1]))
        return 0.02 < tilt < 0.08 and abs(top.v[:, 1].mean() - p.height) < 0.03, f"the cut face is tilted {tilt * 1000:.0f} mm across"
    return plant_checks((0.9, 1.3), (0.44, 0.52), (0.9, 1.3), "small_prop", 2, anchor=(None, 0.0, None)) + [
        on_ground(), custom("axe-cut face", face)]


def build(p):
    r, h = p.radius, p.height
    body = stem([(0, 0, 0), (0, 0.12, 0), (0, h * 0.7, 0), (0, h, 0)], [r * 1.5, r * 1.12, r, r], 12)
    rim = body.v[:, 1] > h - 1e-6
    body.v[rim, 1] += 0.1 * body.v[rim, 0]
    top = disc(r, h, 12)
    top = Mesh(top.v + np.c_[0 * top.v[:, 0], 0.1 * top.v[:, 0], 0 * top.v[:, 0]], top.f, None, top.uv)
    roots = []
    for k, reach in enumerate((0.55, 0.5, 0.58)):
        a = np.radians(20 + 120 * k)
        d = np.array([np.cos(a), 0, np.sin(a)])
        roots.append(stem([d * r * 0.7 + [0, 0.2, 0], d * (r + 0.12) + [0, 0.07, 0], d * reach + [0, -0.02, 0]], [0.09, 0.07, 0.03], 6))
    return Model((grounded(merge(body, *roots)), bark()), (top, flat_material("frp_cut_wood", "wood_pale", roughness=0.85)))
