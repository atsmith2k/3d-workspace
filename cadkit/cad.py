"""build123d helpers that work around OpenCascade rough edges.

Import in a model with:  from cadkit.cad import *
"""
from math import radians, tan

from build123d import Edge, Face, Kind, Location, Sketch, Solid, Vector, Wire, extrude, offset


def closed_spline(points):
    """Smooth closed outline through 2D points, always facing +Z."""
    f = Face(Wire([Edge.make_spline([Vector(*p) for p in points], periodic=True)]))
    return -f if f.normal_at().Z < 0 else f


def clip(a, b):
    """Area of sketch `a` inside sketch `b`. (Sketch & Sketch returns an empty result
    in build123d 0.13, so subtract twice instead.)"""
    return a - (a - b)


def draft_extrude(face, height, draft_deg):
    """Extrude a flat XY face straight up by `height`, with walls leaning `draft_deg`
    (positive narrows upward, negative widens). Holes in the face are kept.

    build123d's extrude(taper>0) goes through LocOpe_DPrism, which can segfault on thin
    or traced shapes; this always lofts between the face and an offset copy instead.
    If the loft fails it falls back to a stack of offset slices (a fine staircase),
    and only then to straight walls."""
    shift = -height * tan(radians(draft_deg))
    up = Location((0, 0, height))
    try:
        def lofted(wire, amount):
            top = wire.offset_2d(amount, kind=Kind.ARC)
            top.move(up)
            return Solid.make_loft([wire, top], ruled=True)
        solid = lofted(face.outer_wire(), shift)
        for hole in face.inner_wires():
            solid = solid.cut(lofted(hole, -shift))
        if solid.is_valid and solid.volume > 0:
            return solid
    except Exception:
        pass
    try:
        steps = 4
        solid = None
        for k in range(steps):
            layer = offset(face, shift * (k + 0.5) / steps, kind=Kind.ARC)
            slab = extrude(layer, amount=height / steps).moved(Location((0, 0, k * height / steps)))
            solid = slab if solid is None else solid + slab
        return solid
    except Exception:
        print(f"  note: draft failed on a {face.area:.0f} mm2 face; extruded it straight")
        return extrude(face, amount=height)


def faces_of(shapes):
    """Accepts a Sketch, a Face or a list of either."""
    if hasattr(shapes, "faces"):
        return shapes.faces()
    return [f for s in shapes for f in (s.faces() if isinstance(s, Sketch) else [s])]
