"""Treasure chest: a plank box with a barrel lid, iron straps and a brass lock.

Spec:
  kind: prop
  size: 0.80 x 0.67 x 0.54 m
  pivot: base centre on Y=0
  budget: 300 triangles, three materials, 512 px textures
  materials: planks; forged iron straps; brass lock (metallic, faint glow so it reads in the dark)
  features: box 0.8 x 0.4 x 0.5 m; lid a half-round of 0.25 m radius; two straps 60 mm wide
            wrapping box and lid; lock plate on the -Z (front) face
  use: the goal or a reward at the end of a room; knee-high beside a 1.8 m player
  engine: body static, box collider
"""
from _dungeon import *

KIND = "prop"
DESCRIPTION = "treasure chest with iron straps"
PARAMS = dict(width=0.8, depth=0.5, body=0.4, strap=0.06)
BUDGET = dict(tris=300, texture=512, materials=3)
ENGINE = dict(body="static", collider="box", rest_y=0.0)


def half_round(r, n=6):
    return [(r * np.cos(t), r * np.sin(t)) for t in np.linspace(0, np.pi, n + 1)]


def checks(p):
    return kit_checks(p.width, p.body + p.depth / 2 + 0.02, (p.depth + 0.03, p.depth + 0.06), 300,
                      mats=3, tex=512)


def build(p):
    r = p.depth / 2
    lid = prism(half_round(r), p.width).rotated(90, "y").moved(0, p.body, 0)
    lid = lid.with_uv(lid.uv * [1.0, 1 / p.width])
    wood = merge(block(p.width, p.body, p.depth), lid)
    straps = []
    for x in (-0.24, 0.24):
        straps.append(block(p.strap, p.body + 0.004, p.depth + 0.04, x))
        straps.append(prism(half_round(r + 0.02), p.strap).rotated(90, "y").moved(x, p.body, 0))
    brass = Material("brass", color=(0.80, 0.58, 0.20), metallic=1.0, roughness=0.35,
                     emissive=(0.8, 0.5, 0.12), emissive_strength=0.6)
    lock = block(0.10, 0.13, 0.03, 0, p.body - 0.09, -(p.depth / 2 + 0.012))
    return Model((wood, planks(512, 4, seed=9)), (box_uv(merge(*straps), 2.0), iron()), (lock, brass))
