"""Dungeon door: a plank slab with three iron straps and a ring pull, sized for dungeon_doorway.

Spec:
  kind: environment
  size: 1.18 x 2.16 x 0.14 m (slab 1.16 x 2.16 x 0.08)
  pivot: base centre on Y=0
  budget: 300 triangles, two materials, 512 px textures
  materials: vertical planks; forged iron straps and ring
  features: 5 planks; straps 90 mm high at 0.3, 1.08 and 1.86 m, 20 mm proud both sides; ring
            pull of 60 mm radius on the -Z face
  use: in a dungeon_doorway with the world kit `door` component (it slides or sinks to open)
  engine: body static, auto collider
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon door, planks and iron straps"
PARAMS = dict(width=1.16, height=2.16, thick=0.08, strap=0.09)
BUDGET = dict(tris=300, texture=512, materials=2)
ENGINE = dict(STATIC)


def checks(p):
    # the slab is centred on the wall line; the ring pull on one face shifts the bounds in Z
    return kit_checks(p.width + 0.02, p.height, (0.12, 0.16), 300, mats=2, tex=512,
                      anchor=(0.5, 0.0, None))


def build(p):
    slab = block(p.width, p.height, p.thick)
    slab = slab.with_uv(slab.uv * [1.25, 1.0])                    # 5 planks across from a 4-plank map
    straps = [block(p.width + 0.02, p.strap, p.thick + 0.04, y=y) for y in (0.3, 1.08, 1.86)]
    ring = torus(0.06, 0.009, 12, 6).rotated(90, "x").moved(0.36, 1.03, -(p.thick / 2 + 0.035))
    boss = block(0.05, 0.05, 0.03, 0.36, 1.07, -(p.thick / 2 + 0.03))
    return Model((slab, planks(512, 4, seed=7, along="y")),
                 (box_uv(merge(*straps, ring, boss), 2.0), iron()))
