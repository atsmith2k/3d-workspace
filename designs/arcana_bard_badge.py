"""Bard merit badge: a lute with music notes swirling out of it and a feathered cap, a
tavern on rolling hills at dusk, BARD on a ribbon banner, merrowed-look satin border.
Arcana & Ink adventurer badge series (frame in `_arcana_badge`).

Spec:
  object:       full round sew-on patch (or a direct design on a jacket, dice bag or tote)
  overall:      `size` mm diameter target; 90 mm stitched at 4x4, 120 mm at 5x7
  fabric:       twill patch blank with tear-away (patch); cut-away on knits
  threads:      wine (dusk sky), rust (far hills, cap), olive (near hills), bark (tavern roof,
                fretboard, soundhole, bridge, pegbox, cap brim), wood (lute bowl,
                ribbon folds), khaki (soundboard, tavern walls), gold (ribbon, rosette,
                notes, windows, pegs, sparkles), bone (strings, plume), bark
                (plume quill, lettering, border): 8 threads, 9 blocks
  must have:    3.0 mm satin border (4x4) sewn last as one ring; spiral (circular) fill
                sky; a lute ~55 mm long on the diagonal with rosette and three strings;
                four notes on a swirl; a feathered cap; hills with a lit tavern; banner
                arc with BARD in block lettering, 8.5 mm caps (4x4)
  lettering:    `cadkit.stitch.lettering.block_text`, set along the banner arc
  density:      every fill knocked out under what sews on top; strings and the swirl
                are single runs over fills; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401  (SIZES: publish)
import _arcana_badge as F

DESCRIPTION = "Bard merit badge patch: lute, swirling notes, feathered cap, tavern hills, banner"
HOOP = "4x4"
DETAIL = (0, -27)
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Bard Adventurer Patch Embroidery Design",
    "A round bard merit badge: lute with swirling notes, feathered cap and a tavern at dusk, BARD banner",
    ["bard", "rpg class", "adventurer patch", "merit badge", "tabletop rpg", "lute",
     "music notes", "minstrel", "patch embroidery", "badge embroidery"],
    "For the party member who solves everything with a song: a golden lute with music "
    "notes swirling out of it, a feathered cap, a cosy tavern on the hills at dusk, and "
    "BARD in bold block letters on a gold ribbon, inside a thick satin border like a "
    "merrowed patch.\n\n"
    "Part of the adventurer merit-badge series. Great on patches, jackets, guitar straps, "
    "dice bags and game-night hoodies.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 9, 20000)


C = np.array([-7.0, -7.0])         # lute body centre
TILT = -40.0                       # local +y (towards the pegbox) points up and right
K = 1.0                            # lute scale


def _place(g):
    return move(rotate(scale(g, K), TILT), *C)


def _place_pts(pts):
    return rotate(np.asarray(pts, float) * K, TILT) + C


def lute():
    body = smooth([(0, -17), (9, -14.5), (14, -6), (13.6, 3), (10.5, 11), (5.5, 18),
                   (-5.5, 18), (-10.5, 11), (-13.6, 3), (-14, -6), (-9, -14.5)])
    board = shrink(body, 2.0)
    hole = circle(0, 4.5, 3.4)
    rosette = circle(0, 4.5, 5.0).difference(circle(0, 4.5, 3.0))
    bridge = rounded_rect(10, 2.4, 0.8, 0, -9)
    neck = rect(5.4, 25.5, 0, 29.75)
    peg = poly([(-2.7, 41.5), (2.7, 41.5), (6.4, 51), (1.6, 52.6)])
    pegs = union(*[circle(x, y, 1.0) for x, y in ((-0.6, 45.5), (6.6, 44.6), (1.4, 50.6), (8.0, 48.8))])
    strings = [[(x, -8), (x, 42)] for x in (-1.3, 0.0, 1.3)]
    return {k: _place(v) for k, v in dict(body=body, board=board, hole=hole, rosette=rosette,
                                          bridge=bridge, neck=neck, peg=peg, pegs=pegs).items()}, \
        [_place_pts(s) for s in strings]


def _note(x, y, h=8.5, beam_to=None, flip=False):
    """An eighth note (or two beamed) with its stem on the right of the head."""
    head = lambda hx, hy: rotate(ellipse(hx, hy, 2.3, 1.65), 22, origin=(hx, hy))
    parts = [head(x, y), rect(1.3, h, x + 1.65, y + h / 2)]
    if beam_to is None:
        flag = poly([(x + 1.0, y + h), (x + 2.3, y + h), (x + 5.6, y + h - 4.2),
                     (x + 4.6, y + h - 5.2), (x + 2.3, y + h - 2.8)])
        parts.append(flag)
    else:
        bx, by = beam_to
        parts += [head(bx, by), rect(1.3, h, bx + 1.65, by + h / 2),
                  poly([(x + 1.0, y + h), (bx + 2.3, by + h), (bx + 2.3, by + h - 2.2),
                        (x + 1.0, y + h - 2.2)])]
    return union(*parts)


def _feather(spine, width):
    """A plume: a smooth outline round a spine, `width` at its widest, pointed at both ends."""
    sp = spline(spine, samples=10)
    t = np.linspace(0, 1, len(sp))
    w = width / 2 * np.sin(np.pi * np.clip(t * 1.15, 0, 1)) ** 0.7
    tan = np.gradient(sp, axis=0)
    nrm = np.c_[-tan[:, 1], tan[:, 0]] / np.linalg.norm(tan, axis=1)[:, None]
    return poly(list(map(tuple, sp + nrm * w[:, None])) + list(map(tuple, (sp - nrm * w[:, None])[::-1])))


def cap():
    """A minstrel's peaked cap in profile: rounded crown, a brim turned up at the back
    and running to a point at the front, a long plume rising from the crown."""
    crown = smooth([(-32.5, 19.5), (-33, 26), (-29, 32), (-22, 33.5), (-16.5, 29),
                    (-14, 22), (-14.5, 19.5)], samples=12)
    brim = smooth([(-37.2, 27.0), (-36, 21.5), (-32, 17.8), (-22, 16.4), (-12, 16.8),
                   (-5.5, 19.4), (-13, 20.4), (-23, 20.0), (-31.5, 21.4), (-35.2, 25.4)], samples=8)
    spine = [(-27.5, 29), (-26, 34), (-21.5, 38.5), (-15, 41)]
    feather = _feather(spine, 6.4)
    return crown, brim, feather, spine


def art():
    d = Design()
    L, strings = lute()
    lute_all = union(*L.values())
    crown, band, feather, spine = cap()
    cap_all = union(crown, band, feather)
    notes = [_note(18, 4), _note(24, 13, beam_to=(30, 16)), _note(6, 31), _note(-2, 36, h=7.0)]
    notes_all = union(*notes)
    swirl = spline([(10, -3), (19, -3.5), (29, 1), (36, 9), (38.5, 18), (37, 26), (33, 29.5),
                    (30, 27.5)], samples=8)
    sparkles = [star(4, 3.2, 0.95, x, y) for x, y in ((-37, 6), (14, 40))]
    far = F.clip(smooth([(-55, -2), (-38, 2.5), (-24, -1), (-8, -9), (10, -7), (26, 0),
                         (40, 3), (55, -2), (55, -45), (-55, -45)], samples=12))
    near = F.clip(smooth([(-55, -10), (-36, -8), (-18, -15), (2, -17), (22, -12),
                          (38, -9), (55, -12), (55, -45), (-55, -45)], samples=12))
    walls = rect(11, 7.5, 32, -9.0)
    roof = poly([(25.4, -5.6), (32, 0.6), (38.6, -5.6)])
    chimney = rect(2.2, 4.4, 35.4, -0.6)
    tavern = union(walls, roof, chimney)
    windows = union(rect(2.2, 2.4, 29.2, -8.4), rect(2.2, 2.4, 34.8, -8.4))
    door = rect(2.0, 3.6, 32, -11.0)   # a lit doorway

    banner = F.banner_all()
    front = [lute_all, cap_all, banner]
    txt = F.lettering("BARD")

    # 1 wine: the dusk sky
    # the spiral's start angle decides where its last ring ends: at 0/90/180 deg it ends
    # in a sliver at the border too short for a tie-off; 15-75 deg is clean at both sizes
    F.backdrop(d, C_["wine"], [far, near, tavern, notes_all, *sparkles, *front], spacing=0.4, angle=30)
    # 2 rust: far hills, the cap crown
    d.fill(knockout(far, near, tavern, *front), C_["rust"], angle=-8, name="far hills")
    d.fill(knockout(crown, band, feather), C_["rust"], angle=-60, name="cap crown")
    # 3 olive: near hills
    d.fill(knockout(near, tavern, *front), C_["olive"], angle=12, name="near hills")
    # 4 bark: tavern roof and chimney, the lute's dark parts, cap band

    d.fill(knockout(roof | chimney, walls, *front), C_["bark"], angle=90, name="tavern roof")
    d.fill(knockout(band, feather), C_["bark"], angle=-30, name="cap brim")
    d.fill(knockout(L["neck"], L["peg"], L["body"]), C_["bark"], angle=TILT + 90, name="neck")
    d.fill(knockout(L["peg"], L["pegs"]), C_["bark"], angle=TILT, name="pegbox")
    d.fill(L["hole"], C_["bark"], angle=TILT, name="soundhole")
    d.fill(L["bridge"], C_["bark"], angle=TILT + 90, name="bridge")
    # 5 wood: the lute's bowl rim, ribbon folds
    d.fill(knockout(L["body"], L["board"], banner), C_["wood"], angle=TILT + 90, name="lute rim")
    d.fill(knockout(F.banner_folds(), F.banner_main(), lute_all), C_["wood"], angle=60,
           name="banner folds")
    # 6 khaki: soundboard, tavern walls
    d.fill(knockout(L["board"], L["rosette"], L["bridge"], banner), C_["khaki"], angle=TILT + 90,
           name="soundboard")
    d.fill(knockout(walls, windows, door, roof, *front), C_["khaki"], angle=0, name="tavern walls")
    # 7 gold: ribbon, rosette, notes, windows, pegs, sparkles
    d.fill(knockout(F.banner_main(), txt, lute_all, overlap=0.3), C_["gold"], angle=2, name="banner")
    d.fill(knockout(L["rosette"], L["hole"]), C_["gold"], angle=TILT, name="rosette")
    d.fill(L["pegs"], C_["gold"], angle=0, name="pegs")
    d.fill(windows | door, C_["gold"], angle=0, name="windows")
    for n in notes:
        d.fill(n, C_["gold"], angle=70, name="note")
    for s in sparkles:
        d.fill(s, C_["gold"], angle=45, name="sparkle")
    d.run(swirl, C_["gold"], bean=1, name="swirl")
    # 8 bone: strings (alternating direction so the travel hides on nut and bridge), feather
    for i, s in enumerate(strings):
        d.run(s if i % 2 == 0 else s[::-1], C_["bone"], name="string")
    d.fill(feather, C_["bone"], angle=60, name="feather")
    # 9 bark: lettering, border
    d.run(spline(spine, samples=8)[2:-5], C_["bark"], name="plume quill")
    F.sew_letters(d, "BARD", C_["bark"])
    F.sew_border(d, C_["bark"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
