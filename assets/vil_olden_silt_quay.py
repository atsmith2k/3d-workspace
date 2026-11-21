"""Silt Quay, a wool freight lane ending at a sheltered tidal landing.

Spec: 48 x 40 m, a clear 4 m escort lane and dry access to the delivery
bay, headroom of 2.25 m, at most 45,000 triangles and 1024 px textures.
"""

from _frp import ball, box, custom, ground, iron_rusted, materials, paving, size, stone, texture_size, timber, tris
from _olden_elimination_venues import Yard, beam, crate_stack, gable, route_fixture, solid, tint_surface
from _olden_ticketed_venues import slab, stake, water

KIND = "environment"
DESCRIPTION = "Silt Quay, a wool cart lane, two slate warehouses and a low tide ferry landing"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=45000, materials=8, texture=1024)
PRODUCT = dict(collection="olden_times", gameplay=dict(map_id="silt_quay",
    footprint_xz_m=[48,40], clear_headroom_m=2.25, collision="separate level fixtures"))


def build(p):
    yard = Yard()
    ground_mat = tint_surface(ground(1024, 75), "quay_dried_silt", (.49,.43,.31), .68)
    setts = tint_surface(paving(1024, 76), "quay_worn_cart_setts", (.43,.48,.46), .64)
    masonry = tint_surface(stone(1024, 77), "quay_brown_mortar", (.53,.48,.37), .53)
    wood = timber(512, 78)
    slate = tint_surface(paving(512, 79), "quay_leaden_shakes", (.24,.28,.31), .73)
    iron = iron_rusted(512, 80)
    rope = tint_surface(ground(512, 81), "quay_linen_and_hemp", (.64,.46,.24), .79)
    tide = water("quay_tidal_water", (.06,.19,.19), 4)
    slab(yard, ground_mat, (-24,24,-20,16))
    slab(yard, setts, (-2.4,2.4,-19.8,15.8), .004, .065)
    slab(yard, tide, (-24,24,16,20), -.26, .10, walk=False)
    slab(yard, wood, (-8,8,16,20))
    for x in (-10.5,10.5):
        solid(yard, masonry, (x-1.5,x+1.5,-7,-3,0,2.75))
        gable(yard,wood,slate,x,-5,3.55,4.6,2.73,1.06)
        yard.add(wood,box(1.37,2.0,.12,.67).moved(x,1.0,-2.95))
    for x in (-11.5,11.5):
        solid(yard,masonry,(x-1.5,x+1.5,6,9,0,3))
        gable(yard,wood,slate,x,7.5,3.65,3.55,2.98,.88)
        yard.add(wood,box(1.32,2.07,.115,.65).moved(x,1.08,5.94))
    for x in (-6,6):
        for z in (16.8,17.45):
            crate_stack(yard,wood,iron,x,z,.54)
        stake(yard,wood,masonry,x,18.8)
    # Ship moorings and rope coils are visual cues at the edges of the landing.
    for x in (-14,14):
        yard.add(wood,box(6.6,.19,2.21,.56).moved(x,-.13,18.08))
        for side in (-1,1):
            yard.add(wood,box(6.25,.75,.19,.65).moved(x,.22,18.08+side*1.15))
            yard.add(wood,beam((x-3.12,.32,18.08+side*1.15),
                               (x-3.78,.41,18.08),.21,.26))
        for j in range(4):
            yard.add(rope,ball(.28+.055*j,12,6).scaled(1,.30,.82).moved(
                x+1.52,.06+.071*j,18.26))
    return yard.finish()


def checks(p):
    def routes(ctx):
        return route_fixture(ctx.model, [(-2,2,-15,7), (3.8,6.4,9,14),
                                         (-2.0,2.0,13.9,19.55)], 2.25)

    return [size(x=48,y=(3.9,4.6),z=40,tol=.001),tris(max=45000),materials(8),
            texture_size(1024),custom("cart lane and delivery approach",routes)]
