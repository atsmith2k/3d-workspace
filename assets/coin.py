"""Coin: a gold collectible with a raised star on each face.

Spec:
  kind: prop
  size: 0.30 m across x 0.30 m tall x 0.05 m thick (disc 30 mm, stars 10 mm proud each side)
  pivot: centre of bounds (it spins about its own vertical axis)
  budget: 100 triangles, one factor-only material (no texture)
  materials: gold: metallic, roughness 0.3, a faint glow so it reads in shade and from a distance
  features: 12 sides; stands on edge facing +Z and -Z; a five-point star raised on both faces
  use: the standard pickup of builder games, with the world kit `pickup` and `spin`, 1 m above the floor
  engine: no body (a pickup is a distance test); rest_y 1.0
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "gold coin pickup with a raised star"
PARAMS = dict(radius=0.15, thick=0.03, relief=0.01)
BUDGET = dict(tris=100, materials=1)
ENGINE = dict(rest_y=1.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["coin", "pickup", "collectible"],
               gameplay=dict(collectible=True, pickup_radius=1.0, spin_deg_per_s=120))


def checks(p):
    return [size(x=2 * p.radius, y=2 * p.radius, z=p.thick + 2 * p.relief, tol=0.004), tris(max=100),
            pivot("centre"), materials(1)]


def star(r, z, relief, sign):
    """A five-point star as a low pyramid: ten triangles rising to a point at the centre."""
    pts = [(np.sin(a) * (r if i % 2 == 0 else r * 0.42), np.cos(a) * (r if i % 2 == 0 else r * 0.42))
           for i, a in enumerate(np.linspace(0, 2 * np.pi, 10, endpoint=False))]
    v = [(0, 0, z + sign * relief)] + [(x, y, z) for x, y in pts]
    f = [(0, 1 + i, 1 + (i + 1) % 10) for i in range(10)]
    m = flat(Mesh(v, f))
    return m if volume_sign(m, sign) else flat(Mesh(v, [t[::-1] for t in f]))


def volume_sign(m, sign):
    return (m.n[:, 2] * sign > 0).all()


def build(p):
    r, t = p.radius, p.thick / 2
    rim = lathe([(r, -t), (r, t)], 12)
    disc_ = merge(rim, disc(r, t, 12), disc(r, -t, 12, up=False)).rotated(90, "x")     # stand it on edge
    gold = Material("coin_gold", color=(1.0, 0.62, 0.08), metallic=1.0, roughness=0.32,
                    emissive=(0.9, 0.45, 0.02), emissive_strength=0.18)      # more than this washes out to cream
    return Model((merge(disc_, star(r * 0.72, t, p.relief, 1), star(r * 0.72, -t, p.relief, -1)), gold))
