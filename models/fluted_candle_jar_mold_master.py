"""Mold masters for a fluted, lidded concrete or Jesmonite candle jar: 102 mm (4 in)
across the rim, 89 mm (3.5 in) tall, 24 vertical flutes below a smooth 10 mm rim band,
and a 104 mm lid with a locating lip and a knob. Holds a poured candle or trinkets.

Four printed pieces make a two-part silicone mold system:
  jar     the jar's outside, standing upside down (rim down) on a keyed base board. Put a
          mold box round the board, pour silicone over it: that is the outer jar mold.
  core    the rigid inner plug for the jar's cavity, hanging from a keyed flange. Fill the
          silicone mold about two-thirds, press the core in until the flange sits on the
          silicone and its groove drops over the silicone key ridge; it centres itself, so
          the wall comes out an even 7 mm. Four vents let air and excess mix out. Use the
          printed core as is (sealed, with release agent) or copy it in silicone.
  lid     the lid's top and knob, standing on its keyed board (underside down). Pour
          silicone over it for the lid mold.
  collar  a keyed ring plate that sits on the lid mold and forms the locating lip: fill
          the lid mold, set the collar on, fill its hole and screed it flat.
Every face the casting leaves is drafted (2 deg outside, 3 deg on the core and lip), so
nothing locks. All four print with no supports.

Spec:
  object:       silicone-mold masters for a fluted lidded cement / Jesmonite candle jar:
                jar master + core plug, lid master + lip collar
  overall:      jar 102 mm (4 in) across the rim flute tips, 89 mm (3.5 in) tall,
                98.9 mm at the foot (2 deg draft); lid 104 mm across, 23 mm with the knob.
                Boards 126 / 128 mm across: a mold box round the board edge gives 12 mm
                silicone walls
  mates with:   core and collar flanges sit on the silicone mold face, keyed by a 3 mm V
                groove at 5 mm outside the piece (the silicone copies the board's groove as
                a ridge; the flanges carry the same groove, 0.2 mm wider)
                lid lip 1.0 mm per side smaller than the jar mouth (concrete-to-concrete)
  casting:      jar wall 7 mm at the flute valleys at the rim, floor 8 mm, cavity 3 deg
                draft (wall grows toward the floor); lid 7 mm at the edge, lip 5 mm deep
  orientation:  jar master: board on the bed, jar rim-down on it, foot up; core: flange
                down, plug up; lid master: board down, knob up; collar: flat, groove down;
                no supports
  must have:    24 rounded flutes, smooth 10 mm rim band, knob 26 mm at the base, vents
                5 mm in the core flange, every cast-touching wall drafted >= 2 deg
  tolerances:   key groove +0.2 mm wide on the flanges; lid lip clearance 1.0 mm per side

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
import math

import numpy as np
from manifold3d import CrossSection, Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Silicone-mold masters for a fluted lidded concrete candle jar (jar, core, lid, collar)"

PRODUCT = dict(
    title="Fluted Lidded Candle Jar Mold Master",
    category="molds",
    tags=["mold master", "silicone mold", "concrete", "cement", "jesmonite", "candle jar",
          "candle vessel", "trinket jar", "fluted", "lidded jar", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="silicone over the masters, then cement, concrete or Jesmonite",
    post_processing=("Sand or prime the jar and lid masters smooth and seal them; silicone copies "
                     "every layer line. Wrap a mold box tight round each board edge (a cut "
                     "cup, foam board or acetate) and pour silicone to 10 mm over the master: "
                     "about 0.55 litre for the jar, 0.35 litre for the lid. Seal the core and "
                     "collar and use release agent on them before every cast."),
    draft=True,
    price=5.99,
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    top_d=101.6,        # jar diameter across the flute tips at the rim (4 in)
    height=88.9,        # jar height (3.5 in)
    flutes=24,
    rim_band=10.0,      # smooth band below the rim
    jar_wall=7.0,       # cast wall at the flute valleys at the rim
    jar_floor=8.0,
    body_draft=2.0,     # jar outside
    core_draft=3.0,     # cavity
    lid_d=0.0,          # 0 = jar diameter + 2 mm
    lid_t=7.0,          # lid edge thickness
    lid_rise=3.0,       # gentle dome from the edge to the knob
    knob_d=26.0,
    knob_h=13.0,
    lip_h=5.0,
    lip_clear=1.0,      # per side, lip to jar mouth
    lip_draft=3.0,
    silicone=12.0,      # silicone wall round each master
    board_t=3.0,
    flange_t=4.0,       # core flange and collar thickness under the groove
    key_w=3.0,          # V key groove width at the face
    key_d=2.6,          # and depth (60 deg sides)
    key_gap=5.0,        # key centre this far outside the piece
    key_clear=0.2,      # extra width of the flange grooves
    vent_d=5.0,
)

EMBED = 0.1
SEG = 256          # smooth round faces: silicone copies every facet


def disc(r):
    return CrossSection.circle(r, SEG)


def flute_section(p, r):
    """Fluted outline with flute tips at radius r."""
    n = p.flutes
    fr = r * math.sin(math.pi / n) * 1.05
    cs = disc(r - fr)
    for i in range(n):
        a = 2 * math.pi * i / n
        cs += CrossSection.circle(fr, 128).translate(((r - fr) * math.cos(a), (r - fr) * math.sin(a)))
    return grow(grow(cs, 1.0), -1.0)


def sizes(p):
    R = p.top_d / 2                                       # rim, flute tips
    lean = draft_offset(p.height, p.body_draft)
    q = np.asarray(flute_section(p, R).to_polygons()[0])
    valley = float(np.hypot(q[:, 0], q[:, 1]).min())     # flute valley radius at the rim
    mouth = valley - p.jar_wall                           # jar opening radius
    depth = p.height - p.jar_floor
    lid_r = (p.lid_d or p.top_d + 2.0) / 2
    lip_r = mouth - p.lip_clear                           # lip at its root
    return dict(R=R, lean=lean, valley=valley, mouth=mouth, depth=depth, lid_r=lid_r,
                lip_r=lip_r, jar_board=R + p.silicone, lid_board=lid_r + p.silicone,
                lid_h=p.lid_t + p.lid_rise + p.knob_h)


def key_groove(r, w, d, z_face, up=True):
    """V groove ring centred on radius r with its mouth at z_face: cut down into a top
    face (up=True) or up into a bottom face (up=False). Overshoots the face by EMBED."""
    sgn = -1 if up else 1
    tri = [(r - w / 2, -sgn * EMBED), (r + w / 2, -sgn * EMBED), (r, sgn * d)]
    if not up:
        tri = tri[::-1]
    return Manifold.revolve(poly(tri), SEG).translate((0, 0, z_face))


def jar_outside(p, s):
    """The jar the right way up, foot at z=0, rim at z=height."""
    H, R, lean = p.height, s["R"], s["lean"]
    r0 = R - lean
    fl = Manifold.extrude(flute_section(p, r0), H, scale_top=(R / r0,) * 2)
    band_h = p.rim_band
    band = Manifold.extrude(disc(R - draft_offset(band_h, p.body_draft)), band_h,
                            scale_top=(R / (R - draft_offset(band_h, p.body_draft)),) * 2)
    return fl + band.translate((0, 0, H - band_h))


def core_plug(p, s):
    """Cavity, the right way up: mouth at z=height, floor at z=jar_floor."""
    lean = draft_offset(s["depth"], p.core_draft)
    m = s["mouth"]
    return Manifold.extrude(disc(m - lean), s["depth"] + EMBED,
                            scale_top=(m / (m - lean),) * 2).translate((0, 0, p.jar_floor))


def lid_body(p, s):
    """Lid top side, underside at z=0 (no lip)."""
    lr = s["lid_r"]
    edge_lean = draft_offset(p.lid_t, p.body_draft)
    lid = Manifold.extrude(disc(lr), p.lid_t, scale_top=((lr - edge_lean) / lr,) * 2)
    top_r = lr - edge_lean - 1.5
    kr = p.knob_d / 2
    # low dome as a cone from the edge shoulder up to the knob foot
    lid += Manifold.extrude(disc(top_r), p.lid_rise + EMBED,
                            scale_top=((kr + 2) / top_r,) * 2).translate((0, 0, p.lid_t - EMBED))
    kz = p.lid_t + p.lid_rise
    k_lean = draft_offset(p.knob_h, 6.0)
    knob = Manifold.extrude(disc(kr), p.knob_h - 2 + EMBED,
                            scale_top=((kr - k_lean) / kr,) * 2).translate((0, 0, kz - EMBED))
    top = kr - k_lean
    knob += Manifold.extrude(disc(top), 2.0, scale_top=((top - 2.0) / top,) * 2) \
        .translate((0, 0, kz + p.knob_h - 2))            # chamfered top
    return lid + knob


def lip(p, s):
    """Locating lip, hanging below the lid underside (z=0 down to -lip_h), narrowing down."""
    lean = draft_offset(p.lip_h, p.lip_draft)
    r = s["lip_r"]
    return Manifold.extrude(disc(r - lean), p.lip_h + EMBED,
                            scale_top=(r / (r - lean),) * 2).translate((0, 0, -p.lip_h))


def checks(p):
    s = sizes(p)
    H, R = p.height, s["R"]
    bt, ft = p.board_t, p.flange_t
    jk = R + p.key_gap
    lk = s["lid_r"] + p.key_gap
    return {
        "jar": [
            dims(x=2 * s["jar_board"], z=bt + H),
            solid((0, 0, bt + H / 2), (R - 1.5, 0, bt + p.rim_band / 2)),
            empty((jk, 0, bt - 0.5), (R + p.silicone / 2 + 3, 0, bt + 1)),     # key groove, clear board
            solid((R - 0.5 - s["lean"], 0, bt + H - 1)),                        # foot is narrower by the draft
            empty((R + 0.3 - s["lean"], 0, bt + H - 1)),
            flat_base(math.pi * s["jar_board"] ** 2 * 0.9),
            no_overhang(),
            single_body(),
        ],
        "core": [
            dims(x=2 * s["jar_board"], z=ft + s["depth"]),
            solid((0, 0, ft + s["depth"] / 2), (s["mouth"] - 0.5, 0, ft + 0.5)),
            empty((s["mouth"] + 0.3, 0, ft + 0.5)),                             # plug edge = jar mouth
            empty((jk, 0, 0.3)),                                                 # key groove underneath
            empty(((s["mouth"] + s["valley"]) / 2 * 0.7071, (s["mouth"] + s["valley"]) / 2 * 0.7071, ft / 2)),  # vent
            custom("cast wall at rim valley", lambda ctx: _wall_ok(p, s)),
            flat_base(math.pi * s["jar_board"] ** 2 * 0.6),
            no_overhang(),
            single_body(),
        ],
        "lid": [
            dims(x=2 * s["lid_board"], z=bt + s["lid_h"]),
            solid((0, 0, bt + s["lid_h"] - 1), (s["lid_r"] - 1, 0, bt + 1)),
            empty((lk, 0, bt - 0.5), (s["lid_r"] + 1, 0, bt + 1)),
            flat_base(math.pi * s["lid_board"] ** 2 * 0.9),
            no_overhang(),
            single_body(),
        ],
        "collar": [
            dims(x=2 * s["lid_board"], z=p.lip_h),
            empty((0, 0, p.lip_h / 2), (s["lip_r"] - 0.5, 0, 0.2)),
            solid((s["lip_r"] + 1.0, 0, p.lip_h / 2)),
            empty((lk, 0, 0.3)),
            hole(2 * s["lip_r"] - 2 * draft_offset(p.lip_h, p.lip_draft), at=(0, 0), tol=0.6),
            flat_base(math.pi * (s["lid_board"] ** 2 - s["lip_r"] ** 2) * 0.8),
            no_overhang(),
            single_body(),
        ],
    }


def _wall_ok(p, s):
    w = s["valley"] - s["mouth"]
    ok = 6.0 <= w <= 8.0 and p.jar_floor >= 6.0
    return ok, f"wall {w:.1f} mm at rim valleys, floor {p.jar_floor:g} mm (want 6-8)"


def build(p):
    s = sizes(p)
    H, bt = p.height, p.board_t
    kw2 = p.key_w + p.key_clear
    # jar master: board + jar upside down, rim on the board
    jar_board = extrude(disc(s["jar_board"]), bt)
    jar_board -= key_groove(s["R"] + p.key_gap, p.key_w, p.key_d, bt, up=True)
    jar = jar_outside(p, s).mirror((0, 0, 1)).translate((0, 0, H + bt - EMBED))
    jar = jar_board + jar

    # core: flange on the bed, plug rising to the jar floor
    ft = p.flange_t
    core = extrude(disc(s["jar_board"]), ft)
    core -= key_groove(s["R"] + p.key_gap, kw2, p.key_d + 0.2, 0.0, up=False)
    plug = core_plug(p, s).mirror((0, 0, 1)).translate((0, 0, H + ft))   # mouth at z=ft
    core += plug
    vent_r = (s["mouth"] + s["valley"]) / 2
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        core -= extrude(circle(vent_r * math.cos(a), vent_r * math.sin(a), p.vent_d / 2), ft + 2, -1)

    # lid master: board + lid upright on it
    lid_board = extrude(disc(s["lid_board"]), bt)
    lid_board -= key_groove(s["lid_r"] + p.key_gap, p.key_w, p.key_d, bt, up=True)
    lid = lid_board + lid_body(p, s).translate((0, 0, bt - EMBED))

    # collar: plate whose hole is the lip; hole widest at the bed (the lid underside)
    collar = extrude(disc(s["lid_board"]), p.lip_h)
    collar -= key_groove(s["lid_r"] + p.key_gap, kw2, p.key_d + 0.2, 0.0, up=False)
    r, lean = s["lip_r"], draft_offset(p.lip_h, p.lip_draft)
    hh = p.lip_h + 2
    collar -= Manifold.extrude(disc(r + lean / p.lip_h), hh,
                               scale_top=((r - lean * (hh - 1) / p.lip_h) / (r + lean / p.lip_h),) * 2)         .translate((0, 0, -1))
    return {"jar": jar, "core": core, "lid": lid, "collar": collar}


def casting(p):
    """What the molds make, for the shop's cast render: the jar with its lid on."""
    s = sizes(p)
    jar = jar_outside(p, s) - core_plug(p, s)
    cap = lid_body(p, s) + lip(p, s)
    return jar + cap.translate((0, 0, p.height))
