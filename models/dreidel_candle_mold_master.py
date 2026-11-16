"""Two-part silicone mold master for a Hanukkah dreidel candle: 76 mm (3 in) tall, a
38 mm (1.5 in) square body with Nun, Gimel, Hei and Shin raised on its four faces, a
pointed tip at the bottom and a short round handle on top.

The dreidel is split along a vertical plane through two opposite corners, so the parting
line runs down two of its edges and no letter is cut. Each half lies cut-face-down on the
floor of its own pour box: the box floor is the parting board, so the silicone poured
into box A and box B gives two mold halves whose flat faces meet exactly at the parting
plane. Box A has the Nun and Gimel half and four hemispherical dimples in its floor; box B
has the Hei and Shin half and four matching bumps. Silicone A therefore grows four bumps
that seat in silicone B's four dimples (the key pattern is symmetric, so the halves only
close one way round). A half-round channel on the floor leads from the handle end to the
box wall (the wick hole) and a half-cone funnel from the tip to the other wall (the pour
sprue), so the closed mold has a 2.4 mm wick hole at the handle and a 12 mm pour funnel
at the tip.

Use: thread the wick through the handle hole and out of the funnel, band the two silicone
halves together, stand the mold tip-up, pull the wick tight and centre it with a wick bar
across the funnel, and pour wax in through the funnel. Top up as it shrinks, then trim
the sprue stub flush to leave the point. The point is blunted to about 4 mm, so the candle
needs a candle plate or holder to stand in.

Spec:
  object:       two-part master (two pour boxes, each with half a dreidel on its parting
                floor) for a two-part silicone dreidel candle mold, cast in wax
  overall:      candle 76 mm tall (3 in): tip 22, body 38 (incl. 3 mm top chamfer),
                handle 16 x 10 mm; body 38 mm across the flats (1.5 in), 4 mm corner radius;
                each box 73 x 99 x 36 mm, fits the A1 mini bed, both fit one A1 plate
  casting:      silicone >= 7 mm round and over each half, 8 mm at the ends;
                about 170 ml of silicone per half, ~340 ml for the pair
  mates with:   silicone half A to half B: four 6 mm hemispherical keys at (+-16, +-32);
                parting plane = box floor top = dreidel's corner-to-corner plane
  orientation:  each box floor-down on the bed, the half dreidel cut-face-down on the
                floor (letters face up at 45 deg); no supports
  must have:    letters Nun, Gimel, Hei, Shin raised 0.8 mm, 20 mm tall, upright and
                reading correctly on the candle (not mirrored: the master is a positive);
                wick channel 2.4 mm on the axis at the handle end; pour funnel 5-12 mm at
                the tip end; 2 deg draft on the box walls
  tolerances:   none (casting); keys are hemispheres, self-centring

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
import math

from manifold3d import Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Two-part silicone mold master for a Hanukkah dreidel candle, 3 in tall with Hebrew letters"

PRODUCT = dict(
    title="Dreidel Candle Mold Master, Two-Part Silicone Mold Kit",
    category="molds",
    tags=["dreidel", "hanukkah", "chanukah", "candle mold", "silicone mold", "mold master",
          "two part mold", "candle making", "judaica", "hebrew letters", "wax", "holiday"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then candle wax",
    post_processing=("Sand or seal the dreidel halves lightly; the silicone copies layer lines. "
                     "Spray release on both boxes, pour about 170 ml of silicone into each so it "
                     "covers the dreidel by 7 mm, and demold after full cure. Band the halves "
                     "together (keys seat them), thread the wick through the handle hole, stand "
                     "the mold tip-up and pour wax through the funnel."),
    draft=True,
)
LICENSE_NOTES = None   # original design; letters drawn with the system Arial Bold outlines

IN = 25.4
PARAMS = dict(
    height=3.0 * IN,        # whole candle, tip to handle top (76.2)
    width=1.5 * IN,         # body across the flats (38.1)
    corner_r=4.0,           # rounding of the body's vertical edges
    tip_h=22.0,             # pointed tip
    tip_end=0.10,           # tip end as a fraction of the body width (blunt point, 3.8 mm)
    handle_h=16.0,
    handle_d=10.0,
    chamfer=3.0,            # body's top edge
    letter_h=20.0,          # letter height on the faces
    letter_raise=0.8,
    font="Arial",
    silicone=7.0,           # silicone round and over each half
    end_gap=8.0,            # silicone beyond the tip and handle (sprue and wick channels)
    wick_d=2.4,
    sprue_d=12.0,           # pour funnel mouth at the box wall
    key_r=3.0,              # alignment key hemispheres
    floor=4.0,
    wall=2.1,
    draft=2.0,              # on the box walls
)

EMBED = 0.1
LETTERS = ["נ", "ג", "ה", "ש"]    # Nun, Gimel, Hei, Shin, counterclockwise from above


def body_h(p):
    return p.height - p.tip_h - p.handle_h


def rsquare(w, r):
    return grow(CrossSection.square((w - 2 * r, w - 2 * r), center=True), r)


def letter(p, ch):
    """Glyph scaled to letter_h tall (and to the face's flat width), centred."""
    cs = text(ch, 20.0, font=p.font, bold=True)
    x0, y0, x1, y1 = cs.bounds()
    s = min(p.letter_h / (y1 - y0), (p.width - 2 * p.corner_r - 4.0) / (x1 - x0))
    return cs.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).scale((s, s))


