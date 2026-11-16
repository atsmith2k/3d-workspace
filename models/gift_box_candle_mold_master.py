"""Two-part silicone mold kit for a gift-box candle: a 3 inch present with a lid, a ribbon
crossing over the top in both directions and a bow, all in raised relief.

The candle is split at the bottom edge of the lid, where the parting line hides under the
lid's overhang. Each half of the master stands in its own pour tray, parting face down on
the tray floor: the top tray holds the lid and bow, the bottom tray the box body standing
on its top face with its base up. Pour silicone into each tray to the rim. Four cone pegs
on the top tray's floor and four matching sockets in the bottom tray's floor make
matching sockets and pegs in the two silicone halves, so they lock together square.

Casting: set the lid-and-bow silicone on the bench, cavity up, and drop the body silicone
onto it so the pegs seat. The candle is poured upside down through the open base. The
wick pin on top of the bow leaves a 2.5 mm hole through the silicone: thread the wick up
through it from underneath (seal it with a wick sticker or a dab of putty outside), pull
it straight through the cavity and out of the open base, and clip it in a wick bar
across the opening. Pour the wax to the brim; the brim forms the candle's flat base.

Spec:
  object:       two-part master (in pour trays) for a two-part silicone gift-box candle mold
  overall:      top tray 116 x 116 x 47.5 mm, bottom tray 117 x 117 x 63 mm (walls flare
                2 deg; both fit the A1 mini); candle 84 x 84 x 91 mm over ribbon and bow
  casting:      candle = box body 76.2 x 76.2 x 58.2 mm under a lid 81.2 x 81.2 x 18 mm (2.5 mm
                overhang lip), so the box is 76.2 mm (3 in) tall; ribbon 14 mm wide, raised
                1.5 mm, over the sides and the top in both directions; bow 62 mm across,
                15 mm tall above the lid (two domed loops with dished openings, a knot,
                two V-cut tails)
  silicone:     12 mm round the widest part of the candle, 10 mm over the bow; the body's
                base is left open as the pour hole (it stands 1 mm proud of the bottom
                tray's rim); about 380 ml for the top tray, 365 ml for the bottom
  parting:      horizontal plane at the lid's bottom edge; both parting faces flat (the
                tray floors); 4 cone keys 8 mm across, 3 mm tall at the corners
  wick:         2.5 mm pin from the top of the bow knot through the top silicone
  orientation:  each tray flat on its floor, master standing on the floor parting face
                down (top: lid then bow up; bottom: box body upside down, base up);
                every master face is vertical or faces up, no supports
  must have:    lid with overhang lip, ribbon both ways, bow in raised relief, flat
                parting faces, alignment keys, wick hole, silicone volume reported
  tolerances:   keys are cast silicone to silicone, so pegs and sockets are the same size;
                tray walls drafted 2 deg so the silicone block lifts out

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
import math

from manifold3d import Manifold, OpType

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Two-part silicone mold master for a 3 inch gift-box candle with lid, ribbon and bow"

PRODUCT = dict(
    title="Gift Box Candle Silicone Mold Master (Two-Part, 3 inch Christmas Present)",
    category="molds",
    tags=["candle mold", "silicone mold", "mold master", "gift box candle", "christmas candle",
          "present candle", "two part mold", "candle making", "christmas", "holiday decor",
          "wax", "soy candle"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then candle wax",
    post_processing=("Sand or seal the master's layer lines (the silicone copies every line) and "
                     "spray mold release on the masters and the trays. Fill each tray to the rim "
                     "with silicone (about 380 ml for the top, 365 ml for the bottom), pouring "
                     "slowly into a corner. Demold after full cure. To cast: lid-and-bow silicone "
                     "cavity up, body silicone on top with the keys seated, wick threaded through "
                     "the bow's wick hole and held in a wick bar across the open base; band the "
                     "halves together and pour the wax to the brim."),
    draft=True,
    sellable=None,
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    box=76.2,           # box body width and depth (3 in)
    height=76.2,        # box height, body + lid (3 in), not counting the bow
    lid_h=18.0,         # lid height
    lid_lip=2.5,        # lid overhang past the body, per side
    ribbon_w=14.0,      # ribbon width
    ribbon_t=1.5,       # ribbon raised above the box/lid surface
    bow_h=15.0,         # bow loops' height above the lid top
    bow_span=62.0,      # bow width, loop tip to loop tip
    corner_r=1.5,       # rounding of the box's vertical edges
    silicone=12.0,      # silicone wall round the candle
    cover=10.0,         # silicone over the bow
    wick_d=2.5,
    key_d=8.0,          # alignment key base diameter
    key_h=3.0,
    floor=4.0,          # tray floor thickness
    wall=2.4,           # tray wall thickness
    tray_draft=2.0,     # degrees, tray walls flare outward
)

EMBED = 0.3


def body_h(p):
    return p.height - p.lid_h


def rsquare(w, r):
    """Square `w` across centred on the origin with vertical edges rounded by `r`."""
    return grow(poly([(-w / 2 + r, -w / 2 + r), (w / 2 - r, -w / 2 + r),
                      (w / 2 - r, w / 2 - r), (-w / 2 + r, w / 2 - r)]), r)


def bar(cx, cy, w, h):
    return poly([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                 (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)])


def lid_w(p):
    return p.box + 2 * p.lid_lip


def cavity_w(p):
    """Inside of the trays at the floor: the lid plus its ribbon plus the silicone wall."""
    return lid_w(p) + 2 * p.ribbon_t + 2 * p.silicone


def dome(cx, cy, a, b, h, z, angle=0.0):
    """Upper part of an ellipsoid (semi-axes a, b, h) whose centre sits EMBED below `z`:
    a heightfield, so no face of it points down."""
    e = Manifold.sphere(1.0, 96) ^ Manifold.cube((3, 3, 2)).translate((-1.5, -1.5, 0))
    e = e.scale((a, b, h + EMBED))
    return e.rotate((0, 0, angle)).translate((cx, cy, z - EMBED))


def bow(p, z):
    """Bow on the lid top (z = lid top). Loops along +-X, tails toward -Y; every face is
    vertical or faces up, so the silicone lifts straight off it."""
    s = p.bow_span / 62.0
    rt = p.ribbon_t
    a, b = 17.0 * s, 12.5 * s
    out = Manifold()
    for side in (1, -1):
        cx = side * (p.bow_span / 2 - a)
        ang = math.radians(side * 10)
        loop = dome(cx, 0, a, b, p.bow_h, z, angle=side * 10)
        # the loop's opening: a shallow dish in its outer half, cut from above
        d = a * 0.42
        dish = Manifold.sphere(1.0, 64).scale((a * 0.42, b * 0.55, p.bow_h * 0.5))
        dish = dish.translate((cx + side * d * math.cos(ang), side * d * math.sin(ang), z + p.bow_h * 1.12))
        out += loop - dish
        # tail: a strip with a V-cut end, lying on the ribbon toward -Y
        L, w = 32 * s, 11 * s
        tail = poly([(-w / 2, 0), (w / 2, 0), (w / 2, -L), (0, -L + 5 * s), (-w / 2, -L)])
        tail = extrude(tail, rt + 1.2 + EMBED, z - EMBED).rotate((0, 0, side * 28))
        out += tail
    out += dome(0, 0, 8.0 * s, 9.5 * s, p.bow_h * 0.82, z)        # knot
    return out


def ribbon_box(w, length, h, z=0.0):
    """Ribbon bands over a block `length` wide and `h` tall, in both directions."""
    return extrude(bar(0, 0, w, length), h, z) + extrude(bar(0, 0, length, w), h, z)


def knot_top(p):
    return p.bow_h * 0.82


def top_half(p):
    """Lid with ribbon and bow, lid bottom (parting face) on Z=0, bow up."""
    lw = lid_w(p)
    lid = extrude(rsquare(lw, p.corner_r + p.lid_lip), p.lid_h - 1.0)
    lid += tapered(rsquare(lw - 2.0, p.corner_r + p.lid_lip - 1), p.lid_h - 1.0 - 0.01, 1.01, -0.0) \
        if False else Manifold.extrude(rsquare(lw, p.corner_r + p.lid_lip), 1.0,
                                       scale_top=((lw - 2.0) / lw,) * 2).translate((0, 0, p.lid_h - 1.0 - 0.01))
    lid += ribbon_box(p.ribbon_w, lw + 2 * p.ribbon_t, p.lid_h + p.ribbon_t)
    return lid + bow(p, p.lid_h)


def bottom_half(p):
    """Box body upside down: its top face (parting face) on Z=0, base up at body_h."""
    bh = body_h(p)
    body = extrude(rsquare(p.box, p.corner_r), bh)
    body += ribbon_box(p.ribbon_w, p.box + 2 * p.ribbon_t, bh)
    return body


def tray(p, rim):
    """Pour tray: floor plate plus walls flaring at `tray_draft`; silicone fills it from the
    floor (z = p.floor) up to `rim`."""
    cw = cavity_w(p)
    h = rim
    lean = draft_offset(h, p.tray_draft)
    outer = tapered(rsquare(cw + 2 * p.wall, 4 + p.wall), 0, h, lean)
    inner_h = rim - p.floor
    inner = tapered(rsquare(cw, 4), p.floor, inner_h + 1, draft_offset(inner_h + 1, p.tray_draft))
    return outer - inner


def key_xy(p):
    k = cavity_w(p) / 2 - p.key_d / 2 - 2.5
    return [(sx * k, sy * k) for sx in (1, -1) for sy in (1, -1)]


def key(p, x, y, z, extra=0.0, socket=False):
    """Truncated cone `key_d` across at the parting face, 60% of that at the tip. A socket
    is the same cone pointing down, so it opens wide at the floor's top face."""
    r = p.key_d / 2
    lo, hi = (r * 0.6, r) if socket else (r, r * 0.6)
    return Manifold.cylinder(p.key_h + extra, lo, hi, 48).translate((x, y, z))


