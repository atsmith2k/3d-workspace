"""Dungeon pillar: a round stone column with a stepped base and capital.

Spec:
  kind: environment
  size: 0.72 x 3.0 x 0.72 m
  pivot: base centre on Y=0
  budget: 300 triangles, one material, 1024 px textures
  materials: stone blocks wrapped once round the shaft
  features: 12 sides; base and capital 0.36 m radius, shaft 0.24 m
  use: free-standing in halls, on cell centres or corners
  engine: body static, auto collider
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon pillar, round column"
PARAMS = dict(base=0.36, shaft=0.24, sides=12)
BUDGET = dict(tris=300, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    return kit_checks(2 * p.base, WALL_H, 2 * p.base, 300)


def build(p):
    b, s, h = p.base, p.shaft, WALL_H
    prof = [(b, 0), (b, 0.22), (s + 0.05, 0.34), (s, 0.42), (s, h - 0.42), (s + 0.05, h - 0.34),
            (b, h - 0.22), (b, h)]
    side = lathe(prof, p.sides, u_repeat=1.0, v_range=(0.0, h / GRID), smooth=False)
    caps = merge(disc(b, 0, p.sides, up=False), disc(b, h, p.sides))
    return Model((merge(side, caps.with_uv(caps.uv * 0.36)), stone()))