def dreidel(p):
    """The candle, upright: tip at Z=0, handle up, faces normal to +-X and +-Y."""
    w, bh = p.width, body_h(p)
    sec = rsquare(w, p.corner_r)
    tip = Manifold.extrude(sec, p.tip_h, scale_top=(p.tip_end, p.tip_end)).mirror((0, 0, 1))
    tip = tip.translate((0, 0, p.tip_h))
    body = extrude(sec, bh - p.chamfer + EMBED, p.tip_h - EMBED)
    k = (w - 2 * p.chamfer) / w
    body += Manifold.extrude(sec, p.chamfer, scale_top=(k, k)).translate((0, 0, p.tip_h + bh - p.chamfer))
    z_h = p.tip_h + bh
    hr = p.handle_d / 2
    handle = extrude(circle(0, 0, hr), p.handle_h - 1.0 + EMBED, z_h - EMBED)
    handle += Manifold.extrude(circle(0, 0, hr), 1.0, scale_top=((hr - 1) / hr,) * 2).translate((0, 0, p.height - 1.0))
    d = tip + body + handle
    zc = p.tip_h + (bh - p.chamfer) / 2
    for i, ch in enumerate(LETTERS):
        g = Manifold.extrude(letter(p, ch), p.letter_raise + EMBED)
        # glyph x -> along the face (viewer's right), glyph y -> up, extrusion -> out of +X face
        g = g.transform([[0, 0, 1, w / 2 - EMBED], [1, 0, 0, 0], [0, 1, 0, zc]])
        d += g.rotate((0, 0, 90 * i))
    return d


def layout(p):
    """Inner box extents (half sizes) and key positions."""
    half_w = p.width / math.sqrt(2) - p.corner_r * (math.sqrt(2) - 1)   # axis to corner crest
    ix = half_w + p.letter_raise + p.silicone
    iy = p.height / 2 + p.end_gap
    ih = half_w + p.silicone
    keys = [(sx * 16.0, sy * (p.height / 2 - 6.0)) for sx in (1, -1) for sy in (1, -1)]
    return half_w, ix, iy, ih, keys


def half(p, side):
    """Half dreidel lying on its cut face (cut face on Z=0, axis along Y, centred).
    side=+1: the Nun/Gimel half, tip toward +Y; side=-1: the Hei/Shin half."""
    d = dreidel(p).rotate((0, 0, 45))            # corners onto the X and Y axes
    h = d.trim_by_plane((0, side, 0), -EMBED)    # keep y*side >= -EMBED (0.1 sliver to sink)
    h = h.rotate((90 * side, 0, 0))              # cut plane -> Z=0, the half above it
    h = h.translate((0, 0, -EMBED))
    y0, y1 = h.bounding_box()[1], h.bounding_box()[4]
    return h.translate((0, -(y0 + y1) / 2, 0))


