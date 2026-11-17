"""Mold for a 6.5 in (165 mm) square cement garden paver lettered
"Home is / wherever / I'm with you / 11.06.2026".

The finished stepping stone is a plain square slab with softly rounded corners; its
face carries the four lines of handwritten-style lettering (Segoe Print Bold) cast as
grooves, like the hand-etched look of the reference photo. On the mold the lettering is
raised ribs on the floor, mirrored so it reads correctly on the paver. Pour cement,
vibrate, cure, flex the mold and lift it off.

Release (designed for a rigid PETG print, which barely flexes): the cavity wall has 5 deg
of draft, the floor meets the wall in a 3 mm round instead of a sharp inside corner (the
stone's face edge comes out softly rounded), the corners are 6 mm radius, the outer wall
leans with the cavity so the wall is a uniform 4 mm, and the letter ribs have 15 deg draft
on a 0.4 mm flared foot so the grooves have no sharp lip for cement to grab or chip.

Spec:
  object:       open-top mold for a 6.5 x 6.5 in square cement paver, cast face-down,
                lettering grooved into the paver face
  overall:      about 178.4 x 178.4 x 30.4 mm at the rim (173.1 at the base); floor 5,
                wall 4 (uniform, both faces drafted), cavity 25.4 deep
  casting:      165.1 x 165.1 mm (6.5 in) at the face, 25.4 mm (1 in) thick, 6 mm corner
                radius, 3 mm rounded face edge, back 4.4 mm wider (5 deg draft); lettering grooved 2 mm deep, widest line about 142 mm across, 4 lines
                centred: "Home is", "wherever", "I'm with you" (22.5 mm font size) and the
                date "11.06.2026" (19 mm); strokes thickened 0.25 mm per side
  orientation:  flat base on the bed, cavity opening up; supports expected: none
  must have:    5 deg draft on the cavity wall, 3 mm floor-edge round, 15 deg on the letter
                ribs with a 0.4 mm root flare; text mirrored on
                the mold floor; ribs at least 1.2 mm wide at the top; fits the A1 mini
  tolerances:   none (no mating parts)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
import numpy as np

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "6.5 in square cement paver mold lettered 'Home is wherever I'm with you' + date"

PRODUCT = dict(
    title="Home Is Wherever I'm With You Paver Mold",
    category="molds",
    tags=["mold", "paver", "cement", "garden", "stepping stone", "wedding", "anniversary"],
    printers=["a1", "a1mini"],
    cast_material="cement",
    sellable=False,   # personalised date; Segoe Print is a Microsoft font, licence unchecked
)
LICENSE_NOTES = ("Lettering set in Segoe Print Bold (Microsoft, ships with Windows); "
                 "check its licence before selling castings or files commercially.")

FONT = "C:/Windows/Fonts/segoeprb.ttf"

PARAMS = dict(
    size=165.1,           # paver width at the face (6.5 in)
    thickness=25.4,       # paver thickness = cavity depth (1 in)
    floor=5.0,            # mold floor under the cavity
    wall=4.0,             # mold wall thickness at the rim
    wall_draft=5.0,       # degrees; cavity widens toward the opening (PETG: no flex)
    corner=6.0,           # paver corner radius
    edge_round=3.0,       # radius where the floor meets the wall (stone's face edge)
    detail_depth=2.0,     # groove depth on the paver face = rib height
    rib_draft=15.0,       # degrees on the letter ribs
    rib_foot=0.4,         # extra width at the rib root, easing out over the lower 40%
    text_size=22.5,       # font size for the three quote lines
    date_size=19.0,       # font size for the date
    line_pitch=31.0,      # baseline to baseline
    date_gap=3.0,         # extra space above the date
    bold=0.25,            # extra stroke width per side so the rib tops stay > 1.2 mm
    line1="Home is",
    line2="wherever",
    line3="I\u2019m with you",
    date="11.06.2026",
)

EMBED = 0.1


def checks(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    outer = p.size + 2 * (p.wall + lean * (p.floor + p.thickness) / p.thickness)   # at the rim
    h = p.size / 2
    return [
        dims(x=outer, y=outer, z=p.floor + p.thickness),
        solid((h - 6, h - 6, p.floor - 0.5)),                # plain floor in a corner
        thickness_at((h - 6, h - 6, 1.0), p.floor - 0.2),    # floor thickness
        empty((h - 6, h - 6, p.floor + 0.5)),                # cavity right above the floor
        empty((0, 0, p.floor + p.detail_depth + 1)),         # nothing above the ribs
        empty((0, 0, p.floor + p.thickness - 1)),            # open at the top
        solid((h + lean + p.wall / 2, 0, p.floor + p.thickness - 1)),  # wall at the rim
        solid((h - 0.4, 0, p.floor + 0.4)),                  # floor-edge round is there
        empty((h - p.edge_round, 0, p.floor + 0.3)),         # ...and only that wide
        thickness_at((h + p.wall / 2 + lean / 2, 0, p.floor + p.thickness / 2), p.wall - 0.3),
        flat_base(p.size ** 2 * 0.9),
        no_overhang(),
        single_body(),
        fits_bed(),
    ]


def line_text(string, size):
    """One line of text as a CrossSection with its baseline on y=0, centred in x."""
    from build123d import Align, Text, extrude as _extrude
    from manifold3d import Mesh
    from cadkit.mesh import to_trimesh
    sk = Text(string, font_size=size, font_path=FONT, align=(Align.CENTER, Align.NONE))
    tm = to_trimesh(_extrude(sk, amount=1.0), tolerance=0.02)
    m = Manifold(Mesh(vert_properties=tm.vertices.astype(np.float32),
                      tri_verts=tm.faces.astype(np.uint32)))
    cs = m.slice(0.5)
    x0, _, x1, _ = cs.bounds()
    return cs.translate((-(x0 + x1) / 2, 0))


def lettering(p):
    """The four lines as they read on the paver face, centred on the origin."""
    lines = [(p.line1, p.text_size), (p.line2, p.text_size), (p.line3, p.text_size)]
    art = CrossSection()
    y = 0.0
    for s, size in lines:
        art += line_text(s, size).translate((0, y))
        y -= p.line_pitch
    art += line_text(p.date, p.date_size).translate((0, y - p.date_gap))
    x0, y0, x1, y1 = art.bounds()
    return art.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def square(size, r):
    return grow(CrossSection.square((size - 2 * r, size - 2 * r), center=True), r)


def build(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    rib_lean = draft_offset(p.detail_depth, p.rib_draft)
    r = p.edge_round
    outline = square(p.size, p.corner)
    top = p.floor + p.thickness
    # outer wall leans with the cavity: uniform wall, less plastic, a little flex
    shell = tapered(grow(outline, p.wall), 0, top, lean * top / p.thickness)
    # cavity: drafted wall from the top of the edge round up through the rim
    z_wall = p.floor + r
    wall_lean = lean * (r / p.thickness)          # draft already gained below z_wall
    mold = shell - tapered(grow(outline, wall_lean), z_wall - 0.05, top - z_wall + 1.05,
                           lean * (top - z_wall + 1) / p.thickness)

    # quarter-round from the floor to the wall, one slice per 0.2 mm layer
    def round_at(f):
        h = f * r
        inset = r - np.sqrt(max(r * r - (r - h) ** 2, 0.0))
        return grow(outline, -inset + lean * h / p.thickness)
    mold -= drafted(round_at, p.floor, r + 0.05, steps=int(round(r / 0.2)))

    art = grow(lettering(p), p.bold).mirror((1, 0))   # mirrored: the paver is the floor's mirror image

    def rib_at(f):
        foot = p.rib_foot * max(0.0, 1 - f / 0.4) ** 2
        return grow(art, foot - f * rib_lean)
    # ribs start EMBED below the floor so the union has no coplanar faces
    mold += drafted(rib_at, p.floor - EMBED, p.detail_depth + EMBED, steps=10)
    return mold


def casting(p):
    return cast_of(build(p))
