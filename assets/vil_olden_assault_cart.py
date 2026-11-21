"""A low wool wagon with steel-banded spoked wheels.

Spec: under 3.5 m long and 2.1 m wide, wheels touch the Y=0 floor,
original wood, iron and wool textures at 512 px or less.
"""

from _frp import Model, ball, box, cylinder, ground, iron_rusted, materials, merge, size, texture_size, timber, torus, tris
from _olden_elimination_venues import beam, tint_surface

KIND = "prop"
DESCRIPTION = "Olden Times wool escort cart"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=8500, materials=3, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(objective="escort", axes="Y up, -Z forward"))


def build(p):
    model=Model()
    ash=timber(512,110)
    iron=iron_rusted(512,111)
    wool=tint_surface(ground(512,112),"quay_cart_wool",(.72,.69,.55),.82)
    planks=[box(1.4,.19,1.89,.70).moved(0,.68,.08)]
    metal=[]
    sacks=[]
    for side in (-1,1):
        x=side*.79
        planks.append(box(.13,.38,1.89,.67).moved(side*.72,.95,.08))
        planks.append(beam((side*.49,.67,-.59),(side*.65,.38,-1.95),.14,.16))
        metal.append(torus(.40,.064,24,8).rotated(90,"z").moved(x,.464,.26))
        metal.append(cylinder(.16,.21,16).rotated(90,"z").moved(x,.464,.26))
        for z in (-.60,.01,.61):
            sacks.append(ball(.38,13,8).scaled(.97,.76,1.06).moved(side*.34,.97,z))
        for i in range(8):
            spoke=box(.084,.76,.075,.75).rotated(i*22.5,"x").moved(x,.464,.26)
            planks.append(spoke)
    for z in (-.92,1.02):
        planks.append(box(1.4,.33,.12,.66).moved(0,.92,z))
    model.add(merge(*planks),ash,"wood")
    model.add(merge(*metal),iron,"metal")
    model.add(merge(*sacks),wool,"wool")
    return model


def checks(p):
    return [size(x=(1.7,2.1),y=(1,1.5),z=(2.9,3.5)),tris(max=8500),
            materials(3),texture_size(512)]
