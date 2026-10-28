"""Vacuum-forming bucks for a heart-shaped treat box with a lid: print the two bucks,
form 0.5 mm PETG or polystyrene sheet over them, trim, and you have clear heart boxes
for Valentine's treats, favours or small gifts.

The box is 80 mm across and 30 mm deep. The lid buck is sized for the sheet thickness so
the formed lid slips about 5 mm down over the formed box and sits snug. Both bucks
taper at 5 deg so the sheet lets go, have rounded top edges so it doesn't tear, and have
a small vent at the heart's notch so the sheet pulls into it. Print them solid-ish (four
walls) so they don't soften under the heater. Both print with no supports in under an
hour on a Bambu A1 or A1 mini.

Spec:
  object:       two vacuum-forming bucks (box + lid) for a heart treat box
  overall:      box buck 80 x 68 x 30 mm; lid buck 82 x 70 x 12 mm
  casting:      formed from 0.5 mm PETG / PS sheet; lid buck outline = box buck base
                outline + sheet 0.5 + clearance 0.4 per side, so the lid engages ~4.6 mm
  orientation:  both flat base on the bed (the face the sheet drapes over is up);
                no supports
  must have:    5 deg draft on every side, 3 mm rounded top edge, 1.5 mm vent through
                each buck at the notch
  tolerances:   lid over box 0.4 mm per side at the rim

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Vacuum-forming bucks for a heart-shaped treat box and its lid"

PRODUCT = dict(
    title="Heart Treat Box Vacuum Forming Bucks",
    category="molds",
    tags=["vacuum forming", "thermoforming", "buck", "mold", "heart", "valentine", "treat box",
          "gift box", "favor box", "petg"],
    printers=["a1", "a1mini"],
    cast_material="0.5 mm PETG or polystyrene sheet",
    post_processing=("Print with 4 walls and 30% infill so the bucks stay rigid under the heater. "
                     "Lightly sand the tops. Form 0.5 mm sheet over each buck, let it cool on the "
                     "buck, pop it off and trim the flange with scissors."),
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    width=80.0,         # box buck width at its base
    box_h=30.0,
    lid_h=12.0,
    draft=5.0,
    round_top=3.0,
    sheet=0.5,
    clearance=0.4,
    vent_d=1.5,
)


def buck(p, width, h):
    """A heart buck `width` mm across at the base, tapering at `draft`, top edge rounded."""
    import math
    base = heart(width)
    lean = draft_offset(h, p.draft)
    body_h = h - p.round_top
    body_lean = lean * body_h / h
    out = tapered(base, 0, body_h + 0.01, -body_lean)        # smooth sides
    # the taper's own top outline (it scales per axis about the bounding-box centre)
    x0, y0, x1, y1 = base.bounds()
    w, d = x1 - x0, y1 - y0
    top = base.scale(((w - 2 * body_lean) / w, (d - 2 * body_lean) / d))
    # rounded top edge: quarter-circle steps, each an inset of that outline, so every step
    # sits inside the one below (no lip, no overhang)
    n = 6
    for i in range(n):
        a0, a1 = math.pi / 2 * i / n, math.pi / 2 * (i + 1) / n
        z0 = body_h + p.round_top * math.sin(a0)
        z1 = body_h + p.round_top * math.sin(a1)
        sec = grow(top, -p.round_top * (1 - math.cos(a1)) - 0.01)
        if sec.is_empty():
            break
        out += extrude(sec, z1 - z0 + 0.02, z0 - 0.01)
    # vent at the notch, through the buck
    notch_y = max(q[1] for q in base.to_polygons()[0] if abs(q[0]) < 0.6)
    vent = extrude(circle(0, notch_y - 4.0, p.vent_d / 2), h + 2, -1)
    return out - vent, notch_y - 4.0


def lid_base(p):
    """Lid buck base: the box buck base grown by the sheet and the clearance."""
    return grow(heart(p.width), p.sheet + p.clearance)


def lid_width(p):
    x0, _, x1, _ = lid_base(p).bounds()
    return x1 - x0


def checks(p):
    lw = lid_width(p)
    _, vy = buck(p, p.width, p.box_h)
    return {
        "box": [
            dims(x=(p.width - 0.5, p.width + 0.5), z=p.box_h),
            solid((0, -5, p.box_h / 2)),
            empty((0, vy, p.box_h / 2)),                     # vent goes through
            flat_base(p.width ** 2 * 0.5),
            no_overhang(),
            single_body(),
        ],
        "lid": [
            dims(x=(lw - 0.5, lw + 0.5), z=p.lid_h),
            solid((0, -5, p.lid_h / 2)),
            flat_base(lw ** 2 * 0.5),
            no_overhang(),
            single_body(),
        ],
    }


def build(p):
    box, _ = buck(p, p.width, p.box_h)
    lid, _ = buck(p, lid_width(p), p.lid_h)
    return {"box": box, "lid": lid}
