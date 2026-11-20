"""Mold master for a Nutcrackercore taper candle holder: a bold, simplified nutcracker
soldier, 6 in (152 mm) tall on a 2 in (51 mm) rectangular plinth, with a tall hat whose
top holds a standard 7/8 in taper candle.

Print the master, make a silicone mold over it, and cast the holder in concrete or
Jesmonite. The master stands on its plinth in a mold box; silicone is poured over it,
and the plinth's underside becomes the open pour face of the mold. Every vertical face
leans in 2 degrees toward the hat, so the silicone peels upward off the master, and every
feature that sticks out (hat band, chin, epaulettes, arms, cuffs, belt, buttons,
mustache, nose) has a 45 degree underside, which is what lets it print with no supports
and keeps the undercuts shallow. The candle socket in the hat is a recess in the master,
so the silicone forms a plug and the cast comes out with the socket.

Spec:
  object:       positive master for a silicone mold that casts a nutcracker soldier
                taper-candle holder in concrete / Jesmonite (the cast is this shape)
  overall:      51 x 38 x 152 mm (2 x 1.5 x 6 in); figure 46 mm wide at the epaulettes
  mates with:   7/8 in taper candle (22.2 mm): socket 22.9 mm at the mouth, 25.4 mm deep,
                1 deg draft (22.0 mm at the floor), so a 22.2 mm candle wedges ~20 mm in
  orientation:  upright on the plinth, hat up; no supports
  mold:         one-piece block (glove) mold with one relief cut up the back; assumed
                silicone Shore 20-30A, 8-10 mm over the master; pour face = plinth bottom
  must have:    rectangular plinth 51 x 38 x 12 mm; boots and legs; jacket with belt,
                buckle and 6 buttons (5 mm, 1.5 mm proud); arms with cuffs and epaulettes;
                big head with beard, mustache, nose and recessed eyes; hat band and tall
                hat with a raised star (13 mm, 1.6 proud); candle socket 22.9 x 25.4 mm deep in the hat
  draft:        2 deg on every vertical face (inward going up), 45 deg undersides
  tolerances:   socket wall >= 5.5 mm of concrete; finest relief 1.5 mm (buttons), others
                up to 4 mm (nose); recessed eyes 4.4 mm x 1.5 deep

Units: mm. Z is up, the master sits on Z=0 on its plinth. Front faces -Y.
"""
import math

from manifold3d import Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Nutcracker soldier taper candle holder, silicone mold master for concrete casting"

PRODUCT = dict(
    title="Nutcracker Soldier Candle Holder Mold Master",
    category="molds",
    tags=["mold master", "silicone mold", "nutcracker", "nutcrackercore", "christmas",
          "candle holder", "taper candle", "concrete mold", "jesmonite", "holiday decor",
          "christmas decor", "soldier"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A) over the master, then concrete or Jesmonite",
    post_processing=(
        "Sand or prime the master: silicone copies every layer line. Glue the plinth face "
        "down in a mold box with 8-10 mm clearance all round and above the hat, spray "
        "release, and pour silicone in a thin stream into a corner. After cure, cut one "
        "zig-zag slit up the back of the silicone from the plinth to the hat brim and peel "
        "it off the master. Close the slit with tape or a mother mold, stand the mold "
        "hat-down, and pour concrete or Jesmonite through the plinth opening; vibrate, "
        "screed flat and demold after cure. Check that the taper candle seats before "
        "sealing the cast."),
    sellable=None,
    draft=True,          # new product: shop's Draft Products review queue
    price=5.99,          # suggested, $4.99-6.99 band
)
LICENSE_NOTES = None   # original stylised design, no brand character

PARAMS = dict(
    height=152.0,        # overall, plinth bottom to hat top (6 in)
    base_w=51.0,         # plinth width (2 in); the figure scales with it
    base_d=38.0,         # plinth depth (1.5 in)
    base_h=12.0,         # plinth height
    draft=2.0,           # degrees on vertical faces
    hat_d=34.0,          # hat diameter at the top rim
    socket_d=22.9,       # candle socket diameter at the mouth (0.9 in)
    socket_depth=25.4,   # 1 in
    socket_draft=1.0,    # degrees; narrows toward the floor so the candle wedges
    button_d=5.0,
    relief=1.5,          # how far buttons, buckle and cuffs stand proud
)

