"""Cat coaster mold set for Jesmonite, plaster, cement or resin: three 100 mm coasters,
picked with `style`.

- head: the coaster is a cat's head with two broad, blunt ears; a sleepy face (closed
  eyes, mouth, whiskers, inner ears) is grooved into it and the nose stands proud.
- paw:  a round coaster with a raised paw print (palm pad and four toe beans) and a
  groove ring near the edge.
- moon: a round coaster with a raised crescent moon, a cat sitting on its lower horn
  with its tail curled round, and three stars.

The coaster is cast face-down: a pocket in the mold floor is a raised area on the
coaster, a rib on the floor is a groove. The back is the pour side: screed it flat and
add cork or felt pads. Every wall the casting touches is drafted. The ears are wide
with rounded tips because thin pointed ears are what fails to fill in cement cat casts.
The moon art is mirrored on the mold floor so the coaster reads the right way round.
The cavity has a chamfer where the wall meets the floor and a flared rim, so the
coaster's face edge is bevelled and nothing sharp holds it in the mold.

Spec:
  object:       open-top mold for a 100 mm cat coaster, 10 mm thick, cast face-down
  overall:      head ~108 x 104 x 14 mm; paw and moon ~108 dia x 14 mm (fit a 180 mm bed)
  casting:      head 100 x ~96 mm; paw and moon 100 mm round; 10 mm thick
  mates with:   nothing
  orientation:  opening up, flat floor on the bed; supports expected: none
  must have:    raised details 1.5 mm (pockets, 8 deg draft); grooves 1.0 deep and
                1.6 wide (ribs, 10 deg draft); ear tips rounded r >= 5 mm; 2 deg
                draft on the cavity wall; floor 4, wall 3; moon art mirrored on the mold;
                1.5 mm 45 deg chamfer where the wall meets the floor (the coaster's face
                edge, so it has no sharp corner to grab or chip on release) and a 1.0 mm
                45 deg flare at the rim (easier pouring, screeding and prying out)
  tolerances:   none (casting)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
import math

import numpy as np

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Cat coaster mold set: cat head, paw print or moon cat, for Jesmonite, plaster or cement"

PRODUCT = dict(
    title="Cat {style} Coaster Mold",   # Cat Head / Cat Paw / Cat Moon
    category="molds",
    tags=["mold", "coaster", "cat", "kitten", "paw print", "moon", "jesmonite",
          "plaster", "cement", "resin", "home decor", "cat lover gift"],
    printers=["a1", "a1mini"],
    cast_material="Jesmonite, plaster, cement or resin",
)
LICENSE_NOTES = None   # original artwork; the default licence applies

PARAMS = dict(
    style="head",        # head | paw | moon
    size=100.0,          # coaster width at its face
    thickness=10.0,      # coaster thickness = cavity depth
    floor=4.0,
    wall=3.0,
    wall_draft=2.0,
    raise_h=1.5,         # raised details on the coaster (pockets in the mold floor)
    groove_depth=1.0,    # grooves in the coaster (ribs on the mold floor)
    groove_w=1.6,
    pocket_draft=8.0,
    rib_draft=10.0,
    edge_chamfer=1.5,    # 45 deg chamfer on the coaster's face edge (bottom of the cavity)
    rim_chamfer=1.0,     # 45 deg flare at the top of the cavity wall
)

EMBED = 0.1
CHORD = 0.5          # max facet length on curves (mm); relief's 48-gon is 6.5 mm on a coaster


def segments(r):
    return max(48, math.ceil(2 * math.pi * r / CHORD))


# finer versions of relief's circle/ellipse, so the coaster edge reads as a true curve
def circle(x, y, r):
    return CrossSection.circle(r, segments(r)).translate((x, y))


def ellipse(x, y, rx, ry):
    a = np.linspace(0, 2 * math.pi, segments(max(rx, ry)), endpoint=False)
    return poly(np.c_[x + rx * np.cos(a), y + ry * np.sin(a)])
ART = 100.0          # every outline below is drawn for a 100 mm coaster, then scaled


def rounded(cs, r):
    """Round convex corners (opening) and concave notches (closing) by `r`."""
    return grow(grow(grow(grow(cs, -r), r), r), -r)


# ---- head ------------------------------------------------------------------------

EAR = [(-47, 6), (-41, 50), (-12, 36)]       # left ear, mirrored


def head_outline():
    face = ellipse(0, -6, 50, 42)
    ears = mirror_x(rounded(poly(EAR), 6.0))
    return rounded(face + ears, 5.0)


def head_grooves(w=1.0):
    """Groove centrelines drawn `w` (1 unit) wide; build() widens them to groove_w."""
    out = CrossSection()
    for side in (1, -1):
        s = lambda pts: [(side * x, y) for x, y in pts]
        out += stroke(bezier(*s([(14, 4), (21, -3), (28, 4)]), n=14), w)            # closed eye
        for a, c, b in [((24, -15), (33, -13.5), (42, -11)), ((25, -19), (34, -19), (43, -19)),
                        ((24, -23), (33, -25), (41, -27.5))]:
            out += stroke(bezier(*s([a, c, b]), n=12), w)                           # whiskers
        out += stroke(bezier(*s([(0, -19), (3.5, -24), (8, -19.5)]), n=10), w)      # mouth
        inner = poly(s([(-38, 20), (-35, 40), (-21, 32)]))
        out += rounded(inner, 3.0) - grow(rounded(inner, 3.0), -w)                  # inner ear
    out += stroke([(0, -14), (0, -19)], w)
    return out


def head_raised():
    return rounded(poly([(-5.5, -8), (5.5, -8), (0, -14)]), 1.5)                   # nose


# ---- paw -------------------------------------------------------------------------

PAD = [(0, -32), (12, -30), (20, -22), (19, -12), (11, -5), (0, -7), (-11, -5), (-19, -12),
       (-20, -22), (-12, -30)]
TOES = [(-24, 2, 7.5, 9.5, 20), (-9, 15, 7.5, 10, 6), (9, 15, 7.5, 10, -6), (24, 2, 7.5, 9.5, -20)]


def paw_raised():
    out = smooth_shape(PAD)
    for x, y, rx, ry, tilt in TOES:
        out += ellipse(0, 0, rx, ry).rotate(tilt).translate((x, y))
    return out.translate((0, 4))


def paw_grooves():
    return circle(0, 0, ART / 2 - 6) - circle(0, 0, ART / 2 - 7)   # 1 unit wide, widened later


# ---- moon ------------------------------------------------------------------------

def star(x, y, r, points=5, ratio=0.5):
    a = np.linspace(0, 2 * math.pi, 2 * points, endpoint=False) + math.pi / 2
    rr = np.where(np.arange(2 * points) % 2 == 0, r, r * ratio)
    return rounded(poly(np.c_[x + rr * np.cos(a), y + rr * np.sin(a)]), 0.7)


def sitting_cat():
    """Cat seen from behind, sitting, about 38 mm tall with its base at y=0."""
    body = smooth_shape([(-10, 0.5), (-12, 8), (-10, 17), (-5, 22), (0, 23), (5, 22), (10, 17),
                         (12, 8), (10, 0.5), (0, -0.5)])
    head = ellipse(0, 28, 8, 7)
    ears = mirror_x(rounded(poly([(-8, 28), (-7, 39), (-1.5, 33)]), 1.2))
    tail = stroke(bezier((8, 2), (22, 1), (21, 14), n=14), 4.0)
    return rounded(body + head + ears + tail, 1.5)


def moon_raised():
    # horn tips rounded so they are not knife edges in the casting
    crescent = rounded(circle(-4, 0, 40) - circle(10, 8, 33), 2.5)
    cat = sitting_cat().translate((8, -27))        # feet sunk into the lower horn
    stars = star(26, 30, 6.0) + star(36, 12, 4.5) + star(12, 38, 3.5)
    art = crescent + cat + stars
    return art.mirror((1, 0))      # mold floor is the mirror of the coaster face


def moon_grooves():
    return CrossSection()


# ---- mold ------------------------------------------------------------------------

def outline(p):
    return head_outline() if p.style == "head" else circle(0, 0, ART / 2)


def art(p):
    """(outline, raised, grooves-centreline-fn) in coaster mm."""
    if p.style == "head":
        return head_outline(), head_raised(), head_grooves
    if p.style == "paw":
        return circle(0, 0, ART / 2), paw_raised(), lambda w: paw_grooves()
    if p.style == "moon":
        return circle(0, 0, ART / 2), moon_raised(), lambda w: moon_grooves()
    raise ValueError(f"style must be head, paw or moon, not {p.style!r}")


def checks(p):
    k = p.size / ART
    h = p.floor + p.thickness
    lean = draft_offset(p.thickness, p.wall_draft)
    w = p.size + 2 * (lean + p.wall)
    out = [
        dims(x=(w - 1.5, w + 1.5), z=h),
        empty((30 * k, -30 * k, p.floor + 2), (0, 0, h - 1)),
        flat_base(p.size ** 2 * 0.5),
        no_overhang(),
        single_body(),
    ]
    # chamfer: material in the floor corner, open just above it; rim flared open
    r, cy = p.size / 2, (-6 * k if p.style == "head" else 0)
    if p.edge_chamfer > 0.5:
        out += [solid((r - p.edge_chamfer * 0.4, cy, p.floor + 0.3)),
                empty((r - 0.3, cy, p.floor + p.edge_chamfer + 0.5))]
    if p.rim_chamfer > 0.5:
        out.append(empty((r + lean + p.rim_chamfer * 0.6, cy, h - 0.2)))
    if p.style == "head":
        out += [
            dims(y=(96 * k + 2 * (lean + p.wall) - 1.5, 96 * k + 2 * (lean + p.wall) + 1.5)),
            empty((-28 * k, 38 * k, p.floor + 2)),                                  # ear is cavity
            empty((0, -11 * k, p.floor - p.raise_h + 0.3)),                         # nose pocket
            thickness_at((0, -11 * k, 0.5), p.floor - p.raise_h - 0.2, direction=(0, 0, 1)),
            solid((-21 * k, 0.5 * k, p.floor + p.groove_depth / 2)),               # eye rib
        ]
    elif p.style == "paw":
        out += [
            empty((0, -15 * k, p.floor - p.raise_h + 0.3)),                         # palm pocket
            empty((-9 * k, 19 * k, p.floor - p.raise_h + 0.3)),                     # toe pocket
            thickness_at((0, -15 * k, 0.5), p.floor - p.raise_h - 0.2, direction=(0, 0, 1)),
            solid((0, (ART / 2 - 6.5) * k, p.floor + p.groove_depth / 2)),          # ring rib
        ]
    else:
        out += [
            empty((38 * k, 0, p.floor - p.raise_h + 0.3)),                          # crescent (mirrored)
            empty((-26 * k, 30 * k, p.floor - p.raise_h + 0.3)),                    # big star (mirrored)
            thickness_at((38 * k, 0, 0.5), p.floor - p.raise_h - 0.2, direction=(0, 0, 1)),
        ]
    return out


def cavity(shape, p):
    """The coaster's space: a 45 deg chamfer at the floor, the drafted wall, a 45 deg
    flare at the rim, and 0.5 mm above the mold so the cut is clean. One ruled loft
    from `shape` shrunk by the chamfer, so the bevels are smooth, not stair-stepped."""
    c, rc = p.edge_chamfer, p.rim_chamfer
    slope = math.tan(math.radians(p.wall_draft))
    h = p.floor + p.thickness
    r_rim = c + (p.thickness - c - rc) * slope
    stations = [(p.floor, 0.0), (p.floor + c, c), (h - rc, r_rim), (h + 0.5, r_rim + rc + 0.5)]
    # simplify drops the tiny edges round offsets leave (their miter rays cross at the
    # rim); keep the tolerance far below a facet's sag so curves stay smooth
    base = grow(shape, -c)
    out = None
    for tol in (0.005, 0.02):
        out = offset_loft(base.simplify(tol), stations)
        if out is not None:
            break
    if out is None:
        raise ValueError("cavity loft self-intersects; lower edge_chamfer or soften the outline")
    return out


def build(p):
    k = p.size / ART
    sc = lambda cs: cs.scale((k, k))
    shape, raised, grooves = art(p)
    shape, raised = sc(shape), sc(raised)
    lean = draft_offset(p.thickness, p.wall_draft)
    h = p.floor + p.thickness

    mold = extrude(grow(shape, lean + p.wall), h)
    mold -= cavity(shape, p)
    # at the ear notches the bevel's ruled faces converge and the cut leaves
    # zero-volume scraps (~1e-9 mm3) on the rim; keep only real material
    mold = Manifold.batch_boolean([b for b in mold.decompose() if abs(b.volume()) > 1.0], OpType.Add)
    # raised details: pockets in the floor that narrow downward
    pocket_lean = draft_offset(p.raise_h, p.pocket_draft)
    mold -= drafted(lambda f: grow(raised, (f - 1) * pocket_lean), p.floor - p.raise_h,
                    p.raise_h + 1, steps=4)
    # grooves: ribs standing on the floor, sunk EMBED so the union has no coplanar faces
    # groove art is drawn 1 unit wide; widen it to groove_w after scaling
    lines = grow(sc(grooves(1.0)), (p.groove_w - k) / 2)
    if not lines.is_empty():
        rib_lean = draft_offset(p.groove_depth, p.rib_draft)
        mold += drafted(lambda f: grow(lines, -f * rib_lean), p.floor - EMBED,
                        p.groove_depth + EMBED, steps=3)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the coaster, face up."""
    return cast_of(build(p))
