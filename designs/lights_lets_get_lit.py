"""Let's Get Lit: a modern straight-bar menorah with all nine flames lit over stacked
"LET'S GET / LIT" block lettering.

Spec:
  object:       Hanukkah pun design for sweatshirts, tees, totes and tea towels
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      navy ("LET'S GET", LIT drop shadow), blue (candles), orange (flames),
                yellow (flame cores), gold (menorah, LIT): 5 colours
  must have:    a modern gold menorah 80 mm wide: a straight 3.4 mm crossbar with round
                ends, nine 6 x 2.4 mm cups, a 4.4 mm stem and a stepped foot; the centre
                shamash on a 6.6 mm riser above the other eight; nine 3.6 x 13 mm blue
                candles, every one lit with an orange teardrop flame and a yellow core;
                "LET'S GET" in navy block lettering (`lettering.block_text`), 7.5 mm cap,
                over a big gold "LIT" (17 mm cap) with a navy offset shadow
  lettering:    our own block alphabet, no font licence; rows 0.35 mm
  density:      cores knock out the flames; the shadow is knocked out under LIT;
                nothing else overlaps; max 3.5
"""
from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Let's Get Lit: modern gold menorah with nine lit candles over stacked block lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Let's Get Lit Menorah Hanukkah Embroidery Design",
    "A modern gold menorah with all nine candles lit over \"LET'S GET LIT\" in bold block letters",
    ["lets get lit", "let's get lit", "menorah", "hanukkah menorah", "funny hanukkah",
     "hanukkah pun", "festival of lights", "hanukkah sweatshirt", "candles"],
    "A clean, modern gold menorah with a straight crossbar and all nine blue candles lit, the "
    "shamash raised in the middle, over \"LET'S GET\" in navy block letters and a big gold "
    "\"LIT\" with a navy drop shadow.\n\n"
    "Made for Hanukkah sweatshirts and tees, and just as fun on totes, tea towels and pillows.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 14000)


def _flame(x, y):
    """Teardrop flame standing on (x, y), with its core."""
    f = smooth([(0, 0), (2.7, 2.3), (2.4, 5.8), (0.6, 9.0), (0, 11), (-1.4, 7.6), (-2.6, 4.6),
                (-2.6, 2.0)], 8).buffer(0)
    core = smooth([(0, 1.3), (1.25, 2.6), (1.0, 4.6), (0.1, 6.6), (-1.0, 4.6), (-1.25, 2.6)], 6).buffer(0)
    return move(f, x, y), move(core, x, y)


def _centred(t, cx, y_base):
    x0, y0, x1, y1 = t.bounds
    return move(t, cx - (x0 + x1) / 2, y_base - y0)


def _solid(t):
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(t)])


BAR_Y = 0.0                  # crossbar bottom
BAR_H = 3.4
SPOTS = [-36.0, -27.0, -18.0, -9.0, 0.0, 9.0, 18.0, 27.0, 36.0]
RISER = 6.6


def menorah():
    bar = rounded_rect(80, BAR_H, BAR_H / 2, 0, BAR_Y + BAR_H / 2)
    riser = rect(7.0, RISER + 0.6, 0, BAR_Y + BAR_H + RISER / 2 - 0.3)
    stem = rect(4.4, 17.0, 0, BAR_Y - 8.2)
    collar = rounded_rect(10.0, 2.4, 0.8, 0, BAR_Y - 15.6)
    base = poly([(-15, -22.4), (15, -22.4), (7, -16.6), (-7, -16.6)])
    foot = rounded_rect(34, 2.6, 1.2, 0, -23.3)
    cups, bases = [], []
    for x in SPOTS:
        y = BAR_Y + BAR_H + (RISER if x == 0 else 0)
        cups.append(rounded_rect(6.2, 2.4, 0.8, x, y + 1.0))
        bases.append((x, y + 2.0))
    shape = union(bar, riser, stem, collar, base, foot, *cups).buffer(0.3).buffer(-0.3)
    return shape, bases


def art():
    d = Design()
    meno, bases = menorah()
    candles = [rect(3.6, 13, x, y + 6.5) for x, y in bases]
    flames = [_flame(x, y + 13.9) for x, y in bases]

    top = _centred(block_text("LET'S GET", cap=7.5, stroke=2.5, tracking=1.3), 0, -36.5)
    lit = _centred(block_text("LIT", cap=17, stroke=2.4, tracking=1.6), -1.0, -58.0)
    shadow = knockout(move(lit, 1.6, -1.6), _solid(lit))

    # navy: lettering and the LIT shadow
    d.fill(top, C_["navy"], angle=0, spacing=0.35, name="LET'S GET")
    d.fill(shadow, C_["navy"], angle=45, name="LIT shadow")
    # blue candles, flames, cores
    for c in candles:
        d.fill(c, C_["blue"], angle=90, name="candle")
    for f, core in flames:
        d.fill(knockout(f, core), C_["orange"], angle=80, name="flame")
    for f, core in flames:
        d.fill(core, C_["yellow"], angle=100, underlay=False, name="flame core")
    # gold menorah and LIT
    d.fill(meno, C_["gold"], angle=0, name="menorah")
    d.fill(lit, C_["gold"], angle=0, spacing=0.35, name="LIT")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
