"""Implicit (signed-distance) modeling on top of manifold3d's level_set.

For organic blends, lattices, gyroid infill, shells, twisted and repeated forms:
things that are awkward in B-rep CAD and slow as mesh booleans. Everything here is a
function f(x, y, z) -> value that is POSITIVE INSIDE the solid (manifold's convention),
zero on the surface, negative outside. x, y, z may be floats or numpy arrays: the
functions are written with numpy ufuncs so the whole grid is evaluated at once.

    from cadkit.sdf import *
    body = smooth_union(sphere(20), cylinder(8, 40, c=(0, 0, 20)), k=6)
    body = lattice_fill(body, cell=8, wall=1.6, skin=2.0)   # gyroid inside, solid skin
    def build(p):
        return build_sdf(body, bounds=(-25, -25, -1, 25, 25, 45), edge=0.6)

`build_sdf` samples f on a grid (fast, vectorised), then runs manifold's level set on
a trilinear lookup of that grid (about 7 us per grid point). A 50 mm part at edge 0.5
is ~1M points and takes ~10 s; keep edge >= 0.8 for parts over 100 mm. Detail finer
than ~2*edge is lost. A custom f written with `math` instead of numpy still works,
just slower (one call per point).

Lattices: a closed skin with a lattice inside (lattice_fill) is robust and prints
well. An open, see-through lattice band thinner than about two cells breaks into
disconnected pieces where the lattice sheet exits the band; make such bands thick or
give them thin skins.
"""
import math

import numpy as np
from manifold3d import Manifold

__all__ = ["sphere", "box", "cylinder", "capsule", "torus", "plane",
           "union", "intersect", "subtract", "smooth_union", "smooth_subtract", "smooth_intersect",
           "translate", "scale", "rotate_z", "rotate_x", "mirror_x", "repeat", "twist", "bend",
           "round_edges", "shell", "gyroid", "schwarz_p", "diamond", "lattice_fill",
           "build_sdf", "to_sdf"]


# ---------------------------------------------------------------- primitives

def sphere(r, c=(0, 0, 0)):
    cx, cy, cz = c
    return lambda x, y, z: r - np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)


def box(sx, sy, sz, c=(0, 0, 0), r=0.0):
    """Axis-aligned box of full size (sx, sy, sz) centred at c, edges rounded by r."""
    hx, hy, hz = sx / 2 - r, sy / 2 - r, sz / 2 - r
    cx, cy, cz = c

    def f(x, y, z):
        qx, qy, qz = np.abs(x - cx) - hx, np.abs(y - cy) - hy, np.abs(z - cz) - hz
        outside = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
        inside = np.minimum(np.maximum(np.maximum(qx, qy), qz), 0)
        return r - (outside + inside)
    return f


def cylinder(r, h, c=(0, 0, 0), axis="z", r_edge=0.0):
    """Cylinder of radius r, length h along `axis`, centred at c (so it spans c-h/2..c+h/2)."""
    cx, cy, cz = c
    ia = "xyz".index(axis)

    def f(x, y, z):
        p = (x - cx, y - cy, z - cz)
        a = p[ia]
        o = [p[i] for i in range(3) if i != ia]
        dr = np.sqrt(o[0] ** 2 + o[1] ** 2) - (r - r_edge)
        dh = np.abs(a) - (h / 2 - r_edge)
        outside = np.sqrt(np.maximum(dr, 0) ** 2 + np.maximum(dh, 0) ** 2)
        return r_edge - (outside + np.minimum(np.maximum(dr, dh), 0))
    return f


def capsule(a, b, r):
    """Round-ended rod from point a to point b."""
    ax, ay, az = a
    bx, by, bz = b
    dx, dy, dz = bx - ax, by - ay, bz - az
    L2 = dx * dx + dy * dy + dz * dz or 1e-12

    def f(x, y, z):
        t = np.clip(((x - ax) * dx + (y - ay) * dy + (z - az) * dz) / L2, 0.0, 1.0)
        px, py, pz = ax + t * dx, ay + t * dy, az + t * dz
        return r - np.sqrt((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2)
    return f


def torus(R, r, c=(0, 0, 0)):
    """Ring of major radius R, tube radius r, in the XY plane."""
    cx, cy, cz = c
    return lambda x, y, z: r - np.sqrt((np.sqrt((x - cx) ** 2 + (y - cy) ** 2) - R) ** 2 + (z - cz) ** 2)


def plane(normal=(0, 0, 1), offset=0.0):
    """Half-space: inside where p . normal <= offset. plane((0,0,1), 5) keeps z <= 5;
    plane((0,0,-1), -5) keeps z >= 5."""
    nx, ny, nz = normal
    n = math.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / n, ny / n, nz / n
    return lambda x, y, z: offset - (x * nx + y * ny + z * nz)


# ---------------------------------------------------------------- combining

def union(*fs):
    def f(x, y, z):
        out = fs[0](x, y, z)
        for g in fs[1:]:
            out = np.maximum(out, g(x, y, z))
        return out
    return f


def intersect(*fs):
    def f(x, y, z):
        out = fs[0](x, y, z)
        for g in fs[1:]:
            out = np.minimum(out, g(x, y, z))
        return out
    return f


def subtract(a, b):
    return lambda x, y, z: np.minimum(a(x, y, z), -b(x, y, z))


def _smax(a, b, k):
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0.0, 1.0)
    return a * h + b * (1 - h) + k * h * (1 - h)


