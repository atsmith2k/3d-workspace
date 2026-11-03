"""Nutcracker Soldier: a classic wooden toy-soldier nutcracker standing to attention.

Spec:
  object:       traditional nutcracker (generic toy soldier, no film or ballet character)
                for stockings, sweatshirts, towels and kids' wear
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7), about 2:5 wide
  fabric:       knits with cut-away; wovens and towels with tear-away (+ topper on towels)
  threads:      navy (tall hat and trousers), red (jacket and arms), cream (face), pink
                (cheeks), white (beard, hair and gloves), black (boots, belt, eyes),
                gold (hat band and badge, buttons, buckle, epaulettes): 7 colours
  must have:    a 22 mm tall hat with a gold band and a star badge; a face with two eyes
                and rosy cheeks over a white beard and moustache; a red jacket with arms,
                three gold buttons, gold epaulettes and a black belt with a gold buckle;
                white gloves; navy trousers with a 1.2 mm gold stripe down each leg;
                black boots
  density:      every part knocks out what it covers; max 3.5 layers
"""
from cadkit.stitch import *

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Classic toy-soldier nutcracker in navy, red and gold"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Nutcracker Soldier Embroidery Design",
    "A classic wooden toy-soldier nutcracker in navy, red and gold",
    ["nutcracker", "toy soldier", "christmas nutcracker", "vintage christmas", "christmas stocking"],
    "The traditional wooden nutcracker soldier: a tall navy hat with a gold star, a white beard "
    "and rosy cheeks, a red jacket with gold buttons and epaulettes, and shiny black boots.\n\n"
    "Great on stockings, sweatshirts, tea towels and kids' wear.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 13000)


def art():
    d = Design()
    hat = rounded_rect(21, 22, 2.5, 0, 42)
    band = rect(21.4, 4, 0, 33.4)
    badge = star(5, 4.2, 1.9, 0, 43)
    face = rounded_rect(18, 18, 4, 0, 22)
    cheeks = [circle(-5.5, 20.5, 2.0), circle(5.5, 20.5, 2.0)]
    eyes = [circle(-4, 25.5, 1.3), circle(4, 25.5, 1.3)]
    hair = [rounded_rect(3.4, 12, 1.6, -10.4, 23), rounded_rect(3.4, 12, 1.6, 10.4, 23)]
    beard = smooth([(-10, 19), (-11, 13), (-6, 6), (0, 4), (6, 6), (11, 13), (10, 19),
                    (5, 17.6), (0, 18.6), (-5, 17.6)], 8).buffer(0)
    jacket = union(rounded_rect(28, 30, 4, 0, -2), rounded_rect(7, 25, 3, -16.5, -1),
                   rounded_rect(7, 25, 3, 16.5, -1))
    gloves = [circle(-16.5, -15, 3.8), circle(16.5, -15, 3.8)]
    epaulettes = [ellipse(-15.5, 11.5, 5.0, 2.4), ellipse(15.5, 11.5, 5.0, 2.4)]
    buttons = [circle(0, y, 1.5) for y in (8, 2.5, -3)]
    belt = rect(28, 4.4, 0, -10)
    buckle = rounded_rect(6, 6, 1, 0, -10)
    trousers = rounded_rect(24, 26, 2, 0, -28)
    boots = [rounded_rect(11.5, 8, 2.5, -6.5, -43), rounded_rect(11.5, 8, 2.5, 6.5, -43)]
    over_body = union(beard, *gloves, *epaulettes, *buttons, belt, buckle)
    d.fill(knockout(trousers, jacket, *boots), C_["navy"], angle=90, name="trousers")
    d.fill(knockout(hat, band, badge), C_["navy"], angle=90, name="hat")
    d.fill(knockout(jacket, over_body, face), C_["red"], angle=90, name="jacket")
    d.fill(knockout(face, beard, *cheeks, *eyes, *hair), C_["cream"], angle=0, name="face")
    for g in cheeks:
        d.fill(knockout(g, beard), C_["pink"], angle=45, underlay=False, name="cheek")
    for g in hair:
        d.fill(g, C_["white"], angle=90, name="hair")
    d.fill(beard, C_["white"], angle=100, name="beard")
    for g in gloves:
        d.fill(g, C_["white"], angle=45, name="glove")
    for g in boots:
        d.fill(g, C_["black"], angle=0, name="boot")
    d.fill(knockout(belt, buckle), C_["black"], angle=90, name="belt")
    for g in eyes:
        d.fill(g, C_["black"], angle=45, underlay=False, name="eye")
    d.fill(knockout(band, badge), C_["gold"], angle=0, name="hat band")
    d.fill(badge, C_["gold"], angle=90, name="badge")
    for g in epaulettes:
        d.fill(g, C_["gold"], angle=0, name="epaulette")
    for g in buttons:
        d.fill(g, C_["gold"], angle=45, underlay=False, name="button")
    d.fill(buckle, C_["gold"], angle=0, name="buckle")
    for x in (-6.5, 6.5):
        d.satin(line((x, -16.5), (x, -38.5)), 1.2, C_["gold"], name="leg stripe", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
