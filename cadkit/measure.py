"""Interrogate a built mesh with numbers instead of eyeballing the preview.

All functions take a trimesh.Trimesh (what `cad build` exports) and work for either
kernel. Points are (x, y, z) in mm. Used by the CHECKS in model scripts
(cadkit.checks) and by `cad measure`.
"""
import numpy as np
from trimesh import proximity

AXIS = dict(x=0, y=1, z=2)


def extents(tm):
    """(lo, hi, size) of the axis-aligned bounding box."""
    lo, hi = tm.bounds
    return lo, hi, hi - lo


def contains(tm, points):
    """True for each point that is inside the solid."""
    return np.asarray(tm.contains(np.atleast_2d(np.asarray(points, float))), bool)


def distance_to_surface(tm, points):
    """Unsigned distance from each point to the nearest surface, mm."""
    return np.asarray(proximity.closest_point(tm, np.atleast_2d(points))[1], float)


def ray_distance(tm, origin, direction):
    """Distance along `direction` from `origin` to the first surface hit, or inf."""
    origin = np.asarray(origin, float)[None]
    direction = np.asarray(direction, float)
    direction = (direction / np.linalg.norm(direction))[None]
    loc, idx, _ = tm.ray.intersects_location(origin, direction, multiple_hits=True)
    if len(loc) == 0:
        return float("inf")
    d = np.linalg.norm(loc - origin, axis=1)
    d = d[d > 1e-6]
    return float(d.min()) if len(d) else float("inf")


def thickness_at(tm, point, direction=None):
    """Material thickness at a point. From a point inside the solid, it is the span of
    material along `direction` (default: through the nearest surface's normal). From a
    point on or outside the surface, it is the wall thickness at the nearest surface
    point. Returns 0 if the point is not in or on material."""
    point = np.asarray(point, float)
    if direction is None:
        close, dist, fid = proximity.closest_point(tm, point[None])
        direction = tm.face_normals[fid[0]]
        if not contains(tm, point[None])[0]:
            point = close[0] - direction * 0.01   # step just inside the surface
    direction = np.asarray(direction, float) / np.linalg.norm(direction)
    if not contains(tm, point[None])[0]:
        return 0.0
    a = ray_distance(tm, point, direction)
    b = ray_distance(tm, point, -direction)
    return float(a + b) if np.isfinite(a) and np.isfinite(b) else 0.0


def hole_diameter(tm, at, axis="z", height=None, rays=12):
    """Measured diameter of a hole whose axis passes through `at` (the two coordinates
    not on `axis`), probed at `height` along the axis (default: bbox mid-height).
    Returns (mean_diameter, min_diameter) or (0, 0) if the probe point is in material."""
    ax = AXIS[axis]
    others = [i for i in range(3) if i != ax]
    lo, hi, _ = extents(tm)
    c = np.zeros(3)
    c[ax] = (lo[ax] + hi[ax]) / 2 if height is None else height
    c[others[0]], c[others[1]] = at
    if contains(tm, c[None])[0]:
        return 0.0, 0.0
    ds = []
    for a in np.linspace(0, 2 * np.pi, rays, endpoint=False):
        d = np.zeros(3)
        d[others[0]], d[others[1]] = np.cos(a), np.sin(a)
        ds.append(ray_distance(tm, c, d))
    ds = np.array(ds)
    if not np.isfinite(ds).all():
        return float("inf"), float("inf")
    # opposite rays pair up into diameters
    pairs = ds[: rays // 2] + ds[rays // 2:]
    return float(pairs.mean()), float(pairs.min())


def probe(tm, point):
    """Everything about one point, for `cad measure --probe`."""
    point = np.asarray(point, float)
    inside = bool(contains(tm, point[None])[0])
    dist = float(distance_to_surface(tm, point[None])[0])
    return dict(point=tuple(round(float(v), 2) for v in point), inside=inside,
                distance_to_surface=round(dist, 2),
                thickness=round(thickness_at(tm, point), 2))


def summary(tm):
    lo, hi, size = extents(tm)
    cen = tm.center_mass if tm.is_watertight else tm.centroid
    return [
        f"size     {size[0]:.2f} x {size[1]:.2f} x {size[2]:.2f} mm",
        f"bounds   x {lo[0]:.2f}..{hi[0]:.2f}  y {lo[1]:.2f}..{hi[1]:.2f}  z {lo[2]:.2f}..{hi[2]:.2f}",
        f"volume   {abs(tm.volume) / 1000:.2f} cm3, surface {tm.area / 100:.1f} cm2",
        f"centroid ({cen[0]:.2f}, {cen[1]:.2f}, {cen[2]:.2f})",
    ]
