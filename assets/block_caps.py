"""Block Caps: a squared, heavy display font for game titles, HUD counts and menus.

Spec:
  kind: font
  family: Block Caps
  style: one stroke weight, square bowls, clipped corners; capitals only (lowercase letters use
         the capitals), the way arcade and sports lettering is set
  covers: A-Z, 0-9 and . , : ; ! ? ' " - + = / \\ ( ) [ ] % # * < > _ ; accented Latin-1 letters fall
          back to their base letter; anything else draws the hollow box
  metrics: 1000 units per em, cap height 700; no kerning (Cinder applies none)
  legible: thinnest stroke at least 1.5 px at 18 px, the smallest size the HUD uses
  distinct: 0 from O (the zero has a centre bar), 1 from I, 5 from S, 8 from B, 2 from Z
  use: titles and HUD in Cinder (`Font.from_file`); ours to license, no third-party typeface involved
  source: the block alphabet in cadkit.stitch.lettering (drawn for embroidery), extended with
          digits and punctuation in the same construction
"""
from cadkit.game.font import *

KIND = "font"
DESCRIPTION = "squared block display font, capitals and digits"
PARAMS = dict(stroke=2.0, tracking=1.1)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["font", "display", "ui"])

DRAWN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;!?'\"-+=/\\()[]%#*<>_"


def checks(p):
    return [covers(DRAWN), stroke_at(18, 1.5), distinct("0", "O"), distinct("1", "I"), distinct("5", "S"),
            distinct("8", "B"), distinct("2", "Z"), distinct("6", "G"), distinct(".", ","), distinct(":", ";")]


def build(p):
    return FontFace(block_glyphs(p.stroke), family="Block Caps", tracking=p.tracking)
