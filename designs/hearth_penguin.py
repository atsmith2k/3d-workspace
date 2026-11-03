"""Skating Penguin: a penguin in a red bobble hat and striped scarf, on ice skates.

Spec:
  object:       cute penguin for kids' wear, sweatshirts, stockings and towels
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; towels with a water-soluble topper
  threads:      black (body, flippers), white (belly, face, hat cuff, pompom), orange
                (beak, feet), red (hat, scarf stripes), green (scarf), silver (skate
                blades): 6 colours
  must have:    a 60 mm egg-shaped black body with two flippers; a white heart-shaped
                face and belly; two eyes, an orange beak; a red bobble hat with a white
                cuff and pompom; a green scarf with red stripes and a tail; orange feet
                on two silver 1.4 mm satin skate blades
  density:      face and details knock out the body; max 3.5
"""
import numpy as np

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Penguin on ice skates in a red bobble hat and a striped scarf"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Ice Skating Penguin Embroidery Design",
    "A little penguin on ice skates in a red bobble hat and a striped scarf",
    ["penguin", "ice skating", "winter animal", "kids winter", "christmas penguin", "cozy winter"],
    "A happy little penguin out on the ice in silver skates, a red bobble hat and a green "
    "striped scarf.\n\nGreat on kids' wear, sweatshirts, stockings and towels.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 12000, between_mm2=2.0)


def art():
    d = Design()
    body = smooth([(0, 30), (12, 24), (19, 6), (21, -14), (16, -28), (0, -32), (-16, -28), (-21, -14),
                   (-19, 6), (-12, 24)], 10).buffer(0)
    flippers = [rotate(ellipse(-21, -6, 4.5, 13), -18, origin=(-21, 4)),
                rotate(ellipse(21, -6, 4.5, 13), 18, origin=(21, 4))]
    dark = union(body, *flippers)
    face = union(circle(-6, 13, 8.5), circle(6, 13, 8.5), ellipse(0, -10, 14, 19)).intersection(
        body.buffer(-2.5))
    eyes = [circle(-5.5, 15, 2.0), circle(5.5, 15, 2.0)]
    beak = poly([(-4, 9.5), (4, 9.5), (0, 4.5)]).buffer(0.6)
    hat = smooth([(-14, 24), (-11, 33), (0, 38), (11, 33), (14, 24)], 8).buffer(0)
    cuff = rounded_rect(30, 6, 2.4, 0, 24.5)
    pom = circle(0, 40, 4.6)
    scarf = union(smooth([(-17, 3.5), (0, 0.5), (17, 3.5), (16, -3), (0, -6), (-16, -3)], 8).buffer(0),
                  poly([(-13, -2), (-6, -2), (-8, -20), (-11.5, -18.5), (-14.5, -20)]))
    stripes = union(*[rect(2.4, 30, x, -4) for x in (-12, -4, 4, 12)],
                    rect(10, 2.2, -10, -12)).intersection(scarf)
    feet = [ellipse(-8, -32, 7, 3.2), ellipse(8, -32, 7, 3.2)]
    blades = [np.array([(x - 8, -37), (x + 7, -37), (x + 9, -35)]) for x in (-8, 8)]
    lid = union(hat, cuff, pom)
    over = union(face, lid, scarf, *feet)
    d.fill(knockout(dark, over), C_["black"], angle=75, name="body")
    for g in eyes:
        d.fill(g, C_["black"], angle=45, underlay=False, name="eye")
    d.fill(knockout(face, *eyes, beak, scarf), C_["white"], angle=0, name="face and belly")
    d.fill(knockout(cuff, pom), C_["white"], angle=90, name="hat cuff")
    d.fill(pom, C_["white"], angle=45, name="pompom")
    d.fill(beak, C_["orange"], angle=0, name="beak")
    for g in feet:
        d.fill(g, C_["orange"], angle=0, name="foot")
    d.fill(knockout(scarf, stripes), C_["green"], angle=0, name="scarf")
    d.fill(knockout(hat, cuff, pom), C_["red"], angle=90, name="hat")
    d.fill(stripes, C_["red"], angle=90, underlay=False, name="scarf stripes")
    for b in blades:
        d.satin(b, 1.4, C_["silver"], name="skate blade", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
