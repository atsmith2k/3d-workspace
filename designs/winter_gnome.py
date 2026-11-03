"""Christmas Gnome: a Scandinavian tomte with a tall red hat, white beard and round nose.

Spec:
  object:       Christmas gnome (tomte) for sweatshirts, stockings, towels and totes
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits and sweatshirts with cut-away; towels with tear-away and a topper
  threads:      cocoa (boots), green (tunic), red (hat), cream (hat brim), white (beard),
                silver (beard strands), blush (nose): 7 colours
  must have:    a 46 mm wide hat whose tip leans and droops right; a 4.6 mm cream brim;
                a 38 mm long cloud beard with four silver bean-stitch strands kept 2 mm
                inside it; a 13 mm round nose over the brim; a green tunic and two cocoa
                boots peeking out under the beard; a small white pom on the hat tip
  density:      each layer knocks out the one under it; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Scandinavian Christmas gnome with a tall red hat and a white beard"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Christmas Gnome Embroidery Design",
    "A Scandinavian tomte with a tall red hat, a fluffy beard and a round nose",
    ["christmas gnome", "tomte", "nisse", "scandinavian gnome", "farmhouse christmas"],
    "A classic Scandinavian tomte: a tall red hat drooping to one side, a cream fur brim, a big "
    "fluffy white beard with silver strands and a round rosy nose, with little boots peeking "
    "out underneath.\n\nGreat on sweatshirts, stockings, tea towels and totes.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 12000)


def art():
    d = Design()
    hat = smooth([(-23, 2), (-20, 16), (-12, 34), (-2, 48), (10, 55), (20, 52), (24, 44),
                  (18, 46), (12, 42), (14, 30), (18, 14), (23, 2)], 10).buffer(0)
    pom = circle(25, 41, 3.6)
    brim = rounded_rect(50, 4.6 * 1.6, 3.6, 0, 3)
    beard = smooth([(-22, 2), (-25, -10), (-20, -24), (-11, -33), (0, -38), (11, -33),
                    (20, -24), (25, -10), (22, 2)], 10).buffer(0)
    nose = circle(0, -1, 6.5)
    tunic = rounded_rect(40, 16, 5, 0, -30).difference(rect(60, 20, 0, -48))
    boots = [ellipse(-10, -40, 7.5, 3.6), ellipse(10, -40, 7.5, 3.6)]
    strands = [spline(np.array(p), 8) for p in (
        [(-15, -8), (-16, -16), (-12, -24)], [(-5, -12), (-6, -22), (-3, -30)],
        [(5, -12), (6, -22), (3, -30)], [(15, -8), (16, -16), (12, -24)])]
    d.fill(knockout(union(*boots), tunic, beard), C_["cocoa"], angle=0, name="boots")
    d.fill(knockout(tunic, beard), C_["green"], angle=90, name="tunic")
    d.fill(knockout(hat, brim, pom, nose), C_["red"], angle=65, name="hat")
    d.fill(knockout(brim, nose, beard), C_["cream"], angle=0, name="brim")
    d.fill(knockout(beard, nose), C_["white"], angle=100, name="beard")
    d.fill(pom, C_["white"], angle=45, name="pom")
    for s in strands:
        d.run(s, C_["silver"], bean=1, name="beard strand", trim_after=True)
    d.fill(nose, C_["blush"], angle=45, name="nose")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
