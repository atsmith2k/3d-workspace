"""Blue Hanukkah Candles: four tall twisted blue-and-white candles, lit, with wax drips.

Spec:
  object:       minimal Hanukkah candles for sweatshirts, napkins, tea towels, pillows
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      white (candle wax), blue (spiral stripes), navy (1.2 mm borders, wicks),
                orange (flames), yellow (flame cores, sparkles): 5 colours
  must have:    four 11 mm candles of different heights (50, 78, 60, 68 mm) on one
                baseline, 3.4 mm blue spiral stripes at 9 mm pitch rising at 35 deg;
                a white wax cap with a drip running down the front (and over the side
                on two candles); 1.2 x 2.4 mm wicks; teardrop flames 8 x 15 mm with
                yellow cores; four-point sparkles 5-8 mm across between the flames;
                no lettering
  density:      stripes and wax tuck under the border, cores knock out the flames;
                max 3.5
"""
import numpy as np

from cadkit.stitch import *

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Four tall twisted blue and white Hanukkah candles, lit, with wax drips and sparkles"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Blue Hanukkah Candles Embroidery Design",
    "Four twisted blue-and-white Hanukkah candles, lit, with a drip of wax and a sparkle",
    ["hanukkah candles", "blue candles", "twisted candles", "minimal hanukkah",
     "modern hanukkah", "candle embroidery", "festival of lights"],
    "Four tall twisted Hanukkah candles in blue and white, each a different height, lit "
    "with warm flames, a drip of wax running down and a few sparkles. No lettering: "
    "simple, modern and calm.\n\nLovely on sweatshirts, napkins, tea towels and pillows.",
    mockups=("tshirt", "tote"),
)

W = 11.0          # candle width
B = 1.2           # border
BASE = -45.0
# (x, height, drip x offset, drip length, drips over the side: -1 left, 1 right, 0 no)
CANDLES = [(-27, 50, 2.0, 9, -1), (-9, 78, -1.5, 13, 0), (9, 60, 1.8, 10, 1), (27, 68, -2.0, 8, 0)]
SPARKLES = [(-38, 22, 4.0), (-17, 46, 2.8), (2, 42, 3.4), (19, 33, 2.6), (37, 40, 3.6)]


def checks(p):
    return standard_checks(p, 5, 14000)


def _candle(x, h, dx, dl, side):
    top = BASE + h
    body = rect(W, h, x, BASE + h / 2)
    wax = rect(W + 1, 4.4, x, top - 2.2)
    drip = union(rect(3.4, dl, x + dx, top - dl / 2), circle(x + dx, top - dl, 1.7))
    wax = union(wax, drip)
    if side:
        ex = x + side * (W / 2 - 0.6)
        over = union(rect(2.6, 6.0, ex, top - 3), circle(ex, top - 6, 1.3))
        body = union(body, over)
        wax = union(wax, over)
    wax = wax.intersection(body).buffer(0.3).buffer(-0.3)
    bands = [rotate(rect(40, 3.4, x, BASE + k * 9.0), 35, origin=(x, BASE + k * 9.0))
             for k in range(-4, int(h / 9.0) + 6)]
    stripes = union(*bands).intersection(body).difference(grow(wax, 0.2))
    stripes = union(*[g for g in polygons_of(stripes.buffer(-0.6).buffer(0.6)) if g.area > 12])
    return body, wax, stripes, top


def _flame(x, y, w=8.0, h=15.0):
    f = smooth([(x, y), (x + w / 2, y + h * 0.28), (x + w * 0.34, y + h * 0.62), (x + 0.4, y + h),
                (x - w * 0.36, y + h * 0.6), (x - w / 2, y + h * 0.28)], 8).buffer(0)
    c = smooth([(x, y + h * 0.1), (x + w * 0.24, y + h * 0.3), (x + w * 0.16, y + h * 0.52),
                (x, y + h * 0.68), (x - w * 0.16, y + h * 0.52), (x - w * 0.24, y + h * 0.3)], 6).buffer(0)
    return f, c


def art():
    d = Design()
    d.hide_jumps_mm = 40     # stripe to stripe under the border sewn later
    parts = [(_candle(*c), c[0]) for c in CANDLES]
    wicks, flames = [], []
    for (body, wax, stripes, top), x in parts:
        wicks.append(rect(1.4, 3.0, x, top + 1.0))
        flames.append(_flame(x, top + 2.2))
    for (body, wax, stripes, top), x in parts:
        d.fill(knockout(tuck(body, B), stripes), C_["white"], angle=35, name="wax")
    for (body, wax, stripes, top), x in parts:
        d.fill(stripes.intersection(tuck(body, B)).buffer(-0.4).buffer(0.4), C_["blue"],
               angle=35, name="stripes")
    for ((body, wax, stripes, top), x), wk in zip(parts, wicks):
        d.outline(body, C_["navy"], width=B, name="border")
        d.fill(wk, C_["navy"], angle=90, underlay=False, name="wick")
    for f, c in flames:
        d.fill(knockout(f, c), C_["orange"], angle=80, name="flame")
    for f, c in flames:
        d.fill(c, C_["yellow"], angle=100, underlay=False, name="core")
    for x, y, r in SPARKLES:
        d.fill(star(4, r, r * 0.34, x, y), C_["yellow"], angle=45, underlay=False, name="sparkle")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
