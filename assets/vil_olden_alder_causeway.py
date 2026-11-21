"""Alder Causeway, a broad river crossed at three defended fords.

Spec: 48 x 40 metres, three continuous 4.5 m routes, 2.25 m headroom,
two timber toll gates, at most 40,000 triangles and 1024 px textures.
"""

from _frp import box, custom, iron_rusted, materials, paving, size, stone, texture_size, timber, tris
from _olden_elimination_venues import Yard, route_fixture, tint_surface
from _olden_ticketed_venues import gate, slab, stake, water

KIND = "environment"
DESCRIPTION = "Alder Causeway, three stone fords and a timber toll gate on either bank"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=40000, materials=8, texture=1024)
PRODUCT = dict(collection="olden_times", gameplay=dict(map_id="alder_causeway",
    footprint_xz_m=[48,40], clear_headroom_m=2.25, collision="separate level fixtures"))

FORDS=(-14,0,14)
BANKS=((-24,24,-20,-5.5),(-24,24,5.5,20))
CROSSINGS=tuple((x-2.65,x+2.65,-5.5,5.5) for x in FORDS)


def build(p):
    yard=Yard()
    clay=tint_surface(stone(1024,48),"causeway_chalk_bank",(.44,.41,.32),.66)
    setts=tint_surface(paving(1024,49),"causeway_wet_setts",(.49,.54,.54),.71)
    river=water("causeway_river",(.061,.235,.249),5)
    masonry=tint_surface(stone(1024,51),"causeway_tollstone",(.55,.49,.40),.58)
    wood=timber(512,52)
    roof=tint_surface(paving(512,53),"causeway_dark_shakes",(.25,.30,.34),.72)
    iron=iron_rusted(512,54)
    slab(yard,river,(-24,24,-5.5,5.5),-.19,.07,walk=False)
    for bank in BANKS:
        slab(yard,clay,bank)
    for cross in CROSSINGS:
        slab(yard,setts,cross)
    for x in FORDS:
        for side in (-1,1):
            for i in range(9):
                z=-4.85+i*1.2
                yard.add(masonry,box(.24,.24,.82,.52).moved(x+side*2.53,.12,z))
            stake(yard,wood,masonry,x+side*2.67,6.15)
            stake(yard,wood,masonry,x+side*2.67,-6.15)
    for z in (-11.4,11.4):
        gate(yard,masonry,wood,roof,iron,z)
    for side in (-1,1):
        for x in (-22.5,22.5):
            for z in (8.7,13.5,18.1):
                stake(yard,wood,masonry,x,side*z)
    return yard.finish()


def checks(p):
    def crossings(ctx):
        return route_fixture(ctx.model, [(x-2.25,x+2.25,-8.5,8.5) for x in FORDS], 2.25)

    return [size(x=48,y=(3.9,4.5),z=40,tol=.001),tris(max=40000),materials(8),
            texture_size(1024),custom("three fords",crossings)]
