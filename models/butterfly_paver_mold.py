"""Mold for a 5 in (127 mm) cement garden paver in the shape of a butterfly.

The finished paver is a butterfly silhouette about 1 in thick, its face carrying a fine
border line, wing veins, two spots on each forewing and an eyespot on each hindwing,
all cast as crisp grooves, with the body standing slightly proud. Pour cement, let it
cure, flex the mold and lift it off. Every wall and rib is drafted so the paver releases
cleanly, and the mold prints opening-up with no supports in about ten hours on a Bambu
A1 or A1 mini.

A square variant (`style=square`, 5 x 5 in) raises the whole butterfly on a square
paver and adds grooved antennae.

Spec:
  object:       open-top mold for a 5 in cement paver shaped like a butterfly (or a
                square paver with a raised butterfly), cast face-down
  overall:      about 137 x 129 x 30 mm (shaped), 137 x 137 x 30 mm (square); floor 5,
                wall 4, cavity 25.4 deep
  casting:      127 mm wide, 25.4 mm (1 in) thick paver; veins, border, spots and
                eyespots grooved 2 mm deep and 1.9 mm wide; body raised 2 mm
  orientation:  flat base on the bed, cavity opening up; supports expected: none
  must have:    2 deg draft on the cavity wall, 10 deg on the ribs; the slits between
                body and hindwings and between fore- and hindwing are webbed over so no
                mold wall is thinner than 1.2 mm
  tolerances:   none (no mating parts)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "5 in cement paver mold with butterfly relief (shaped or square)"

PRODUCT = dict(
    title="Butterfly Paver Mold",
    category="molds",
    tags=["mold", "paver", "cement", "garden", "butterfly"],
    printers=["a1", "a1mini"],
    cast_material="cement",
)
LICENSE_NOTES = None   # original artwork; the default licence applies


def checks(p):
    wing = (30, 30)   # a point well inside the right forewing
    return [
        dims(z=p.floor + p.thickness),
        solid((*wing, 1.0)),                                   # floor under the wing
        thickness_at((*wing, 1.0), p.floor - p.detail_depth),  # floor left under a pocket
        empty((*wing, p.floor + p.detail_depth + 5)),          # cavity above the art
        empty((0, 0, p.floor + p.thickness - 1)),              # opening is open at the top
        flat_base(5000),
        no_overhang(),
        single_body(),
    ]

PARAMS = dict(
    style="shaped",       # shaped | square
    size=127.0,           # paver width (mm); the art is scaled to fit
    thickness=25.4,       # paver thickness = cavity depth
    floor=5.0,            # mold floor under the cavity
    wall=4.0,             # mold wall thickness
    wall_draft=2.0,       # degrees; cavity widens toward the opening
    detail_depth=2.0,     # groove depth / raised height on the paver face
    line_width=1.9,       # vein groove width at the paver surface
    rib_draft=10.0,       # degrees on the ribs that form grooves
)

# Right half of the butterfly in a 127 mm-wide design space; mirrored about X=0.
ART_WIDTH = 127.0
FOREWING = [(3, 9), (12, 31), (30, 51), (50, 61), (62, 59), (63, 46), (55, 26), (40, 9), (20, 3), (4, 1)]
HINDWING = [(4, 1), (20, -1), (40, -9), (52, -24), (50, -41), (38, -54), (22, -57), (12, -49), (5, -29), (3, -9)]
VEINS = [  # quadratic bezier (start, control, end); ends overshoot and get clipped
    ((4, 6), (30, 41), (70, 67)),
    ((4, 5), (40, 36), (72, 51)),
    ((4, 4), (45, 26), (70, 33)),
    ((4, 3), (40, 13), (60, 17)),
    ((4, -1), (30, -9), (62, -21)),
    ((4, -2), (35, -19), (60, -41)),
    ((4, -3), (28, -29), (45, -64)),
    ((4, -4), (18, -34), (24, -69)),
]
FORE_SPOTS = [(51, 48, 4.0), (42, 53, 2.4)]
EYESPOT = (33, -39, 6.0, 3.8, 1.6)  # x, y, ring outer r, ring inner r, pupil r
ANTENNA = ((1.5, 39), (6, 56), (18, 63))
ANTENNA_TIP_R = 2.0
TIP_ROUND = 0.55   # opening radius on clipped vein ends (removes slivers under 1.1 wide)
EMBED = 0.1


def wings():
    return mirror_x(smooth_shape(FOREWING) + smooth_shape(HINDWING))


def body():
    return ellipse(0, -2, 5.0, 33.0) + circle(0, 35.5, 5.2)


WEB_RADIUS = 3.0         # closes any slit narrower than 2x this anywhere on the outline
WEB_RADIUS_LOWER = 6.0   # and wider ones below the forewings (tail and wing junction)


def silhouette():
    """Wings and body as one outline for the cavity. The slits between the body and
    each wing root, and between fore- and hindwing near the body, are only 1-3 units
    wide: in the mold they would be fins under 1.2 mm. A morphological closing
    (grow, then shrink) webs them over; the stronger closing is limited to below the
    forewings so the head keeps its shape."""
    shape = wings() + body()
    closed = grow(grow(shape, WEB_RADIUS), -WEB_RADIUS)
    closed_low = grow(grow(shape, WEB_RADIUS_LOWER), -WEB_RADIUS_LOWER)
    lower = CrossSection.square((160, 80), center=True).translate((0, -32))
    return shape + closed + (closed_low ^ lower)


def pattern(widen, line_width, border):
    """2D art grooved into the paver face; `widen` < 0 narrows it for the rib draft."""
    ex, ey, ro, ri, rp = EYESPOT
    keep_out = grow(body(), 1.5) + mirror_x(
        circle(ex, ey, ro + 1.5) + sum((circle(x, y, r + 1.5) for x, y, r in FORE_SPOTS), CrossSection()))
    # the clip region moves with `widen` too, so clipped vein ends get draft as well
    region = grow(wings(), -5.0 + widen) - grow(keep_out, -widen)
    veins = CrossSection()
    for v in VEINS:
        veins += mirror_x(stroke(bezier(*v), line_width + 2 * widen))
    # clipping a stroke obliquely leaves a sharp tip thinner than a printable rib;
    # an opening (shrink, then grow) rounds those off and keeps the full-width strokes
    art = grow(grow(veins ^ region, -TIP_ROUND), TIP_ROUND)
    for x, y, r in FORE_SPOTS:
        art += mirror_x(circle(x, y, r + widen))
    art += mirror_x(circle(ex, ey, ro + widen) - circle(ex, ey, ri - widen) + circle(ex, ey, rp + widen))
    if border:
        art += grow(wings(), -4.0 + widen) - grow(wings(), -4.0 - line_width - widen)
    return art


def antennae(widen, line_width):
    stalk = stroke(bezier(*ANTENNA, n=20), line_width + 2 * widen)
    tip = circle(*ANTENNA[-1], ANTENNA_TIP_R + widen)
    return mirror_x(stalk + tip) - grow(wings() + body(), 0.8)


def build(p):
    k = p.size / ART_WIDTH
    d = p.detail_depth
    lean = draft_offset(p.thickness, p.wall_draft)
    rib_lean = draft_offset(d, p.rib_draft)

    def scaled(cs, s):
        return cs.scale((s, s))

    if p.style == "shaped":
        art_k = k
        outline = scaled(silhouette(), k)
        shell = extrude(grow(outline, lean + p.wall), p.floor + p.thickness)
        relief = body()               # raised on the paver -> pocket in the floor
        lines = lambda w: pattern(w, p.line_width / art_k, border=True)
        line_height = d
    elif p.style == "square":
        art_k = k * 0.84
        outline = grow(CrossSection.square((p.size - 6, p.size - 6), center=True), 3.0)
        shell = extrude(grow(outline, lean + p.wall), p.floor + p.thickness)
        relief = silhouette()         # whole butterfly raised on the paver
        lines = lambda w: pattern(w, p.line_width / art_k, border=False)
        line_height = d * 0.7         # grooves cut into the raised butterfly
    else:
        raise ValueError(f"style must be 'shaped' or 'square', not {p.style!r}")

    mold = shell - drafted(lambda f: grow(outline, f * lean), p.floor, p.thickness + 1, steps=18)
    mold -= drafted(lambda f: grow(scaled(relief, art_k), -0.4 + f * 0.4), p.floor - d, d + 0.01, steps=4)
    # ribs start EMBED below the surface they stand on so the union never has
    # coplanar faces (those leave zero-area slivers in the mesh)
    rib_floor = (p.floor if p.style == "shaped" else p.floor - d) - EMBED
    mold += drafted(lambda f: scaled(lines(-f * rib_lean / art_k), art_k),
                    rib_floor, line_height + EMBED, steps=4)
    if p.style == "square":
        mold += drafted(lambda f: scaled(antennae(-f * rib_lean / art_k, p.line_width / art_k), art_k),
                        p.floor - EMBED, d * 0.8 + EMBED, steps=4)
    return mold
