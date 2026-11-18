"""Three-legged stool: the seat of a poor house, light enough to kick over.

Spec:
  kind: prop
  size: about 0.40 x 0.45 x 0.40 m
  pivot: centre of the bounds (it is a dynamic body: the world kit centres the collider)
  budget: 800 triangles, one material, 1024 px textures
  materials: dark weathered timber
  features: round seat 0.34 m across and 40 mm thick, its top 0.45 m off the floor; three
            legs splayed outward so the feet stand wider than the seat
  use: interiors sub-pack; at int_table (0.75 m), by the hearth
  engine: body dynamic, box collider (the kit has no convex collider: it slides, it does not tip)
"""
from _frp_interior import *

KIND = "prop"
DESCRIPTION = "three-legged stool"
PARAMS = dict(seat=0.34, height=SEAT_H, splay=0.19)
BUDGET = dict(BUDGET_OF["small_prop"], materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = product("interiors", "furniture", "seat", gameplay=dict(seat_y=SEAT_H, collider_wanted="convex hull"))


def checks(p):
    def stance(ctx):
        v = ctx.model.parts[0][0].v
        feet = v[v[:, 1] < v[:, 1].min() + 0.01]
        r = float(np.hypot(feet[:, 0], feet[:, 2]).max())
        return r > p.seat / 2, f"feet reach {r:.2f} m from the axis, the seat {p.seat / 2:.2f} m: it stands wider than it sits"
    return [size(x=(0.36, 0.44), y=p.height, z=(0.36, 0.44)), tris(max=BUDGET["tris"]), pivot("centre"), materials(1),
            texture_size(1024), custom("stands wide", stance)]


def build(p):
    h, r = p.height, p.seat / 2
    rim = lathe([(r - 0.012, h - 0.04), (r, h - 0.03), (r, h - 0.008), (r - 0.012, h)], 20, smooth=False)
    rim = rim.with_uv(np.c_[rim.uv[:, 0] * 2 * np.pi * r, rim.v[:, 1]] / FINE)      # grain round the edge
    faces = merge(disc(r - 0.012, h, 20), disc(r - 0.012, h - 0.04, 20, up=False))
    faces = faces.with_uv(np.c_[faces.v[:, 0], faces.v[:, 2]] / FINE)              # boards across the seat
    parts = [rim, faces]
    for k in range(3):
        a = np.radians(90 + 120 * k)
        foot = (p.splay * np.cos(a), 0.0, p.splay * np.sin(a))
        head = (0.09 * np.cos(a), h - 0.038, 0.09 * np.sin(a))
        length = float(np.linalg.norm(np.subtract(head, foot)))
        leg = cylinder(0.024, length, 10, r_top=0.019, caps=False)
        leg = leg.with_uv(np.c_[leg.v[:, 1] / FINE, leg.uv[:, 0] * 0.19])           # grain up the leg
        sole = disc(0.024, 0.0, 10, up=False)
        leg = merge(leg, sole.with_uv(sole.uv * 0.06))                              # end grain under the foot
        parts.append(along(leg, foot, head))
    m = merge(*parts)
    lo, hi = m.bounds
    return Model((m.moved(*(-(lo + hi) / 2)), timber()))
