"""Christmas Tree Truck: a vintage red pickup bringing home a Christmas tree.

Spec:
  object:       vintage farm pickup carrying a tree, for sweatshirts, totes, pillows, towels
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      green (tree), red (truck), ice (window), black (door seam, tyres),
                silver (bumpers, hubs), gold (star, headlight): 6 colours
  must have:    a rounded side-view pickup 90 mm long with a cab window, door seam and
                handle, two 16 mm tyres with 7 mm silver hubs, front and rear bumpers,
                a headlight; a 36 mm three-tier tree standing in the bed with a gold
                star on top
  density:      the truck knocks out the tree's base, tyres knock out the body; max 3.5
"""
import numpy as np

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Vintage red pickup truck carrying home a Christmas tree"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Christmas Tree Truck Embroidery Design",
    "A vintage red pickup truck bringing home the Christmas tree",
    ["christmas truck", "red truck", "vintage truck", "farm fresh christmas trees",
     "christmas tree truck", "christmas sweatshirt"],
    "A vintage red farm pickup with rounded fenders and chrome bumpers, bringing home a fresh "
    "green Christmas tree topped with a gold star.\n\nGreat on sweatshirts, totes, pillows and "
    "tea towels.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 11000)


def art():
    d = Design()
    # truck body: bed, cab with a rounded roof, hood with a rounded nose
    bed = rounded_rect(42, 15, 2.0, -21, -8.5)
    cab = smooth([(-3, -16), (-3, 14), (-1, 19), (14, 19), (19, 12), (22, 2), (22, -16)], 6).buffer(0)
    hood = smooth([(20, -16), (20, 3.5), (34, 4.5), (42, 2.0), (45, -4), (45, -16)], 6).buffer(0)
    body = union(bed, cab, hood)
    window = smooth([(1, 4), (1, 15), (13, 15), (17.5, 8), (18.5, 4)], 5).buffer(0)
    tyres = [circle(x, -17, 8.0) for x in (-26, 27)]
    hubs = [circle(x, -17, 3.4) for x in (-26, 27)]
    bumpers = [rounded_rect(5, 4.5, 1.6, 46, -12.5), rounded_rect(4.5, 4.5, 1.6, -43, -12.5)]
    lamp = circle(41, -2.0, 2.0)
    # tree in the bed: three tiers, a little sunk behind the bed rail
    tiers = [poly([(-21, 38 - 13 * k), (-21 - (8 + 4.5 * k), 24 - 13 * k), (-21 + (8 + 4.5 * k), 24 - 13 * k)])
             for k in range(3)]
    tree = union(*tiers, rect(5, 4, -21, -2.5)).buffer(0.8).buffer(-0.8)
    star_ = star(5, 5.2, 2.2, -21, 40.5)
    seam = np.array([(4, -14), (4, 1.5)])
    handle = rounded_rect(5, 1.6, 0.8, 9.5, -1.5)
    d.fill(knockout(tree, body, star_), C_["green"], angle=75, name="tree")
    d.fill(knockout(body, window, *tyres, lamp, *bumpers, handle), C_["red"], angle=0, name="truck")
    d.fill(window, C_["ice"], angle=45, name="window")
    d.run(seam, C_["black"], bean=1, name="door seam", trim_after=True)
    d.fill(handle, C_["black"], angle=0, underlay=False, name="handle")
    for t, h in zip(tyres, hubs):
        d.fill(knockout(t, h), C_["black"], angle=45, name="tyre")
    for g in hubs + bumpers:
        d.fill(g, C_["silver"], angle=90, name="chrome")
    d.fill(star_, C_["gold"], angle=90, name="star")
    d.fill(lamp, C_["gold"], angle=45, underlay=False, name="headlight")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
