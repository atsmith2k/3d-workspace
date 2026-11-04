"""Polar Bear: a sitting polar bear cub in a green knit hat and a red scarf.

Spec:
  object:       cute polar bear for kids' wear, sweatshirts, blankets and stockings
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; fleece with a water-soluble topper
  threads:      white (fur), sky (1.4 mm satin outline), cream (snout, ear and paw
                pads, hat cuff, pompom), red (scarf), green (hat), black (eyes, nose): 6 colours
  must have:    a 40 mm head with round ears and a cream snout, black eyes and nose; a
                sitting 54 mm body with two feet and cream paw pads; a red scarf with a
                hanging tail; a green knit hat with a cream cuff and pompom
  density:      details knock out the fur; the fur tucks under the outline,
                which runs under the scarf and hat; max 3.5
"""
from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Sitting polar bear cub in a green knit hat and a red scarf"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Polar Bear Cub Embroidery Design",
    "A sitting polar bear cub in a knit hat and a cosy red scarf",
    ["polar bear", "winter animal", "kids winter", "baby christmas", "cozy winter", "arctic"],
    "A round little polar bear cub sitting in the snow, wrapped in a red scarf and a green knit "
    "hat with a cream pompom.\n\nGreat on kids' wear, sweatshirts, baby blankets and stockings.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.4


def checks(p):
    return standard_checks(p, 6, 13000)


def art():
    d = Design()
    head = ellipse(0, 14, 20, 17.5)
    ears = [circle(-20.5, 17.5, 5.2), circle(20.5, 17.5, 5.2)]
    body = ellipse(0, -20, 25, 23)
    feet = [ellipse(-14, -38, 10, 7), ellipse(14, -38, 10, 7)]
    fur = union(head, *ears, body, *feet)
    snout = ellipse(0, 7.5, 9, 6.5)
    nose = ellipse(0, 10.5, 3.4, 2.4)
    eyes = [circle(-7, 16, 2.0), circle(7, 16, 2.0)]
    pads = [ellipse(-14, -38.5, 5, 3.5), ellipse(14, -38.5, 5, 3.5)]
    inner_ears = [circle(-21, 17.5, 2.4), circle(21, 17.5, 2.4)]
    hat = smooth([(-13.5, 23), (-11.5, 33), (-4.5, 38.5), (5.5, 38.5), (11.5, 33), (13.5, 23)], 8).buffer(0)
    cuff = rounded_rect(30, 6.5, 2.5, 0, 24)
    pom = circle(4, 41.5, 5)
    scarf = union(smooth([(-19, -1), (0, -4), (19, -1), (18, -7.5), (0, -10.5), (-18, -7.5)], 8).buffer(0),
                  smooth([(5, -6), (13, -6), (14.5, -26), (4, -26.5)], 6).buffer(0))
    lid = union(hat, cuff, pom)
    inner_ears = [knockout(g, lid.buffer(0.8)) for g in inner_ears]
    over = union(lid, scarf, snout, *eyes, *pads, *inner_ears)
    d.fill(knockout(tuck(fur, BORDER), over), C_["white"], angle=70, name="fur")
    d.outline(fur, C_["sky"], width=BORDER, name="outline")
    for g in [snout, *pads, *inner_ears]:
        d.fill(knockout(g, nose), C_["cream"], angle=0, name="cream")
    d.fill(knockout(cuff, pom), C_["cream"], angle=90, name="hat cuff")
    d.fill(pom, C_["cream"], angle=45, name="pompom")
    d.fill(scarf, C_["red"], angle=10, name="scarf")
    d.fill(knockout(hat, cuff, pom, overlap=0.3), C_["green"], angle=90, name="hat")
    d.fill(nose, C_["black"], angle=0, name="nose")
    for g in eyes:
        d.fill(g, C_["black"], angle=45, underlay=False, name="eye")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
