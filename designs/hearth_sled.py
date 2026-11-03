"""Vintage Sled: a wooden sled with curled red runners carrying two wrapped gifts.

Spec:
  object:       vintage snow sled for sweatshirts, pillows, totes, kids' wear
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      cocoa (stanchions), ginger (deck), red (runners, big gift), ice (small
                gift), gold (ribbons, bows): 5 colours
  must have:    a 70 mm wooden deck on three stanchions; 2 mm red satin runners curling
                up at the front; a 22 x 18 mm red gift and a 16 x 13 mm ice-blue gift
                sitting on the deck, each with a 3.4 mm gold ribbon and a gold bow
  density:      gifts knock out the deck, ribbons and bows knock out the gifts; max 3.5
"""
from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hearth import C_, SIZES, fit, hoop_for, product, sew_bow, standard_checks

DESCRIPTION = "Vintage wooden sled with curled red runners carrying two wrapped gifts"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Vintage Sled with Gifts Embroidery Design",
    "A vintage wooden sled with red runners carrying two wrapped presents",
    ["sled", "vintage sled", "snow day", "christmas gifts", "winter fun", "kids winter"],
    "A vintage wooden sled with curled red runners, loaded with two presents tied up in gold "
    "ribbon and bows.\n\nGreat on sweatshirts, pillows, totes and kids' wear.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 11000)


def art():
    d = Design()
    runner = spline([(-40, -18), (0, -18), (22, -18), (33, -16.5), (38.5, -11), (37, -5.5), (32.5, -5),
                     (31, -8.5)], samples=10)
    stanchions = [rect(2.8, 8.5, x, -13.5) for x in (-29, -7, 15)]
    deck = rounded_rect(70, 5, 2.2, -4, -8)
    big = rect(22, 18.5, -20, 3.5)
    small = rect(16, 13, 2.5, 0.8)
    rib_big = union(rect(3.4, 18.5, -20, 3.5), rect(22, 3.4, -20, 3.5))
    rib_small = union(rect(3.4, 13, 2.5, 0.8), rect(16, 3.4, 2.5, 0.8))
    bow_big = [move(g, -20, 13.5) for g in M.bow(15)]
    bow_small = [move(g, 2.5, 8.0) for g in M.bow(11)]
    bows = union(*bow_big, *bow_small)
    d.fill(knockout(union(*stanchions), deck), C_["cocoa"], angle=90, name="stanchion")
    d.fill(knockout(deck, big, small), C_["ginger"], angle=0, name="deck")
    d.satin(runner, 2.0, C_["red"], name="runner", trim_after=True)
    d.fill(knockout(big, rib_big, bows, small), C_["red"], angle=45, name="big gift")
    d.fill(knockout(small, rib_small, bows), C_["ice"], angle=135, name="small gift")
    d.fill(knockout(union(rib_big, rib_small), bows, knockout(small, rib_small)), C_["gold"], angle=None,
           name="ribbon")
    sew_bow(d, bow_big, C_["gold"], C_["gold"])
    sew_bow(d, bow_small, C_["gold"], C_["gold"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
