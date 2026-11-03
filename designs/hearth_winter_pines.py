"""Winter Pines: three modern pine trees under a crescent moon and twinkling stars.

Spec:
  object:       minimal winter pines for sweatshirts, totes, mugs rugs and all-winter decor
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      cocoa (trunks), leaf, green and pine (one tree each), gold (moon, stars),
                silver (snowy ground line): 6 colours
  must have:    three four-tier pines 46, 62 and 50 mm tall in three greens, each on a
                cocoa trunk; a 14 mm gold crescent moon; three four-point gold stars
                (4-6 mm); a silver bean-stitch ground line across the trunks
  density:      trees do not overlap; the ground run lies on the trunks; max 3.5
"""
from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Three modern pine trees under a crescent moon and twinkling stars"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Winter Pines and Moon Embroidery Design",
    "Three modern pine trees under a gold crescent moon and twinkling stars",
    ["pine trees", "winter forest", "minimalist winter", "evergreen", "woodland winter",
     "winter night"],
    "Three modern pine trees in three shades of green under a gold crescent moon and "
    "twinkling stars. A quiet winter design that sews all season, not just at Christmas.\n\n"
    "Great on sweatshirts, totes, mug rugs and pillows.",
    mockups=("tshirt", "tote"),
    base=["winter embroidery design", "machine embroidery", "winter", "holiday"],
)

GROUND = -30.0


def checks(p):
    return standard_checks(p, 6, 11000)


def _pine(x, h, w):
    """Four stepped tiers, tip at GROUND + h, on a short trunk."""
    base = GROUND + 4
    tiers = []
    for k in range(4):
        top = base + h - k * (h - 4) * 0.23
        bot = top - (h - 4) * 0.36
        half = w * (0.42 + 0.19 * k)
        tiers.append(poly([(x, top), (x - half, bot), (x + half, bot)]))
    tree = union(*tiers).buffer(0.5).buffer(-0.5)
    trunk = rect(4, 6, x, GROUND + 2.5)
    return tree, trunk


def art():
    d = Design()
    trees = [(_pine(-36, 46, 14), "leaf"), (_pine(0, 62, 20), "green"), (_pine(36, 50, 14), "pine")]
    moon = circle(-34, 34, 7).difference(circle(-30.5, 36, 6.2))
    stars = [star(4, 3.0, 0.9, 20, 36, rot=90), star(4, 2.2, 0.7, 34, 30, rot=90),
             star(4, 2.4, 0.7, -12, 40, rot=90)]
    d.fill(union(*[knockout(t[1], t[0]) for (t, _) in trees]), C_["cocoa"], angle=90, name="trunks")
    for (tree, trunk), c in trees:
        d.fill(tree, C_[c], angle=70 if c != "green" else 110, name=f"{c} pine")
    d.fill(moon, C_["gold"], angle=60, name="moon")
    for s in stars:
        d.fill(s, C_["gold"], angle=45, underlay=False, name="star")
    d.run(spline([(-50, GROUND - 0.5), (-24, GROUND + 0.8), (0, GROUND - 0.3), (24, GROUND + 0.9),
                  (50, GROUND)], samples=10), C_["silver"], bean=1, name="ground", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
