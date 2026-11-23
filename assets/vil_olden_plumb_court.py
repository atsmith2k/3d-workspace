"""Plumb Court's paved sparring courts, rubble walls and tiled town frontage."""

from _frp import custom, materials, texture_size, tris
from _olden_practice_courts import (
    PLUMB_FLOOR, PLUMB_OBSTACLES, PLUMB_RINGS,
    clear_ring_routes, plumb_court, scenery_inside_collision,
)


KIND = "environment"
DESCRIPTION = "Stone town practice courts with a timber gate and a view of surrounding lodges"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=14000, materials=7, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(
    map_id="plumb_court", floor=PLUMB_FLOOR, obstacles=PLUMB_OBSTACLES,
    rings=PLUMB_RINGS, visual_only=True,
))


def build(p):
    return plumb_court()


def checks(p):
    def routes(ctx):
        return clear_ring_routes(ctx.model, PLUMB_RINGS, ((-13, 13, -1.5, 1.5), (-2, 2, 0, 11.8)))

    def collision(ctx):
        return scenery_inside_collision(ctx.model, PLUMB_FLOOR, PLUMB_OBSTACLES)

    return [tris(max=14000), materials(7), texture_size(512),
            custom("clear sparring rings and cross routes", routes),
            custom("scenery versus collision", collision)]
