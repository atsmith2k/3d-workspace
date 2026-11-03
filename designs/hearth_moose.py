"""Merry Moose: a woodland moose face with Christmas lights strung on its antlers.

Spec:
  object:       woodland moose for sweatshirts, kids' wear, pillows, cabin decor
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; fleece with a water-soluble topper
  threads:      cocoa (antlers, nostrils), ginger (head, ears), tan (muzzle), black
                (eyes), red, gold and sky (bulbs): 7 colours
  must have:    a 24 mm wide head with two side ears and a 23 mm tan muzzle with
                nostrils; two eyes; broad palmate antlers 84 mm tip to tip with five
                points each; eight 3.6 mm lights in red, gold and sky on the antlers
  density:      the head knocks out the antler bases, bulbs knock out the antlers
"""
from shapely.affinity import scale as _scl

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Woodland moose face with Christmas lights strung on its antlers"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Merry Moose Embroidery Design",
    "A woodland moose with Christmas lights strung on its antlers",
    ["moose", "christmas moose", "woodland christmas", "cabin christmas", "kids christmas",
     "winter animal"],
    "A friendly woodland moose with big palmate antlers wrapped in red, gold and blue "
    "Christmas lights.\n\nGreat on sweatshirts, kids' wear, pillows and cabin decor.",
    mockups=("tshirt", "tote"),
)

LIGHTS = [((-20, 18.5), "red"), ((-30, 21), "gold"), ((-37, 25.5), "sky"), ((-26, 27), "red"),
          ((20, 18.5), "gold"), ((30, 21), "sky"), ((37, 25.5), "red"), ((26, 27), "gold")]


def checks(p):
    return standard_checks(p, 7, 12000)


def _antler():
    """The left antler, base at the head's top."""
    return smooth([(-7, 13), (-15, 14.5), (-25, 14), (-34, 17), (-41, 23), (-43, 30), (-39, 28.5),
                   (-37, 33.5), (-33.5, 29), (-30.5, 35), (-27, 29.5), (-23, 35), (-20.5, 28),
                   (-16, 22), (-8, 19.5)], 3).buffer(0)


def art():
    d = Design()
    head = smooth([(-9, 15), (-11, 4), (-10, -8), (-12.5, -20), (-10, -28), (0, -31), (10, -28), (12.5, -20),
                   (10, -8), (11, 4), (9, 15), (0, 17)], 8).buffer(0)
    ears = [rotate(ellipse(-16, 8, 7.5, 3.4), 22, origin=(-16, 8)),
            rotate(ellipse(16, 8, 7.5, 3.4), -22, origin=(16, 8))]
    muzzle = ellipse(0, -22.5, 11.5, 8.5)
    nostrils = [ellipse(-4.2, -23.5, 1.7, 2.4), ellipse(4.2, -23.5, 1.7, 2.4)]
    eyes = [circle(-6.5, 3, 2.0), circle(6.5, 3, 2.0)]
    left = _antler()
    antlers = union(left, _scl(left, -1, 1, origin=(0, 0)))
    bulbs = [(circle(x, y, 1.8), c) for (x, y), c in LIGHTS]
    face = union(head, *ears)
    d.fill(knockout(antlers, face, *[b for b, _ in bulbs]), C_["cocoa"], angle=None, name="antlers")
    for g in nostrils:
        d.fill(g, C_["cocoa"], angle=90, underlay=False, name="nostril")
    d.fill(knockout(face, muzzle, *eyes), C_["ginger"], angle=90, name="head")
    d.fill(knockout(muzzle, *nostrils), C_["tan"], angle=0, name="muzzle")
    for g in eyes:
        d.fill(g, C_["black"], angle=45, underlay=False, name="eye")
    for c in ("red", "gold", "sky"):
        for b, bc in bulbs:
            if bc == c:
                d.fill(b, C_[c], angle=45, underlay=False, name="light")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
