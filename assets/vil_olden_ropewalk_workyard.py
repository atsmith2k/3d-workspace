"""Ropewalk, a covered ropeworks with two running lanes and timber screens.

Spec:
    The floor spans 46 by 20 m. Low works and screens fit the eight authored
    collision boxes. Both 2.4 m running lanes and the crossovers stay clear
    to 2.3 m. Opaque PBR maps fit 512 px and the mesh fits 30000 triangles.
"""

from _frp import custom, materials, size, texture_size, tris
from _olden_elimination_venues import route_fixture
from _olden_ladder_workyards import fixture_bounds, ROPEWALK_FIXTURES, ROPEWALK_FLOORS, ropewalk

KIND = "environment"
DESCRIPTION = "Textured timber ropeworks with covered edges, hemp reels and open running lanes"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=30000, materials=8, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(
    map_id="ropewalk",
    floor_patches=ROPEWALK_FLOORS,
    obstacle_boxes=ROPEWALK_FIXTURES,
    visual_only=True,
))


def build(p):
    return ropewalk()


def checks(p):
    def lanes(ctx):
        return route_fixture(ctx.model, [
            (-21.0, 20.0, -3.7, -1.3), (-21.0, 20.0, 1.3, 3.7),
            (5.7, 8.3, -3.5, 3.5), (-18.4, -15.7, -3.5, 3.5),
        ], 2.3)

    def collision(ctx):
        return fixture_bounds(ctx.model, ROPEWALK_FIXTURES, 23, 10)

    return [size(x=46, y=(4.5, 4.9), z=20, tol=.002), tris(max=30000),
            materials(8), texture_size(512), custom("dressing versus collision", collision), custom("headroom in both lanes and crossovers", lanes)]
