"""Round alarm/warning light prop: a flat dark bezel ring with eight hex bolt heads and
a raised rim, plus a separate red dome lens that drops into the bezel pocket. Two parts
so each can be painted (bezel dark grey/black, lens red) and glued after.

Spec:
  object:       wall/door prop light, decorative only (no electronics), painted after print
  overall:      bezel 100 x 100 x 13 mm; lens 59.6 dia x 23 mm; assembled height 29 mm
  mates with:   lens skirt 59.6 mm in a 60.0 mm pocket (0.2 mm per side sliding fit),
                skirt 7 mm tall sits in the 4 mm pocket and the 3 mm rim so the dome
                starts flush with the rim top
  orientation:  bezel back face on the bed, bolts up; lens flat face on the bed, dome up;
                supports expected: none
  must have:    8 hex bolt heads (7 mm AF, 2 mm tall) on a 84 mm circle, a raised rim
                5 mm wide / 3 mm tall around the lens, lens pocket 4 mm deep, dome 16 mm
                high, outer edge chamfer 3 mm
  tolerances:   sliding 0.2 mm/side on the lens skirt

Units: mm. Z is up and each part sits on Z=0 in the orientation it should print.
"""
from math import cos, pi, radians, sin

from build123d import *

from cadkit.checks import *

DESCRIPTION = "Round red alarm light prop with a bolted dark bezel (two parts, paint-ready)"

PRODUCT = dict(
    title="Alarm Light Prop (bolted bezel + red dome)",
    category="parts",
    tags=["prop", "cosplay", "light", "alarm", "decor"],
    printers=["a1", "a1mini"],
    sellable=None,
)

PARAMS = dict(
    outer_d=100.0,       # bezel outside diameter
    base_h=10.0,         # bezel plate thickness
    edge_chamfer=3.0,    # chamfer on the bezel's top outer edge
    lens_d=60.0,         # lens pocket diameter (the lens is this minus 2 * clearance)
    pocket_depth=4.0,    # recess the lens skirt sits in
    rim_w=5.0,           # raised ring around the pocket
    rim_h=3.0,
    dome_h=16.0,         # height of the spherical cap above the rim
    clearance=0.2,       # per side, lens skirt in pocket
    bolts=8,
    bolt_af=7.0,         # hex head across flats
    bolt_h=2.0,
    bolt_ring_d=84.0,    # circle the bolt centres sit on
)


def _skirt_h(p):
    return p.pocket_depth + p.rim_h


def checks(p):
    r_pocket = p.lens_d / 2
    r_rim = r_pocket + p.rim_w
    rb = p.bolt_ring_d / 2
    a = 2 * pi / p.bolts
    lens_r = r_pocket - p.clearance
    skirt = _skirt_h(p)
    return {
        "bezel": [
            dims(x=p.outer_d, y=p.outer_d, z=p.base_h + p.rim_h),
            flat_base(pi * (p.outer_d / 2) ** 2 * 0.9),
            no_overhang(), single_body(),
            solid((0, 0, 1.0)),                                         # floor under the pocket
            empty((0, 0, p.base_h - p.pocket_depth + 1.0)),             # pocket is open
            empty((r_pocket - 0.5, 0, p.base_h - 0.5)),                 # pocket reaches full diameter
            solid((r_pocket + p.rim_w / 2, 0, p.base_h + p.rim_h - 0.5)),  # rim stands up
            empty((r_rim + 1.5, 0, p.base_h + 0.5)),                    # flat plate outside the rim
            solid((rb, 0, p.base_h + p.bolt_h - 0.5)),                  # bolt head at angle 0
            solid((rb * cos(a), rb * sin(a), p.base_h + p.bolt_h - 0.5)),
            empty((rb * cos(a / 2), rb * sin(a / 2), p.base_h + 0.5)),  # gap between bolts
            thickness_at((0, 0, 1.0), p.base_h - p.pocket_depth - 0.3),
        ],
        "lens": [
            dims(x=2 * lens_r, y=2 * lens_r, z=skirt + p.dome_h),
            flat_base(pi * lens_r ** 2 * 0.95),
            no_overhang(), single_body(),
            solid((0, 0, skirt + p.dome_h - 1.0)),                       # dome apex is solid
            solid((lens_r - 0.5, 0, skirt / 2)),                        # skirt at full diameter
            empty((lens_r + 1.0, 0, skirt + 1.0)),                      # nothing wider than the skirt
        ],
    }


def assembly(p):
    """Lens printed flat-face-down at Z=0; assembled it sits on the pocket floor."""
    return {"lens": (0, 0, p.base_h - p.pocket_depth, 0, 0, 0)}


def _bezel(p):
    r_out = p.outer_d / 2
    r_pocket = p.lens_d / 2
    r_rim = r_pocket + p.rim_w
    plate = Cylinder(r_out, p.base_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plate = chamfer(plate.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], p.edge_chamfer)
    # raised rim, sunk 0.1 mm into the plate so the faces are not coplanar
    rim = (Cylinder(r_rim, p.rim_h + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
           - Cylinder(r_pocket, p.rim_h + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    rim = rim.moved(Location((0, 0, p.base_h - 0.1)))
    rim = chamfer(rim.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1].sort_by(SortBy.RADIUS)[-1], 1.0)
    part = plate + rim
    # lens pocket
    part -= Cylinder(r_pocket, p.pocket_depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(
        Location((0, 0, p.base_h - p.pocket_depth)))
    # hex bolt heads with a chamfered top
    rb = p.bolt_ring_d / 2
    hex_r = p.bolt_af / 2 / cos(radians(30))
    for i in range(p.bolts):
        ang = 360 * i / p.bolts
        head = extrude(RegularPolygon(hex_r, 6), p.bolt_h + 0.1)
        head = chamfer(head.edges().group_by(Axis.Z)[-1], 0.5)
        head = head.rotate(Axis.Z, 15).moved(Location((rb * cos(radians(ang)), rb * sin(radians(ang)), p.base_h - 0.1)))
        part += head
    return part


def _lens(p):
    r = p.lens_d / 2 - p.clearance
    skirt = _skirt_h(p)
    h = p.dome_h
    R = (r * r + h * h) / (2 * h)                       # sphere radius for a cap of base r and height h
    cap = Sphere(R).moved(Location((0, 0, skirt + h - R)))
    cap &= Cylinder(r, h + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, skirt - 0.5)))
    body = Cylinder(r, skirt, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body + cap


def build(p):
    return {"bezel": _bezel(p), "lens": _lens(p)}
