"""Wax melter shaped like a small oven (first version, dimensions not yet confirmed by
the customer). A lamp hangs from the oven roof and shines down on a pie plate that
slides into the oven opening and holds one 3 in pie-shaped wax tart.

Two parts. The oven prints lying on its BACK (front opening up), so the roof, floor and
side walls are all vertical in the print and nothing bridges; the knobs end up on the
top face. The pie plate prints upright. In the model the oven is therefore in print
pose: X = oven width, Y = oven height (feet at Y=0), Z = oven depth (back wall on the bed).

Spec:
  object:       oven-shaped wax melter body + removable pie plate for a 3 in wax tart
  overall:      oven about 113 W x 147 H x 108 D mm (prints 113 x 147 footprint, 111 tall);
                plate 101 mm diameter x 14 mm
  mates with:   wax tart 76.2 mm (3 in) diameter: plate well floor 80 mm (1.9 mm/side);
                plate in oven: 3 mm clearance per side, 2 mm behind;
                lamp holder: ASSUMED 1/8-IP threaded lamp nipple (10.3 mm OD) through a
                10.8 mm roof hole; ASSUMED socket + bulb hang 80 mm below the roof and
                the bulb face sits 40 mm above the plate rim. None of the lamp hardware
                is confirmed; lamp_hole_d, lamp_drop and bulb_gap are the knobs to turn.
  orientation:  oven on its back wall, opening up; plate on its base, well up; supports: none
  must have:    lamp port in the roof centred over the plate (teardrop, so it prints
                without support); front opening the plate passes through; plate well
                that takes a 76.2 mm tart flat on its floor; heat vents in the back wall;
                oven look: control fascia with knobs above the opening, feet
  tolerances:   loose sliding fits only (2-3 mm); walls 3 mm, roof 4 mm, plate floor 2 mm

Assumptions to confirm with the customer are listed in ASSUMPTIONS below.

Units: mm. Z is up and each part sits on Z=0 in the orientation it should print.
"""
import math

from build123d import *

from cadkit.checks import *

DESCRIPTION = "Oven-shaped wax melter with a top lamp port and a pie plate for 3 in tarts"

ASSUMPTIONS = [
    "Tart is 76.2 mm (3 in) across at its widest and under 12 mm tall.",
    "Lamp holder mounts on a 1/8-IP threaded nipple (10.3 mm OD) through the roof; cord exits the top.",
    "Socket + bulb hang 80 mm below the roof (about a GU10 holder with an MR16 halogen).",
    "Bulb face 40 mm above the plate rim; untested, tune bulb_gap after a melt test.",
    "PLA/PETG soften near a halogen bulb and under molten wax: this version is a fit and "
    "form prototype. A working unit needs a heat-rated material and a metal, glass or "
    "ceramic plate (or liner) plus a properly rated, strain-relieved lamp kit.",
]

PRODUCT = dict(
    title="Oven Wax Melter (prototype)",
    category="parts",
    tags=["wax melter", "wax warmer", "oven", "pie plate"],
    printers=["a1", "a1mini"],
    sellable=False,             # mains lamp + heat: unverified, dimensions unconfirmed
)

# Every tunable dimension lives here so it can be changed with --set name=value.
PARAMS = dict(
    # --- wax tart and pie plate ---
    tart_d=76.2,          # 3 in tart, widest diameter
    tart_clear=1.9,       # per side, tart to well floor edge
    plate_depth=12.0,     # well depth
    plate_floor=2.0,
    plate_slope=25.0,     # well wall angle from vertical, like a pie tin
    plate_rim=5.0,        # flat rim width
    plate_wall=2.0,       # wall thickness at the base (horizontal)
    rim_edge=1.6,         # vertical land on the rim's outer edge (no knife edge)
    # --- oven cavity ---
    side_clear=3.0,       # plate rim to side wall, per side
    back_clear=2.0,       # plate rim to back wall (and to the front face)
    bulb_gap=40.0,        # bulb face to plate rim            (ASSUMED)
    lamp_drop=80.0,       # socket + bulb length below roof   (ASSUMED)
    lamp_hole_d=10.8,     # 1/8-IP nipple 10.3 mm + clearance (ASSUMED)
    # --- oven shell ---
    wall=3.0,             # side and back walls
    floor=3.0,
    roof=4.0,
    corner=4.0,           # outside corner radius
    foot_h=6.0,
    foot_w=10.0,
    foot_inset=8.0,
    # --- oven look ---
    panel_h=18.0,         # control fascia height above the opening
    face_t=3.0,           # fascia thickness at its lower edge
    knob_count=3,
    knob_d=10.0,
    knob_h=2.5,
    # --- vents (back wall, near the roof) ---
    vent_count=5,
    vent_w=4.0,
    vent_h=20.0,
    vent_pitch=12.0,
)