def top_rim(p):
    return p.floor + p.lid_h + p.bow_h + p.cover


def bottom_rim(p):
    return p.floor + body_h(p)


def build_top(p):
    rim = top_rim(p)
    t = tray(p, rim)
    for x, y in key_xy(p):
        t += key(p, x, y, p.floor - 0.1, extra=0.1)
    master = top_half(p).translate((0, 0, p.floor - 0.1))
    pin_z = p.floor + p.lid_h + knot_top(p) - 1.0
    pin = extrude(circle(0, 0, p.wick_d / 2), rim + 0.5 - pin_z, pin_z)
    return t + master + pin


def build_bottom(p):
    rim = bottom_rim(p)
    t = tray(p, rim)
    for x, y in key_xy(p):
        t -= key(p, x, y, p.floor - p.key_h, extra=0.1, socket=True)
    master = bottom_half(p).translate((0, 0, p.floor - 0.1))
    # the base stands 1 mm proud of the rim so the pour opening stays open
    master += extrude(rsquare(p.box, p.corner_r), 1.0 + 0.2, rim - 0.2)
    return t + master


def silicone_ml(p, which):
    cw = cavity_w(p)
    if which == "top":
        rim, master = top_rim(p), top_half(p)
    else:
        rim, master = bottom_rim(p), bottom_half(p)
    h = rim - p.floor
    fill = tapered(rsquare(cw, 4), 0, h, draft_offset(h, p.tray_draft))
    keys = Manifold()
    for x, y in key_xy(p):
        keys += key(p, x, y, -0.01)
    if which == "top":
        fill -= keys
    else:
        fill += Manifold.batch_boolean([key(p, x, y, -p.key_h, socket=True) for x, y in key_xy(p)],
                                       OpType.Add)
    return (fill - master).volume() / 1000.0


