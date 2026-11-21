"""Toll Orchard, a walled fruit garden with an open central toll path.

Spec: 34 x 28 m in Y-up metres, walkable level floor, 4 m central approach
and transverse orchard lanes, 2.25 m headroom, 40,000 triangles and 1024 px textures.
"""

from _frp import ball, box, custom, ground, materials, paving, size, stone, texture_size, timber, tris
from _olden_elimination_venues import Yard, apple_tree, gable, route_fixture, solid, tint_surface

KIND = "environment"
DESCRIPTION = "Toll Orchard, a clear toll road between clipped hedges and fruit trees"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=40000, materials=8, texture=1024)
PRODUCT = dict(collection="olden_times", gameplay=dict(map_id="toll_orchard",
    footprint_xz_m=[34, 28], clear_headroom_m=2.25, collision="separate level fixtures"))


def build(p):
    yard = Yard()
    grass = tint_surface(ground(1024, 33), "orchard_meadow", (.34, .43, .23), .68)
    gravel = tint_surface(paving(1024, 34), "orchard_toll_road", (.52, .48, .35), .70)
    limestone = tint_surface(stone(1024, 35), "orchard_limestone", (.54, .53, .40), .56)
    oak = timber(512, 36)
    hedge = tint_surface(ground(512, 37), "orchard_box_hedge", (.16, .30, .16), .72)
    leaves = tint_surface(ground(512, 38), "orchard_apple_canopy", (.29, .43, .17), .70)
    fruit = tint_surface(paving(256, 39), "orchard_red_fruit", (.75, .13, .045), .84)
    roof = tint_surface(stone(512, 40), "orchard_mossy_tiles", (.31, .33, .23), .66)
    yard.add(grass, box(34, .22, 28, .57).moved(0, -.11, 0), walk=True)
    yard.add(gravel, box(4.35, .045, 27.9, .62).moved(0, -.0185, 0), walk=True)
    for x in (-15.9, 15.9):
        solid(yard, limestone, (x - .48, x + .48, -13.7, 13.7, 0, 1.7))
        for z in (-10, 0, 10):
            yard.add(limestone, box(1.07, .25, .82, .8).moved(x, 1.83, z))
    for side in (-1, 1):
        x = side * 5.7
        for z in (-6.1, 6.1):
            solid(yard, limestone, (x - .73, x + .73, z - 3, z + 3, 0, .33))
            for j in range(13):
                yard.add(hedge, ball(.64, 9, 5).scaled(1.08, 1.08 + .08 * (j % 3), 1.12)
                         .moved(x, .83, z - 2.38 + j * .40))
        for i, z in enumerate((-9, -5.1, 5.1, 9)):
            trunk_x = side * (10.8 if i % 2 == 0 else 12.2)
            apple_tree(yard, oak, leaves, fruit, trunk_x, z, .83 + .08 * (i % 3))
        shelter_x = side * 12.7
        for z in (-11.8, 11.8):
            solid(yard, limestone, (shelter_x - 1.4, shelter_x + 1.4, z - .78, z + .78, 0, 2.4))
            gable(yard, oak, roof, shelter_x, z, 3.5, 2.13, 2.38, .82)
        for z in (-12.4, 12.4):
            post = side * 3.34
            yard.add(oak, box(.20, 2.52, .24, .65).moved(post, 1.26, z),
                     box(.60, .43, .09, .72).moved(post + side * .35, 1.96, z))
    return yard.finish()


def checks(p):
    def lanes(ctx):
        return route_fixture(ctx.model, [(-2, 2, -12, 12),
                                         (-13.4, 13.4, -1.5, 1.5)], 2.25)

    return [size(x=34, y=(4, 5.4), z=28, tol=.001), tris(max=40000),
            materials(8), texture_size(1024), custom("toll path and orchard crossing", lanes)]
