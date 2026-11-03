"""The Tower tarot card (XVI): a dark stone tower on a black crag, struck by a jagged gold
lightning bolt, its crown blasted off in flames, sparks falling through a stormy navy sky.

Spec:
  object:       tarot card "XVI - THE TOWER" (original scene; tarot imagery is centuries-old
                public domain, no published deck's artwork copied), part of the Arcana & Ink
                tarot series; tees, hoodies, totes, jackets, tarot bags, patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7); the card is
                66 x 100 nominal (about 59 x 90 at 4x4, 106 x 160 at 5x7)
  fabric:       knits with cut-away; wovens, canvas and denim with tear-away
  threads:      bone (card face), navy (sky, plaques), dark gray (storm clouds, shaded side
                of the tower), gray (lit stone, cloud tops), black (crag),
                vermilion (flames), harvest gold (flame cores, lit windows), deep gold
                (lightning, falling crown, sparks, frame, lettering): 8 colours
  frame:        the series frame (`_tarot.py`): 2.4 mm gold outer border, 1.3 mm inner
                rule with notched corners and gold corner diamonds, 1.3 mm picture frame,
                "XVI" in the top plaque between two diamonds, "THE TOWER" in the bottom
                banner, block lettering 6.8 mm caps nominal (6.1 mm at 4x4), counters
                filled in the banner colour
  must have:    a 15 mm wide tapering tower, 34 mm tall, with a broken jagged top, a shaded
                right side and three lit arched windows; a jagged
                gold bolt 2.2 mm wide from the clouds to the broken top; flames bursting
                from the top and a gold crown tumbling away; storm clouds across the top;
                a jagged black crag; eight falling gold sparks
  density:      every fill knocked out under everything above it; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401
import _tarot as T

DESCRIPTION = "Tarot card XVI, The Tower: a stone tower struck by gold lightning, its crown blasted off in flames"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "The Tower Tarot Card Embroidery Design",
    "Tarot card XVI, The Tower: a dark stone tower struck by a gold lightning bolt, its crown "
    "blasted off in flames, framed as a bone-and-gold tarot card",
    ["tarot", "tarot card", "the tower tarot", "the tower", "major arcana", "dark fantasy",
     "witchy", "occult", "gothic", "lightning", "tarot embroidery"],
    "Card XVI of the Arcana & Ink tarot series: a dark stone tower on a black crag takes a "
    "jagged gold lightning strike, flames burst from its broken top, its crown tumbles away "
    "and sparks fall through a stormy navy sky. The scene sits in a bone card face with a "
    "gold double border, notched corners, a numeral plaque and the card name in bold block "
    "letters.\n\n"
    "Great on hoodies, tees, denim jackets, tote bags and tarot pouches, and pairs with The "
    "Mage and The Moon from the same series.",
    mockups=("tshirt", "tote"),
)

ORDER = ["bone", "navy", "charcoal", "gray", "black", "ember", "yellow", "gold"]


def checks(p):
    return standard_checks(p, len(ORDER), 20000)


def flame(x, y, h, w, lean=0.0):
    """A flame tongue standing on (x, y): `h` tall, `w` wide, tip leaning `lean` mm."""
    return smooth([(x - w / 2, y), (x - w * 0.45, y + h * 0.35), (x - w * 0.15 + lean * 0.5, y + h * 0.7),
                   (x + lean, y + h), (x + w * 0.3 + lean * 0.4, y + h * 0.6), (x + w / 2, y + h * 0.25),
                   (x, y - h * 0.08)], 8)


def spark(x, y, r):
    return poly([(x, y + r * 1.5), (x + r * 0.6, y), (x, y - r), (x - r * 0.6, y)])


def window(x, y, w=2.4, h=4.4):
    """(path, widths) of an arched window sewn as one vertical satin column."""
    r = w / 2
    ys = np.linspace(y - h / 2 + 0.15, y + h / 2 - 0.35, 14)
    yc = y + h / 2 - r
    ws = np.where(ys <= yc, w, 2 * np.sqrt(np.clip(r ** 2 - (ys - yc) ** 2, 0, None)))
    return np.c_[np.full_like(ys, x), ys], np.maximum(ws, 0.9)


def art():
    d = Design()
    F = T.frame("XVI", "THE TOWER")
    scene = F["scene"]

    # tower: tapering body with a broken, jagged top
    top = [(-6.6, 11.0), (-5.0, 14.2), (-3.4, 12.2), (-1.6, 15.4), (0.6, 12.6), (2.4, 14.6),
           (4.0, 11.8), (6.6, 13.2)]
    tower = poly([(-7.8, -20), (7.8, -20), (6.6, 13.2)] + top[::-1][1:])
    shade = tower & poly([(2.8, -21), (9, -21), (9, 16), (2.4, 16)])
    tower, shade = (scale(g, 1.3, 1.0) for g in (tower, shade))
    windows = [window(-2.6, 4.5), window(1.2, -6.0), window(-3.0, -13.5)]
    win_area = union(*[LineString(p).buffer(1.2, cap_style="flat") for p, _ in windows])

    crag = poly([(-25, -32), (-25, -21), (-19, -23.5), (-15, -18.5), (-11, -20.5), (-7.6, -16.8),
                 (-3, -18.2), (2, -16.4), (8.2, -17.6), (12, -20.4), (16, -18), (20, -22.5),
                 (25, -20), (25, -32)])
    puffs = [(-24, 27.5), (-18, 29.5), (-12.5, 30.5), (-6.5, 32), (-20.5, 24.5),
             (13, 31.5), (18.5, 29.5), (24, 27), (21.5, 24.5), (8, 33)]
    clouds = union(*[circle(x, y, 4.6 if abs(x) > 20 else 3.8, 64) for x, y in puffs])
    clouds = clouds.buffer(0.6).buffer(-0.6)

    flames = [flame(-6.8, 11.0, 9.5, 5.4, 1.5), flame(-1.4, 12.0, 14.0, 6.6, 2.5),
              flame(4.2, 11.5, 11.5, 5.8, 3.5), flame(8.8, 9.0, 7.5, 4.4, 3.0),
              flame(-10.4, 7.0, 6.5, 3.8, -1.2)]
    cores = [flame(-1.2, 12.4, 9.0, 3.4, 1.8), flame(4.4, 12.0, 6.6, 3.0, 2.2)]
    fire = union(*flames)
    # lightning: a jagged bolt from the clouds into the broken top
    bolt = poly([(-22.0, 30.6), (-16.4, 30.6), (-11.4, 24.2), (-7.4, 25.0), (-2.2, 13.4),
                 (-9.8, 21.0), (-13.8, 20.2)])
    crown = rotate(union(rect(8.0, 2.2, 0, 0),
                         poly([(-4, 0.8), (-4.2, 5.0), (-2.0, 2.6), (0, 5.8), (2.0, 2.6), (4.2, 5.0), (4, 0.8)])),
                   -32, origin=(0, 0))
    crown = move(crown, 15.0, 19.0)
    sparks = [spark(x, y, r) for x, y, r in
              [(-14, 12, 1.4), (-18.5, 3, 1.2), (-12, -4, 1.3), (-19, -12, 1.1), (13, 9, 1.4),
               (18.5, 13.5, 1.1), (16, -1, 1.3), (20, -9, 1.2), (11.5, -11, 1.1)]]

    L = [("fill", scene, "navy", dict(angle=30, name="sky")),
         ("fill", clouds, "charcoal", dict(angle=-15, name="clouds")),
         ("fill", (clouds - move(clouds, 0.6, -2.0)).buffer(-0.3).buffer(0.3), "gray",
          dict(angle=-15, name="cloud light"))]
    L += [("fill", g, "gold", dict(angle=45, name="spark")) for g in sparks]
    L += [("fill", tower, "gray", dict(angle=90, name="stone")),
          ("fill", shade, "charcoal", dict(angle=90, name="shade"))]
    L += [("satin", (p, w), "yellow", dict(name="window", taper=True)) for p, w in windows]
    L += [("fill", crag, "black", dict(angle=60, name="crag")),
          ("fill", fire, "ember", dict(angle=80, name="flames"))]
    L += [("fill", g, "yellow", dict(angle=80, name="flame core")) for g in cores]
    L += [("fill", crown, "gold", dict(angle=58, name="crown")),
          ("fill", bolt, "gold", dict(angle=0, name="lightning"))]

    T.sew_face(d, F, C_["bone"])
    T.sew_scene(d, F, L, ORDER, C_, hooks={"navy": lambda d: T.sew_plaques(d, F, C_["navy"]),
                                           "gold": lambda d: T.sew_gold(d, F, C_["gold"])})
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
