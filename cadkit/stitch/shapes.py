"""2D geometry for embroidery designs: shapely polygons for fills, numpy polylines for
satin columns and running stitches. Millimetres, Y up, the design centred on the origin.

Fill shapes are shapely (Multi)Polygons, so every shapely operation works on them
(`a | b`, `a - b`, `a & b`, `.buffer(mm)`). Paths are (N, 2) arrays.
"""
import math

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

__all__ = ["circle", "ellipse", "rect", "rounded_rect", "poly", "smooth", "star", "heart",
           "ring", "regular_polygon", "union", "knockout", "grow", "shrink", "move", "rotate", "scale",
           "mirror_x", "from_cs", "text_shape", "svg", "trace", "line", "arc", "bezier",
           "spline", "circle_path", "outline_paths", "centered", "polygons_of"]


# ---------- fill shapes ----------

def circle(x, y, r, res=96):
    return ellipse(x, y, r, r, res)


def ellipse(x, y, rx, ry, res=96):
    t = np.linspace(0, 2 * np.pi, res, endpoint=False)
    return Polygon(np.c_[x + rx * np.cos(t), y + ry * np.sin(t)])


def rect(w, h, x=0.0, y=0.0):
    """Rectangle w x h centred on (x, y)."""
    return Polygon([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2),
                    (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)])


def rounded_rect(w, h, r, x=0.0, y=0.0):
    r = min(r, w / 2 - 1e-3, h / 2 - 1e-3)
    return rect(w - 2 * r, h - 2 * r, x, y).buffer(r, quad_segs=16)


def poly(points):
    """Polygon from points (either winding); self-intersections repaired."""
    return shapely.make_valid(Polygon(np.asarray(points, float)))


def smooth(points, samples=12):
    """Smooth closed shape through the points (Catmull-Rom)."""
    return poly(_catmull_rom(np.asarray(points, float), samples, closed=True))


def regular_polygon(n, r, x=0.0, y=0.0, rot=90.0):
    t = np.radians(rot) + np.arange(n) * 2 * np.pi / n
    return Polygon(np.c_[x + r * np.cos(t), y + r * np.sin(t)])


def star(points, r_out, r_in, x=0.0, y=0.0, rot=90.0):
    t = np.radians(rot) + np.arange(2 * points) * np.pi / points
    r = np.where(np.arange(2 * points) % 2 == 0, r_out, r_in)
    return Polygon(np.c_[x + r * np.cos(t), y + r * np.sin(t)])


def heart(width, x=0.0, y=0.0, res=160):
    """Heart `width` mm across, centred on its bounding box, notch up."""
    t = np.linspace(0, 2 * np.pi, res, endpoint=False)
    hx = 16 * np.sin(t) ** 3
    hy = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    pts = np.c_[hx, hy]
    pts -= (pts.min(0) + pts.max(0)) / 2
    pts *= width / np.ptp(pts[:, 0])
    return Polygon(pts + (x, y))


def ring(x, y, r_out, r_in, res=128):
    return circle(x, y, r_out, res) - circle(x, y, r_in, res)


def union(*shapes):
    return unary_union([s for s in shapes if s is not None and not s.is_empty])


def knockout(shape, *above, overlap=0.4, min_width=1.0):
    """`shape` with everything sewn on top of it cut out, leaving `overlap` mm under
    each upper shape so no fabric shows at the seam. Stacking fills doubles the
    density (stiff, puckered, needle breaks); knocking out is how digitizers layer.
    Slivers narrower than `min_width` left by the cut are dropped (they would sew as
    a mess of tiny stitches); the upper shapes cover those spots anyway."""
    top = union(*above)
    if top.is_empty:
        return shape
    cut = shape.difference(top.buffer(-overlap, quad_segs=16))
    if min_width:
        cut = cut.buffer(-min_width / 2, quad_segs=8).buffer(min_width / 2, quad_segs=8)
    return cut


def grow(shape, mm):
    """Offset outward (negative shrinks), round corners."""
    return shape.buffer(mm, quad_segs=16)


def shrink(shape, mm):
    return shape.buffer(-mm, quad_segs=16)


def move(g, dx=0.0, dy=0.0):
    if isinstance(g, np.ndarray):
        return g + (dx, dy)
    return affinity.translate(g, dx, dy)


def rotate(g, deg, origin=(0, 0)):
    if isinstance(g, np.ndarray):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        o = np.asarray(origin, float)
        return (g - o) @ np.array([[c, s], [-s, c]]) + o
    return affinity.rotate(g, deg, origin=origin)


