"""Hanukkah Menorah: a gold nine-branch menorah with blue candles and "Happy Hanukkah".

Spec:
  object:       Hanukkah menorah for sweatshirts, napkins, tea towels, pillows
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      sky (candles), orange (flames), gold (menorah, flame cores), navy
                (lettering): 4 colours
  must have:    a gold menorah 76 mm wide: a 30 mm foot, a 4 mm stem, four curved 2.6 mm
                branches each side and a raised centre shamash; nine 3.4 x 13 mm sky-blue
                candles on 5 mm cups, the shamash candle higher; teardrop flames with gold
                cores; "HAPPY HANUKKAH" in the house block lettering
                (`lettering.block_text`), 6.5 mm cap height, 0.35 mm rows
  density:      cores knock out the flames; nothing else overlaps; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Gold Hanukkah menorah with blue candles and Happy Hanukkah lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Hanukkah Menorah Embroidery Design",
    "A gold menorah with nine glowing blue candles and \"Happy Hanukkah\"",
    ["hanukkah", "chanukah", "menorah", "happy hanukkah", "festival of lights", "jewish holiday"],
    "A gold nine-branch menorah with all its blue candles lit and the shamash raised in the "
    "middle, over \"Happy Hanukkah\" in navy block letters.\n\nGreat on sweatshirts, napkins, tea "
    "towels and pillows.",
    mockups=("tshirt", "tote"),
    base=["hanukkah embroidery design", "holiday embroidery", "machine embroidery", "holiday"],
)



def checks(p):
    return standard_checks(p, 4, 12000)


def _flame(x, y):
    f = smooth([(0, 0), (2.6, 2.4), (2.2, 6.0), (0, 10), (-2.2, 6.0), (-2.6, 2.4)], 8).buffer(0)
    core = smooth([(0, 1.2), (1.2, 2.6), (0.9, 4.6), (0, 6.4), (-0.9, 4.6), (-1.2, 2.6)], 6).buffer(0)
    return move(f, x, y), move(core, x, y)


def art():
    d = Design()
    parts = [poly([(-15, -24), (15, -24), (8, -19), (-8, -19)]), rect(4, 42, 0, -2)]
    tops = []
    for k in range(1, 5):
        r = 9.0 * k
        t = np.linspace(np.pi, 2 * np.pi, 40)
        pts = np.c_[r * np.cos(t), 3 + 0.5 * r * np.sin(t)]
        parts.append(LineString(pts).buffer(1.3, cap_style="flat"))
        tops += [(-r, 3.0), (r, 3.0)]
    cups = [rounded_rect(5.5, 2.6, 0.8, x, y + 1.0) for x, y in tops] + [rounded_rect(5.5, 2.6, 0.8, 0, 19.8)]
    menorah = union(*parts, *cups).buffer(0.3).buffer(-0.3)
    spots = tops + [(0, 18.8)]
    candles = [rect(3.4, 13, x, y + 9.0) for x, y in spots]
    flames = [_flame(x, y + 16.3) for x, y in spots]
    word = move(centered(block_text("HAPPY HANUKKAH", cap=6.5, stroke=2.4)), 0, -32)
    for c in candles:
        d.fill(c, C_["sky"], angle=90, name="candle")
    for f, core in flames:
        d.fill(knockout(f, core), C_["orange"], angle=90, name="flame")
    for f, core in flames:
        d.fill(core, C_["gold"], angle=90, underlay=False, name="flame core")
    d.fill(menorah, C_["gold"], angle=None, name="menorah")
    d.fill(word, C_["navy"], angle=0, spacing=0.35, name="Happy Hanukkah")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
