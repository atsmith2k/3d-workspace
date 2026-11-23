"""Lintel Green's outdoor sparring turf, observation bank and surrounding coppice."""

from _frp import custom, materials, texture_size, tris
from _olden_practice_courts import (
    LINTEL_FLOOR, LINTEL_OBSTACLES, LINTEL_RINGS,
    clear_ring_routes, lintel_green, scenery_inside_collision,
)


KIND = "environment"
DESCRIPTION = "Village practice green with a timber lintel and a terraced observation bank"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=14000, materials=7, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(
    map_id="lintel_green", floor=LINTEL_FLOOR, obstacles=LINTEL_OBSTACLES,
    rings=LINTEL_RINGS, visual_only=True,
))


def build(p):
    return lintel_green()


def checks(p):
    def routes(ctx):
        return clear_ring_routes(ctx.model, LINTEL_RINGS, ((-17, 17, -2, 0), (-2, 2, -12, 10.5)))

    def collision(ctx):
        return scenery_inside_collision(ctx.model, LINTEL_FLOOR, LINTEL_OBSTACLES)

    return [tris(max=14000), materials(7), texture_size(512),
            custom("clear sparring rings and cross routes", routes),
            custom("scenery versus collision", collision)]