def checks(p):
    cw = cavity_w(p)
    outer = cw + 2 * p.wall
    lw = lid_w(p)
    f = p.floor
    k = key_xy(p)[0]
    ml_top, ml_bot = silicone_ml(p, "top"), silicone_ml(p, "bottom")
    top_lean = draft_offset(top_rim(p), p.tray_draft)
    bot_lean = draft_offset(bottom_rim(p) + 1, p.tray_draft)
    return {
        "top": [
            dims(x=(outer, outer + 2 * top_lean + 0.5), y=(outer, outer + 2 * top_lean + 0.5),
                 z=top_rim(p) + 0.5),
            solid((0, 0, f + p.lid_h / 2),                          # lid
                  (lw / 2 - 1, lw / 4, f + 1),                        # lid lip edge
                  (lw / 2 + p.ribbon_t / 2, 0, f + p.lid_h / 2),     # ribbon over the lid side
                  (0, lw / 3, f + p.lid_h + p.ribbon_t / 2),         # ribbon over the lid top
                  (p.bow_span / 2 - 17.0 * p.bow_span / 62, 0, f + p.lid_h + p.bow_h * 0.5),  # loop
                  (0, 0, f + p.lid_h + knot_top(p) - 0.5),            # knot
                  (0, 0, top_rim(p) + 0.2),                            # wick pin
                  (k[0], k[1], f + p.key_h - 0.3)),                    # alignment peg
            empty((lw / 2 + 4, lw / 4, f + 5),                        # silicone round the lid
                  (lw / 4, lw / 4, f + p.lid_h + p.bow_h + p.cover / 2)),
            thickness_at((cw / 2 + p.wall / 2, 0, top_rim(p) / 2), p.wall - 0.3),
            custom("silicone to mix", lambda ctx: (True, f"{ml_top:.0f} ml (about {ml_top * 1.1:.0f} g)")),
            flat_base(outer * outer * 0.9),
            no_overhang(),
            single_body(),
        ],
        "bottom": [
            dims(x=(outer, outer + 2 * bot_lean + 0.5), y=(outer, outer + 2 * bot_lean + 0.5),
                 z=bottom_rim(p) + 1.0),
            solid((0, 0, f + body_h(p) / 2),                           # box body
                  (p.box / 2 + p.ribbon_t / 2, 0, f + body_h(p) / 2),  # ribbon down the side
                  (0, 0, bottom_rim(p) + 0.5)),                         # base proud of the rim
            empty((p.box / 2 + 4, p.box / 4, f + 5),                   # silicone round the body
                  (k[0], k[1], f - 0.5)),                               # alignment socket
            custom("silicone to mix", lambda ctx: (True, f"{ml_bot:.0f} ml (about {ml_bot * 1.1:.0f} g)")),
            flat_base(outer * outer * 0.9),
            no_overhang(),
            single_body(),
        ],
    }


def build(p):
    return {"top": build_top(p), "bottom": build_bottom(p)}


def casting(p):
    """The candle, standing on its base."""
    bh = body_h(p)
    body = bottom_half(p).rotate((180, 0, 0)).translate((0, 0, bh))
    lid = top_half(p).translate((0, 0, bh - 0.05))
    return body + lid
