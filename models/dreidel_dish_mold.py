"""Mold for a cement, plaster or Jesmonite trinket / ring dish shaped like a dreidel seen
from the side: a round-topped handle, a square body with rounded corners and a point.
The dish is 125 mm long and 20 mm tall, with an 11 mm deep well in the body and point
and a Star of David engraved on the well floor.

The dish is cast upside down in a one-piece open mold: the mold floor shapes the dish's
top face and a drafted island standing on the floor forms the well, with a raised star
on the island that engraves the well floor. Pour, screed the back flat, and lift the
dish out once cured; every surface is tapered so it releases from the rigid mold.
Prints opening-up with no supports.

Spec:
  object:       mold for a dreidel-shaped cement / plaster / Jesmonite ring dish
  overall:      dish 125 x 80 mm at its top face (handle 15 wide, 22 long; body 80 x 60,
                10 mm corners; point 43 long), 20 mm tall; mold ~87 x 132 x 23 mm
                (fits a 180 mm bed)
  mates with:   nothing
  orientation:  opening up, flat floor on the bed, no supports; handle toward +Y
  must have:    well 11 mm deep, 8 mm rim round the body and point (the handle stays
                solid), 8 deg draft on the well wall with its floor edge rounded 3 mm;
                Star of David on the well floor 34 mm point to point, two triangle lines
                1.6 wide x 0.8 deep, 10 deg draft; 2 deg draft on the body; floor 3, wall 3
  tolerances:   none (casting); the dreidel and star are symmetric, so nothing needs
                mirroring

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Dreidel-shaped trinket / ring dish mold with a Star of David, for cement or Jesmonite"

PRODUCT = dict(
    title="Dreidel Trinket Dish Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "plaster", "hanukkah", "chanukah",
          "judaica", "dreidel", "star of david", "trinket tray", "ring dish", "holiday"],
    printers=["a1", "a1mini"],
    cast_material="cement, plaster or Jesmonite",
    motif="dreidel",
    draft=True,
    collection="festival-of-lights",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    body_w=80.0,
    body_h=60.0,        # body length along Y
    body_round=10.0,
    handle_w=15.0,
    handle_len=22.0,
    point_len=43.0,
    tip_round=6.0,       # at least the 6 mm shoulder rounding, so the tip length stays exact
    height=20.0,        # dish height
    rim=8.0,            # flat rim round the well
    well_depth=11.0,
    well_draft=8.0,
    well_round=3.0,     # well floor edge rounded to this
    star=34.0,          # point to point
    star_line=1.6,
    star_depth=0.8,
    star_draft=10.0,
    floor=3.0,
    wall=3.0,
    body_draft=2.0,
)

EMBED = 0.1


def layout(p):
    """Y positions: body centred so the whole dreidel is centred on the origin."""
    total = p.handle_len + p.body_h + p.point_len
    y_top = total / 2                       # top of the handle
    body_top = y_top - p.handle_len
    body_bot = body_top - p.body_h
    tip = body_bot - p.point_len            # = -total / 2
    return y_top, body_top, body_bot, tip, (body_top + body_bot) / 2


def outline(p):
    y_top, body_top, body_bot, tip, yc = layout(p)
    r = p.body_round
    body = grow(CrossSection.square((p.body_w - 2 * r, p.body_h - 2 * r), center=True), r).translate((0, yc))
    hw = p.handle_w / 2
    handle = stroke([(0, body_top - 5), (0, y_top - hw)], p.handle_w)
    # the point tapers from where the body's sides are still straight, so the sides run
    # into it without a notch; its shoulder is rounded below
    y0 = body_bot + r
    half = math.atan2(p.body_w / 2, y0 - tip)                # half angle at the tip
    pull = p.tip_round / math.sin(half) - p.tip_round        # rounding pulls the tip back by this
    point = poly([(-p.body_w / 2, y0), (p.body_w / 2, y0), (0, tip - pull)])
    point = grow(grow(point, -p.tip_round), p.tip_round)
    cs = body + handle + point
    cs = grow(grow(cs, 4.0), -4.0)              # fillet where the handle meets the body
    return grow(grow(cs, -6.0), 6.0)            # round the shoulders into the point


def well(p):
    """Well outline at the dish's top face: rim in from the outline, handle left solid."""
    cs = grow(outline(p), -p.rim)
    return grow(grow(cs, -6.0), 6.0)            # drops the handle stub, keeps corners round


