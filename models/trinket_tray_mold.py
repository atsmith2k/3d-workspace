"""One-piece mold for a round trinket tray / ring dish with a fluted outside and a smooth,
shallow well, for cement, plaster or Jesmonite.

Cast upside down: the mold floor forms the tray's top, and a dome standing on the floor
forms the well. The dome's profile starts at about 40 deg from vertical at its foot and
flattens to the top, so it releases easily and leaves a soft bowl. The pour face is the
tray's flat base.

Spec:
  object:       mold for a 100 mm cement / plaster / Jesmonite ring dish
  overall:      tray 100 mm across the flutes at the top, 20 mm tall; well 82 mm across,
                11 mm deep; mold ~108 x 108 x 23 mm (fits the A1 mini)
  mates with:   nothing
  orientation:  opening up, flat floor on the bed, no supports
  must have:    shape fluted (28 flutes) or round; flat rim 9 mm; dome profile with draft at
                its foot; 2 deg draft on the body; floor 3, wall 3
  tolerances:   none (casting)

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Fluted round trinket tray / ring dish mold for cement, plaster or Jesmonite"

PRODUCT = dict(
    title="Fluted Trinket Tray Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "plaster", "jesmonite", "trinket tray", "ring dish",
          "jewelry dish", "fluted", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="cement, plaster or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    shape="fluted",     # fluted | round
    diameter=100.0,     # tray diameter at its top face (across the flutes)
    height=20.0,
    rim=9.0,            # flat rim from the outside to the edge of the well
    well_depth=11.0,
    flutes=28,
    floor=3.0,
    wall=3.0,
    body_draft=2.0,
)

EMBED = 0.1


def body_section(p, r):
    if p.shape == "round":
        return circle(0, 0, r)
    n = p.flutes
    fr = r * math.sin(math.pi / n) * 1.05
    cs = circle(0, 0, r - fr)
    for i in range(n):
        a = 2 * math.pi * i / n
        cs += circle((r - fr) * math.cos(a), (r - fr) * math.sin(a), fr)
    return grow(grow(cs, 1.0), -1.0)


def well_radius(p, f):
    """Well radius at fraction f of its depth (0 = rim level, 1 = bottom of the well)."""
    R = p.diameter / 2 - p.rim
    return R * (1 - 0.25 * f - 0.6 * f * f)


def checks(p):
    R = p.diameter / 2
    lean = draft_offset(p.height, p.body_draft)
    outer = p.diameter + 2 * (lean + p.wall)
    return [
        dims(x=(outer - 2, outer + 1), z=p.floor + p.height),
        empty((R - p.rim / 2, 0, p.floor + 1), (0, 0, p.floor + p.well_depth + 1)),   # rim, above the dome
        solid((0, 0, p.floor + p.well_depth - 0.5), (well_radius(p, 0.5) - 0.5, 0, p.floor + p.well_depth * 0.5)),
        thickness_at((R - p.rim / 2, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(math.pi * R * R * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    r = p.diameter / 2
    lean = draft_offset(p.height, p.body_draft)
    mold = extrude(body_section(p, r + lean + p.wall), p.floor + p.height)
    mold -= drafted(lambda f: body_section(p, r + f * lean), p.floor, p.height + 1, steps=8)
    # dome: one slice per print layer so the bowl is as smooth as the printer can make it
    steps = max(8, round(p.well_depth / 0.2))
    mold += drafted(lambda f: circle(0, 0, well_radius(p, f)), p.floor - EMBED, p.well_depth + EMBED, steps=steps)
    return mold