EMBED = 0.5   # overlap where one part grows out of another (never coplanar)


# ---------------------------------------------------------------- helpers
def rrect(w, d, r, cx=0.0, cy=0.0):
    r = max(0.2, min(r, w / 2 - 0.05, d / 2 - 0.05))
    hw, hd = w / 2 - r, d / 2 - r
    return grow(poly([(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]), r).translate((cx, cy))


def sec(cs, z):
    return extrude(cs, 0.01, z)


def hull(*parts):
    return Manifold.batch_hull(list(parts))


class Fig:
    """Figure dimensions derived from the params (z levels scale with the height, widths
    with the plinth width)."""

    def __init__(self, p):
        self.p = p
        self.t = math.tan(math.radians(p.draft))
        sz = (p.height - p.base_h) / 140.0
        sw = p.base_w / 51.0
        self.sw = sw
        z = lambda k: p.base_h + k * sz          # noqa: E731  (k: mm above the plinth at 152 mm)
        self.boot_top = z(14)
        self.leg_top = z(38)
        self.jacket_bot = z(38)
        self.belt = (z(44), z(49))
        self.cuff = (z(50), z(54))
        self.arm_bot = z(48)
        self.buttons = [z(56), z(64), z(72)]
        self.ep = (z(74), z(81))
        self.jacket_top = z(78)
        self.head_bot = z(82)
        self.head_top = z(105)
        self.band_bot = z(111)
        self.hat_bot = z(117)
        self.top = p.height
        self.star_z = z(129)
        # widths
        self.jw, self.jd = 36 * sw, 24 * sw              # jacket at its hem
        self.hw, self.hd = 30 * sw, 26 * sw              # head
        self.band_d = p.hat_d + 2 * (self.top - self.hat_bot) * self.t + 1.0
        self.socket_bot = self.top - p.socket_depth

    def lean(self, dz):
        return dz * self.t

    def jacket_front(self, zz):
        return -(self.jd / 2 - self.lean(zz - self.jacket_bot))

    def head_front(self, zz):
        return -(self.hd / 2 - self.lean(zz - self.head_bot))


def block(f, z0, z1, w, d, r, cx=0.0, cy=0.0, under=0.0, top=0.0):
    """Drafted rounded box from z0 to z1; `under` adds a 45 deg chamfer below (into the
    part it stands on), `top` a 45 deg chamfer at the top."""
    l = f.lean(z1 - z0)
    secs = [sec(rrect(w, d, r, cx, cy), z0)]
    if under:
        secs.append(sec(rrect(w - 2 * under, d - 2 * under, r, cx, cy), z0 - under))
    zt = z1 - top
    secs.append(sec(rrect(w - 2 * f.lean(zt - z0), d - 2 * f.lean(zt - z0), r, cx, cy), zt))
    if top:
        secs.append(sec(rrect(w - 2 * l - 2 * top, d - 2 * l - 2 * top, r, cx, cy), z1))
    return hull(*secs)


def stud(cs, y_face, depth, z, embed=1.0):
    """Front relief: 2D shape `cs` in the X-Z plane (centred on z=0), standing `depth`
    proud of a face at y_face, with a 45 deg underside and an embedded back."""
    plate = extrude(cs, 0.01).rotate((90, 0, 0))     # (x, v) -> (x, ~0, v)
    low = plate.translate((0, y_face + embed, z - depth - embed))
    back = plate.translate((0, y_face + embed, z))
    front = plate.translate((0, y_face - depth, z))
    return hull(low, back, front)


def star(r, inner=0.45):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return poly(pts)


# ---------------------------------------------------------------- checks
def checks(p):
    f = Fig(p)
    sb = f.socket_bot
    d_mid = p.socket_d - 2 * f.lean(0) - 2 * math.tan(math.radians(p.socket_draft)) * p.socket_depth / 2
    return [
        dims(x=p.base_w, y=p.base_d, z=p.height),
        hole(round(d_mid, 2), at=(0, 0), span=(sb + 0.6, p.height - 1.5), tol=0.3),
        solid((0, 0, sb - 1.5)),                                    # socket floor
        empty((0, 0, sb + 0.5)),                                    # socket reaches full depth
        thickness_at((p.socket_d / 2 + 2.5, 0, p.height - 6), 5.0, direction=(1, 0, 0)),
        solid((0, 0, p.base_h / 2)),                                # plinth
        solid((7.4 * f.sw, 0, f.boot_top - 3), (-6.3 * f.sw, 0, f.leg_top - 5), (0, 0, f.leg_top - 5)),   # boots, legs
        solid((19 * f.sw, 0, (f.cuff[1] + f.ep[0]) / 2),            # arms
              (-19 * f.sw, 0, (f.cuff[1] + f.ep[0]) / 2)),
        solid((5.5 * f.sw, f.jacket_front(f.buttons[1]) - p.relief + 0.4, f.buttons[1])),  # a button stands proud
        solid((0, 0, (f.head_bot + f.head_top) / 2), (p.socket_d / 2 + 2.5, 0, f.star_z)),
        solid((0, -(p.hat_d / 2 + f.lean(f.top - f.star_z)) - 0.6, f.star_z)),   # star stands proud
        flat_base(p.base_w * p.base_d * 0.85),
        no_overhang(),
        single_body(),
    ]


# ---------------------------------------------------------------- build
def build(p):
    f = Fig(p)
    sw, t = f.sw, f.t
    parts = []

    # plinth: drafted, 1.5 mm chamfer round the top edge
    parts.append(block(f, 0, p.base_h, p.base_w, p.base_d, 4 * sw, top=1.5))

    # boots (toes forward), touching in the middle so the V between them is not a slot
    for s in (-1, 1):
        parts.append(block(f, p.base_h - EMBED, f.boot_top, 15.5 * sw, 23 * sw, 5 * sw,
                           cx=s * 7.4 * sw, cy=-1.5 * sw, top=1.5))
        parts.append(block(f, f.boot_top - 2, f.leg_top + 1, 14.5 * sw, 19 * sw, 4.5 * sw,
                           cx=s * 6.3 * sw))

    # jacket: hem chamfered 45 deg down onto the legs, shoulders sloping into the neck
    jl = f.lean(f.jacket_top - f.jacket_bot)
    jacket = block(f, f.jacket_bot, f.jacket_top, f.jw, f.jd, 6 * sw, under=4 * sw)
    neck = hull(sec(rrect(f.jw - 2 * jl, f.jd - 2 * jl, 6 * sw), f.jacket_top - 0.01),
                sec(rrect(22 * sw, 18 * sw, 6 * sw), f.head_bot + 1))
    parts += [jacket, neck]

    # belt and buckle
    b0, b1 = f.belt
    bl = f.lean(b0 - f.jacket_bot)
    parts.append(block(f, b0, b1, f.jw - 2 * bl + 2.4, f.jd - 2 * bl + 2.4, 7 * sw, under=1.2))
    belt_front = -(f.jd - 2 * bl + 2.4) / 2
    parts.append(stud(rrect(10 * sw, 7 * sw, 1.2), belt_front, p.relief, (b0 + b1) / 2))

    # buttons, two columns of three
    for zb in f.buttons:
        for s in (-1, 1):
            parts.append(stud(circle(0, 0, p.button_d / 2), f.jacket_front(zb), p.relief, zb)
                         .translate((s * 5.5 * sw, 0, 0)))

    # arms hanging at the sides, 45 deg undersides sloping into the jacket
    for s in (-1, 1):
        cx = s * 19 * sw
        out = 6 * sw                    # how far the arm sits outside the jacket side
        aw, ad = 9 * sw, 13 * sw
        arm_top = f.ep[1] - 1
        al = f.lean(arm_top - f.arm_bot)
        parts.append(hull(sec(rrect(aw, ad, 3.5 * sw, cx - s * out), f.arm_bot - out),
                          sec(rrect(aw, ad, 3.5 * sw, cx), f.arm_bot),
                          sec(rrect(aw - 2 * al, ad - 2 * al, 3.5 * sw, cx - s * al), arm_top)))
        c0, c1 = f.cuff
        parts.append(block(f, c0, c1, aw + 2 * p.relief, ad + 2 * p.relief, 4 * sw,
                           cx=cx - s * f.lean(c0 - f.arm_bot), under=p.relief))
        e0, e1 = f.ep
        parts.append(block(f, e0, e1, 12 * sw, 15 * sw, 4 * sw,
                           cx=cx - s * (f.lean(e0 - f.arm_bot) - 0.5), under=2.0, top=2.0))

    # head with a 45 deg jaw into the neck
    parts.append(block(f, f.head_bot, f.head_top, f.hw, f.hd, 9 * sw, under=4 * sw))
    # face: beard, mustache, nose (all studs on the face front)
    zf = f.head_bot + 4 * sw
    parts.append(stud(rrect(19 * sw, 10 * sw, 4.5 * sw), f.head_front(zf), 3.0 * sw, zf, embed=3.0))
    yb = f.head_front(zf) - 3.0 * sw
    zm = f.head_bot + 10.5 * sw
    for s in (-1, 1):
        parts.append(stud(ellipse(s * 5.0 * sw, 0, 5.6 * sw, 2.6 * sw), yb + 1.0, 2.0 * sw, zm))
    zn = f.head_bot + 14.5 * sw
    parts.append(stud(circle(0, 0, 3.8 * sw), f.head_front(zn), 4.0 * sw, zn))

    # hat: brim slope from the head (45 deg at the front), band, tall drafted crown
    band_r = f.band_d / 2
    slope = max(band_r - (f.hd / 2 - f.lean(f.head_top - f.head_bot)),
                band_r - (f.hw / 2 - f.lean(f.head_top - f.head_bot)))
    head_top_cs = rrect(f.hw - 2 * f.lean(f.head_top - f.head_bot),
                        f.hd - 2 * f.lean(f.head_top - f.head_bot), 9 * sw)
    parts.append(hull(sec(head_top_cs, f.band_bot - slope),
                      sec(circle(0, 0, band_r), f.band_bot),
                      sec(circle(0, 0, band_r - f.lean(f.hat_bot - f.band_bot)), f.hat_bot)))
    crown_r = p.hat_d / 2 + f.lean(f.top - f.hat_bot)
    parts.append(hull(sec(circle(0, 0, crown_r), f.hat_bot - EMBED),
                      sec(circle(0, 0, p.hat_d / 2 + f.lean(1.0)), f.top - 1.0),
                      sec(circle(0, 0, p.hat_d / 2 - 0.0), f.top - 0.01)))

    fig = Manifold.batch_boolean(parts, OpType.Add)

    # recessed eyes
    ze = f.head_bot + 19.0 * sw
    for s in (-1, 1):
        eye = Manifold.cylinder(6.0, 2.2 * sw, 2.2 * sw, 40).rotate((90, 0, 0))
        fig -= eye.translate((s * 7.5 * sw, f.head_front(ze) + 1.5, ze))   # 1.5 mm deep

    # raised star on the hat front, following the crown's curve
    rz = p.hat_d / 2 + f.lean(f.top - f.star_z)
    star_cs = grow(grow(star(6.5 * sw, 0.5), -0.7), 0.7)
    star_m = extrude(star_cs, rz + 5).rotate((90, 0, 0)).translate((0, 0, f.star_z))
    shell = tapered(circle(0, 0, rz + 1.6 + f.lean(8)), f.star_z - 8, 16, -2 * f.lean(8))
    fig += star_m ^ shell

    # candle socket: 1 deg draft, small chamfer at the mouth
    rt = p.socket_d / 2
    rb = rt - math.tan(math.radians(p.socket_draft)) * p.socket_depth
    sock = hull(sec(circle(0, 0, rb), f.socket_bot),
                sec(circle(0, 0, rt + math.tan(math.radians(p.socket_draft))), p.height + 1))
    mouth = hull(sec(circle(0, 0, rt - 0.05), p.height - 0.8),
                 sec(circle(0, 0, rt + 0.8), p.height - 0.005),
                 sec(circle(0, 0, rt + 0.8), p.height + 1))
    # half a segment round, so measuring rays at 30 deg steps hit facets, not vertices
    fig -= (sock + mouth).rotate((0, 0, 180.0 / CIRC))
    return fig


def casting(p):
    """The cast is the master's own shape (positive master, silicone mold)."""
    return build(p)
