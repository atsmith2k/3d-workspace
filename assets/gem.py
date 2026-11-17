"""Gem: a faceted red crystal that glows, the kit's pickup.

Spec:
  kind: prop
  size: 0.28 x 0.36 x 0.28 m
  pivot: centre of bounds (it spins about its own centre, floating at chest height)
  budget: 40 triangles, one material, no textures
  materials: ruby (emissive red, strength 0.6: stronger tone-maps to pink, low roughness)
  features: six sides; crown above, long pavilion below
  use: with the world kit `pickup` and `spin`, floating 1 m above the floor
  engine: no body; rest_y 1.0
"""
from _dungeon import *

KIND = "prop"
DESCRIPTION = "glowing red gem pickup"
PARAMS = dict(radius=0.14, glow=0.6)
BUDGET = dict(tris=40, materials=1)
ENGINE = dict(rest_y=1.0)


def checks(p):
    return [size(x=(0.24, 0.29), y=0.36, z=(0.24, 0.29)), tris(max=40), pivot((0.5, 0.5, 0.5), tol=0.02),
            materials(1)]


def build(p):
    r = p.radius
    body = flat(lathe([(0.0, -0.20), (r, 0.03), (r * 0.6, 0.16), (0.0, 0.16)], 6)).moved(0, 0.02, 0)
    ruby = Material("ruby", color=(0.55, 0.02, 0.04), roughness=0.15,
                    emissive=(0.9, 0.0, 0.03), emissive_strength=p.glow)
    return Model((body, ruby))
