"""Apothecary Potions: a round flask, a tall vial and a square bottle of bubbling potions.

Spec:
  object:       three corked potion bottles (red, blue and green brews) for tees, totes,
                dice bags, aprons and game-night patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; totes, aprons and wovens with tear-away
  threads:      ice (empty glass), bone (label tag), red (flask brew, heart on the tag),
                blue (vial brew), leaf (bottle brew), wood (corks), white (glints,
                bubbles), charcoal (bottle outlines, tag edge): 8 colours
  must have:    a 42 mm round flask in front centre with a neck lip; a 16 x 50 mm vial on
                the right; a 24 x 32 mm square bottle on the left; wavy brew levels with
                ice glass above; 11 mm wood corks; a 16 x 11 mm bone tag with a red heart
                on the square bottle; 1.6 mm white glints, 2.4-3.6 mm bubbles; a 1.2 mm
                charcoal satin outline round each bottle, 3 mm apart
  density:      fills tucked under the outlines; upper layers knock out lower; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Three corked potion bottles, a round flask, a tall vial and a square bottle"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Apothecary Potions Embroidery Design",
    "Three bubbling potion bottles in red, blue and green: a round flask, a tall vial and "
    "a square bottle with a heart tag",
    ["potion", "potion bottles", "alchemy", "apothecary", "health potion", "mana potion",
     "tabletop rpg", "game night", "witchy", "dice bag"],
    "Stock up before the dungeon: a round red flask, a tall blue vial and a square green "
    "bottle, each corked, glinting and bubbling, with a little heart tag on the green one. "
    "Bold charcoal outlines keep it bright and playful at any size.\n\n"
    "Great on tees, totes, aprons, dice bags and game-night patches.",
    mockups=("tshirt", "tote"),
)

OUT = 1.2   # outline satin width


def checks(p):
    return standard_checks(p, 8, 14000)


def _below(level, amp=1.0, k=0.55, phase=0.0):
    """Everything under a wavy brew surface at `level`."""
    x = np.linspace(-70, 70, 141)
    top = np.c_[x, level + amp * np.sin(k * x + phase)]
    return poly(np.vstack([top, [(70, -80), (-70, -80)]]))


def art():
    d = Design()
    # square bottle (left), round flask (centre front), tall vial (right)
    sq_body = rounded_rect(24, 32, 3.5, -36, -24)
    sq_neck = rect(9, 7, -36, -5)
    sq_cork = rounded_rect(12, 7, 1.5, -36, 1.5)
    fl_body = circle(0, -19, 21)
    fl_neck = rect(10, 15, 0, 5)
    fl_lip = rounded_rect(14, 3.4, 1.4, 0, 12.8)
    fl_cork = rounded_rect(11, 8, 1.5, 0, 18.2)
    vi_body = rounded_rect(16, 50, 7.5, 33, -15)
    vi_neck = rect(9, 6.5, 33, 12)
    vi_cork = rounded_rect(12, 8, 1.5, 33, 18.6)

    bottles = [
        (union(sq_body, sq_neck), sq_cork, _below(-14, phase=1.0), "leaf", 0),
        (union(fl_body, fl_neck, fl_lip), fl_cork, _below(-13), "red", 30),
        (union(vi_body, vi_neck), vi_cork, _below(1, phase=2.0), "blue", -30),
    ]
    tag = rounded_rect(16, 11, 2.0, -36, -25)
    heart_ = heart(6.5, -36, -25)
    glints = [line((-44.6, -14), (-44.6, -32)),
              arc(0, -19, 16, 122, 168),
              line((28.4, 5), (28.4, -28))]
    bubbles = [circle(7, -29, 1.8), circle(-6, -33, 1.3), circle(11, -19, 1.4),
               circle(35, -31, 1.6), circle(36, -19, 1.2), circle(34, -9, 1.4),
               circle(-29, -36, 1.3), circle(-42, -36.5, 1.2)]
    shine = union(*[_band(g, 0.8) for g in glints], *bubbles)   # white sews on top

    for glass, cork, below, col, ang in bottles:
        d.fill(knockout(tuck(glass, OUT).difference(below), cork, shine), C_["ice"],
               angle=ang + 90, name="glass")
    d.fill(knockout(tag, heart_), C_["bone"], angle=0, name="tag")
    for glass, cork, below, col, ang in bottles:
        if col == "red":
            d.fill(knockout(tuck(glass, OUT).intersection(below), shine), C_["red"], angle=ang,
                   name="red brew")
    d.fill(heart_, C_["red"], angle=45, name="heart")
    for colour in ("blue", "leaf"):
        for glass, cork, below, col, ang in bottles:
            if col == colour:
                d.fill(knockout(tuck(glass, OUT).intersection(below), shine, tag), C_[col],
                       angle=ang, name=f"{col} brew")
    for glass, cork, below, col, ang in bottles:
        d.fill(knockout(tuck(cork, OUT), glass), C_["wood"], angle=90, name="cork")
    for g in glints:
        d.satin(g, 1.6, C_["white"], name="glint", underlay="center")
    for g in bubbles:
        d.fill(g, C_["white"], angle=45, underlay=False, name="bubble")
    for glass, cork, below, col, ang in bottles:
        d.outline(union(glass, cork), C_["charcoal"], width=OUT, name="bottle outline")
    d.outline(tag, C_["charcoal"], name="tag edge")
    return d


def _band(path, r):
    return LineString(np.asarray(path)).buffer(r, cap_style="flat")


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
