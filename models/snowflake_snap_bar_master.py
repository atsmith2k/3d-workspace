"""Silicone mold master for a snowflake wax melt snap bar: a printed mold box with one
4 x 2 in (102 x 51 mm), 1/2 in (12.7 mm) thick bar inside, split into six snap-apart
segments by V-grooves, each segment carrying its own raised snowflake.

The master is the wax bar itself (a positive): pour silicone into the box to just over
the rim, let it cure and peel it out, and you have a snap-bar mold. The bar's top face
here becomes the silicone cavity floor, so the snowflakes and the snap grooves come out
on the face of the wax bar (the side you see), and the pour side stays flat. The bar
walls lean in 2 deg towards the face so the wax releases from the silicone. Prints in
one piece, open side up, with no supports.

Spec:
  object:       one-piece silicone mold master (positive + mold box) for a 6-segment wax melt snap bar
  overall:      bar 102 x 51 x 12.7 mm at the face (4 x 2 x 0.5 in); box 122.8 x 71.8 x 20.7 mm
  casting:      silicone 8 mm round the bar, 6 mm over its face; bar walls 2 deg draft,
                3 mm rounded vertical corners; bar 102.9 x 51.9 mm at the pour side
  orientation:  floor on the bed, opening up; no supports
  must have:    6 segments in a 3 x 2 grid (34 x 25.5 mm each); V snap grooves 2.5 mm deep,
                3 mm wide at the face, between every segment; six different snowflakes,
                19 mm across, raised 0.8 mm, arms 1.6 mm and branches 1.3 mm wide;
                silicone volume reported by the build
  tolerances:   none (casting)

Units: mm. Z is up, the part sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Silicone mold master for a 6-segment snowflake wax melt snap bar (4 x 2 in)"

PRODUCT = dict(
    title="Snowflake Wax Melt Snap Bar Silicone Mold Master",
    category="molds",
    tags=["mold", "silicone mold", "wax melt mold", "snap bar", "snap bar mold", "mold master",
          "wax melts", "candle making", "snowflake", "christmas", "winter", "holiday"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then wax",
    post_processing=("Brush a sealer or spray release over the master; the silicone copies layer "
                     "lines. Mix about 85 ml of silicone, pour slowly into one corner until it "
                     "covers the bar by about 6 mm, and demold after full cure. Pour wax to the "
                     "rim of the cavity; the snowflake face comes out on the bottom."),
    draft=True,          # goes to the shop's Draft Products review queue
    price=5.99,          # suggested listing price (USD), market band 4.99-6.99
)
LICENSE_NOTES = None   # original artwork

PARAMS = dict(
    bar_l=102.0,        # bar length at the face (4 in)
    bar_w=51.0,         # bar width at the face (2 in)
    bar_h=12.7,         # bar thickness (1/2 in)
    cols=3,             # segments along the length
    rows=2,             # segments across the width
    corner=3.0,         # bar vertical corner radius
    draft=2.0,          # draft on the bar walls, degrees
    groove_d=2.5,       # snap groove depth
    groove_w=3.0,       # snap groove width at the face
    flake=19.0,         # snowflake size, tip to tip
    arm=1.6,            # snowflake arm line width
    branch=1.3,         # snowflake branch line width
    relief=0.8,         # snowflake height above the face
    gap=8.0,            # silicone round the bar
    back=6.0,           # silicone over the bar face
    floor=2.0,
    wall=2.4,
    box_corner=4.0,
)

EMBED = 0.1

# Six designs: branches as (position along the arm 0..1, length as a fraction of the
# radius, angle from the arm in degrees), plus the centre ("disc" or "hex").
DESIGNS = [
    ([(0.45, 0.32, 55), (0.75, 0.20, 55)], "disc"),
    ([(0.35, 0.22, 45), (0.60, 0.28, 45), (0.85, 0.12, 45)], "hex"),
    ([(0.55, 0.40, 65)], "disc"),
    ([(0.30, 0.18, 35), (0.58, 0.30, 50), (0.82, 0.16, 60)], "hex"),
    ([(0.40, 0.36, 60)], "hex"),
    ([(0.50, 0.30, 30), (0.78, 0.22, 75)], "disc"),
]


def hexagon(r, rot=30.0):
    return poly([(r * math.cos(math.radians(rot + 60 * i)), r * math.sin(math.radians(rot + 60 * i)))
                 for i in range(6)])


def snowflake(p, design):
    branches, centre = design
    R = p.flake / 2 - p.arm / 2
    out = CrossSection()
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ux, uy = math.cos(a), math.sin(a)
        out += stroke([(0, 0), (R * ux, R * uy)], p.arm)
        for t, ln, ang in branches:
            bx, by = R * t * ux, R * t * uy
            for s in (1, -1):
                b = a + s * math.radians(ang)
                out += stroke([(bx, by), (bx + R * ln * math.cos(b), by + R * ln * math.sin(b))], p.branch)
    if centre == "disc":
        out += circle(0, 0, p.arm * 1.4)
    else:
        out += hexagon(p.arm * 2.2) - hexagon(p.arm * 2.2 - p.branch)
    # round the sharp notches between arms and branches: thin silicone teeth tear
    return grow(grow(out, 0.3), -0.3)


def seg_size(p):
    return p.bar_l / p.cols, p.bar_w / p.rows


def centres(p):
    sx, sy = seg_size(p)
    return [((i - (p.cols - 1) / 2) * sx, ((p.rows - 1) / 2 - j) * sy)
            for j in range(p.rows) for i in range(p.cols)]


def groove_lines(p):
    """('x', pos) is a groove across the bar at x=pos; ('y', pos) runs along it at y=pos."""
    sx, sy = seg_size(p)
    return ([("x", (i - p.cols / 2) * sx) for i in range(1, p.cols)] +
            [("y", (j - p.rows / 2) * sy) for j in range(1, p.rows)])


def box_size(p):
    return p.bar_l + 2 * p.gap, p.bar_w + 2 * p.gap


def v_groove(p, length):
    """V prism along Y, apex at z=-groove_d, opening at z=0 (extended 1 mm above)."""
    d, hw = p.groove_d, p.groove_w / 2
    up = 1.0
    tri = poly([(-hw * (up + d) / d, up), (0, -d), (hw * (up + d) / d, up)])
    if tri.area() < 0:
        tri = poly([(hw * (up + d) / d, up), (0, -d), (-hw * (up + d) / d, up)])
    return extrude(tri, length, -length / 2).rotate((90, 0, 0))


def bar(p):
    """The wax bar as the master's raised shape, pour side on z=0, face on top."""
    lean = draft_offset(p.bar_h, p.draft)
    sq = grow(CrossSection.square((p.bar_l - 2 * p.corner + 2 * lean, p.bar_w - 2 * p.corner + 2 * lean),
                                  center=True), p.corner)
    body = tapered(sq, 0, p.bar_h, -lean)
    for axis, pos in groove_lines(p):
        if axis == "x":
            body -= v_groove(p, p.bar_w + 10).translate((pos, 0, p.bar_h))
        else:
            body -= v_groove(p, p.bar_l + 10).rotate((0, 0, 90)).translate((0, pos, p.bar_h))
    art = CrossSection()
    for k, (x, y) in enumerate(centres(p)):
        art += snowflake(p, DESIGNS[k % len(DESIGNS)]).translate((x, y))
    body += extrude(art, p.relief + EMBED, p.bar_h - EMBED)
    return body


