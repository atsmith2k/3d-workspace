"""One-piece cement mold for a pebble-shaped incense stick holder: a soft organic outline,
a shallow ash well, and a tapered hole in the middle of the well that holds a stick upright.

Cast upside down: the mold floor forms the holder's top, a dome on the floor forms the ash
well, and a tapered pin on top of the dome forms the stick hole. The pour face becomes the
flat base.

Spec:
  object:       mold for a cement / Jesmonite incense stick holder (also takes cones)
  overall:      holder 120 x 72 mm, 22 mm tall; well 6 mm deep with an 8 mm rim;
                mold ~128 x 80 x 25 mm (fits the A1 mini)
  mates with:   incense sticks with a 1.5-2.5 mm core; hole 3.2 mm at the well widening
                from 2.4 mm at the bottom, 12 mm deep
  orientation:  opening up, flat floor on the bed, no supports
  must have:    pebble outline, ash well dome with draft at its foot, central stick hole;
                2 deg draft on the body; floor 3, wall 3
  tolerances:   none (casting); the hole is a wedge fit

Units: mm. Z is up, the mold sits on Z=0.
"""
from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Pebble incense stick holder mold with an ash well, for cement or Jesmonite"

PRODUCT = dict(
    title="Pebble Incense Holder Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "incense holder", "incense burner",
          "pebble", "minimalist", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="cement, concrete or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    length=120.0,
    width=72.0,
    height=22.0,
    rim=8.0,
    well_depth=6.0,
    hole_top=3.2,       # stick hole at the well
    hole_bottom=2.4,
    hole_depth=12.0,
    floor=3.0,
    wall=3.0,
    body_draft=2.0,
)

EMBED = 0.1
# pebble outline in a 100 x 60 design space, centred on the origin
PEBBLE = [(-50, 2), (-44, 20), (-24, 29), (2, 30), (28, 26), (46, 14), (50, -4),
          (40, -22), (16, -30), (-12, -29), (-36, -22), (-48, -10)]


def pebble(p):
    return smooth_shape(PEBBLE, samples=12).scale((p.length / 100, p.width / 60))


def well(p, f):
    k = 1 - 0.25 * f - 0.6 * f * f
    return grow(pebble(p), -p.rim).scale((k, k))


def checks(p):
    lean = draft_offset(p.height, p.body_draft)
    z_dome = p.floor + p.well_depth
    return [
        dims(x=(p.length + 2 * p.wall, p.length + 2 * (lean + p.wall) + 2),
             y=(p.width + 2 * p.wall, p.width + 2 * (lean + p.wall) + 2), z=p.floor + p.height),
        solid((0, 0, z_dome - 1), (0, 0, z_dome + p.hole_depth - 0.5)),    # dome and the stick pin
        empty((0, 0, z_dome + p.hole_depth + 1), (2.5, 0, z_dome + 1)),      # pin ends; well around it
        thickness_at((p.length / 2 - p.rim / 2, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(p.length * p.width * 0.7),
        no_overhang(),
        single_body(),
    ]


def build(p):
    lean = draft_offset(p.height, p.body_draft)
    outline = pebble(p)
    mold = extrude(grow(outline, lean + p.wall), p.floor + p.height)
    mold -= drafted(lambda f: grow(outline, f * lean), p.floor, p.height + 1, steps=8)
    steps = max(8, round(p.well_depth / 0.2))
    mold += drafted(lambda f: well(p, f), p.floor - EMBED, p.well_depth + EMBED, steps=steps)
    z_dome = p.floor + p.well_depth
    rt, rb = p.hole_top / 2, p.hole_bottom / 2
    mold += drafted(lambda f: circle(0, 0, rt + (rb - rt) * f), z_dome - EMBED, p.hole_depth + EMBED, steps=4)
    return mold
