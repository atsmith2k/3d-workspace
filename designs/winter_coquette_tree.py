"""Coquette Bow Tree: a three-tier Christmas tree hung with pink ribbon bows.

Spec:
  object:       coquette-trend Christmas tree for sweatshirts, totes, pillows and kids' wear
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits and sweatshirts with cut-away; wovens with tear-away
  threads:      cocoa (trunk), green (three tiers), pink (bows), blush (bow knots): 4
  must have:    three overlapping scalloped-hem tiers 72, 56 and 38 mm wide; a 10 mm
                trunk; seven 13 mm pink bows hung on the tiers; a 26 mm bow on top
  density:      upper tiers and bows knock out what they cover; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, sew_bow, standard_checks

DESCRIPTION = "Coquette Christmas tree hung with pink ribbon bows"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Coquette Bow Christmas Tree Embroidery Design",
    "A green Christmas tree hung with pink coquette ribbon bows",
    ["coquette christmas", "coquette bow", "pink christmas", "bow tree", "girly christmas"],
    "The coquette trend meets Christmas: a three-tier green tree hung with seven little pink "
    "ribbon bows and a big bow on top in place of a star.\n\nGreat on sweatshirts, totes, "
    "pillows and kids' wear.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 4, 11000)


def _tier(w, top, bottom):
    """A tree tier: a triangle with a scalloped hem, apex at `top`."""
    hem = [(w / 2 * (1 - 2 * t), bottom - 2.2 * abs(np.sin(np.pi * 4 * t))) for t in np.linspace(0, 1, 49)]
    return poly([(0, top)] + hem).buffer(0)


def art():
    d = Design()
    tiers = [_tier(72, 2, -34), _tier(56, 22, -12), _tier(38, 40, 8)]      # bottom to top
    tiers = [t.buffer(1.2).buffer(-1.2) for t in tiers]
    trunk = rect(10, 10, 0, -38)
    spots = [(-22, -27), (0, -24), (22, -27), (-15, -6), (15, -6), (-7, 13), (8, 15)]
    bows = [[move(g, x, y) for g in M.bow(13)] for x, y in spots]
    top = [move(g, 0, 41.5) for g in M.bow(26)]
    every_bow = union(*[g for b in bows + [top] for g in b])
    d.fill(knockout(trunk, tiers[0]), C_["cocoa"], angle=90, name="trunk")
    for i, t in enumerate(tiers):
        above = union(*tiers[i + 1:], every_bow) if i < 2 else every_bow
        d.fill(knockout(t, above), C_["green"], angle=(30, 150, 60)[i], name=f"tier {i + 1}")
    for b in bows + [top]:
        lo, ro, knot, lt, rt = b
        d.fill(union(knockout(lt, lo, ro, knot), knockout(rt, lo, ro, knot)), C_["pink"], angle=90, name="bow tails")
        d.fill(knockout(lo, knot), C_["pink"], angle=150, name="bow loop")
        d.fill(knockout(ro, knot), C_["pink"], angle=30, name="bow loop")
    for b in bows + [top]:
        d.fill(b[2], C_["blush"], angle=90, underlay=False, name="bow knot")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
