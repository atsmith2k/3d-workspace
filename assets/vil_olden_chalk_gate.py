"""The removable timber leaves of Chalk March's initial breach.

Spec: fits a 4.5 m opening, touches floor, below 3.4 m tall and one metre
deep. Textured oak and iron only, at most 3,000 triangles.
"""

from _frp import Model, box, iron_rusted, materials, merge, size, texture_size, timber, tris
from _olden_elimination_venues import beam

KIND = "prop"
DESCRIPTION = "Chalk March's iron-braced breach doors"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=3000, materials=2, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(objective="breach", radius_m=2.25))


def build(p):
    model=Model()
    wood=timber(512,106)
    iron=iron_rusted(512,107)
    planks=[]
    rails=[]
    for side in (-1,1):
        planks.append(box(.22,3.36,.48,.66).moved(side*2.14,1.68,0))
        for j in range(8):
            x=side*(.14+j*.251)
            planks.append(box(.238,2.92,.22,.55).moved(x,1.46,0))
        for face in (-1,1):
            planks.append(beam((side*.13,.29,face*.19),(side*2.03,2.68,face*.19),.19,.145))
            for y in (.46,1.7,2.56):
                rails.append(box(2.02,.134,.10,.66).moved(side*1.08,y,face*.14))
    planks.append(box(4.5,.23,.61,.67).moved(0,3.23,0))
    model.add(merge(*planks),wood,"leaves")
    model.add(merge(*rails),iron,"bands")
    return model


def checks(p):
    return [size(x=4.5,y=(3.31,3.4),z=(.55,1.0)),tris(max=3000),
            materials(2),texture_size(512)]
