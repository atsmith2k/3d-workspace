"""Leather folio with a scarlet seal for the Silt Quay handoff.

Spec: 0.6 m folio with a raised wax impression, under 2,200 triangles and
three original materials at 512 px or less.
"""

from _frp import Model, bevel_box, box, cylinder, ground, iron_rusted, materials, merge, size, texture_size, tris
from _olden_elimination_venues import tint_surface

KIND = "prop"
DESCRIPTION = "Silt Quay's sealed folio"
PARAMS = {}
ENGINE = dict(rest_y=0)
BUDGET = dict(tris=2200, materials=3, texture=512)
PRODUCT = dict(collection="olden_times", gameplay=dict(objective="carry"))


def build(p):
    model=Model()
    leather=tint_surface(ground(512,126),"quay_seal_leather",(.36,.25,.16),.73)
    bands=iron_rusted(512,127)
    wax=tint_surface(ground(256,128),"quay_seal_red_wax",(.75,.14,.08),.85)
    model.add(bevel_box(.62,.12,.40,.045).moved(0,.06,0),leather,"folio")
    model.add(merge(box(.52,.026,.060,.7).moved(0,.119,0),
                    box(.06,.024,.354,.7).moved(0,.119,0)),bands,"bands")
    seal=cylinder(.126,.042,24).moved(.087,.145,.012)
    crest=merge(*[box(.028,.014,.07,.67).rotated(30*i,"y").moved(.087,.170,.012)
                   for i in range(3)])
    model.add(merge(seal,crest),wax,"wax")
    return model


def checks(p):
    return [size(x=(.58,.64),y=(.15,.20),z=(.36,.42)),tris(max=2200),
            materials(3),texture_size(512)]
