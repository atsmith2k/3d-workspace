"""Love and Light: one tall blue candle with a heart on it and a gold flame, beside
"LOVE AND LIGHT" stacked in navy block letters. Quiet, tonal blue with a gold accent.

Spec:
  object:       minimal Hanukkah / winter design for sweatshirts, tees, pillows, napkins
  overall:      `size` mm wide (95 for the 4x4 hoop, 160 for 5x7; the 4x4 keeps 5 mm
                clear of the hoop edge)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      blue (candle), ice (heart), gold (flame), yellow (flame core), navy (wick,
                saucer, lettering): 5 colours
  must have:    a 12 x 32 mm blue candle on an 18 mm navy saucer, a 7.5 mm ice heart on
                its face, a 1.4 mm navy wick and a 9 x 15 mm gold teardrop flame with a
                yellow core; "LOVE" and "LIGHT" at 11 mm cap with a smaller "AND" (7 mm cap)
                between them, left-aligned 12 mm right of the candle, house block lettering
                (`lettering.block_text`), 0.35 mm rows
  density:      heart knocks out the candle, core knocks out the flame; nothing else
                overlaps; max 3.5
"""
from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "A blue candle with a heart and a gold flame beside Love and Light lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Love and Light Embroidery Design",
    "A single blue candle with a gold flame beside \"Love and Light\"",
    ["love and light", "hanukkah candle", "minimal hanukkah", "blue and gold",
     "festival of lights", "candle embroidery", "winter quote"],
    "A quiet, minimal design: one tall blue candle with a little heart on it and a glowing "
    "gold flame, beside \"Love and Light\" stacked in navy block letters.\n\nLovely on "
    "sweatshirts, tees, pillows and napkins, and simple enough for a first holiday project.",
    mockups=("tshirt", "tote"),
)

CX = -24.0


def checks(p):
    return standard_checks(p, 5, 9000)


def art():
    d = Design()
    candle = rounded_rect(12, 32, 1.5, CX, 0)
    heart_ = heart(7.5, CX, 3)
    saucer = rounded_rect(18, 3.4, 1.6, CX, -17.2)
    wick = rect(1.4, 2.6, CX, 17.0)
    flame = smooth([(0, 0), (4.4, 4.0), (3.6, 9.0), (0, 15), (-3.6, 9.0), (-4.4, 4.0)], 8).buffer(0)
    core = smooth([(0, 1.6), (2.0, 4.0), (1.5, 7.2), (0, 10), (-1.5, 7.2), (-2.0, 4.0)], 6).buffer(0)
    flame, core = move(flame, CX, 18.0), move(core, CX, 18.0)
    x0 = -12.0
    love = block_text("LOVE", cap=11, stroke=2.4)
    and_ = block_text("AND", cap=7, stroke=2.0)
    light = block_text("LIGHT", cap=11, stroke=2.4)
    words = [move(love, x0, 9.0), move(and_, x0, -1.0), move(light, x0, -16.0)]
    d.fill(knockout(candle, heart_), C_["blue"], angle=90, name="candle")
    d.fill(heart_, C_["ice"], angle=45, name="heart")
    d.fill(knockout(flame, core), C_["gold"], angle=90, name="flame")
    d.fill(core, C_["yellow"], angle=90, underlay=False, name="flame core")
    d.fill(wick, C_["navy"], angle=0, name="wick")
    d.fill(saucer, C_["navy"], angle=0, name="saucer")
    for w, nm in zip(words, ("Love", "and", "Light")):
        d.fill(w, C_["navy"], angle=0, spacing=0.35, name=nm)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