class _D:
    """Derived dimensions, shared by build, checks and assembly."""

    def __init__(s, p):
        s.r_ib = p.tart_d / 2 + p.tart_clear                              # well floor radius
        s.r_it = s.r_ib + p.plate_depth * math.tan(math.radians(p.plate_slope))
        s.r_rim = s.r_it + p.plate_rim
        s.r_bo = s.r_ib + p.plate_wall                                    # base outer radius
        s.plate_h = p.plate_floor + p.plate_depth
        s.plate_od = 2 * s.r_rim

        s.cav_w = s.plate_od + 2 * p.side_clear
        s.cav_d = s.plate_od + 2 * p.back_clear
        s.cav_h = s.plate_h + p.bulb_gap + p.lamp_drop
        s.W = s.cav_w + 2 * p.wall
        s.D = s.cav_d + p.wall
        s.y_floor = p.foot_h + p.floor                                    # cavity floor
        s.y_ceil = s.y_floor + s.cav_h                                    # cavity ceiling
        s.H = s.y_ceil + p.roof
        s.open_h = s.cav_h - p.panel_h                                    # front opening height
        s.z_plate = p.wall + p.back_clear + s.r_rim                       # plate / lamp centre
        s.y_knob = (s.y_ceil - p.panel_h + s.H) / 2
        s.wedge = 1.2 * p.panel_h                                         # fascia slope run (40 deg)
        s.vent_x = [(i - (p.vent_count - 1) / 2) * p.vent_pitch for i in range(int(p.vent_count))]
        s.y_vent = s.y_ceil - 6 - p.vent_h / 2
        n = int(p.knob_count)
        span = s.cav_w - 30
        s.knob_x = [0.0] if n == 1 else [-span / 2 + span * i / (n - 1) for i in range(n)]


def checks(p):
    d = _D(p)
    r = p.lamp_hole_d / 2
    y_roof = d.H - p.roof / 2
    oven = [
        dims(x=d.W, y=d.H, z=d.D + p.knob_h),
        fits_bed(), flat_base(d.W * d.H * 0.7), no_overhang(), single_body(),
        # cavity is open, from the floor to the roof, and out through the front
        empty((0, d.y_floor + d.cav_h / 2, p.wall + d.cav_d / 2),
              (0, d.y_floor + d.open_h / 2, d.D - 0.5),
              (d.cav_w / 2 - 0.5, d.y_floor + 0.5, p.wall + 0.5),
              (0, d.y_ceil - 0.5, d.z_plate)),
        # the plate (plus clearance) passes the opening and sits under the lamp
        empty((d.r_rim + p.side_clear - 0.3, d.y_floor + d.plate_h, d.z_plate),
              (-(d.r_rim + p.side_clear - 0.3), d.y_floor + d.plate_h, d.z_plate),
              (0, d.y_floor + d.plate_h, d.D - 0.5)),
        # shell thicknesses
        thickness_at((20, p.foot_h + p.floor / 2, d.D / 2), p.floor - 0.2),
        thickness_at((20, y_roof, d.D / 2), p.roof - 0.2),
        thickness_at((d.W / 2 - p.wall / 2, d.H / 2, d.D / 2), p.wall - 0.2),
        thickness_at((0, d.y_floor + 20, p.wall / 2), p.wall - 0.2),
        # lamp port: through the roof over the plate centre, the stated diameter
        empty((0, y_roof, d.z_plate), (r - 0.3, y_roof, d.z_plate), (-(r - 0.3), y_roof, d.z_plate),
              (0, d.H - 0.2, d.z_plate), (0, d.y_ceil + 0.2, d.z_plate)),
        solid((r + 0.5, y_roof, d.z_plate), (-(r + 0.5), y_roof, d.z_plate), (0, y_roof, d.z_plate - r - 0.5)),
        # fascia above the opening is there, and the opening below it is clear
        solid((d.cav_w / 2 - 4, d.y_ceil - p.panel_h / 2, d.D - 1)),
        empty((0, d.y_ceil - p.panel_h - 1, d.D - 1)),
        # vents go through the back wall
        empty(*[(x, d.y_vent, p.wall / 2) for x in d.vent_x]),
        # feet
        solid((d.W / 2 - p.foot_inset - p.foot_w / 2, p.foot_h / 2, d.D / 2)),
        empty((0, p.foot_h / 2, d.D / 2)),
    ]
    plate = [
        dims(x=d.plate_od, y=d.plate_od, z=d.plate_h),
        fits_bed(), flat_base(math.pi * d.r_bo ** 2 * 0.9), no_overhang(), single_body(),
        solid((0, 0, p.plate_floor / 2)),
        thickness_at((0, 0, p.plate_floor / 2), p.plate_floor - 0.1),
        # a 3 in tart sits flat on the well floor
        empty((p.tart_d / 2, 0, p.plate_floor + 0.3), (0, -p.tart_d / 2, p.plate_floor + 0.3),
              (0, 0, d.plate_h - 0.5)),
        solid((d.r_rim - 1, 0, d.plate_h - 0.5)),                         # rim
    ]
    return {"oven": oven, "plate": plate}


