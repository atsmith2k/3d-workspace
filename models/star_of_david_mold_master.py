"""Silicone mold master for a Star of David: the finished cast is a six-pointed star
102 mm (4 in) point to point and 25 mm (1 in) thick, with crisp points and a flat back,
for casting in concrete, Jesmonite, plaster or wax (a big wax melt). It pairs with the
Hanukkah Menorah mold.

The print is a one-piece master: the star stands on a 2 mm floor inside a star-shaped
pour wall that follows its outline 10 mm away. Pour silicone into the wall until it
covers the star by about 6 mm, let it cure and peel it out: the silicone is a one-cavity
star mold. Cast into it face down; the screeded open side becomes the star's flat back.
The star narrows 2 deg toward its face and the pour wall flares 2 deg so both release.
Prints floor down with no supports.

Spec:
  object:       one-piece silicone mold master (positive star + pour wall) for a cast
                Star of David
  overall:      star 102 mm point to point (4 in), 25 mm thick (1 in); master about
                110 x 127 x 33 mm, fits the A1 mini
  casting:      cast = the star; back (flat, open face of the silicone) 102 mm point to
                point, face 2 deg smaller (about 100.3 mm); silicone 10 mm round the star
                at its base, 6 mm over its face
  mates with:   nothing (cast in silicone made from it)
  orientation:  floor on the bed, star and pour wall up; no supports
  must have:    hexagram of two equilateral triangles, one point up; 2 deg draft on the
                star sides and on the pour wall; points rounded 1.5 mm at the back,
                about 0.6 mm at the face so the tips stay >= 1.2 mm; flat 2 mm floor;
                pour wall 2.4 mm; silicone needed reported by the build
  tolerances:   none (casting)

Units: mm. Z is up, the part sits on Z=0. The star's points lie on +-Y (one point up).
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Silicone mold master for a 4 in (102 mm) Star of David, 1 in thick, with pour wall"

PRODUCT = dict(
    title="Star of David Mold Master",
    category="molds",
    tags=["mold master", "silicone mold", "star of david", "hanukkah", "chanukah", "judaica",
          "concrete mold", "jesmonite", "wax melt mold", "candle mold", "holiday decor"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then concrete, Jesmonite, "
                  "plaster or wax",
    post_processing=("Brush a sealer or spray release over the master; the silicone copies layer "
                     "lines. Mix about 150 ml of silicone, pour slowly into one corner until it "
                     "covers the star by about 6 mm, and demold after full cure. Cast face down "
                     "and screed the open side flat for a level back."),
    draft=True,       # goes to the shop's Draft Products review queue
    price=5.99,       # suggested, within the $4.99-6.99 band for mold masters
)
LICENSE_NOTES = None   # original design (the hexagram itself is a traditional symbol)

PARAMS = dict(
    span=101.6,         # star point to point at its back (4 in)
    thickness=25.4,     # star thickness (1 in)
    tip_r=1.5,          # point rounding at the back; the face gets tip_r - draft lean
    draft=2.0,          # degrees, star sides and pour wall
    gap=10.0,           # silicone round the star at its base
    cover=6.0,          # silicone over the star's face
    floor=2.0,
    wall=2.4,
)

EMBED = 0.1


def outline(p):
    """Hexagram at the star's back, `span` point to point, points on +-Y, tips rounded."""
    R = p.span / 2
    r = R / math.sqrt(3)            # inner (notch) vertices of two equilateral triangles
    pts = [((R if i % 2 == 0 else r) * math.cos(math.pi / 2 + math.pi * i / 6),
            (R if i % 2 == 0 else r) * math.sin(math.pi / 2 + math.pi * i / 6)) for i in range(12)]
    # rounding the tips moves them in: start from a slightly larger star so the rounded
    # points still reach `span` (tip of a 60 deg point recedes by r / sin 30 - r = r)
    k = (R + p.tip_r) / R
    sharp = poly([(x * k, y * k) for x, y in pts])
    return grow(grow(sharp, -p.tip_r), p.tip_r)


def lean(p):
    return draft_offset(p.thickness, p.draft)


def star(p, z=0.0, sink=0.0):
    """The star (the cast piece), back on z, narrowing at `draft` toward its face;
    `sink` extends it that far below z (straight) to embed it in the floor."""
    cs = outline(p)
    h = p.thickness
    s = offset_loft(cs, [(-sink, 0.0), (0.0, 0.0), (h, -lean(p))] if sink else [(0.0, 0.0), (h, -lean(p))])
    if s is None:
        s = drafted(lambda f: grow(cs, -lean(p) * f), 0.0, h, steps=int(h / 0.2))
    return s.translate((0, 0, z))


def top_z(p):
    return p.floor + p.thickness + p.cover


def silicone_ml(p):
    h = p.thickness + p.cover
    a0 = grow(outline(p), p.gap).area()
    a1 = grow(outline(p), p.gap + draft_offset(h, p.draft)).area()
    return ((a0 + a1) / 2 * h - star(p).volume()) / 1000.0


def checks(p):
    R = p.span / 2
    ol = grow(outline(p), p.gap + p.wall + draft_offset(p.thickness + p.cover, p.draft))
    x0, y0, x1, y1 = ol.bounds()
    ml = silicone_ml(p)
    zf = p.floor
    notch = R / math.sqrt(3)
    a = math.radians(60)                # direction of a notch between two points
    return [
        dims(x=x1 - x0, y=y1 - y0, z=top_z(p)),
        fits_bed(),
        # star body, its points (up, down and a side one) and its face height
        solid((0, 0, zf + p.thickness / 2), (0, R - 2, zf + 1), (0, -(R - 2), zf + 1),
              (R * math.cos(math.radians(30)) - 2, R / 2 - 1, zf + 1), (0, 0, zf + p.thickness - 0.3)),
        empty((0, 0, zf + p.thickness + 0.5), (0, R + p.gap / 2, zf + 1),
              ((notch + 6) * math.cos(a), (notch + 6) * math.sin(a), zf + 1)),
        # point tips stay printable at the face (>= 1.2 mm across 2.5 mm from the tip)
        thickness_at((0, R - lean(p) - 2.5, zf + p.thickness - 0.5), 1.2, direction=(1, 0, 0)),
        thickness_at((0, R + p.gap / 2, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        custom("silicone to mix", lambda ctx: (True, f"{ml:.0f} ml (about {ml * 1.1:.0f} g)")),
        flat_base(ol.area() * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    cs = outline(p)
    h = p.thickness + p.cover
    wl = draft_offset(h, p.draft)
    top = top_z(p)
    outer = grow(cs, p.gap + p.wall + wl)
    box = extrude(outer, top)
    cavity = offset_loft(grow(cs, p.gap), [(0.0, 0.0), (h + 1.0, draft_offset(h + 1.0, p.draft))])
    if cavity is None:
        cavity = tapered(grow(cs, p.gap), 0.0, h + 1.0, draft_offset(h + 1.0, p.draft))
    box -= cavity.translate((0, 0, p.floor))
    return box + star(p, p.floor, sink=EMBED)


def casting(p):
    """What the mold makes, for the shop's cast render: the star, face up."""
    return star(p)
