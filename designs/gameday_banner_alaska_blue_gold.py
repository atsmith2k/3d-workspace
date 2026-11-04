"""Alaska game-day arched banner design: 'ALASKA' arched in block letters over the state, blue & gold.

Spec:
  object:       game-day badge for sweatshirts, caps, totes, stadium blankets
  overall:      `size` mm on the longest side (95 for 4x4, 160 for 5x7, capped by the hoop)
  source:       state outline from US Census cartographic boundaries (public domain);
                lettering is our own block alphabet (cadkit.stitch.lettering)
  fabric:       sweatshirt fleece and knits with cut-away and a topper; wovens tear-away
  threads:      in sewing order: accent #1d252d (drop shadow); primary #00539f (state fill,
                letter plate, plate edge); secondary #ffd200 (state border, letters): 3 blocks
  must have:    'ALASKA' arched over the state, on a solid arched
                primary banner from baseline to cap line (a rocker) with a satin edge and a drop shadow
                under it; the state below with a satin border (2 mm on the 4x4, growing with
                the square root of the size), at least 3.5 mm clear; no school names or marks
  efficiency:   3 colour blocks; plate, edge and shadow each one piece; travel buried under
                same-or-darker later stitching (hide_jumps_mm) instead of trimmed
  density:      plate knocked out under the letters, fills tucked under satins; max 3.5
"""
from cadkit.stitch import *

from _gameday import SIZES, build, product, standard_checks

STATE, COLOURWAY = "alaska", "blue_gold"
DESCRIPTION = "Alaska block letters on an arched banner over the state outline, blue & gold"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(STATE, COLOURWAY, banner=True)


def checks(p):
    return standard_checks(p, COLOURWAY)


def design(p):
    return build(STATE, COLOURWAY, p.size, HOOP, banner=True, thin=0.9, island=0.5, smooth=1.6, border=0.65, channel=0.6, raw_necks=True, plate_angle=85)     # Aleutian tail: islands too small for a border as solid dots; plate rows at 85 (at 95 its travel ran 4x through one hole under the edge)
