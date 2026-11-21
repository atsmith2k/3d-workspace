"""Ferry Stores, a weathered cargo yard with twin loading-bay flanks.

Spec: 34 x 28 m in Y-up metres, walkable level floor, two continuous
3 m flanks, headroom of 2.25 m, at most 40,000 triangles and 1024 px textures.
"""

from _frp import box, custom, iron_rusted, materials, paving, size, stone, texture_size, timber, tris
from _olden_elimination_venues import Yard, beam, crate_stack, gable, route_fixture, solid, tint_surface

KIND = "environment"
DESCRIPTION = "Ferry Stores, a slate cargo warehouse and timber hoists between two cart lanes"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=40000, materials=7, texture=1024)
PRODUCT = dict(collection="olden_times", gameplay=dict(map_id="ferry_stores",
    footprint_xz_m=[34, 28], clear_headroom_m=2.25, collision="separate level fixtures"))

BAY = (-4.8, 4.8, -5.4, 5.4, 0, 3.65)


def build(p):
    yard = Yard()
    cobbles = tint_surface(paving(1024, 22), "ferry_gray_setts", (.43, .43, .39), .63)
    apron = tint_surface(paving(512, 23), "ferry_apron", (.55, .45, .34), .51)
    granite = tint_surface(stone(1024, 24), "ferry_granite", (.43, .40, .36), .65)
    ash = tint_surface(timber(512, 25), "ferry_oiled_ash", (.55, .36, .21), .48)
    tar = tint_surface(paving(512, 26), "ferry_tarred_shakes", (.24, .31, .33), .72)
    iron = iron_rusted(512)
    yard.add(cobbles, box(34, .22, 28, .58).moved(0, -.11, 0), walk=True)
    for x in (-9.4, 9.4):
        yard.add(apron, box(3.2, .06, 27.6, .62).moved(x, -.026, 0), walk=True)
    solid(yard, granite, BAY)
    gable(yard, ash, tar, 0, 0, 10.2, 11.2, 3.62, 1.42)
    for z in (-5.43, 5.43):
        for x in (-3.6, 0, 3.6):
            yard.add(ash, box(1.54, 2.44, .09, .8).moved(x, 1.22, z))
            yard.add(iron, box(1.5, .11, .13, .9).moved(x, 1.45, z))
        yard.add(ash, box(9.8, .22, .18, 1).moved(0, 2.72, z))
    for x in (-14.7, 14.7):
        for z in (-8.65, 8.65):
            solid(yard, granite, (x - 1.75, x + 1.75, z - 3, z + 3, 0, 2.84))
            gable(yard, ash, tar, x, z, 4.2, 6.4, 2.82, 1.02)
        for z in (-3.6, 0, 3.6):
            crate_stack(yard, ash, iron, x, z, 1.02)
    for x, sign in ((-5.7, -1), (5.7, 1)):
        for z in (-6.2, 6.2):
            yard.add(granite, box(.74, .36, .75, .75).moved(x, .18, z))
            yard.add(ash, box(.24, 4.8, .24, .75).moved(x, 2.62, z),
                     beam((x, 3.4, z), (x + sign * 1.1, 4.45, z), .15, .15),
                     beam((x - sign * .16, 4.45, z), (x + sign * 1.43, 4.45, z), .21, .26))
            yard.add(iron, box(.033, 1.12, .033).moved(x + sign * 1.34, 3.88, z))
    return yard.finish()


def checks(p):
    def lanes(ctx):
        return route_fixture(ctx.model, [(x - 1.5, x + 1.5, -12, 12)
                                         for x in (-9.4, 9.4)], 2.25)

    return [size(x=34, y=(5, 5.5), z=28, tol=.001), tris(max=40000),
            materials(7), texture_size(1024), custom("both cart lanes", lanes)]