def smooth_union(a, b, k=4.0):
    """Union with a fillet-like blend of radius ~k mm."""
    return lambda x, y, z: _smax(a(x, y, z), b(x, y, z), k)


def smooth_intersect(a, b, k=4.0):
    return lambda x, y, z: -_smax(-a(x, y, z), -b(x, y, z), k)


def smooth_subtract(a, b, k=4.0):
    return lambda x, y, z: -_smax(-a(x, y, z), b(x, y, z), k)


# ---------------------------------------------------------------- transforms

def translate(f, dx=0.0, dy=0.0, dz=0.0):
    return lambda x, y, z: f(x - dx, y - dy, z - dz)


def scale(f, s):
    """Uniform scale about the origin."""
    return lambda x, y, z: f(x / s, y / s, z / s) * s


def rotate_z(f, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return lambda x, y, z: f(c * x + s * y, -s * x + c * y, z)


def rotate_x(f, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return lambda x, y, z: f(x, c * y + s * z, -s * y + c * z)


def mirror_x(f):
    """Shape plus its mirror image across x=0."""
    return lambda x, y, z: np.maximum(f(x, y, z), f(-x, y, z))


def repeat(f, px=None, py=None, pz=None):
    """Tile f with the given periods (None = no repeat on that axis). The cell is
    centred on the origin, so f should sit within +-period/2."""
    def wrap(v, p):
        return v if p is None else np.mod(v + p / 2, p) - p / 2
    return lambda x, y, z: f(wrap(x, px), wrap(y, py), wrap(z, pz))


def twist(f, degrees_per_mm):
    """Twist about Z: each mm of height rotates the section."""
    k = math.radians(degrees_per_mm)

    def g(x, y, z):
        c, s = np.cos(k * z), np.sin(k * z)
        return f(c * x + s * y, -s * x + c * y, z)
    return g


def bend(f, degrees_per_mm):
    """Bend about Y: the X axis curls up as it goes along."""
    k = math.radians(degrees_per_mm)

    def g(x, y, z):
        c, s = np.cos(k * x), np.sin(k * x)
        return f(c * x + s * z, y, -s * x + c * z)
    return g


def round_edges(f, r):
    """Grow by r (rounds convex edges; negative r shrinks)."""
    return lambda x, y, z: f(x, y, z) + r


def shell(f, t):
    """Hollow f into a wall `t` thick, centred on the original surface.
    For a wall inside the original surface use shell(round_edges(f, -t/2), t)."""
    return lambda x, y, z: t / 2 - np.abs(f(x, y, z))


# ---------------------------------------------------------------- lattices

def _tpms(g, cell, wall):
    """Triply-periodic minimal surface thickened to a wall. `wall` is approximate:
    the implicit value is scaled by cell/2pi, which is within ~30% of true distance."""
    k = 2 * math.pi / cell
    s = cell / (2 * math.pi)
    return lambda x, y, z: wall / 2 - np.abs(g(x * k, y * k, z * k)) * s


def gyroid(cell=10.0, wall=1.6):
    return _tpms(lambda x, y, z: np.sin(x) * np.cos(y) + np.sin(y) * np.cos(z) + np.sin(z) * np.cos(x),
                 cell, wall)


def schwarz_p(cell=10.0, wall=1.6):
    return _tpms(lambda x, y, z: np.cos(x) + np.cos(y) + np.cos(z), cell, wall)


def diamond(cell=10.0, wall=1.6):
    def g(x, y, z):
        sx, sy, sz, cx, cy, cz = np.sin(x), np.sin(y), np.sin(z), np.cos(x), np.cos(y), np.cos(z)
        return sx * sy * sz + sx * cy * cz + cx * sy * cz + cx * cy * sz
    return _tpms(g, cell, wall)


def lattice_fill(f, cell=10.0, wall=1.6, skin=2.0, lattice=gyroid):
    """Keep the outer `skin` mm of f solid and fill the inside with a lattice
    (gyroid, schwarz_p or diamond). The sealed air cells show up in the build
    report as 'enclosed voids'; slicers print them hollow."""
    lat = lattice(cell, wall)

    def g(x, y, z):
        v = f(x, y, z)
        return np.maximum(np.minimum(v, skin - v), np.minimum(v, lat(x, y, z)))
    return g


# ---------------------------------------------------------------- output

def build_sdf(f, bounds, edge=0.5, level=0.0, flat_bottom=True):
    """Mesh the solid where f > level. `bounds` = (xmin, ymin, zmin, xmax, ymax, zmax)
    or ((xmin, ymin, zmin), (xmax, ymax, zmax)); `edge` is the grid spacing in mm.
    Returns a manifold3d.Manifold, which the model can return directly or combine
    with other Manifolds (cadkit.relief shapes, text...).

    The level set rounds sharp edges by about edge/2. With `flat_bottom` (and bounds
    that reach below z=0) the result is trimmed flat at z=0 afterwards, so a part that
    sits on the bed keeps a crisp bottom edge instead of a tiny chamfer the overhang
    check would flag."""
    if len(bounds) == 2:
        bounds = (*bounds[0], *bounds[1])
    edge = float(edge)
    trim = flat_bottom and bounds[2] <= 0 < bounds[5]
    # offset the grid so no sample plane coincides with a flat face at a round
    # coordinate (z=0 bottoms): sampling exactly on the surface gives a jagged skin
    lo = np.array(bounds[:3], float) - 0.37 * edge
    hi = np.array(bounds[3:], float) + 0.37 * edge
    if trim:
        lo[2] = min(lo[2], -2 * edge)
    axes = [np.arange(l, h + edge, edge) for l, h in zip(lo, hi)]
    try:
        X, Y, Z = np.meshgrid(*axes, indexing="ij")
        # extrude the section just above the bed straight down, so after trimming at
        # z=0 the bottom edge is sharp rather than rounded by the level set
        G = np.asarray(f(X, Y, np.maximum(Z, 2 * edge) if trim else Z), float)
        if G.shape != X.shape:
            raise TypeError("not vectorised")
        callable_ = _trilinear(G, lo, edge)
    except Exception:
        print("  note: SDF is not numpy-vectorised; evaluating point by point (slow)")
        callable_ = (lambda x, y, z: float(f(x, y, max(z, 2 * edge)))) if trim else (lambda x, y, z: float(f(x, y, z)))
    m = Manifold.level_set(callable_, [*lo, *(lo + edge * (np.array(G.shape) - 1))] if "G" in dir() else list(bounds),
                           edge, float(level))
    if m.is_empty():
        raise ValueError("SDF produced no solid inside the bounds; check signs (positive = inside) and bounds")
    if trim:
        span = hi - lo
        m = m ^ Manifold.cube([span[0], span[1], hi[2] + 1]).translate([lo[0], lo[1], 0.0])
    return m


def _trilinear(G, lo, edge):
    """Fast pure-Python trilinear lookup into a sampled grid for manifold's level_set."""
    nx, ny, nz = G.shape
    L = G.tolist()
    inv = 1.0 / edge
    lx, ly, lz = (float(v) for v in lo)

    def f(x, y, z):
        fx, fy, fz = (x - lx) * inv, (y - ly) * inv, (z - lz) * inv
        i, j, k = int(fx), int(fy), int(fz)
        if i < 0 or j < 0 or k < 0 or i >= nx - 1 or j >= ny - 1 or k >= nz - 1:
            return -1.0
        tx, ty, tz = fx - i, fy - j, fz - k
        a, b = L[i], L[i + 1]
        a0, a1, b0, b1 = a[j], a[j + 1], b[j], b[j + 1]
        c00 = a0[k] * (1 - tz) + a0[k + 1] * tz
        c01 = a1[k] * (1 - tz) + a1[k + 1] * tz
        c10 = b0[k] * (1 - tz) + b0[k + 1] * tz
        c11 = b1[k] * (1 - tz) + b1[k + 1] * tz
        return (c00 * (1 - ty) + c01 * ty) * (1 - tx) + (c10 * (1 - ty) + c11 * ty) * tx
    return f


def to_sdf(manifold_or_mesh):
    """An SDF (positive inside) for an existing watertight mesh or Manifold, so CAD
    or mesh parts can be blended and lattice-filled. Nearest-surface distance with
    an inside test, vectorised over the grid."""
    import trimesh
    from trimesh import proximity
    obj = manifold_or_mesh
    if not isinstance(obj, trimesh.Trimesh):
        from .mesh import to_trimesh
        obj = to_trimesh(obj)
    q = proximity.ProximityQuery(obj)

    def f(x, y, z):
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
        pts = np.c_[x.ravel(), y.ravel(), z.ravel()]
        return q.signed_distance(pts).reshape(x.shape)
    return f
