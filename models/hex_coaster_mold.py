"""Mold for a 100 mm hexagon coaster in Jesmonite, plaster, a terrazzo mix or resin, with
two concentric hexagon grooves on its face.

The coaster is 10 mm thick, and the back is the pour side: screed it flat and add cork
or felt pads. Make a set in different colours, or pair it with the oak leaf coaster mold.
Prints opening-up with no supports in about 4 hours on a Bambu A1 or A1 mini.

Spec:
  object:       mold for a 100 mm hexagon coaster, 10 mm thick
  overall:      coaster 100 mm across the flats (115.5 across the corners);
                mold ~108 x 123 x 13 mm (fits the A1 mini)
  mates with:   nothing
  orientation:  opening up, flat floor on the bed, no supports
  must have:    pattern "rings" (two hexagon grooves 1.0 deep, 1.6 wide, 10 and 22 mm in
                from the edge) or "plain"; 4 mm rounded corners; 2 deg draft on the wall,
                10 deg on the ribs; floor 3, wall 3
  tolerances:   none (casting)

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "100 mm hexagon coaster mold with concentric grooves, for Jesmonite or plaster"

PRODUCT = dict(
    title="Hexagon Coaster Mold",
    category="molds",
    tags=["mold", "coaster", "hexagon", "jesmonite", "plaster", "terrazzo", "resin",
          "geometric", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="Jesmonite, plaster or resin",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    pattern="rings",    # rings | plain
    flats=100.0,        # coaster size across the flats, at its face
    thickness=10.0,
    corner=4.0,
    ring_insets=(10.0, 22.0),
    groove_depth=1.0,
    groove_w=1.6,
    floor=3.0,
    wall=3.0,
    wall_draft=2.0,
    rib_draft=10.0,
)

EMBED = 0.1


def hexagon(flats, corner):
    """Hexagon with flats parallel to X, `flats` across, corners rounded to `corner`."""
    r = (flats / 2 - corner) / math.cos(math.pi / 6)
    pts = [(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i))) for i in range(6)]
    return grow(poly(pts), corner)


def checks(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    y_out = p.flats + 2 * (lean + p.wall)
    x_out = y_out / math.cos(math.pi / 6)
    inset = p.ring_insets[0] + p.groove_w / 2 if p.pattern == "rings" else 0
    out = [
        dims(y=(y_out - 1, y_out + 1), x=(x_out - 3, x_out + 1), z=p.floor + p.thickness),
        empty((0, 0, p.floor + 1), (0, p.flats / 2 - 2, p.floor + p.thickness - 1)),
        thickness_at((0, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(p.flats ** 2 * 0.8),
        no_overhang(),
        single_body(),
    ]
    if p.pattern == "rings":
        out.append(solid((0, p.flats / 2 - inset, p.floor + p.groove_depth / 2)))
    return out


def build(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    mold = extrude(hexagon(p.flats + 2 * (lean + p.wall), p.corner + p.wall), p.floor + p.thickness)
    mold -= tapered(hexagon(p.flats, p.corner), p.floor, p.thickness + 1, lean * (p.thickness + 1) / p.thickness)
    if p.pattern == "rings":
        rib_lean = draft_offset(p.groove_depth, p.rib_draft)
        for inset in p.ring_insets:
            f_out = p.flats - 2 * inset
            ring = hexagon(f_out, p.corner) - hexagon(f_out - 2 * p.groove_w, max(p.corner - p.groove_w, 0.5))
            mold += drafted(lambda f: grow(ring, -f * rib_lean), p.floor - EMBED, p.groove_depth + EMBED, steps=3)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the coaster, face up."""
    return cast_of(build(p))
