"""The Mage tarot card (I): a robed, bearded mage raising a wand under an infinity sign,
behind a table holding a cup, a blade, a coin and a staff, in a starry violet sky.

Spec:
  object:       tarot card "I - THE MAGE" (original scene; tarot imagery is centuries-old
                public domain, no published deck's artwork copied), first of the Arcana &
                Ink tarot series; tees, totes, hoodies, tarot bags, altar cloths, patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7); the card is
                66 x 100 nominal (about 59 x 90 at 4x4, 106 x 160 at 5x7)
  fabric:       knits with cut-away; wovens, canvas and tarot bags with tear-away
  threads:      bone (card face), violet (sky, coin star, plaques), red (robe, altar cloth), khaki
                (face, hands), silver (beard, blade, wand), dark brown (table edge, grip),
                light brown (table top, staff), deep gold (stars, infinity sign, cup, coin,
                belt, frame, lettering): 8 colours
  frame:        the series frame (`_tarot.py`): 2.4 mm gold outer border, 1.3 mm inner
                rule with notched corners and gold corner diamonds, 1.3 mm picture frame,
                "I" in the top plaque between two diamonds, "THE MAGE" in the bottom banner,
                block lettering 6.8 mm caps nominal (6.1 mm at 4x4), counters
                filled in the banner colour
  must have:    a 16 mm infinity sign sewn as one satin (1.4 mm) whose crossing strand
                passes through the gap at its ends; hooded mage 22 mm wide with a silver
                beard, raised wand (silver satin, gold star tip) and a gold belt; a table
                across the picture with a gold goblet, an upright silver dagger with a
                gold guard, a gold coin with a violet star and a wooden staff topped by a
                gold orb; five gold four-point stars
  density:      every fill knocked out under everything above it; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401
import _tarot as T

DESCRIPTION = "Tarot card I, The Mage: a robed mage with a raised wand under an infinity sign, with cup, blade, coin and staff"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "The Mage Tarot Card Embroidery Design",
    "Tarot card I, The Mage: a robed mage with a raised wand under a golden infinity sign, "
    "framed as a bone-and-gold tarot card",
    ["tarot", "tarot card", "the magician tarot", "the mage", "major arcana", "witchy",
     "occult", "mystic", "tarot embroidery", "wizard", "celestial"],
    "Card I of the Arcana & Ink tarot series: a hooded, bearded mage raises a wand beneath "
    "a golden infinity sign, a table before him set with a goblet, a dagger, a coin and a "
    "staff, under a starry violet sky. The scene sits in a bone card face with a gold "
    "double border, notched corners, a numeral plaque and the card name in bold block "
    "letters.\n\n"
    "Great on tees, hoodies, tote bags, tarot pouches and altar cloths, and pairs with The "
    "Tower and The Moon from the same series.",
    mockups=("tshirt", "tote"),
)

ORDER = ["bone", "violet", "red", "khaki", "silver", "bark", "wood", "gold"]


def checks(p):
    return standard_checks(p, len(ORDER), 20000)


def lemniscate(cx, cy, a, gap=1.5):
    """Infinity sign as one open path: starts and ends just either side of the centre,
    so the strand that crosses the middle passes through the gap."""
    t0 = np.pi / 2
    dt = gap / a * 0.75
    t = np.linspace(t0 + dt, t0 + 2 * np.pi - dt, 140)
    s = 1 + np.sin(t) ** 2
    return np.c_[cx + a * np.cos(t) / s, cy + a * np.sin(t) * np.cos(t) / s]


def sparkle(x, y, r):
    return star(4, r, r * 0.3, x, y, rot=90)


def mage():
    """(robe, sleeves, hood, face, beard, hands) in nominal mm."""
    robe = poly([(-6.5, 8.5), (6.5, 8.5), (11.5, -13), (-11.5, -13)])
    raised = poly([(-6.8, 8.2), (-2.5, 5.0), (-11.0, 17.6), (-15.6, 16.2)])       # right arm up
    lowered = poly([(4.5, 8.4), (8.0, 8.0), (14.0, -5.5), (9.6, -7.5)])           # left arm down
    hood = smooth([(-5.2, 6.5), (-5.0, 12.5), (-2.8, 17.0), (0, 19.2), (2.8, 17.0), (5.0, 12.5),
                   (5.2, 6.5), (0, 5.4)], 10)
    face = ellipse(0, 12.0, 2.6, 3.4, 64)
    beard = smooth([(-2.7, 10.6), (-2.4, 8.5), (-1.2, 5.6), (0, 3.2), (1.2, 5.6), (2.4, 8.5),
                    (2.7, 10.6), (0, 9.6)], 8)
    hands = [circle(-13.4, 17.4, 1.7, 48), circle(12.2, -7.4, 1.7, 48)]
    return robe, union(raised, lowered), hood, face, beard, hands


def art():
    d = Design()
    F = T.frame("I", "THE MAGE")
    scene = F["scene"]
    robe, sleeves, hood, face, beard, hands = mage()

    K, DY = 1.15, -3.5                       # the figure, enlarged about its hem
    fig = lambda g: move(scale(g, K, K, origin=(0, -13)), 0, DY)
    robe, sleeves, hood, face, beard = (fig(g) for g in (robe, sleeves, hood, face, beard))
    hands = [fig(g) for g in hands]
    figp = lambda *pts: move(scale(line(*pts), K, K, origin=(0, -13)), 0, DY)

    TOP = -15.0                              # table top front edge
    table_top = poly([(-21.5, TOP + 3.2), (21.5, TOP + 3.2), (24.5, TOP), (-24.5, TOP)])
    edge = rect(52, 2.6, 0, TOP - 1.1)                 # dark front edge of the slab
    cloth = rect(52, 20, 0, TOP - 12.2)                # red altar cloth to the floor
    trim = (line((-21.0, TOP - 5.2), (21.0, TOP - 5.2)), 1.4)
    cup = union(smooth([(-21.2, TOP + 12.2), (-14.0, TOP + 12.2), (-14.6, TOP + 9.0),
                        (-16.0, TOP + 7.4), (-17.6, TOP + 6.9), (-19.2, TOP + 7.4), (-20.6, TOP + 9.0)], 8),
                rect(1.5, 4.6, -17.6, TOP + 5.0),
                poly([(-20.4, TOP + 0.4), (-14.8, TOP + 0.4), (-16.6, TOP + 2.4), (-18.6, TOP + 2.4)]))
    blade = poly([(-8.1, TOP + 8.2), (-5.9, TOP + 8.2), (-5.9, TOP + 16.0), (-7.0, TOP + 19.0), (-8.1, TOP + 16.0)])
    guard = rect(6.4, 1.5, -7.0, TOP + 7.6)
    grip = rect(1.7, 3.0, -7.0, TOP + 5.4)
    pommel = circle(-7.0, TOP + 2.6, 1.3, 40)
    coin = circle(7.5, TOP + 5.0, 4.3, 80)
    pent = star(5, 2.9, 1.25, 7.5, TOP + 5.0, rot=90)
    staff = (line((19.6, TOP + 0.9), (20.3, 16.0)), 1.6)
    orb = circle(20.35, 18.0, 2.1, 48)
    wand = (figp((-13.6, 18.6), (-17.0, 24.2)), 1.3)
    wx, wy = figp((-17.7, 25.6))[0]
    wand_star = sparkle(wx, wy, 2.6)
    belt = (figp((-8.6, -2.4), (8.6, -2.4)), 1.6)
    inf = (lemniscate(0.0, 26.6, 8.0), 1.4)
    stars = [sparkle(-17, 7, 2.2), sparkle(-12, 28, 2.0), sparkle(18.5, 5, 2.0),
             sparkle(-9.5, 17.5, 1.8), sparkle(12.5, 20.5, 1.8), sparkle(17.5, 27.5, 2.4)]

    L = [("fill", scene, "violet", dict(angle=30, name="sky"))]
    L += [("fill", g, "gold", dict(angle=45, name="star")) for g in stars]
    L += [("fill", robe, "red", dict(angle=80, name="robe")),
          ("satin", belt, "gold", dict(name="belt")),
          ("fill", sleeves, "red", dict(angle=110, name="sleeves")),
          ("fill", hood, "red", dict(angle=95, name="hood")),
          ("fill", face, "khaki", dict(angle=0, name="face")),
          ("fill", beard, "silver", dict(angle=90, name="beard"))]
    L += [("fill", g, "khaki", dict(angle=0, name="hand")) for g in hands]
    L += [("satin", wand, "silver", dict(name="wand")),
          ("fill", wand_star, "gold", dict(angle=45, name="wand star")),
          ("satin", inf, "gold", dict(name="infinity")),
          ("fill", cloth, "red", dict(angle=90, name="altar cloth")),
          ("satin", trim, "gold", dict(name="cloth trim")),
          ("fill", edge, "bark", dict(angle=0, name="table edge")),
          ("fill", table_top, "wood", dict(angle=0, name="table top")),
          ("satin", staff, "wood", dict(name="staff")),
          ("fill", orb, "gold", dict(angle=45, name="orb")),
          ("fill", cup, "gold", dict(angle=90, name="cup")),
          ("fill", blade, "silver", dict(angle=90, name="blade")),
          ("fill", grip, "bark", dict(angle=0, name="grip")),
          ("fill", union(guard, pommel), "gold", dict(angle=0, name="guard")),
          ("fill", coin, "gold", dict(angle=45, name="coin")),
          ("fill", pent, "violet", dict(angle=0, name="coin star"))]

    T.sew_face(d, F, C_["bone"])
    T.sew_scene(d, F, L, ORDER, C_, hooks={"violet": lambda d: T.sew_plaques(d, F, C_["violet"]),
                                           "gold": lambda d: T.sew_gold(d, F, C_["gold"])})
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
