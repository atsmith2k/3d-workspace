"""Dungeon doorway: a 2 m wall with a 1.2 x 2.2 m opening and a proud lintel.

Spec:
  kind: environment
  size: 2.0 x 3.0 x 0.52 m
  pivot: base centre on Y=0; the opening is centred
  budget: 72 triangles, one material, 1024 px textures
  materials: stone blocks, as dungeon_wall
  features: opening 1.2 m wide x 2.2 m high; jambs 0.4 m with plinths; lintel 0.3 m deep
            standing 40 mm proud of the wall face
  use: between two cells; dungeon_door (1.16 x 2.16 m) closes it
  engine: body static, auto collider (triangle mesh, so the opening is walkable)
"""
from _dungeon import *

KIND = "environment"
DESCRIPTION = "dungeon doorway, 1.2 x 2.2 m opening"
PARAMS = dict(lintel=0.3, proud=0.04)
BUDGET = dict(tris=72, texture=1024, materials=1)
ENGINE = dict(STATIC)


def checks(p):
    def opening(ctx):
        v = sum(abs(volume(m)) for m, _ in ctx.model.parts)
        solid = GRID * WALL_H * WALL_T
        return v < solid, f"{v:.2f} m3 of stone against {solid:.2f} m3 for a blank wall: the opening is there"
    return kit_checks(GRID, WALL_H, WALL_T + 2 * PLINTH_OUT, 72) + [custom("opening", opening)]


def build(p):
    jamb = (GRID - DOOR_W) / 2
    x = DOOR_W / 2 + jamb / 2
    parts = [wall_run(jamb, -x, DOOR_H), wall_run(jamb, x, DOOR_H),
             block(GRID, p.lintel, WALL_T + 2 * p.proud, 0, DOOR_H),
             block(GRID, WALL_H - DOOR_H - p.lintel, WALL_T, 0, DOOR_H + p.lintel)]
    return Model((stoned(merge(*parts)), stone()))
