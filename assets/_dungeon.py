"""Dungeon kit: what every piece shares. One grid, one stone, one licence.

Grid: 2 m cells. Walls are 3 m high and 0.4 m thick, centred on the cell edge they stand on.
Doorways open 1.2 x 2.2 m. Floors have their walking surface at Y=0. A piece faces -Z.
Stone is one 1024 px texture over a 2 m tile (512 px per metre): blocks 1.0 x 0.5 m on
walls, 0.5 m flags on floors, world-projected so courses line up across neighbouring pieces.
"""
from cadkit.game import *

GRID, WALL_H, WALL_T = 2.0, 3.0, 0.4
DOOR_W, DOOR_H = 1.2, 2.2
PLINTH_H, PLINTH_OUT = 0.35, 0.06
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["dungeon", "modular", "medieval"])
STATIC = dict(body="static", collider="auto", rest_y=0.0)


def stone():
    return stone_blocks(1024, rows=4, cols=2, seed=1)


def paving():
    return flagstones(1024, rows=4, cols=4, seed=2)


def stoned(mesh):
    """World-scale stone UVs: one texture repeat every 2 m."""
    return box_uv(mesh, 1 / GRID)


def wall_run(width, x=0.0, height=WALL_H, y=0.0, plinth=True):
    """A stretch of wall standing on Y=y, centred on X=x: a plinth course and the wall above."""
    if not plinth:
        return block(width, height, WALL_T, x, y)
    return merge(block(width, PLINTH_H, WALL_T + 2 * PLINTH_OUT, x, y),
                 block(width, height - PLINTH_H, WALL_T, x, y + PLINTH_H))


def kit_checks(x, y, z, tris_max, mats=1, anchor="base", tex=1024):
    return [size(x=x, y=y, z=z), tris(max=tris_max), pivot(anchor), materials(mats), texture_size(tex)]
