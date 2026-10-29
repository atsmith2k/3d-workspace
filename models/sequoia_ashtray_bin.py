"""Slide-in storage cubby that replaces the dash ashtray drawer of a 2001-2007 Toyota
Sequoia (also 2000-2006 Tundra). Pull the factory ash drawer out of its housing and
slide this in its place: a two-level cubby open to the front, a shelf between levels
and a ramped lip on each level so things stay put under braking.

Spec:
  object:       front-opening storage cubby for the dash ashtray housing
  overall:      82.4 W (over the crush ribs; body 81.6) x 66.6 H x 140 deep (in the car)
  mates with:   ashtray housing opening ~82.3-82.5 W x ~67 H, from a proven slide-in insert
                (KJE3DESIGNS, MakerWorld 1163944: 82.3 x 67.0 x 150, a "tight fit"; one
                user found 150 deep bottomed out in their truck, so this is 140 deep).
                Body 81.6 W with two 0.4 mm crush ribs per side (82.4 over ribs) so it
                grips without being forced; height 66.6 = 0.2 mm/side under 67.0.
  orientation:  prints standing on its BACK face (the end that goes into the dash),
                front opening up. Print coords: X = car width, Y = car height (+Y up in
                the car), Z = depth from back (z=0) to front (z=depth). Shelf and walls
                are then vertical; supports expected: none
  must have:    lower level 32 mm tall (phone, wallet), upper level ~26 mm (keys,
                sunglasses, coins); shelf 1.68; lip ramps 9 mm tall on the floor and 6 mm
                on the shelf at the front edge; back 2 mm closed; rear outer edges
                chamfered 1 mm as an insertion lead-in
  tolerances:   walls 1.68 (4 lines), sliding fit 0.2 mm/side on height, ribs 0.4 interference
  material:     PETG (a parked car's dash gets hot enough to soften PLA)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from build123d import *

from cadkit.checks import *
from cadkit.recipes import chamfer_bottom

DESCRIPTION = "Slide-in storage cubby replacing the 2001-2007 Toyota Sequoia dash ashtray"

# Not for sale until the licence of the design it borrows fit dimensions from is
# checked: the housing opening (82.3 x 67.0 mm) comes from a published third-party model.
PRODUCT = dict(sellable=False, category="parts", tags=["automotive", "toyota", "sequoia", "tundra"])
LICENSE_NOTES = (
    "Fit dimensions (housing opening 82.3 x 67.0 mm, 150 mm depth) are taken from the "
    "Toyota Sequoia ashtray insert by KJE3DESIGNS, MakerWorld model 1163944. That "
    "model's licence has not been reviewed; this part must not be sold or redistributed "
    "until it is, and any release must credit the source."
)

PARAMS = dict(
    width=81.6,        # body width; crush ribs add 2 x rib
    height=66.6,       # in-car height
    depth=140.0,       # how far it goes into the dash (print height)
    wall=1.68,         # sides, top, floor and shelf
    back=2.0,          # closed back plate (on the bed)
    corner_r=2.0,      # rounding of the long outer edges
    lower_h=32.0,      # clear height of the lower level
    shelf=True,        # False = one tall level
    lip=9.0,           # ramp lip height at the front of the floor
    shelf_lip=6.0,     # ramp lip height at the front of the shelf
    lip_run=15.0,      # length of the ramp (steeper than 45 deg when printed)
    rib=0.4,           # crush rib proud of each side face (0 = no ribs)
    lead_in=1.0,       # chamfer on the rear outer edges
)


def _levels(p):
    floor_top = -p.height / 2 + p.wall
    shelf_bot = floor_top + p.lower_h
    shelf_top = shelf_bot + p.wall
    ceiling = p.height / 2 - p.wall
    return floor_top, shelf_bot, shelf_top, ceiling


def checks(p):
    floor_top, shelf_bot, shelf_top, ceiling = _levels(p)
    side_x = p.width / 2 - p.wall / 2
    upper_mid = (shelf_top + ceiling) / 2 if p.shelf else (floor_top + ceiling) / 2
    c = [
        dims(x=p.width + 2 * p.rib, y=p.height, z=p.depth),
        flat_base(p.width * p.height * 0.9),
        no_overhang(),
        single_body(),
        fits_bed(),
        solid((0, 0, p.back / 2)),                                   # closed back
        empty((0, (floor_top + shelf_bot) / 2, p.depth / 2)),        # lower level open
        empty((0, upper_mid, p.depth - 1)),                          # open to the front
        thickness_at((side_x, 0, p.depth / 2), p.wall - 0.1),        # side wall
        solid((0, floor_top + 1, p.depth - 1)),                      # floor lip
        empty((0, floor_top + p.lip + 2, p.depth - 1)),              # above the lip
    ]
    if p.shelf:
        c += [solid((0, shelf_bot + p.wall / 2, p.depth / 2)),       # shelf
              empty((0, upper_mid, p.depth / 2)),
              solid((0, shelf_top + 1, p.depth - 1))]                # shelf lip
    return c


def _ramp(y0, h, run, z_front, width):
    """Wedge across the cavity: vertical front face h tall at z_front with a 1.5 mm flat
    top, sloping back down to y0 over `run`. Sinks 0.1 into the surface it sits on."""
    with BuildPart() as w:
        with BuildSketch(Plane.YZ):
            Polygon((y0 - 0.1, z_front), (y0 + h, z_front), (y0 + h, z_front - 1.5),
                    (y0 - 0.1, z_front - run), align=None)
        extrude(amount=width / 2, both=True)
    return w.part


def build(p):
    floor_top, shelf_bot, shelf_top, ceiling = _levels(p)
    cw = p.width - 2 * p.wall

    body = Box(p.width, p.height, p.depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = fillet(body.edges().filter_by(Axis.Z), p.corner_r)
    body = chamfer_bottom(body, p.lead_in)
    cavity = Box(cw, ceiling - floor_top, p.depth,
                 align=(Align.CENTER, Align.MIN, Align.MIN)).moved(Location((0, floor_top, p.back)))
    part = body - cavity

    span = cw + 0.2   # every insert sinks 0.1 into the side walls
    if p.shelf:
        part += Box(span, p.wall, p.depth - p.back + 0.1,
                    align=(Align.CENTER, Align.MIN, Align.MIN)).moved(Location((0, shelf_bot, p.back - 0.1)))
        part += _ramp(shelf_top, p.shelf_lip, p.lip_run, p.depth, span)
    part += _ramp(floor_top, p.lip, p.lip_run, p.depth, span)

    if p.rib > 0:
        r = 0.8
        z0, z1 = 25.0, p.depth - 10.0
        for sx in (-1, 1):
            for y in (-p.height / 4, p.height / 4):
                x = sx * (p.width / 2 + p.rib - r)
                part += Cylinder(r, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
                    Location((x, y, z0)))
    return part
