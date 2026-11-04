"""Mini Hanukkah Icons: a 2x2 sampler of menorah, dreidel, Star of David and sufganiyah.

Spec:
  object:       a set of four small Hanukkah icons for napkins, kids' tees, sleeves,
                pockets, gift tags; sew the set or pick one
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7); each icon ~40 mm
                in the 100 mm nominal space, centred in its quarter
  fabric:       knits with cut-away; wovens with tear-away
  threads:      blue (candles, dreidel front, up triangle), navy (dreidel side, down
                triangle), gold (menorah, dreidel handle and tip band, doughnut),
                white (dreidel top, powdered sugar), red (jam), orange (flames): 6 colours
  must have:    top left a gold menorah 40 mm wide with 2 mm branches and nine 2.4 x 7 mm
                blue candles (the shamash raised 4 mm) with orange teardrop flames;
                top right a 3/4-view dreidel 26 x 40 mm, blue front, navy side, gold
                handle; bottom left a 40 mm Star of David of two 5.2 mm bands, the blue
                one up, the navy one laid over it; bottom right a 38 x 26 mm jelly doughnut,
                gold dough, white sugar top with drips, a red jam dollop
  density:      every layer knocks out the one under it; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Four mini Hanukkah icons: menorah, dreidel, Star of David and jelly doughnut"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Mini Hanukkah Icons Embroidery Design Set",
    "Four little Hanukkah icons: menorah, dreidel, Star of David and a jelly doughnut",
    ["mini hanukkah", "hanukkah mini designs", "menorah", "dreidel", "star of david",
     "sufganiyah", "jelly doughnut", "small embroidery", "festival of lights"],
    "Four bold little Hanukkah icons in one hoop: a gold menorah with blue candles, a blue "
    "dreidel, a woven Star of David and a sugar-dusted jelly doughnut. Sew the whole sampler "
    "or hoop just the icon you want.\n\nSized for napkins, kids' tees, sleeves, pockets, "
    "gift bags and tags.",
    mockups=("tshirt", "tote"),
)

Q = 25.0      # quarter centre offset


def checks(p):
    return standard_checks(p, 6, 14000)


def _flame(x, y, w=2.8, h=4.8):
    return smooth([(x, y), (x + w / 2, y + h * 0.3), (x + w * 0.38, y + h * 0.65), (x, y + h),
                   (x - w * 0.38, y + h * 0.65), (x - w / 2, y + h * 0.3)], 8).buffer(0)


def _menorah(cx, cy):
    parts = [poly([(-8, -20), (8, -20), (3.5, -16.6), (-3.5, -16.6)]), rect(2.6, 21.5, 0, -6.6)]
    tops = []
    for k in range(1, 5):
        r = 4.5 * k
        t = np.linspace(np.pi, 2 * np.pi, 40)
        parts.append(LineString(np.c_[r * np.cos(t), 0.55 * r * np.sin(t)]).buffer(1.0, cap_style="flat"))
        tops += [(-r, 0.0), (r, 0.0)]
    cups = [rect(3.6, 1.6, x, y + 0.6) for x, y in tops] + [rect(3.6, 1.6, 0, 4.6)]
    body = union(*parts, *cups).buffer(0.3).buffer(-0.3)
    spots = tops + [(0, 4.0)]
    candles = [rect(2.4, 7.0, x, y + 1.4 + 3.5) for x, y in spots]
    flames = [_flame(x, y + 9.4) for x, y in spots]
    m = lambda g: move(g, cx, cy)
    return m(body), [m(c) for c in candles], [m(f) for f in flames]


def _dreidel(cx, cy):
    front = poly([(-11, -4), (5, -4), (5, 12), (-11, 12)])
    side = poly([(5, -4), (11, 0), (11, 16), (5, 12)])
    top = poly([(-11, 12), (5, 12), (11, 16), (-5, 16)])
    tipf = poly([(-11, -4), (5, -4), (-1, -20)])
    tips = poly([(5, -4), (11, 0), (-1, -20)])
    handle = rounded_rect(4.0, 9.0, 1.2, 0, 19.5)
    band = poly([(-11, -4), (5, -4), (11, 0), (11, 3), (5, -1), (-11, -1)])
    m = lambda g: move(g, cx, cy)
    return dict(front=m(union(front, tipf)), side=m(union(side, tips)), top=m(top),
                handle=m(handle), band=m(band))


def _triangle(r, deg):
    return poly([(r * np.cos(np.radians(deg + 120 * i)), r * np.sin(np.radians(deg + 120 * i)))
                 for i in range(3)])


def _star(cx, cy, r=20.5, band=5.2):
    rings = []
    for deg in (90, -90):
        t = _triangle(r, deg)
        rings.append(t.difference(t.buffer(-band, join_style="mitre")))
    up, down = rings
    m = lambda g: move(g, cx, cy)
    return m(knockout(up, down)), m(down)


def _doughnut(cx, cy):
    dough = smooth([(-19, -6), (-18, 2), (-12, 8.5), (0, 11), (12, 8.5), (18, 2), (19, -6),
                    (14, -11), (0, -12.5), (-14, -11)], 12).buffer(0)
    sugar_edge = [(-20, 0), (-15, -1), (-13, -5), (-10.5, -1.5), (-4, -0.5), (0, -4.5),
                  (3, -0.5), (9, -1), (12, -4.5), (14.5, -0.5), (20, 0), (20, 20), (-20, 20)]
    sugar = shrink(dough, 1.6).intersection(smooth(sugar_edge, 8).buffer(0))
    sugar = sugar.buffer(-0.6).buffer(0.6)
    jam = smooth([(-4, 8.5), (-4.5, 11.5), (-2, 14), (2, 14), (4.5, 11.5), (4, 8.5), (1.5, 6),
                  (0.5, 3.5), (-0.5, 3.5), (-1.5, 6)], 8).buffer(0)
    m = lambda g: move(g, cx, cy)
    return m(dough), m(sugar), m(jam)


def art():
    d = Design()
    body, candles, flames = _menorah(-Q, Q)
    dr = _dreidel(Q, Q)
    up, down = _star(-Q, -Q - 2)
    dough, sugar, jam = _doughnut(Q, -Q)

    # blue
    for c in candles:
        d.fill(c, C_["blue"], angle=90, name="candle")
    d.fill(knockout(dr["front"], dr["band"]), C_["blue"], angle=80, name="dreidel front")
    d.fill(up, C_["blue"], angle=0, name="star up")
    # navy
    d.fill(knockout(dr["side"], dr["band"]), C_["navy"], angle=35, name="dreidel side")
    d.fill(down, C_["navy"], angle=60, name="star down")
    # gold
    d.fill(body, C_["gold"], angle=None, name="menorah")
    d.fill(dr["band"], C_["gold"], angle=10, underlay=False, name="dreidel band")
    d.fill(dr["handle"], C_["gold"], angle=90, name="dreidel handle")
    d.fill(knockout(dough, sugar, jam), C_["gold"], angle=20, name="dough")
    # white, red, orange
    d.fill(knockout(dr["top"], dr["handle"]), C_["white"], angle=0, name="dreidel top")
    d.fill(knockout(sugar, jam), C_["white"], angle=150, name="sugar")
    d.fill(jam, C_["red"], angle=90, name="jam")
    for f in flames:
        d.fill(f, C_["orange"], angle=90, underlay=False, name="flame")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
