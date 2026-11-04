"""Maryland game-day arched banner design: 'MARYLAND' arched in block letters over the state, red & gold.

Spec:
  object:       game-day badge for sweatshirts, caps, totes, stadium blankets
  overall:      `size` mm on the longest side (95 for 4x4, 160 for 5x7, capped by the hoop)
  source:       state outline from US Census cartographic boundaries (public domain);
                lettering is our own block alphabet (cadkit.stitch.lettering)
  fabric:       sweatshirt fleece and knits with cut-away and a topper; wovens tear-away
  threads:      in sewing order: accent #2a1301 (drop shadow); primary #e21833 (state fill,
                letter plate, plate edge); secondary #ffd200 (state border, letters): 3 blocks
  must have:    'MARYLAND' arched over the state, on a solid arched
                primary banner from baseline to cap line (a rocker) with a satin edge and a drop shadow
                under it; the state below with a satin border (2 mm on the 4x4, growing with
                the square root of the size), at least 3.5 mm clear; no school names or marks
  efficiency:   3 colour blocks; plate, edge and shadow each one piece; travel buried under
                same-or-darker later stitching (hide_jumps_mm) instead of trimmed
  density:      plate knocked out under the letters, fills tucked under satins; max 3.5
"""
from cadkit.stitch import *

from _gameday import SIZES, build, product, standard_checks

STATE, COLOURWAY = "maryland", "red_gold"
DESCRIPTION = "Maryland block letters on an arched banner over the state outline, red & gold"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(STATE, COLOURWAY, banner=True)


def checks(p):
    return standard_checks(p, COLOURWAY)


def design(p):
    return build(STATE, COLOURWAY, p.size, HOOP, banner=True, thin=1.0, smooth=1.2, border=0.6, channel=1.1)     # panhandle neck in the border colour; narrow bay water closed (1.1: the bay neck where two borders met piled to 3.5 layers on the 5x7)
