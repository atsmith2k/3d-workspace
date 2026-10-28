"""Plaster ornament mold: a plate with four different snowflake cavities, each with a pin that
forms the hanging hole through the ornament's top arm.

The snowflakes are flat, 6 mm thick, cast face-down: the mold floor gives the show face and
the pour face is the back. A shallow hexagon pocket in each cavity floor becomes a raised
hexagon at the snowflake's centre. Walls of the cavities are drafted 8 deg because the arms are
narrow and the mold is rigid.

Spec:
  object:       mold for four plaster / Jesmonite / resin snowflake ornaments, 62 mm each
  overall:      plate ~145 x 145 x 9 mm (fits the A1 mini)
  mates with:   ribbon or hook through a 3.2 mm hole (pin 3.4 mm at the floor, drafted)
  orientation:  opening up, flat floor on the bed, no supports
  must have:    4 designs; arms 6.5 mm wide, branches 4.5 mm; ornament 6 mm thick;
                hanging hole in a 10 mm ring at the top arm tip; raised hexagon 1.0 mm at
                the centre; floor 3, 8 deg draft on cavities and the hexagon
  tolerances:   none (casting)

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Plaster ornament mold with four 62 mm snowflakes and hanging holes"

PRODUCT = dict(
    title="Snowflake Ornament Mold",
    category="molds",
    tags=["mold", "plaster", "jesmonite", "resin", "ornament", "snowflake", "christmas",
          "winter", "holiday decor"],
    printers=["a1", "a1mini"],
    cast_material="plaster, Jesmonite or resin",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    size=62.0,          # ornament size, tip to tip
    thickness=6.0,
    arm_w=6.5,
    branch_w=4.5,
    hole_d=3.4,
    ring_d=10.0,
    boss_h=1.0,         # raised hexagon at the centre of the face
    floor=3.0,
    gap=6.0,            # plate material between cavities and around the edge
    draft=8.0,
    boss_draft=8.0,
    notch=1.6,          # inside corners of the outline rounded to this radius
)

EMBED = 0.1
# branches per design as (position along the arm 0..1, length as a fraction of the radius,
# angle from the arm in degrees); every design is drawn on six arms
DESIGNS = [
    [(0.45, 0.30, 60), (0.72, 0.20, 60)],
    [(0.35, 0.22, 45), (0.60, 0.28, 45), (0.82, 0.14, 45)],
    [(0.55, 0.38, 70)],
    [(0.30, 0.16, 30), (0.55, 0.30, 50), (0.80, 0.18, 60)],
]


def snowflake(p, design):
    R = p.size / 2 - p.arm_w / 2           # stroke centreline radius
    out = circle(0, 0, p.arm_w * 1.2)
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ux, uy = math.cos(a), math.sin(a)
        out += stroke([(0, 0), (R * ux, R * uy)], p.arm_w)
        for t, ln, ang in design:
            bx, by = R * t * ux, R * t * uy
            for s in (1, -1):
                b = a + s * math.radians(ang)
                out += stroke([(bx, by), (bx + R * ln * math.cos(b), by + R * ln * math.sin(b))], p.branch_w)
    # hanging ring at the tip of the top arm (the arm at 90 deg)
    out += circle(0, p.size / 2 - p.ring_d / 2, p.ring_d / 2)
    # fill the sharp notches between arms and branches: they would be thin, fragile teeth
    # in the mold and knife edges in the plaster
    return grow(grow(out, p.notch), -p.notch)


def centres(p):
    c = (p.size + p.gap) / 2
    return [(-c, c), (c, c), (-c, -c), (c, -c)]


def hexagon(r):
    return poly([(r * math.cos(math.radians(60 * i + 30)), r * math.sin(math.radians(60 * i + 30)))
                 for i in range(6)])


def checks(p):
    span = 2 * p.size + 3 * p.gap
    top = p.floor + p.thickness
    hole_y = p.size / 2 - p.ring_d / 2
    pins = [(x, y + hole_y, p.floor + p.thickness / 2) for x, y in centres(p)]
    arms = [(x, y - p.size / 4, p.floor + p.thickness / 2) for x, y in centres(p)]
    return [
        dims(x=(span, span + 2), y=(span, span + 2), z=top),
        fits_bed(),
        solid(*pins),                       # hanging-hole pins stand in every ring
        empty(*arms),                       # the lower arm of each snowflake is cavity
        thickness_at((centres(p)[0][0], centres(p)[0][1], 0.5), p.floor - p.boss_h - 0.2, direction=(0, 0, 1)),
        flat_base(span * span * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    span = 2 * p.size + 3 * p.gap
    top = p.floor + p.thickness
    mold = extrude(grow(CrossSection.square((span - 8, span - 8), center=True), 4), top)
    lean = draft_offset(p.thickness, p.draft)
    pocket_lean = draft_offset(p.boss_h, p.boss_draft)
    pin_lean = draft_offset(p.thickness, 2.0)
    for (cx, cy), design in zip(centres(p), DESIGNS):
        flake = snowflake(p, design)
        mold -= drafted(lambda f: grow(flake, (f - 1) * lean), p.floor, p.thickness + 1, steps=6).translate((cx, cy, 0))
        # hexagon pocket in the floor at the centre: a raised boss on the ornament's face,
        # kept inside the centre disc so it never undercuts the mold floor
        hexr = p.arm_w * 1.2 + 0.2
        mold -= drafted(lambda f: grow(hexagon(hexr), (f - 1) * pocket_lean), p.floor - p.boss_h,
                        p.boss_h + 0.5, steps=3).translate((cx, cy, 0))
        # hanging-hole pin, slightly tapered
        hy = cy + p.size / 2 - p.ring_d / 2
        mold += drafted(lambda f: circle(cx, hy, p.hole_d / 2 + (1 - f) * pin_lean), p.floor - EMBED, p.thickness + EMBED, steps=3)
    return mold
