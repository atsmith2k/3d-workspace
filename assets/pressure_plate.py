"""Pressure plate: a bronze plate in a stone surround, to mark a world-kit trigger.

Spec:
  kind: environment
  size: 1.0 x 0.06 x 1.0 m
  pivot: base centre on Y=0
  budget: 24 triangles, two materials, 1024 px textures
  materials: stone surround (flagstones); bronze plate (metallic, roughness 0.45)
  features: surround 1.0 m square x 40 mm; plate 0.8 m square standing 20 mm above it
  use: under a `trigger` volume; give it no body, it is low enough to walk over
  engine: no body (visual marker)
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "pressure plate, bronze on stone"
PARAMS = dict(size=1.0, plate=0.8)
BUDGET = dict(tris=24, texture=1024, materials=2)
ENGINE = dict(rest_y=0.0)


def checks(p):
    return kit_checks(p.size, 0.06, p.size, 24, mats=2)


def build(p):
    bronze = Material("bronze", color=(0.60, 0.38, 0.15), metallic=1.0, roughness=0.45)
    return Model((stoned(block(p.size, 0.04, p.size)), paving()),
                 (block(p.plate, 0.022, p.plate, y=0.038), bronze))
