"""Fallen log: a length of trunk lying on the ground.

Spec:
  kind: environment
  size: about 2.4 x 0.5 x 0.75 m
  pivot: on Y=0, at the middle of its length; it lies along X
  budget: 800 triangles, two materials, 1024 px textures
  materials: furrowed bark; pale cut wood on the ends
  features: 2.4 m long, 0.22 m in radius, slightly bent; one branch stub; sunk 30 mm
            into the ground so it does not balance on a line
  use: wilderness sub-pack; a seat or a barrier at the edge of a clearing
  engine: body static, auto collider
"""
from _frp_nature import *
from nat_stump import grounded

KIND = "environment"
DESCRIPTION = "fallen log"
PARAMS = dict(length=2.4, radius=0.22)
BUDGET = BUDGET_OF["small_prop"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("wilderness", "tree", "log", gameplay=dict(seat_y=0.4))


def checks(p):
    return plant_checks((2.3, 2.6), (0.38, 0.75), (0.45, 0.9), "small_prop", 2, anchor=(None, 0.0, None)) + [on_ground()]


def build(p):
    L, r = p.length, p.radius
    y = r - 0.03
    pts = [(-L / 2, y, 0.0), (-L / 4, y + 0.01, 0.05), (L / 5, y, 0.06), (L / 2, y - 0.01, -0.02)]
    radii = [r, r * 0.97, r * 0.93, r * 0.88]
    stub_pts = [(0.3, y + 0.1, 0.1), (0.42, y + 0.22, 0.4), (0.45, y + 0.3, 0.52)]
    wood = merge(stem(pts, radii, 10), stem(stub_pts, [0.07, 0.055, 0.04], 6))

    def end(at, toward, radius, sides):
        """A disc closing a stem at `at`, facing along `toward`."""
        return along(disc(radius, 0.0, sides), at, np.add(at, toward)).with_uv(disc(radius, 0.0, sides).uv * 0.3)
    d0, d1 = np.subtract(pts[0], pts[1]), np.subtract(pts[-1], pts[-2])
    ends = merge(end(pts[0], d0, radii[0], 10), end(pts[-1], d1, radii[-1], 10),
                 end(stub_pts[-1], np.subtract(stub_pts[-1], stub_pts[-2]), 0.04, 6))
    return Model((grounded(wood), bark()), (grounded(ends), flat_material("frp_cut_wood", "wood_pale", roughness=0.85)))
