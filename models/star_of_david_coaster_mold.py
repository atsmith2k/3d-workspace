"""Mold for a 100 mm round coaster in Jesmonite, cement, plaster or resin with an
interlaced Star of David on its face: two triangle bands, each outlined by a pair of
grooves, woven over and under each other at the six crossings, inside a border groove.

The coaster is cast face-down: the mold floor is its decorative face and the ribs on the
floor become grooves in the coaster. The back is the pour side: screed it flat and add
cork or felt pads. Prints opening-up with no supports.

Spec:
  object:       mold for a 100 mm round Star of David coaster, 10 mm thick
  overall:      coaster 100 mm across at its face, 10 mm thick; mold ~107 x 107 x 13 mm
                (fits a 180 mm bed)
  mates with:   nothing
  orientation:  opening up, flat floor on the bed, no supports
  must have:    Star of David 76 mm point to point as two 7 mm triangle bands, each
                outlined by grooves 1.6 wide and 1.0 deep, the under band's grooves
                stopping 0.8 mm short of the over band at the six crossings, alternating
                over / under along each band; border groove 1.6 wide, 6 mm in from the
                edge; 2 deg draft on the wall, 10 deg on the ribs; floor 3, wall 3
  tolerances:   none (casting); the cast is the mirror image of the floor, which only
                swaps which crossings go over (the star itself is symmetric)

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "100 mm round coaster mold with an interlaced Star of David, for Jesmonite or cement"

PRODUCT = dict(
    title="Star of David Coaster Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "plaster", "coaster", "hanukkah",
          "chanukah", "judaica", "star of david", "magen david", "holiday", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="Jesmonite, cement, plaster or resin",
    motif="Star of David",
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    diameter=100.0,     # coaster diameter at its face
    thickness=10.0,
    star=76.0,          # point to point, outer edge of the bands
    band=7.0,           # width of each triangle band
    tip_round=1.5,      # outer band corners rounded to this
    groove_w=1.6,
    groove_depth=1.0,
    weave_gap=0.8,      # under-band grooves stop this far from the over band
    border_inset=6.0,   # border groove, from the coaster edge
    floor=3.0,
    wall=3.0,
    wall_draft=2.0,
    rib_draft=10.0,
)

EMBED = 0.1


def triangle(R, up, rnd=0.0):
    a0 = 90 if up else -90
    pts = [(R * math.cos(math.radians(a0 + 120 * k)), R * math.sin(math.radians(a0 + 120 * k)))
           for k in range(3)]
    cs = poly(pts)
    return grow(grow(cs, -rnd), rnd) if rnd else cs


def band(p, up):
    """One triangle band: outer triangle (circumradius star/2) minus the inner one."""
    R = p.star / 2
    R_in = R - 2 * p.band               # circumradius = 2 x inradius for a triangle
    return triangle(R, up, p.tip_round) - triangle(R_in, up)


def lines(p, up):
    """The two grooves outlining a band (its outer and inner edges)."""
    b = band(p, up)
    return b - grow(b, -p.groove_w)


def crossings():
    """Crossings of the two triangles (the inner hexagon corners), with which band goes
    over: walking round the up triangle they alternate, starting over at 120 deg."""
    return [(a, a in (0, 120, 240)) for a in range(0, 360, 60)]   # (angle, up band is over)


def star_ribs(p):
    up, dn = lines(p, True), lines(p, False)
    b_up, b_dn = band(p, True), band(p, False)
    r_hex = (p.star / 2 - p.band) / math.sqrt(3)   # where the band centre lines cross
    for a, up_over in crossings():
        cx, cy = r_hex * math.cos(math.radians(a)), r_hex * math.sin(math.radians(a))
        zone = circle(cx, cy, 1.4 * p.band)    # this crossing only, clear of its neighbours
        if up_over:
            dn -= grow(b_up, p.weave_gap) ^ zone
        else:
            up -= grow(b_dn, p.weave_gap) ^ zone
    return up + dn


def border(p):
    r = p.diameter / 2 - p.border_inset
    return circle(0, 0, r) - circle(0, 0, r - p.groove_w)


def rib(cs, p):
    lean = draft_offset(p.groove_depth, p.rib_draft)
    return drafted(lambda f: grow(cs, -f * lean), p.floor - EMBED, p.groove_depth + EMBED, steps=3)


def checks(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    out = p.diameter + 2 * (lean + p.wall)
    R = p.star / 2
    zg = p.floor + p.groove_depth / 2
    return [
        dims(x=(out - 1, out + 1), y=(out - 1, out + 1), z=p.floor + p.thickness),
        fits_bed(),
        # outer groove of the up band along its bottom edge, and its inner groove
        solid((0, -R / 2 + p.groove_w / 2, zg), (0, -R / 2 + p.band - p.groove_w / 2, zg)),
        # border groove; centre of the star and the middle of a band are bare floor
        solid((0, p.diameter / 2 - p.border_inset - p.groove_w / 2, zg)),
        empty((0, 0, p.floor + 0.5), (0, -R / 2 + p.band / 2, p.floor + 0.5),
              (0, p.diameter / 2 - 2, p.floor + p.thickness - 1)),
        thickness_at((0, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(math.pi * (p.diameter / 2) ** 2 * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    lean = draft_offset(p.thickness, p.wall_draft)
    r = p.diameter / 2
    mold = extrude(circle(0, 0, r + lean + p.wall), p.floor + p.thickness)
    mold -= tapered(circle(0, 0, r), p.floor, p.thickness + 1, lean * (p.thickness + 1) / p.thickness)
    mold += rib(star_ribs(p), p)
    mold += rib(border(p), p)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the coaster, face up."""
    return cast_of(build(p))
