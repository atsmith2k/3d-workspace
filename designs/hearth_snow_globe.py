"""Snow Globe: a night-sky snow globe with a pine tree, snowfall and a wooden base.

Spec:
  object:       snow globe for sweatshirts, pillows, stockings and ornaments
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      navy (night sky), white (snow drift, snowflakes), green (tree), gold
                (star, base band), ginger (base), ice (1.6 mm glass rim): 6 colours
  must have:    a 64 mm glass globe filled with navy sky; a white snow drift across the
                bottom; a 30 mm pine tree with a gold star; fourteen 2 mm snow dots; a
                ginger wooden base 54 mm wide with a gold band; a continuous ice satin rim
  density:      tree, drift and dots knock out the sky; the sky tucks under the rim
"""
from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Night-sky snow globe with a pine tree, snowfall and a wooden base"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Snow Globe Embroidery Design",
    "A snow globe with a starry-night pine tree, falling snow and a wooden base",
    ["snow globe", "christmas snow globe", "winter scene", "christmas tree", "kids christmas"],
    "A classic snow globe: a little pine tree with a gold star stands in a snow drift under a "
    "deep blue night sky full of falling snow, set on a wooden base with a gold band.\n\nGreat "
    "on sweatshirts, pillows, stockings and ornaments.",
    mockups=("tshirt", "tote"),
)

R = 32.0
CY = 8.0
RIM = 1.6
DOTS = [(-18, 26), (-6, 31), (8, 30), (19, 22), (-24, 12), (24, 9), (-14, 18), (15, 15),
        (-22, 0), (21, -2), (-10, 34.5), (0, 23.5), (-16, 5), (14, 4)]


def checks(p):
    return standard_checks(p, 6, 13000)


def art():
    d = Design()
    globe = circle(0, CY, R)
    drift = smooth([(-34, -10), (-20, -6), (-6, -8.5), (8, -5.5), (22, -8), (34, -6), (34, -30), (-34, -30)], 8)
    drift = drift.buffer(0).intersection(globe)
    tiers = [poly([(0, 31 - 9 * k), (-(6 + 3.5 * k), 21 - 9 * k), (6 + 3.5 * k, 21 - 9 * k)]) for k in range(3)]
    tree = union(*tiers, rect(4, 6, 0, 1)).buffer(0.6).buffer(-0.6)
    star_ = star(5, 4.2, 1.8, 0, 32.5)
    dots = [circle(x, y, 1.1) for x, y in DOTS]
    base = poly([(-24, -21), (24, -21), (28, -35), (-28, -35)])
    band = knockout(rect(52, 4.2, 0, -26.5).intersection(base), grow(globe, RIM / 2))
    over = union(drift, tree, star_, *dots)
    d.fill(knockout(tuck(globe, RIM), over), C_["navy"], angle=30, name="night sky")
    d.fill(knockout(base, band, grow(globe, RIM / 2)), C_["ginger"], angle=0, name="base")
    d.fill(knockout(tuck(drift, RIM), tree), C_["white"], angle=0, name="snow drift")
    for g in dots:
        d.fill(g, C_["white"], angle=45, underlay=False, name="snow")
    d.fill(tree, C_["green"], angle=80, name="tree")
    d.fill(star_, C_["gold"], angle=90, name="star")
    d.fill(band, C_["gold"], angle=90, name="base band")
    d.outline(globe, C_["ice"], width=RIM, name="glass rim")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