def scale(g, sx, sy=None, origin=(0, 0)):
    sy = sx if sy is None else sy
    if isinstance(g, np.ndarray):
        o = np.asarray(origin, float)
        return (g - o) * (sx, sy) + o
    return affinity.scale(g, sx, sy, origin=origin)


def mirror_x(shape):
    """Shape plus its mirror image across the Y axis."""
    return union(shape, affinity.scale(shape, -1, 1, origin=(0, 0)))


def centered(shape):
    """Shape moved so its bounding box is centred on the origin."""
    x0, y0, x1, y1 = shape.bounds
    return affinity.translate(shape, -(x0 + x1) / 2, -(y0 + y1) / 2)


def polygons_of(shape):
    """List of Polygons in a Polygon / MultiPolygon / GeometryCollection."""
    if shape is None or shape.is_empty:
        return []
    if isinstance(shape, Polygon):
        return [shape]
    if isinstance(shape, MultiPolygon):
        return list(shape.geoms)
    return [g for part in getattr(shape, "geoms", []) for g in polygons_of(part)]


def from_cs(cs):
    """shapely shape from a manifold3d CrossSection (relief/image helpers): rings are
    combined even-odd, so counters in letters stay holes."""
    out = None
    for ring_pts in cs.to_polygons():
        if len(ring_pts) < 3:
            continue
        p = shapely.make_valid(Polygon(ring_pts))
        out = p if out is None else out.symmetric_difference(p)
    return out if out is not None else Polygon()


def text_shape(string, size, font="Arial", bold=True, font_path=None):
    """Text outline (cap height `size` mm) centred on the origin, for fills.
    Lettering under ~6 mm cap height does not read as a fill: use bigger text."""
    from ..relief import text
    return from_cs(text(string, size, font=font, bold=bold, font_path=font_path))


def svg(path, width=None, height=None):
    """Filled paths of an SVG file as a shape, scaled to width (or height) mm."""
    from ..image import svg_shape
    return from_cs(svg_shape(path, width=width, height=height))


def trace(image, width=None, height=None, threshold=128, invert=False, min_area=4.0):
    """Dark shapes of an image (logo, silhouette, sketch) traced into a shape."""
    from ..image import trace as _trace
    return from_cs(_trace(image, width=width, height=height, threshold=threshold,
                          invert=invert, min_area=min_area))


# ---------- paths (satin columns, running stitch) ----------

def line(*points):
    return np.asarray(points, float)


def arc(x, y, r, a0, a1, res_deg=5.0):
    """Circular arc from angle a0 to a1 (degrees, CCW positive)."""
    n = max(2, int(abs(a1 - a0) / res_deg) + 1)
    t = np.radians(np.linspace(a0, a1, n))
    return np.c_[x + r * np.cos(t), y + r * np.sin(t)]


def circle_path(x, y, r, res=96):
    """Closed circle as a path (first point repeated at the end)."""
    return arc(x, y, r, 90, 450, 360 / res)


def bezier(p0, c0, c1, p1, n=32):
    """Cubic bezier p0 -> p1 with control points c0, c1."""
    t = np.linspace(0, 1, n)[:, None]
    p0, c0, c1, p1 = (np.asarray(v, float) for v in (p0, c0, c1, p1))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * c0 + 3 * (1 - t) * t ** 2 * c1 + t ** 3 * p1


def spline(points, samples=10, closed=False):
    """Smooth path through the points (Catmull-Rom)."""
    return _catmull_rom(np.asarray(points, float), samples, closed)


def outline_paths(shape):
    """Every ring of a shape (exteriors and holes) as closed paths, for outlining a
    fill with a running stitch or a satin border."""
    out = []
    for p in polygons_of(shape):
        out.append(np.asarray(p.exterior.coords))
        out += [np.asarray(r.coords) for r in p.interiors]
    return out


def _catmull_rom(pts, samples, closed):
    if closed:
        P = np.vstack([pts[-1], pts, pts[0], pts[1]])
    else:
        P = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    out = []
    t = np.linspace(0, 1, samples, endpoint=False)[:, None]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out = np.vstack(out)
    return np.vstack([out, out[:1]]) if closed else np.vstack([out, pts[-1:]])


def path_length(path):
    return float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())


def as_line(path):
    return LineString(np.asarray(path, float))
