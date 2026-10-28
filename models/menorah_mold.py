"""Mold for a modern cement or Jesmonite Hanukkah menorah: a straight bar with eight
candle cups in a row at one height and the shamash raised in the middle.

The finished menorah is 168 mm long, 30 mm deep and 26 mm tall, with the shamash block
12 mm higher. The cups take standard 9-10 mm Hanukkah candles and narrow slightly so
the candles stand straight. Cement does not burn, which makes it a good material for a
menorah. Pour, screed the back flat, and lift it out once cured. Prints opening-up with
no supports in under 2 hours, and fits the A1 mini bed.

Spec:
  object:       mold for a cement / Jesmonite menorah, poured straight into the print
  overall:      menorah 168 x 30 mm, 26 mm tall, shamash block 12 mm higher;
                mold ~176 x 38 x 44 mm, fits the A1 mini bed (180 mm)
  mates with:   standard Hanukkah candles, 9-10 mm at the base; cup 10.2 mm at the bottom
                widening at 4 deg to ~12 mm at the rim, 13 deep, so candles wedge upright
  orientation:  opening up, flat floor on the bed, no supports
  must have:    9 cups at 18.5 mm pitch in one straight line; the 8 Hanukkah lights level,
                the shamash raised 12 mm; 2 deg draft on the body, 3 mm rounded corners;
                floor 3, wall 3
  tolerances:   none (casting); cup size is a wedge fit for 9-10 mm candles

Units: mm. Z is up, the mold sits on Z=0.
"""
from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Hanukkah menorah cement mold, 9 candles in a row with a raised shamash"

PRODUCT = dict(
    title="Hanukkah Menorah Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "menorah", "hanukkah", "chanukah", "judaica",
          "candle holder", "holiday"],
    printers=["a1", "a1mini"],
    cast_material="cement, concrete or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    pitch=18.5,             # candle spacing
    end_margin=10.0,        # from the end cups to the ends of the bar
    width=30.0,             # front-to-back depth of the bar at its top face
    height=26.0,            # bar height
    shamash_raise=12.0,     # how much higher the shamash block stands
    shamash_width=22.0,     # length of the shamash block along the bar
    cup_d=10.2,             # cup diameter at the bottom
    cup_depth=13.0,
    cup_draft=4.0,
    corner=3.0,
    floor=3.0,
    wall=3.0,
    body_draft=2.0,
)

EMBED = 0.1


def rounded_rect(lx, ly, r):
    return grow(CrossSection.square((lx - 2 * r, ly - 2 * r), center=True), r)


def cup_xs(p):
    return [(i - 4) * p.pitch for i in range(9)]


def bar_length(p):
    return 8 * p.pitch + 2 * p.end_margin


def checks(p):
    L = bar_length(p)
    lean = draft_offset(p.height + p.shamash_raise, p.body_draft)
    z_bar = p.floor + p.shamash_raise                     # mold floor under the eight lights
    top = z_bar + p.height
    cup_r = p.cup_d / 2
    return [
        dims(x=(L + 2 * p.wall, L + 2 * p.wall + 2 * lean + 1), y=(p.width + 2 * p.wall, p.width + 2 * p.wall + 2 * lean + 1),
             z=top),
        fits_bed(),
        # a cup boss at each end and the shamash cup in its well
        solid((cup_xs(p)[0], 0, z_bar + p.cup_depth / 2), (cup_xs(p)[8], 0, z_bar + p.cup_depth / 2),
              (0, 0, p.floor + p.cup_depth / 2)),
        # cups wide enough at the bottom for a 10 mm candle
        solid((cup_xs(p)[0] + cup_r - 0.3, 0, z_bar + p.cup_depth - 0.3)),
        empty((cup_xs(p)[0], 0, z_bar + p.cup_depth + 1.0)),
        # bar cavity between cups, and the shamash well below the bar floor level
        empty((p.pitch * 1.5, p.width / 2 - 4, z_bar + 2), (0, p.width / 2 - 4, p.floor + 2)),
        solid((p.pitch * 1.5, 0, z_bar - 1)),                              # floor under the lights
        thickness_at((p.shamash_width / 2 - 3, p.width / 2 - 4, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(L * p.width * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    L = bar_length(p)
    H = p.height + p.shamash_raise
    lean = draft_offset(H, p.body_draft)
    z_bar = p.floor + p.shamash_raise
    top = z_bar + p.height
    mold = extrude(rounded_rect(L + 2 * (lean + p.wall), p.width + 2 * (lean + p.wall), p.corner + p.wall), top)
    # menorah body: the bar from the lights' level up, the shamash block from the floor up;
    # both lean outward at the same rate so their sides stay flush where they meet
    rate = lean / H                                       # sideways per mm of height
    bar = tapered(grow(rounded_rect(L, p.width, p.corner), p.shamash_raise * rate), z_bar, p.height + 1,
                  (p.height + 1) * rate)
    sw = p.shamash_width
    block = tapered(rounded_rect(sw, p.width, p.corner), p.floor, p.shamash_raise + 0.5,
                    (p.shamash_raise + 0.5) * rate)
    mold -= bar + block
    # candle cups: bosses narrowing upward to the cup size
    boss_lean = draft_offset(p.cup_depth, p.cup_draft)
    r = p.cup_d / 2
    for x in cup_xs(p):
        z0 = p.floor if x == 0 else z_bar
        mold += tapered(circle(x, 0, r + boss_lean), z0 - EMBED, p.cup_depth + EMBED, -boss_lean)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the menorah the right way up."""
    return cast_of(build(p))