def assembly(p):
    """The oven stays in print pose (on its back); the plate tips to stand on the oven
    floor (its axis along oven-up = +Y), centred under the lamp."""
    d = _D(p)
    return {"plate": (0, d.y_floor, d.z_plate, -90, 0, 0)}


def _oven(p):
    d = _D(p)
    body_h = d.H - p.foot_h
    with BuildSketch(Plane.XY) as prof:
        with Locations((0, p.foot_h + body_h / 2)):
            RectangleRounded(d.W, body_h, p.corner)
        fx = d.W / 2 - p.foot_inset - p.foot_w / 2
        with Locations((-fx, (p.foot_h + 1) / 2), (fx, (p.foot_h + 1) / 2)):
            Rectangle(p.foot_w, p.foot_h + 1)                             # overlaps the body by 1
    part = extrude(prof.sketch, d.D)

    # cavity: open at the front (z = D); a 40 deg wedge is left under the roof at the
    # front so the control fascia grows out of the roof without bridging
    cavity = Box(d.cav_w, d.cav_h, d.cav_d + 1, align=(Align.CENTER, Align.MIN, Align.MIN)) \
        .moved(Location((0, d.y_floor, p.wall)))
    y0, y1 = d.y_ceil - p.panel_h, d.y_ceil
    z_face = d.D - p.face_t
    with BuildSketch(Plane.YZ) as wp:                                     # local (x, y) = global (Y, Z)
        Polygon((y1 + 1, d.D + 2), (y0, d.D + 2), (y0, z_face), (y1, z_face - d.wedge),
                (y1 + 1, z_face - d.wedge), align=None)
    cavity -= extrude(wp.sketch, d.cav_w, both=True)
    part -= cavity

    # lamp port: teardrop through the roof, point toward the print's top
    r = p.lamp_hole_d / 2
    k = r / math.sqrt(2)
    with BuildSketch(Plane((0, d.H + 1, d.z_plate), x_dir=(1, 0, 0), z_dir=(0, -1, 0))) as tp:
        Circle(r)
        Polygon((k, k), (0, r * math.sqrt(2)), (-k, k), align=None)
    part -= extrude(tp.sketch, p.roof + 2)

    # vents through the back wall
    for x in d.vent_x:
        part -= Box(p.vent_w, p.vent_h, p.wall + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x, d.y_vent, -1)))

    # knobs on the fascia (top face of the print)
    for x in d.knob_x:
        knob = Cylinder(p.knob_d / 2, p.knob_h + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        knob = chamfer(knob.edges().sort_by(Axis.Z)[-1], 0.6)
        part += knob.moved(Location((x, d.y_knob, d.D - 0.1)))
    return part


def _plate(p):
    d = _D(p)
    with BuildSketch(Plane.XZ) as prof:
        Polygon((0, 0), (d.r_bo, 0), (d.r_rim, d.plate_h - p.rim_edge), (d.r_rim, d.plate_h),
                (d.r_it, d.plate_h),
                (d.r_ib, p.plate_floor), (0, p.plate_floor), align=None)
    return revolve(prof.sketch, Axis.Z)


def build(p):
    return {"oven": _oven(p), "plate": _plate(p)}
