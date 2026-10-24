"""Reusable building blocks for engineered parts (build123d), so common shapes are
assembled from reviewed pieces instead of rebuilt from primitives every time.

    from cadkit.recipes import *
    base = shell_box(80, 50, 30, wall=2, r=4)                 # open-top box, floor 2
    base = add_bosses(base, "M3", points=boss_corners(80, 50, 2, "M3"), height=28, floor=2)
    top = lid(80, 50, 3, r=4, lip_h=4, wall=2)                 # drops into the box
    top = screw_holes(top, "M3", points=..., csk=True)
    hook = j_hook(drop=50, arm=35, lip=14, t=5, width=20)      # lies on its side to print
    k = knob(30, 18, shaft_d=6, shaft_flat=5.5)                # D-shaft grip knob
    clip = cable_clip(cable_d=5, count=3)                      # press-in cable holder
    pull = u_handle(110, bar_h=12, bar_mid_h=18)               # lofted drawer pull
    race = swept_channel([(0, 0), (40, 10), (80, 0)], 12, 8)   # U-channel along a spline

All sizes mm, parts sit on z=0 in print pose, boxes centred on the origin in XY.
Worked models: enclosure_box, coat_hook, shaft_knob, cable_clip, drawer_pull,
cable_raceway.
"""
from math import cos, pi, sin, sqrt

from build123d import *

from .hardware import HEX_NUT, clearance, head_pocket, insert, self_tap

__all__ = ["rounded_box", "shell_box", "lid", "boss", "add_bosses", "boss_corners",
           "screw_holes", "slot", "hex_pocket", "chamfer_bottom",
           "j_hook", "knob", "cable_clip", "lofted_bar", "u_handle", "swept_channel"]


def rounded_box(w, d, h, r=3.0, top_r=0.0):
    """Box centred in XY on z=0 with vertical edges rounded by r and, optionally,
    the top edges rounded by top_r."""
    b = Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if r > 0:
        b = fillet(b.edges().filter_by(Axis.Z), r)
    if top_r > 0:
        b = fillet(b.faces().sort_by(Axis.Z)[-1].edges(), top_r)
    return b


def shell_box(w, d, h, wall=2.0, r=3.0, floor=None, top_r=0.0):
    """Open-top box: outer w x d x h, walls `wall` thick, floor `floor` (default wall)."""
    floor = wall if floor is None else floor
    outer = rounded_box(w, d, h, r, top_r)
    inner = rounded_box(w - 2 * wall, d - 2 * wall, h, max(r - wall, 0.01)).moved(Location((0, 0, floor)))
    return outer - inner


def lid(w, d, t=3.0, r=3.0, lip_h=4.0, wall=2.0, clearance_mm=0.2, top_r=0.0):
    """Lid plate for shell_box, printed top-face-down: a w x d x t plate with a lip
    of height lip_h that drops inside the box walls with `clearance_mm` per side.
    Returned in its PRINT pose (lip up); see assembly() in the enclosure example for
    the flip into place."""
    plate = rounded_box(w, d, t, r, top_r)
    li = w - 2 * wall - 2 * clearance_mm, d - 2 * wall - 2 * clearance_mm
    lip = rounded_box(li[0], li[1], lip_h + 0.1, max(r - wall - clearance_mm, 0.01)).moved(Location((0, 0, t - 0.1)))
    lip -= rounded_box(li[0] - 2 * wall, li[1] - 2 * wall, lip_h + 2, max(r - 2 * wall, 0.01)).moved(Location((0, 0, t - 1)))
    return plate + lip


def boss(size="M3", height=10.0, od=None, floor=0.0):
    """Cylindrical standoff with a heat-set insert pocket in the top, standing on z=0;
    `floor` sinks it into the floor it stands on so the union has no coplanar faces."""
    ins = insert(size)
    od = od or ins["boss"]
    b = Cylinder(od / 2, height + floor, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -floor)))
    b -= Cylinder(ins["hole"] / 2, ins["depth"] + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
        .moved(Location((0, 0, height - ins["depth"])))
    return b


def boss_corners(w, d, wall, size="M3", inset=None):
    """XY centres for four corner bosses that touch the inside walls."""
    inset = inset or (wall + insert(size)["boss"] / 2 + 0.3)
    return [(sx * (w / 2 - inset), sy * (d / 2 - inset)) for sx in (-1, 1) for sy in (-1, 1)]


def add_bosses(part, size, points, height, floor=2.0, od=None):
    """Union bosses onto a part at the given XY points, sunk 0.1 mm into its floor."""
    for x, y in points:
        part += boss(size, height - floor, od, floor=0.1).moved(Location((x, y, floor)))
    return part


def screw_holes(part, size, points, csk=False, cap=False, from_top=True):
    """Through clearance holes at XY points, optionally countersunk or counterbored
    on the top face (or the bottom, for a lid printed upside down: from_top=False)."""
    bb = part.bounding_box()
    h = bb.max.Z - bb.min.Z
    for x, y in points:
        part -= Cylinder(clearance(size) / 2, h + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x, y, bb.min.Z - 1)))
        if csk or cap:
            dia, dep = head_pocket(size, "csk" if csk else "cap")
            if csk:
                # Cone(bottom_radius, top_radius, height): 90 deg, so height = radius
                R = dia / 2
                if from_top:   # wide at the top face, narrowing down into the part
                    cone = Cone(0, R + 0.5, R + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    part -= cone.moved(Location((x, y, bb.max.Z - R)))
                else:          # wide at the bottom face (a lid printed upside down)
                    cone = Cone(R + 0.5, 0, R + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
                    part -= cone.moved(Location((x, y, bb.min.Z - 0.5)))
            else:
                z = bb.max.Z - dep if from_top else bb.min.Z - 1
                part -= Cylinder(dia / 2, dep + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, z)))
    return part


