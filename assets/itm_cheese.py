"""Cheese: a wedge cut from a wheel.

Spec:
  kind: prop
  size: about 0.17 x 0.08 x 0.13 m
  pivot: on Y=0, under the wedge
  budget: 800 triangles, two materials, no textures
  materials: yellow paste on the cut faces; a darker rind on the curved back, top and bottom
  features: a sixth of a wheel 0.17 m in radius and 0.08 m thick: two flat cut faces meeting
            at a point, a curved rind
  use: items sub-pack (food); icon frame `cheese`
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "wedge of cheese"
PARAMS = dict(radius=0.17, height=0.08, angle=50.0)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("cheese", "food", "consumable", stack=10, restores="health")


def checks(p):
    return item_checks((0.14, 0.19), p.height, (0.1, 0.16), 2)


def build(p):
    r, h, n = p.radius, p.height, 5
    ang = np.radians(np.linspace(-p.angle / 2, p.angle / 2, n + 1))
    arc = [(r * np.cos(a), r * np.sin(a)) for a in ang]
    m = prism(ccw([(0.0, 0.0)] + arc), h).rotated(-90, "x").moved(0, h / 2, 0)       # extruded along Z, stood up along Y
    cx = (m.bounds[0][0] + m.bounds[1][0]) / 2
    m = m.moved(-cx, 0, 0)
    fn = m.n[m.f].mean(1)
    centre = m.v[m.f].mean(1)
    radial = np.hypot(centre[:, 0] + cx, centre[:, 2]) > r * 0.9                    # the curved back
    rind = (np.abs(fn[:, 1]) > 0.5) | (radial & (np.abs(fn[:, 1]) < 0.5))

    def part(mask):
        idx = np.unique(m.f[mask])
        remap = -np.ones(len(m.v), int)
        remap[idx] = np.arange(len(idx))
        return Mesh(m.v[idx], remap[m.f[mask]], m.n[idx], m.uv[idx])
    return Model((part(~rind), flat_material("frp_cheese", "cheese", roughness=0.7)),
                 (part(rind), flat_material("frp_rind", "cloth_ochre", roughness=0.85)))