def box(p, side):
    half_w, ix, iy, ih, keys = layout(p)
    lean = draft_offset(ih, p.draft)
    inner = CrossSection.square((2 * ix, 2 * iy), center=True)
    outer = grow(inner, p.wall)
    total = p.floor + ih
    tray = tapered(outer, 0, total, lean) - tapered(inner, p.floor, total, lean)
    master = half(p, side).translate((0, 0, p.floor))
    # wick channel at the handle end, pour funnel at the tip end
    tip_y = side * p.height / 2
    hand_y = -side * p.height / 2
    wick = Manifold.cylinder(p.end_gap + 1.0, p.wick_d / 2, p.wick_d / 2, 24)
    wick = wick.rotate((90 * side, 0, 0)).translate((0, hand_y + side * 1.0, p.floor - EMBED))
    tip_r = p.width * p.tip_end / 2
    sprue = Manifold.cylinder(p.end_gap + 1.5, tip_r * 0.9, p.sprue_d / 2, 48)
    sprue = sprue.rotate((-90 * side, 0, 0)).translate((0, tip_y - side * 1.5, p.floor - EMBED))
    # keep only the upper halves of the channels; anything past the inner wall sinks into it
    cut = extrude(CrossSection.square((2 * ix, 2 * iy + 2 * p.wall), center=True), 50, p.floor - EMBED)
    part = tray + master + ((wick + sprue) ^ cut)
    for kx, ky in keys:
        ball = Manifold.sphere(p.key_r, 48).translate((kx, ky, p.floor))
        part = part - ball if side > 0 else part + (ball ^ extrude(circle(kx, ky, p.key_r + 1), p.key_r + 1, p.floor - EMBED))
    return part


def silicone_ml(p):
    half_w, ix, iy, ih, keys = layout(p)
    lean = draft_offset(ih, p.draft)
    fill = (2 * ix + lean) * (2 * iy + lean) * ih
    return (fill - dreidel(p).volume() / 2) / 1000.0


def checks(p):
    half_w, ix, iy, ih, keys = layout(p)
    lean = draft_offset(ih, p.draft)
    W = 2 * (ix + p.wall)
    L = 2 * (iy + p.wall)
    top = p.floor + ih
    ml = silicone_ml(p)
    kx, ky = keys[0]
    common = [
        dims(x=(W - 0.5, W + 2 * lean + 0.5), y=(L - 0.5, L + 2 * lean + 0.5), z=top),
        empty((0, 0, top - p.silicone / 2), (ix - 2, 0, top - 2)),         # silicone over and beside the half
        solid((0, 0, p.floor + half_w / 2),                                # body, tip and handle ends
              (0, p.height / 2 - 3.0, p.floor + 1.0), (0, -p.height / 2 + 3.0, p.floor + 1.0),
              (0, iy - 2.0, p.floor + 0.5), (0, -iy + 2.0, p.floor + 0.5)),  # wick / sprue channels
        custom("silicone to mix", lambda ctx: (True, f"{ml:.0f} ml per half (about {ml * 1.1:.0f} g)")),
        flat_base(W * L * 0.9),
        no_overhang(),
        single_body(),
        fits_bed(),
    ]
    return {
        "half_a": common + [empty((kx, ky, p.floor - 1.0), (-kx, -ky, p.floor - 1.0))],    # dimples
        "half_b": common + [solid((kx, ky, p.floor + 1.0), (-kx, -ky, p.floor + 1.0))],    # bumps
    }


def display(p):
    """Product shot: the two boxes side by side, tipped toward the camera so the half
    dreidels and their letters show over the walls."""
    half_w, ix, iy, ih, keys = layout(p)
    dx = ix + p.wall + 6.0
    return {"half_a": (-dx, 0, 0, 35, 0, 0), "half_b": (dx, 0, 0, 35, 0, 0)}


def build(p):
    return {"half_a": box(p, +1), "half_b": box(p, -1)}


def casting(p):
    """What the mold makes: the dreidel candle, upright on its tip."""
    return dreidel(p)
