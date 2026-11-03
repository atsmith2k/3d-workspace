"""Snowman: a cheerful two-ball snowman in a top hat and a red scarf, with twig arms.

Spec:
  object:       classic snowman for kids' wear, sweatshirts, towels, stockings
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; towels with tear-away and a water-soluble topper
  threads:      white (body), sky (1.4 mm satin outline so it reads on white fabric),
                cocoa (twig arms), red (scarf and hat band), carrot (nose), black (hat,
                coal eyes, smile and buttons): 6 colours
  must have:    a 52 mm body ball and a 34 mm head; a black top hat with a red band; a
                red scarf with a hanging tail and fringe notches; a carrot nose pointing
                right; two coal eyes, a five-dot smile, three coal buttons; twig arms
                with a side twig each (bean stitch, starting just outside the outline)
  density:      every detail knocks out the white; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Two-ball snowman in a top hat and red scarf, with twig arms"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Snowman Embroidery Design",
    "A cheerful snowman in a top hat and a red scarf, with twig arms",
    ["snowman", "frosty", "kids christmas", "winter kids", "christmas towel"],
    "A cheerful two-ball snowman with a black top hat, a red scarf, a carrot nose, coal eyes, "
    "smile and buttons, and twig arms. A pale blue outline keeps him crisp on white fabric.\n\n"
    "Great on kids' wear, sweatshirts, tea towels and stockings.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.4


def checks(p):
    return standard_checks(p, 6, 12000)


def art():
    d = Design()
    body = circle(0, -20, 26)
    head = circle(0, 15, 17)
    snow = union(body, head)
    hat = union(rounded_rect(36, 3.6, 1.4, 0, 31), rounded_rect(22, 20, 1.8, 0, 41))
    band = rect(22.4, 4, 0, 34.8)
    scarf = union(smooth([(-16, 3.5), (0, 1.5), (16, 3.5), (15, -3.5), (0, -5.5), (-15, -3.5)], 8).buffer(0),
                  poly([(6, -2), (14, -2), (16, -20), (13, -18.5), (10.5, -20.5), (7.5, -18.8), (5, -20.5)]))
    nose = poly([(1, 13.5), (1, 9.5), (15, 10.5)])
    eyes = [circle(-6, 19, 1.9), circle(6, 19, 1.9)]
    smile = [circle(10 * np.sin(t), 12 - 6 * np.cos(t) + 1.5, 1.2) for t in np.linspace(-0.85, 0.85, 5)]
    buttons = [circle(0, y, 2.0) for y in (-12, -20, -28)]
    over = union(hat, scarf, nose, *eyes, *smile, *buttons)
    d.fill(knockout(tuck(snow, BORDER), over), C_["white"], angle=60, name="snow")
    d.outline(knockout(snow, hat.buffer(BORDER / 2), scarf.buffer(BORDER / 2)), C_["sky"], width=BORDER, name="outline")
    for sign in (-1, 1):
        root = (sign * 27.5, -12)
        tip = (sign * 46, 4)
        d.run(np.array([root, tip]), C_["cocoa"], bean=1, name="arm", trim_after=False)
        mid = (sign * 38.5, -2.5)
        d.run(np.array([mid, (sign * 45, -7)]), C_["cocoa"], bean=1, name="twig", trim_after=True)
    d.fill(band, C_["red"], angle=90, name="hat band")
    d.fill(scarf, C_["red"], angle=10, name="scarf")
    d.fill(nose, C_["carrot"], angle=0, name="nose")
    d.fill(knockout(hat, band), C_["black"], angle=90, name="hat")
    for g in eyes + smile + buttons:
        d.fill(g, C_["black"], angle=45, underlay=False, name="coal")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
