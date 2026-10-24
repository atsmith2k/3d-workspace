"""Reusable building blocks for engineered parts (build123d), so common shapes are
assembled from reviewed pieces instead of rebuilt from primitives every time.

    from cadkit.recipes import *
    base = shell_box(80, 50, 30, wall=2, r=4)                 # open-top box, floor 2
    base = add_bosses(base, "M3", points=boss_corners(80, 50, 2, "M3"), height=28, floor=2)
    top = lid(80, 50, 3, r=4, lip_h=4, wall=2)                 # drops into the box
    top = screw_holes(top, "M3", points=..., csk=True)

All sizes mm, parts sit on z=0, boxes centred on the origin in XY.
"""
from math import sqrt

from build123d import *

from .hardware import clearance, head_pocket, insert

__all__ = ["rounded_box", "shell_box", "lid", "boss", "add_bosses", "boss_corners",
           "screw_holes", "slot", "hex_pocket", "chamfer_bottom"]


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
                cone = Cone(dia / 2 + 0.5, 0, dia / 2 + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
                z = bb.max.Z - dia / 2 if from_top else bb.min.Z - 0.5
                if not from_top:
                    cone = cone.rotate(Axis.X, 180).moved(Location((0, 0, dia / 2 + 0.5)))
                part -= cone.moved(Location((x, y, z)))
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