def slot(length, width, depth, at=(0, 0, 0), angle=0.0):
    """Rounded slot cutter: subtract from a part. `at` is the centre of the top."""
    s = SlotCenterToCenter(length - width, width)
    cutter = extrude(s, amount=depth + 0.1).rotate(Axis.Z, angle)
    return cutter.moved(Location((at[0], at[1], at[2] - depth)))


def hex_pocket(across_flats, depth, at=(0, 0, 0)):
    """Hex cutter for a captive nut; `at` is the centre of the pocket mouth."""
    cutter = extrude(RegularPolygon(across_flats / sqrt(3), 6), amount=depth + 0.1)
    return cutter.moved(Location((at[0], at[1], at[2] - depth)))


def chamfer_bottom(part, size=0.5):
    """Chamfer the bottom edges (helps elephant's foot on printers without compensation)."""
    try:
        return chamfer(part.faces().sort_by(Axis.Z)[0].edges(), size)
    except Exception:
        return part


# ---------------------------------------------------------------- hooks, knobs, clips

def j_hook(drop=50.0, arm=35.0, lip=14.0, t=5.0, width=20.0, r=3.0):
    """Coat/J hook lying on its side for printing: the profile is in XY (back plate
    up the Y axis from the origin, arm out along +X at the bottom, lip turning up at
    the end), extruded `width` along Z. Mount it with the x=0 face on the wall, +Y up.
    Inner corners filleted by r, outer edges by r/2."""
    back = Rectangle(t, drop, align=(Align.MIN, Align.MIN))
    base = Rectangle(arm, t, align=(Align.MIN, Align.MIN))
    tip = Rectangle(t, lip, align=(Align.MIN, Align.MIN)).moved(Location((arm - t, 0)))
    part = extrude(back + base + tip, amount=width)
    try:
        inner = part.edges().filter_by(Axis.Z).filter_by(
            lambda e: (abs(e.center().X - t) < 0.01 and abs(e.center().Y - t) < 0.01)
            or (abs(e.center().X - (arm - t)) < 0.01 and abs(e.center().Y - t) < 0.01))
        part = fillet(inner, min(r, t / 2 - 0.1))
    except Exception:
        pass
    try:
        part = fillet(part.edges().filter_by(Axis.Z), r / 2)
    except Exception:
        pass
    return part