def well_floor_at(p):
    return layout(p)[4] - 4.0                     # star centre, a little below the body centre


def hexagram_lines(p):
    R = p.star / 2
    yc = well_floor_at(p)
    out = CrossSection()
    for a0 in (90, -90):
        pts = [(R * math.cos(math.radians(a0 + 120 * k)), yc + R * math.sin(math.radians(a0 + 120 * k)))
               for k in range(3)]
        out += stroke(pts + [pts[0]], p.star_line)
    return out


def island(p):
    """Positive core on the floor that forms the well: drafted wall, rounded top edge."""
    z0 = p.floor - EMBED
    top = p.floor + p.well_depth
    lean = draft_offset(p.well_depth - p.well_round, p.well_draft)
    stations = [(z0, 0.0), (top - p.well_round, -lean)]
    for k in range(1, 7):                       # quarter round over the last well_round mm
        t = k / 6 * math.pi / 2
        stations.append((top - p.well_round + p.well_round * math.sin(t),
                         -lean - p.well_round * (1 - math.cos(t))))
    base = well(p).simplify(0.01)                # near-duplicate points break the offset rays
    out = offset_loft(base, stations)
    if out is None:
        lean_all = lean + p.well_round
        return drafted(lambda f: grow(base, -f * lean_all), z0, top - z0, steps=round(p.well_depth / 0.2))
    return out


def checks(p):
    lean = draft_offset(p.height, p.body_draft)
    y_top, body_top, body_bot, tip, yc = layout(p)
    total = y_top - tip
    top = p.floor + p.well_depth
    star_y = well_floor_at(p)
    R = p.star / 2
    rim_x = p.body_w / 2 - p.rim / 2
    return [
        dims(x=(p.body_w + 2 * (lean + p.wall) - 1, p.body_w + 2 * (lean + p.wall) + 1),
             y=(total + 2 * (lean + p.wall) - 1, total + 2 * (lean + p.wall) + 1),
             z=p.floor + p.height),
        fits_bed(),
        # island under the well; rim and handle cavity are open down to the floor
        solid((0, yc + 15, top - 1), (0, body_bot - 10, p.floor + 2)),
        empty((rim_x, yc, p.floor + 1), (0, y_top - p.handle_w / 2, p.floor + 1),
              (0, yc + 15, top + 1.5)),
        # star lines stand on the island; the star centre is bare well floor
        solid((0, star_y + R - 1.0, top + p.star_depth / 2)),
        empty((0, star_y, top + 0.3)),
        thickness_at((rim_x, yc, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(p.body_w * total * 0.6),
        no_overhang(),
        single_body(),
    ]


def build(p):
    h = p.height
    lean = draft_offset(h, p.body_draft)
    cs = outline(p)
    mold = extrude(grow(cs, lean + p.wall), p.floor + h)
    cav = offset_loft(cs, [(p.floor, 0.0), (p.floor + h + 1, lean * (h + 1) / h)])
    if cav is None:
        cav = tapered(cs, p.floor, h + 1, lean * (h + 1) / h)
    mold -= cav
    mold += island(p)
    # Star of David: raised lines on the island engrave the well floor
    s_lean = draft_offset(p.star_depth, p.star_draft)
    lines = hexagram_lines(p)
    top = p.floor + p.well_depth
    mold += drafted(lambda f: grow(lines, -f * s_lean), top - EMBED, p.star_depth + EMBED, steps=3)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the dish the right way up."""
    return cast_of(build(p))
