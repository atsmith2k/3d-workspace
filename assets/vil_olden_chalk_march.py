"""Chalk March, a limestone breach line and exposed signal stores.

Spec: 48 x 40 m, a clear corridor through the detachable gate, two
3 m outlying paths, the stores approach and 2.25 m headroom. Maximum
45,000 triangles and 1024 px textures.
"""

from _frp import ball, box, custom, ground, iron_rusted, materials, paving, size, stone, texture_size, timber, tris
from _olden_elimination_venues import Yard, beam, crate_stack, gable, route_fixture, solid, tint_surface
from _olden_ticketed_venues import slab

KIND = "environment"
DESCRIPTION = "Chalk March, pale gate cliffs, switchback lanes and paired signal sheds"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=45000, materials=8, texture=1024)
PRODUCT = dict(collection="olden_times", gameplay=dict(map_id="chalk_march",
    footprint_xz_m=[48,40], clear_headroom_m=2.25, collision="separate level fixtures"))


def build(p):
    yard = Yard()
    dust = tint_surface(ground(1024, 91), "march_chalk_dust", (.60,.55,.44), .66)
    setts = tint_surface(paving(1024, 92), "march_abrasion_setts", (.44,.43,.39), .60)
    chalk = tint_surface(stone(1024, 93), "march_flaked_chalk", (.71,.70,.59), .64)
    shingles = tint_surface(paving(512, 94), "march_weathered_tile", (.31,.31,.34), .71)
    wood = timber(512, 95)
    iron = iron_rusted(512, 96)
    red = tint_surface(ground(512, 97), "march_signal_cloth", (.65,.27,.13), .79)
    slab(yard,dust,(-24,24,-20,20))
    slab(yard,setts,(-2.15,2.15,-19.8,19.8),.004,.065)
    for side in (-1,1):
        edges=sorted((side*2.25,side*19.4))
        solid(yard,chalk,(edges[0],edges[1],-1.25,1.25,0,3.6))
        for i in range(5):
            x=side*(4.2+3.25*i)
            yard.add(chalk,box(1.22,.72,2.52,.56).moved(x,3.95,0),
                     box(1.1,.54,.57,.58).moved(x,3.89,-1.27))
        for i in range(6):
            x=side*(3.38+2.63*i)
            yard.add(chalk,box(.39,2.68,.23,.57).moved(x,1.36,-1.24))
        x=side*8.75
        solid(yard,chalk,(x-1.25,x+1.25,5.5,8.5,0,3))
        gable(yard,wood,shingles,x,7,2.94,3.62,2.97,1.04)
        yard.add(wood,box(1.23,2.19,.09,.71).moved(x,1.10,5.44))
        yard.add(red,box(.62,.83,.035,.6).moved(x,.86,5.37))
        yard.add(wood,beam((x,1.95,5.42),(x,3.31,5.25),.075,.085))
        crate_stack(yard,wood,iron,side*4,10.27,.81)
    # The signal store objective is marked by a pair of empty fire baskets.
    for x in (-2.73,2.73):
        yard.add(iron,ball(.33,16,8).scaled(1,.47,1).moved(x,1.23,7.18),
                 box(.16,1.05,.16,.63).moved(x,.52,7.18))
    return yard.finish()


def checks(p):
    def routes(ctx):
        return route_fixture(ctx.model,[(-1.8,1.8,-6.2,8.4),
                                         (-22.85,-19.8,-9,9),
                                         (19.8,22.85,-9,9)],2.25)

    return [size(x=48,y=(4.2,4.9),z=40,tol=.001),tris(max=45000),materials(8),
            texture_size(1024),custom("breach approach and bypasses",routes)]
