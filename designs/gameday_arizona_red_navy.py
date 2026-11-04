"""Arizona game-day design: 'ARIZONA' arched in block letters over the state, red & navy.

Spec:
  object:       game-day badge for sweatshirts, caps, totes, stadium blankets
  overall:      `size` mm on the longest side (95 for 4x4, 160 for 5x7, capped by the hoop)
  source:       state outline from US Census cartographic boundaries (public domain);
                lettering is our own block alphabet (cadkit.stitch.lettering)
  fabric:       sweatshirt fleece and knits with cut-away and a topper; wovens tear-away
  threads:      in sewing order: accent #878787 (drop shadow); primary #ce1126 (state fill,
                letter plate, plate edge); secondary #14213d (state border, letters): 3 blocks
  must have:    'ARIZONA' arched over the state, on one connected
                primary plate (gaps and counters bridged) with a satin edge and a drop shadow
                under it; the state below with a satin border (2 mm on the 4x4, growing with
                the square root of the size), at least 3.5 mm clear; no school names or marks
  efficiency:   3 colour blocks; plate, edge and shadow each one piece; travel buried under
                same-or-darker later stitching (hide_jumps_mm) instead of trimmed
  density:      plate knocked out under the letters, fills tucked under satins; max 3.5
"""
from cadkit.stitch import *

from _gameday import SIZES, build, product, standard_checks

STATE, COLOURWAY = "arizona", "red_navy"
DESCRIPTION = "Arizona block letters arched over the state outline, red & navy"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(STATE, COLOURWAY)


def checks(p):
    return standard_checks(p, COLOURWAY)


def design(p):
    return build(STATE, COLOURWAY, p.size, HOOP, close=4.6)     # bridge pockets beside T, L, Y ...
