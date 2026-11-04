"""Festival of Lights: nine blue candles on a gold arch over "FESTIVAL OF LIGHTS".

Spec:
  object:       Hanukkah lettering for sweatshirts, pillows, table runners, totes
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      blue (candles), orange (flames), yellow (flame cores), gold (arch,
                rules), navy (lettering): 5 colours
  must have:    nine 4.2 mm blue candles standing on a 2 mm gold satin arch 80 mm wide
                that rises 10 mm in the middle, 16 mm tall, the centre shamash 22 mm;
                teardrop flames 5.4 x 9 mm with yellow cores; "FESTIVAL" at 13 mm and
                "OF LIGHTS" at 7.5 mm cap height in the house block lettering
                (`lettering.block_text`), 0.35 mm rows; a gold diamond-tipped rule each
                side of "OF LIGHTS"
  density:      cores knock out the flames, candles stop on the arch (tucked 0.5 mm
                under it); max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Nine blue Hanukkah candles on a gold arch over FESTIVAL OF LIGHTS lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Festival of Lights Hanukkah Embroidery Design",
    "Nine glowing blue candles arched over \"Festival of Lights\" in navy and gold",
    ["festival of lights", "hanukkah lettering", "hanukkah candles", "nine candles",
     "blue and gold", "hanukkah sweatshirt", "hanukkah pillow"],
    "Nine slim blue candles, the centre one standing tallest, rise from a gold arch with "
    "their flames lit, over \"FESTIVAL OF LIGHTS\" in navy block letters with gold rules. "
    "Blue and gold, simple and elegant.\n\nLovely on sweatshirts, pillows, table runners "
    "and totes.",
    mockups=("tshirt", "tote"),
)

HALF = 40.0      # arch half-width
RISE = 10.0
Y0 = 2.0         # arch ends


def checks(p):
    return standard_checks(p, 5, 13000)


def _arch_y(x):
    return Y0 + RISE * (1 - (x / HALF) ** 2)


def _flame(x, y, w=5.4, h=9.0):
    f = smooth([(x, y), (x + w / 2, y + h * 0.28), (x + w * 0.36, y + h * 0.62), (x, y + h),
                (x - w * 0.36, y + h * 0.62), (x - w / 2, y + h * 0.28)], 8).buffer(0)
    c = smooth([(x, y + h * 0.12), (x + w * 0.24, y + h * 0.3), (x + w * 0.17, y + h * 0.52),
                (x, y + h * 0.7), (x - w * 0.17, y + h * 0.52), (x - w * 0.24, y + h * 0.3)], 6).buffer(0)
    return f, c


def art():
    d = Design()
    xs = np.linspace(-HALF + 4, HALF - 4, 9)
    candles, flames = [], []
    for i, x in enumerate(xs):
        h = 22.0 if i == 4 else 16.0
        yb = _arch_y(x) + 0.5
        candles.append(rect(4.2, h, x, yb + h / 2))
        flames.append(_flame(x, yb + h + 1.2))
    t = np.linspace(-HALF, HALF, 41)
    arch = np.c_[t, _arch_y(t)]
    word1 = move(centered(block_text("FESTIVAL", cap=13, stroke=2.5)), 0, -10)
    word2 = move(centered(block_text("OF LIGHTS", cap=7.5, stroke=1.9, tracking=1.6)), 0, -26)
    x2 = (word2.bounds[2] - word2.bounds[0]) / 2
    rules = []
    for s in (-1, 1):
        a, b = s * (x2 + 3.5), s * (HALF - 2)
        rules.append(union(rect(abs(b - a), 1.3, (a + b) / 2, -26),
                           rotate(rect(3.2, 3.2, b, -26), 45, origin=(b, -26))))
    for c in candles:
        d.fill(c, C_["blue"], angle=90, name="candle")
    for f, c in flames:
        d.fill(knockout(f, c), C_["orange"], angle=90, name="flame")
    for f, c in flames:
        d.fill(c, C_["yellow"], angle=90, underlay=False, name="flame core")
    d.satin(arch, 2.0, C_["gold"], name="arch")
    for r in rules:
        d.fill(r, C_["gold"], angle=0, underlay=False, name="rule")
    d.fill(word1, C_["navy"], angle=0, spacing=0.35, name="FESTIVAL")
    d.fill(word2, C_["navy"], angle=0, spacing=0.35, name="OF LIGHTS")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