def silicone_ml(p):
    bx, by = box_size(p)
    fill = bx * by * (p.bar_h + p.back) - (4 - math.pi) * p.box_corner ** 2 * (p.bar_h + p.back)
    return (fill - bar(p).volume()) / 1000.0


def checks(p):
    bx, by = box_size(p)
    top = p.floor + p.bar_h + p.back
    face = p.floor + p.bar_h
    ml = silicone_ml(p)
    sx, sy = seg_size(p)
    gx = groove_lines(p)[0][1]                      # first cross groove
    off_y = centres(p)[0][1] + sy / 2 - 3.0         # near a segment edge, clear of the flake
    return [
        dims(x=bx + 2 * p.wall, y=by + 2 * p.wall, z=top),
        fits_bed(),
        solid(*[(x, y, p.floor + p.bar_h / 2) for x, y in centres(p)]),
        solid(*[(x, y, face + p.relief / 2) for x, y in centres(p)]),   # flake centres raised
        empty((p.bar_l / 2 + p.gap / 2, 0, p.floor + 1), (0, p.bar_w / 2 + p.gap / 2, p.floor + 1)),
        # snap groove: open just under the face, solid below its apex
        empty((gx, off_y, face - 0.4), (centres(p)[0][0], 0, face - 0.4)),
        solid((gx, off_y, face - p.groove_d - 0.5)),
        custom("silicone to mix", lambda ctx: (True, f"{ml:.0f} ml (about {ml * 1.1:.0f} g)")),
        flat_base(bx * by * 0.95),
        no_overhang(),
        single_body(),
    ]


def build(p):
    bx, by = box_size(p)
    top = p.floor + p.bar_h + p.back
    c = p.box_corner
    outer = grow(CrossSection.square((bx - 2 * c, by - 2 * c), center=True), c + p.wall)
    inner = grow(CrossSection.square((bx - 2 * c, by - 2 * c), center=True), c)
    mold = extrude(outer, top) - extrude(inner, top + 1, p.floor)
    return mold + bar(p).translate((0, 0, p.floor - EMBED))


def casting(p):
    """What the mold makes, for the shop's cast render: the snap bar, snowflake face up."""
    return bar(p)
