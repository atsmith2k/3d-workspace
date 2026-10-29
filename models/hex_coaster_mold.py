"""Mold for a coaster in Jesmonite, plaster, a terrazzo mix or resin, with two grooves on
its face that follow the outline: a 100 mm hexagon, or a 105 x 89 mm heart (see the title).

The coaster is 10 mm thick, and the back is the pour side: screed it flat and add cork
or felt pads. Make a set in different colours, or pair it with the oak leaf coaster mold.
Prints opening-up with no supports in under an hour on a Bambu A1 or A1 mini.

Spec:
  object:       mold for a 100 mm hexagon coaster, 10 mm thick
  overall:      coaster 100 mm across the flats (115.5 across the corners);
                mold ~108 x 123 x 13 mm (fits the A1 mini)
  mates with:   nothing
  orientation:  opening up, flat floor on the bed, no supports
  heart:        shape=heart: a 105 x 89 mm heart, grooves 9 and 18 mm in, following
                the outline; mold ~112 x 96 x 13 mm (build with --set ring_insets=9,18)
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
    title="{shape} Coaster Mold",               # filled from params per variant
    category="molds",
    tags=["mold", "coaster", "hexagon", "jesmonite", "plaster", "terrazzo", "resin",
          "geometric", "heart", "valentine", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="Jesmonite, plaster or resin",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    shape="hexagon",    # hexagon | heart (a heart is 1.05 x flats wide, rings follow its outline)
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


def outline(p, inset=0.0):
    """The coaster's face outline, `inset` mm in from the edge (a groove ring's outside)."""
    if p.shape == "heart":
        h = heart(p.flats * 1.05)
        return grow(h, -inset) if inset else h
    return hexagon(p.flats - 2 * inset, p.corner)


def ring(p, inset):
    if p.shape == "heart":
        return outline(p, inset) - outline(p, inset + p.groove_w)
    f_out = p.flats - 2 * inset
    return hexagon(f_out, p.corner) - hexagon(f_out - 2 * p.groove_w, max(p.corner - p.groove_w, 0.5))


def checks(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    if p.shape == "heart":
        import numpy as np
        w = p.flats * 1.05 + 2 * (lean + p.wall)
        out = [
            dims(x=(w - 1, w + 1), z=p.floor + p.thickness),
            empty((0, 0, p.floor + 1)),
            thickness_at((0, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
            flat_base(p.flats ** 2 * 0.5),
            no_overhang(),
            single_body(),
        ]
        if p.pattern == "rings":
            x, y = np.asarray(outline(p, p.ring_insets[0] + p.groove_w / 2).to_polygons()[0][0], float)
            out.append(solid((float(x), float(y), p.floor + p.groove_depth / 2)))
        return out
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
    if p.shape == "heart":
        mold = extrude(grow(outline(p), lean + p.wall), p.floor + p.thickness)
    else:
        mold = extrude(hexagon(p.flats + 2 * (lean + p.wall), p.corner + p.wall), p.floor + p.thickness)
    mold -= tapered(outline(p), p.floor, p.thickness + 1, lean * (p.thickness + 1) / p.thickness)
    if p.pattern == "rings":
        rib_lean = draft_offset(p.groove_depth, p.rib_draft)
        for inset in p.ring_insets:
            r = ring(p, inset)
            mold += drafted(lambda f: grow(r, -f * rib_lean), p.floor - EMBED, p.groove_depth + EMBED, steps=3)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the coaster, face up."""
    return cast_of(build(p))
