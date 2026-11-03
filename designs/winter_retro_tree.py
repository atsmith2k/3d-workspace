"""Retro Christmas Tree: a mid-century tree with gold swag garlands and coloured baubles.

Spec:
  object:       retro / mid-century modern Christmas tree for sweatshirts, totes, pillows
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      cocoa (trunk), green (tree), gold (three swag garlands and the starburst
                topper), pink, red and ice (baubles): 6 colours
  must have:    a tall 64 x 76 mm triangle tree with softly rounded corners; three gold
                1.8 mm satin swags sagging across it, ending 2 mm inside its edges; six
                4 mm baubles in pink, red and ice hung from the swags; an eight-ray gold
                starburst on top; a 10 mm trunk
  density:      baubles and starburst knock out the tree; the swags lie on it (2.7
                layers); max 3.5 layers
"""
from cadkit.stitch import *

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Mid-century retro Christmas tree with gold swags and coloured baubles"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Retro Christmas Tree Embroidery Design",
    "A mid-century retro tree with gold swags, coloured baubles and a starburst",
    ["retro christmas", "mid century christmas", "vintage christmas tree", "atomic starburst",
     "christmas sweatshirt"],
    "A mid-century modern Christmas tree: a tall green triangle draped with gold swag garlands, "
    "hung with pink, red and ice-blue baubles and topped with an atomic starburst.\n\nGreat on "
    "sweatshirts, totes and pillows.",
    mockups=("tshirt", "tote"),
)

TOP, BOT, HALF = 40.0, -36.0, 32.0


def checks(p):
    return standard_checks(p, 6, 11000)


def _half_width(y):
    return HALF * (TOP - y) / (TOP - BOT)


def art():
    d = Design()
    tree = poly([(0, TOP), (HALF, BOT), (-HALF, BOT)]).buffer(-2.5).buffer(2.5)
    trunk = rect(10, 9, 0, BOT - 3.5)
    burst = union(*[rotate(rect(1.8 if i % 2 else 2.4, 15 if i % 2 else 20, 0, TOP + 4), 22.5 * i,
                           origin=(0, TOP + 4)) for i in range(8)], circle(0, TOP + 4, 3.0))
    swags, baubles = [], []
    colors = ["pink", "red", "ice"]
    for k, y in enumerate((12.0, -4.0, -20.0)):
        hw = _half_width(y + 4) - 2.0                           # ends 2 mm inside the edge
        y_end = y + 4
        sag = 3.0 + k
        path = bezier((-hw, y_end), (-hw / 3, y - sag), (hw / 3, y - sag), (hw, y_end), 32)
        swags.append(path)
        n = 1 + k
        for j in range(n):
            t = (j + 1) / (n + 1)
            i = int(round(t * (len(path) - 1)))
            x0, y0 = path[i]
            baubles.append((circle(x0, y0 - 4.6, 4.0), colors[(j + k) % 3]))
    over = union(burst, *[b for b, _ in baubles])
    d.fill(knockout(trunk, tree), C_["cocoa"], angle=90, name="trunk")
    d.fill(knockout(tree, over), C_["green"], angle=70, name="tree")
    for s in swags:
        d.satin(s, 1.8, C_["gold"], name="swag", trim_after=True)
    d.fill(burst, C_["gold"], angle=0, name="starburst")
    for c in colors:
        for b, bc in baubles:
            if bc == c:
                d.fill(b, C_[c], angle=45, name=f"{c} bauble")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
