"""Mold for a cement or Jesmonite Star of David tealight holder: a six-point star block
105 mm point to point and 28 mm tall, with rounded points and a pocket for a standard
tealight in the middle.

The holder is cast upside down: the mold floor shapes its top face and a drafted boss
standing on the floor forms the tealight pocket. Pour, tap out the air, screed the back
flat, and lift the holder out once cured: every wall is tapered so it releases from the
rigid mold. Prints opening-up with no supports.

Spec:
  object:       mold for a cement / Jesmonite Star of David tealight holder, poured
                straight into the print
  overall:      holder 105 mm point to point (91 mm across the flats of the star), 28 mm
                tall; mold ~113 x 99 x 31 mm, fits a 180 mm bed
  mates with:   standard tealight (aluminium cup 38-39.5 mm dia x ~16 mm, the common
                "tea light" size; no tealight entry in cadkit.hardware): pocket 40.5 mm
                at the bottom (39.5 + 0.5 per side), 17 mm deep, opening at 3 deg so the
                cup lifts out
  orientation:  opening up, flat floor on the bed, no supports
  must have:    hexagram outline, points rounded to 4 mm, inner corners to 2 mm;
                2 deg draft on the body, 3 deg on the pocket boss; floor 3, wall 3;
                at least 8 mm of cement between the pocket and the star's inner corners
  tolerances:   pocket +0.5 mm per side for the tealight cup

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Star of David tealight holder mold for cement or Jesmonite"

PRODUCT = dict(
    title="Star of David Tealight Holder Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "hanukkah", "chanukah", "judaica",
          "star of david", "magen david", "tealight", "candle holder", "holiday"],
    printers=["a1", "a1mini"],
    cast_material="cement, concrete or Jesmonite",
    motif="Star of David",
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    size=105.0,         # point to point, at the holder's top face
    height=28.0,
    tip_round=4.0,      # radius on the six points
    notch_round=2.0,    # radius in the six inner corners
    candle_d=39.5,      # tealight cup diameter
    clear=0.5,          # per side at the bottom of the pocket
    pocket_depth=17.0,
    pocket_draft=3.0,
    floor=3.0,
    wall=3.0,
    body_draft=2.0,
)

EMBED = 0.1


def star(p):
    """Hexagram outline at the holder's top face, one point up (+Y), centred."""
    R = p.size / 2 + p.tip_round              # rounding a 60 deg point pulls it back by r
    r_in = R / math.sqrt(3)
    pts = []
    for k in range(12):
        a = math.radians(90 + 30 * k)
        r = R if k % 2 == 0 else r_in
        pts.append((r * math.cos(a), r * math.sin(a)))
    cs = poly(pts)
    cs = grow(grow(cs, -p.tip_round), p.tip_round)
    return grow(grow(cs, p.notch_round), -p.notch_round)


def body(p, z, height, lean):
    """The star prism from z up, grown by `lean` at the top (exact draft on every side)."""
    cs = star(p)
    out = offset_loft(cs, [(z, 0.0), (z + height, lean)])
    return out if out is not None else tapered(cs, z, height, lean)


def pocket_r(p):
    return p.candle_d / 2 + p.clear


def _cement_ok(p, need=8.0):
    import numpy as np
    q = np.asarray(star(p).to_polygons()[0])
    rim = pocket_r(p) + draft_offset(p.pocket_depth, p.pocket_draft)
    gap = float(np.hypot(q[:, 0], q[:, 1]).min() - rim)
    return gap >= need, f"{gap:.1f} mm (need {need:g})"


def checks(p):
    lean = draft_offset(p.height, p.body_draft)
    out_y = p.size + 2 * (lean + p.wall)
    out_x = p.size * math.cos(math.pi / 6) + 2 * (lean + p.wall)
    r = pocket_r(p)
    mid = (r + p.size / 2 / math.sqrt(3)) / 2 + 3      # cement zone between pocket and notch
    return [
        dims(x=(out_x - 2, out_x + 1.5), y=(out_y - 1.5, out_y + 1.5), z=p.floor + p.height),
        fits_bed(),
        empty((0, p.size / 2 - 6, p.floor + p.height / 2),     # top point cavity
              (0, mid, p.floor + 1)),
        solid((0, 0, p.floor + p.pocket_depth / 2),             # pocket boss
              (r - 0.3, 0, p.floor + p.pocket_depth - 0.3)),    # boss top wide enough for the cup
        empty((0, 0, p.floor + p.pocket_depth + 1.0)),          # boss stops at pocket depth
        thickness_at((0, mid, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        custom("cement round pocket", lambda ctx: _cement_ok(p)),
        flat_base(p.size ** 2 * 0.45),
        no_overhang(),
        single_body(),
    ]


def build(p):
    h = p.height
    lean = draft_offset(h, p.body_draft)
    mold = extrude(grow(star(p), lean + p.wall), p.floor + h)
    mold -= body(p, p.floor, h + 1, lean * (h + 1) / h)
    # tealight pocket: a boss on the floor, narrowing upward to the cup size
    boss_lean = draft_offset(p.pocket_depth, p.pocket_draft)
    mold += tapered(circle(0, 0, pocket_r(p) + boss_lean), p.floor - EMBED, p.pocket_depth + EMBED,
                    -boss_lean)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the holder the right way up."""
    return cast_of(build(p))