def knob(d=30.0, height=18.0, lobes=6, lobe_depth=2.5, top_r=3.0, shaft_d=None, shaft_flat=None,
         shaft_depth=None, bolt=None):
    """Round grip knob standing on its flat (shaft) face, rounded edge on top,
    scalloped sides. Either a D-shaft socket (`shaft_d`, with `shaft_flat` = the
    across-flat size, `shaft_depth`) or a `bolt` size ("M4") with a through clearance
    hole and a captive hex nut pocket in the base."""
    body = Cylinder(d / 2, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = fillet(body.faces().sort_by(Axis.Z)[-1].edges(), min(top_r, height / 2 - 0.1))
    if lobes and lobe_depth > 0:
        rl = d * pi / lobes / 2 * 0.9
        for k in range(lobes):
            a = 2 * pi * k / lobes
            cx, cy = (d / 2 + rl - lobe_depth) * cos(a), (d / 2 + rl - lobe_depth) * sin(a)
            body -= Cylinder(rl, height + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((cx, cy, -1)))
    if shaft_d:
        depth = shaft_depth or height * 0.7
        shaft = Cylinder(shaft_d / 2 + 0.15, depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
        if shaft_flat:
            shaft -= Box(shaft_d + 2, shaft_d, depth + 2, align=(Align.CENTER, Align.MIN, Align.MIN)) \
                .moved(Location((0, shaft_flat - shaft_d / 2 + 0.1, -1)))
        body -= shaft.moved(Location((0, 0, -1)))
    if bolt:
        body -= Cylinder(clearance(bolt) / 2, height + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((0, 0, -1)))
        af, nt = HEX_NUT[_norm_size(bolt)]
        body -= extrude(RegularPolygon((af + 0.3) / sqrt(3), 6), amount=nt + 0.5).moved(Location((0, 0, -0.1)))
    return body


def _norm_size(size):
    s = str(size).upper().replace(" ", "")
    return s if s.startswith("M") else "M" + s


def cable_clip(cable_d=5.0, count=3, wall=1.6, base_t=2.0, pitch=None, grip=1.2, width=None):
    """Strip of C-clips, open at the top, that cables press into; prints flat on the
    base with the clips as vertical walls. `grip` is how much narrower the mouth is
    than the cable (the snap). Returns a part on z=0, centred on the origin in XY."""
    pitch = pitch or cable_d + 2 * wall + 2
    width = width or cable_d + 2 * wall + 1
    total = pitch * count
    base = Box(total, width, base_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = fillet(base.edges().filter_by(Axis.Z), min(2.0, width / 4))
    ro, ri = cable_d / 2 + wall, cable_d / 2 + 0.1
    cz = base_t + ro - 0.1
    # the mouth is a radial sector cut from the crown, so the lips keep the full
    # ring wall right to their tips (a vertical slot would leave feather edges)
    from math import asin, degrees
    half = min(asin((cable_d - grip) / (2 * ri)), 1.2)
    for k in range(count):
        x = (k - (count - 1) / 2) * pitch
        ring = Cylinder(ro, width, align=(Align.CENTER, Align.CENTER, Align.CENTER)).rotate(Axis.X, 90)
        ring -= Cylinder(ri, width + 2, align=(Align.CENTER, Align.CENTER, Align.CENTER)).rotate(Axis.X, 90)
        wedge = Polygon((0, 0), ((ro + 2) * sin(half), (ro + 2) * cos(half)),
                        (-(ro + 2) * sin(half), (ro + 2) * cos(half)), align=None)
        wedge = extrude(Plane.XZ * wedge, amount=width / 2 + 1, both=True)
        ring -= wedge
        ring = ring.moved(Location((x, 0, cz)))
        # keep only what stands above the base (sunk 0.1)
        ring &= Box(2 * ro + 2, width + 2, 2 * ro + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
            .moved(Location((x, 0, base_t - 0.1)))
        part += ring
    return part


# ---------------------------------------------------------------- loft and sweep

def lofted_bar(sections, t, r=2.0, axis_y=0.0, z=0.0):
    """A bar along X whose cross-section height (in Y) changes smoothly: `sections` is
    a list of (x, height) pairs from one end to the other; thickness in Z is `t`,
    section corners rounded by r. Centred on y = axis_y, sitting on z. Lofted through
    all sections, so steps blend into a curve."""
    faces = []
    for x, h in sections:
        pl = Plane(origin=(x, axis_y, z + t / 2), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        faces.append(pl * RectangleRounded(h, t, min(r, h / 2 - 0.05, t / 2 - 0.05)))
    return loft(faces, ruled=False)


def u_handle(length=110.0, bar_h=12.0, bar_mid_h=18.0, leg_h=28.0, leg_w=14.0, t=10.0, r=2.0,
             bolt="M4", bolt_depth=12.0):
    """Drawer/cabinet pull as a planar U lying flat for printing: two legs along Y from
    y=0 (the mounting face) up to a lofted bar that is `bar_h` tall at the ends and
    `bar_mid_h` in the middle. Blind self-tapping bolt holes enter the leg ends at y=0."""
    bar_y = leg_h + bar_h / 2
    bar = lofted_bar([(-length / 2, bar_h), (-length / 4, (bar_h + bar_mid_h) / 2), (0, bar_mid_h),
                      (length / 4, (bar_h + bar_mid_h) / 2), (length / 2, bar_h)], t, r, axis_y=bar_y)
    part = bar
    for sx in (-1, 1):
        x = sx * (length / 2 - leg_w / 2)
        leg = Box(leg_w, leg_h + bar_h / 2 + 0.1, t, align=(Align.CENTER, Align.MIN, Align.MIN)).moved(Location((x, 0, 0)))
        leg = fillet(leg.edges().filter_by(Axis.Z).filter_by(lambda e: e.center().Y < 1), r)
        part += leg
        if bolt:
            part -= Cylinder(self_tap(bolt) / 2, bolt_depth + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
                .rotate(Axis.X, -90).moved(Location((x, -1, t / 2)))
    return part


def swept_channel(path_pts, width=12.0, height=8.0, wall=1.6, smooth=True):
    """U-channel (cable raceway, drip channel) following a path of XY points, open at
    the top, flat bottom on z=0. The path is a smooth spline through the points when
    `smooth`, else straight segments with rounded transitions."""
    pts = [Vector(x, y, 0) for x, y in path_pts]
    path = Spline(*pts) if smooth else Polyline(*pts)
    start, tangent = path @ 0, path % 0
    pl = Plane(origin=start, z_dir=tangent, x_dir=Vector(0, 0, 1).cross(tangent))
    outer = Rectangle(width, height, align=(Align.CENTER, Align.MIN))
    inner = Rectangle(width - 2 * wall, height, align=(Align.CENTER, Align.MIN)).moved(Location((0, wall)))
    return sweep(pl * (outer - inner), path, transition=Transition.ROUND)
