"""Mold for a trinket tray / ring dish in cement, plaster or Jesmonite.

Choose the version in the title. The fluted tray is 100 mm across with 28 rounded flutes
around the outside; the heart tray is 100 x 85 mm. Both have a smooth, shallow well
11 mm deep for rings, keys or a candle. Pour, screed the
back flat, and lift it out once cured; every surface is tapered so it releases from the
rigid mold. Prints opening-up with no supports in under 2 hours on a Bambu A1 or A1
mini.

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
    title="{shape} Trinket Tray Mold",          # filled from params per variant
    category="molds",
    tags=["mold", "concrete", "cement", "plaster", "jesmonite", "trinket tray", "ring dish",
          "jewelry dish", "fluted", "heart", "valentine", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="cement, plaster or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    shape="fluted",     # fluted | round | heart
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
    if p.shape == "heart":
        return heart(2 * r)
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


def rim_point(p):
    """A point on the flat rim, halfway between the outside and the well, where the
    outline is widest (y = 0 for round shapes)."""
    R = p.diameter / 2
    if p.shape != "heart":
        return R - p.rim / 2, 0.0
    import numpy as np
    pts = [np.asarray(heart(2 * r).to_polygons()[0]) for r in (R, well_radius(p, 0))]
    a, b = (q[np.argmax(q[:, 0])] for q in pts)
    return tuple(float(v) for v in (a + b) / 2)


def checks(p):
    R = p.diameter / 2
    lean = draft_offset(p.height, p.body_draft)
    outer = p.diameter + 2 * (lean + p.wall)
    rx, ry = rim_point(p)
    return [
        dims(x=(outer - 2, outer + 1), z=p.floor + p.height),
        empty((rx, ry, p.floor + 1), (0, 0, p.floor + p.well_depth + 1)),             # rim, above the dome
        solid((0, 0, p.floor + p.well_depth - 0.5), (well_radius(p, 0.5) * 0.8, 0, p.floor + p.well_depth * 0.5)),
        thickness_at((rx, ry, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(math.pi * R * R * (0.6 if p.shape == "heart" else 0.9)),
        no_overhang(),
        single_body(),
    ]


def build(p):
    r = p.diameter / 2
    lean = draft_offset(p.height, p.body_draft)
    if p.shape == "heart":   # an even wall round the notch: offset, not scale
        mold = extrude(grow(body_section(p, r + lean), p.wall), p.floor + p.height)
    else:
        mold = extrude(body_section(p, r + lean + p.wall), p.floor + p.height)
    mold -= tapered(body_section(p, r), p.floor, p.height + 1, lean * (p.height + 1) / p.height)
    # dome: a smooth scaled loft, one band per print layer (stacked slices shred in viewers)
    steps = max(8, round(p.well_depth / 0.2))
    R = well_radius(p, 0)
    base = heart(2 * R) if p.shape == "heart" else circle(0, 0, R)
    mold += scaled_loft(base, p.floor - EMBED, p.well_depth + EMBED,
                        lambda f: well_radius(p, f) / R, steps=steps)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the tray the right way up."""
    return cast_of(build(p))
