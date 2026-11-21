"""Beacon Fen, dry islands and connecting back lanes around a defended signal bell.

Spec: 48 x 40 metres, three occupied islands, 2.6 m shore trails, usable
island back lanes, 2.25 m headroom, at most 40,000 triangles and 1024 px textures.
"""

from _frp import ball, box, custom, ground, iron_rusted, materials, paving, size, stone, texture_size, timber, tris
from _olden_elimination_venues import Yard, route_fixture, tint_surface
from _olden_ticketed_venues import bell, slab, stake, water

KIND = "environment"
DESCRIPTION = "Beacon Fen, three reed-ringed islands and signal bells on stone landings"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=40000, materials=8, texture=1024)
PRODUCT = dict(collection="olden_times", gameplay=dict(map_id="beacon_fen",
    footprint_xz_m=[48,40], clear_headroom_m=2.25, collision="separate level fixtures"))

ISLANDS=(-14,0,14)
SHORES=((-24,24,-20,-8),(-24,24,8,20))
BEDS=tuple((x-4.75,x+4.75,-4.3,4.3) for x in ISLANDS)
PATHS=tuple((x-1.55,x+1.55,z0,z1) for x in ISLANDS for z0,z1 in ((-8,-4.3),(4.3,8)))
LINKS=tuple((x0,x1,z-1.25,z+1.25) for z in (-2.6,2.6) for x0,x1 in ((-9.25,-4.75),(4.75,9.25)))


def build(p):
    yard=Yard()
    hummock=tint_surface(ground(1024,57),"fen_turf",(.34,.43,.25),.62)
    gravel=tint_surface(paving(1024,58),"fen_shingle",(.49,.45,.36),.70)
    mire=water("fen_siltwater",(.061,.145,.120),8)
    shale=tint_surface(stone(1024,60),"fen_lichen_stone",(.43,.41,.31),.57)
    wood=timber(512,61)
    bronze=tint_surface(iron_rusted(512,62),"fen_signal_bronze",(.63,.44,.16),.74)
    roof=tint_surface(paving(512,63),"fen_signal_roof",(.29,.36,.35),.66)
    reeds=tint_surface(ground(512,64),"fen_reed_leaf",(.38,.48,.19),.75)
    slab(yard,mire,(-24,24,-8,8),-.19,.08,walk=False)
    for rect in (*SHORES,*BEDS):
        slab(yard,hummock,rect)
    for rect in (*PATHS,*LINKS):
        slab(yard,gravel,rect)
    for x in ISLANDS:
        for side in (-1,1):
            for z in (-3.8,3.8):
                stake(yard,wood,shale,x+side*3.98,z)
            for z in (-6.8,-1.1,.1,1.05,6.8):
                base_x=x+side*(4.99 if abs(z)<2 else 2.08)
                for stem in range(7):
                    sx=base_x+side*(.12*(stem%3))
                    sz=z+.12*(stem//3)
                    height=.57+.115*(stem%4)
                    yard.add(reeds,box(.031,height,.024,.62).rotated(side*(stem%3+1)*8,"z")
                             .moved(sx,height/2-.1,sz))
                    yard.add(wood,ball(.06,9,6).scaled(.75,2.43,.73).moved(sx,height-.04,sz))
    for z in (-12.65,12.65):
        bell(yard,shale,wood,bronze,roof,z)
    return yard.finish()


def checks(p):
    def crossings(ctx):
        routes=[(x-1.3,x+1.3,-10,10) for x in ISLANDS]
        routes.extend([(-17.4,17.4,z-.83,z+.83) for z in (-2.6,2.6)])
        return route_fixture(ctx.model,routes,2.25)

    return [size(x=48,y=(4,5),z=40,tol=.001),tris(max=40000),materials(8),
            texture_size(1024),custom("island and shore lanes",crossings)]
