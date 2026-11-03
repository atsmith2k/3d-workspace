"""Hot Cocoa: a red mug of cocoa piled with whipped cream, a candy cane and steam.

Spec:
  object:       cosy hot-chocolate mug for sweatshirts, tea towels, mug rugs, aprons
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens (towels, mug rugs) with tear-away
  threads:      red (mug, cane stripes), white (cream, heart, cane), cocoa (chocolate
                drizzle), silver (cream outline, steam): 4 colours
  must have:    a 46 x 40 mm mug with a 9 mm loop handle and a white heart on its face;
                a heaped whipped-cream swirl with a 1.2 mm silver
                satin edge and a chocolate drizzle; a 3 mm red-and-white candy-cane
                stick leaning out of the cream; three steam curls above
  density:      cream knocks out the mug top; drizzle bean run lies on the cream; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Red mug of hot cocoa with whipped cream, a candy cane and steam"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Hot Cocoa Mug Embroidery Design",
    "A red mug of hot chocolate piled with whipped cream and a candy cane",
    ["hot cocoa", "hot chocolate", "cocoa mug", "winter mug", "mug rug", "cozy winter"],
    "A cosy red mug of hot chocolate with a heart on the front, piled high with whipped cream, "
    "a chocolate drizzle and a peppermint candy cane, steaming away.\n\nGreat on sweatshirts, "
    "tea towels, mug rugs and aprons.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.2


def checks(p):
    return standard_checks(p, 4, 12000)


def art():
    d = Design()
    mug = rounded_rect(46, 40, 6, -4, -18)
    handle = ring(19, -16, 12, 6.5).difference(rect(30, 40, 4, -16))
    cream = union(circle(-17, 5, 6.5), circle(-6.5, 7, 7.5), circle(5.5, 5.5, 6.5),
                  circle(-11, 13.5, 6.2), circle(0, 14, 5.8), circle(-5.5, 20.5, 4.4),
                  ellipse(-4, 2.5, 21, 3.5)).buffer(0.5).buffer(-0.5)
    heart_ = rotate(heart(13, -4, -18), 0)
    # candy-cane stick leaning out of the cream to the right
    stick_path = np.array([(8, 8), (17, 27)])
    stick = LineString(stick_path).buffer(1.6, cap_style="round").union(
        LineString(arc(20.5, 26.5, 3.6, 170, 0)).buffer(1.6, cap_style="round"))
    stick = stick.difference(cream.buffer(0.2))
    stripes = union(*[rotate(rect(2.2, 8, 8 + 3.6 * k, 9 + 7.6 * k), 35, origin=(8 + 3.6 * k, 9 + 7.6 * k))
                      for k in range(3)]).intersection(stick)
    drizzle = np.array([(-20, 6), (-14, 9.5), (-10, 5.5), (-4, 11.5), (0, 7.5), (5, 10), (8, 6.5)])
    steam = [spline([(x, 29), (x + 2.5, 33), (x - 1.5, 37), (x + 1.5, 41)], samples=8) for x in (-16, -6, 4)]
    edge = grow(cream, BORDER / 2)
    d.fill(knockout(union(mug, handle), edge, heart_, min_width=1.5), C_["red"], angle=0, name="mug")
    d.fill(stripes, C_["red"], angle=None, underlay=False, name="cane stripes")
    d.fill(knockout(stick, stripes), C_["white"], angle=None, name="candy cane")
    d.fill(tuck(cream, BORDER), C_["white"], angle=20, name="whipped cream")
    d.fill(heart_, C_["white"], angle=45, name="heart")
    d.run(drizzle, C_["cocoa"], bean=1, name="drizzle", trim_after=True)
    d.outline(cream, C_["silver"], width=BORDER, name="cream edge")
    for s in steam:
        d.run(s, C_["silver"], bean=1, name="steam", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
