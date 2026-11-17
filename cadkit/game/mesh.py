"""Game-mesh primitives and operations. Metres, Y up, counter-clockwise front faces.

Every primitive comes with normals and UVs. Hard edges are duplicated vertices, the way a
GPU wants them; `flat(mesh)` makes every face hard.
"""
import numpy as np

from .model import Mesh, merge, vertex_normals   # noqa: F401  (re-exported)


def _orient(v, f, n):
    """Flip triangles whose winding disagrees with their vertex normals."""
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    want = n[f].sum(1)
    bad = (fn * want).sum(1) < 0
    f = f.copy()
    f[bad] = f[bad][:, ::-1]
    return f


def box(sx=1.0, sy=1.0, sz=1.0, uv="face"):
    """Cuboid centred on the origin, 24 vertices. uv="face": every face spans 0..1.
    uv=<number>: world-space UVs at that many repeats per metre (for tiling materials)."""
    h = np.array([sx, sy, sz]) / 2
    vs, ns, uvs, fs = [], [], [], []
    for axis in range(3):
        for sign in (1, -1):
            a, b = [(1, 2), (2, 0), (0, 1)][axis]
            nrm = np.zeros(3); nrm[axis] = sign
            quad = []
            for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = np.zeros(3); p[axis] = sign * h[axis]; p[a] = du * h[a]; p[b] = dv * h[b]
                quad.append(p)
                if uv == "face":
                    uvs.append(((du + 1) / 2, (1 - dv) / 2))
                else:
                    uvs.append((p[a] * uv, -p[b] * uv))
            i = len(vs)
            vs += quad; ns += [nrm] * 4
            fs += [(i, i + 1, i + 2), (i, i + 2, i + 3)]
    v, n = np.array(vs), np.array(ns)
    return Mesh(v, _orient(v, np.array(fs), n), n, np.array(uvs))


def lathe(profile, sides=24, u_repeat=1.0, v_range=(0.0, 1.0), phase=0.0, smooth=True):
    """Revolve a profile of (radius, y) points, bottom to top, about the Y axis.
    u runs round the axis (0..u_repeat), v along the profile's length from v_range[1] at the
    bottom to v_range[0] at the top (image top = model top). No caps: add `disc`s.
    The surface faces to the right of the direction of travel: bottom to top faces outward
    (a vase), top to bottom faces the axis (the inside of a bowl, a rim's inner wall)."""
    prof = np.asarray(profile, float)
    seg = np.diff(prof, axis=0)
    length = np.concatenate([[0], np.cumsum(np.linalg.norm(seg, axis=1))])
    t = length / max(length[-1], 1e-12)
    vcoord = v_range[1] + (v_range[0] - v_range[1]) * t
    sn = np.stack([seg[:, 1], -seg[:, 0]], 1)                 # outward in the (r, y) plane
    sn /= np.maximum(np.linalg.norm(sn, axis=1, keepdims=True), 1e-12)
    ang = np.radians(phase) + np.linspace(0, 2 * np.pi, sides + 1)
    cos, sin = np.cos(ang), np.sin(ang)

    def ring(r, y, nr, ny, vc):
        v = np.stack([r * cos, np.full_like(cos, y), r * sin], 1)
        n = np.stack([nr * cos, np.full_like(cos, ny), nr * sin], 1)
        uv = np.stack([np.linspace(0, u_repeat, sides + 1), np.full_like(cos, vc)], 1)
        return v, n, uv

    vs, ns, uvs, fs = [], [], [], []
    if smooth:
        pn = np.zeros_like(prof)
        pn[:-1] += sn; pn[1:] += sn
        pn /= np.maximum(np.linalg.norm(pn, axis=1, keepdims=True), 1e-12)
        for (r, y), (nr, ny), vc in zip(prof, pn, vcoord):
            a, b, c = ring(r, y, nr, ny, vc); vs.append(a); ns.append(b); uvs.append(c)
        rings = [(i, i + 1) for i in range(len(prof) - 1)]
    else:
        rings = []
        for i in range(len(prof) - 1):
            for j in (i, i + 1):
                a, b, c = ring(prof[j, 0], prof[j, 1], sn[i, 0], sn[i, 1], vcoord[j])
                vs.append(a); ns.append(b); uvs.append(c)
            rings.append((2 * i, 2 * i + 1))
    w = sides + 1
    for lo, hi in rings:
        for k in range(sides):
            a, b, c, d = lo * w + k, lo * w + k + 1, hi * w + k + 1, hi * w + k
            fs += [(a, b, c), (a, c, d)]
    v, n = np.vstack(vs), np.vstack(ns)
    f = np.array(fs)
    area = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
    f = f[area > 1e-12]                                       # a profile point on the axis
    return Mesh(v, _orient(v, f, n), n, np.vstack(uvs))


def disc(r, y=0.0, sides=24, up=True, uv_rect=(0.0, 0.0, 1.0, 1.0), phase=0.0):
    """Flat disc at height y facing +Y (up) or -Y. Its UVs fill uv_rect = (u0, v0, u1, v1)."""
    ang = np.radians(phase) + np.linspace(0, 2 * np.pi, sides, endpoint=False)
    rim = np.stack([r * np.cos(ang), np.full_like(ang, y), r * np.sin(ang)], 1)
    v = np.vstack([[0, y, 0], rim])
    u0, v0, u1, v1 = uv_rect
    uv = np.stack([u0 + (v[:, 0] / r + 1) / 2 * (u1 - u0), v0 + (v[:, 2] / r + 1) / 2 * (v1 - v0)], 1)
    n = np.tile([0, 1.0 if up else -1.0, 0], (len(v), 1))
    f = np.array([(0, 1 + (k + 1) % sides, 1 + k) for k in range(sides)])
    return Mesh(v, _orient(v, f, n), n, uv)


def cylinder(r, h, sides=24, r_top=None, caps=True, u_repeat=1.0):
    """Upright cylinder or cone frustum, base on Y=0."""
    rt = r if r_top is None else r_top
    m = lathe([(r, 0), (rt, h)], sides, u_repeat)
    if caps:
        m = merge(m, disc(r, 0, sides, up=False), disc(rt, h, sides) if rt > 0 else None)
    return m


def torus(R, r, segments=24, sides=10):
    """Ring of major radius R and tube radius r lying in the XZ plane, centred on the origin."""
    a = np.linspace(0, 2 * np.pi, segments + 1)
    b = np.linspace(0, 2 * np.pi, sides + 1)
    A, B = np.meshgrid(a, b, indexing="ij")
    n = np.stack([np.cos(B) * np.cos(A), np.sin(B), np.cos(B) * np.sin(A)], -1).reshape(-1, 3)
    c = np.stack([R * np.cos(A), np.zeros_like(A), R * np.sin(A)], -1).reshape(-1, 3)
    v = c + r * n
    uv = np.stack([A / (2 * np.pi), B / (2 * np.pi)], -1).reshape(-1, 2)
    w = sides + 1
    fs = []
    for i in range(segments):
        for j in range(sides):
            p, q, s, t = i * w + j, (i + 1) * w + j, (i + 1) * w + j + 1, i * w + j + 1
            fs += [(p, q, s), (p, s, t)]
    return Mesh(v, _orient(v, np.array(fs), n), n, uv)


def prism(points, depth, cap_uv=1.0, centre=None):
    """Extrude a polygon of (x, y) points along Z, centred on Z=0, with flat-shaded sides and
    capped ends. Points go counter-clockwise seen from +Z. The polygon must be convex, or, with
    `centre=(x, y)`, visible from that point (a star, an arrow): the caps then fan from it.
    UVs are in metres times `cap_uv` on the caps, and run round the outline (u) and along the
    depth (v) on the sides."""
    pts = np.asarray(points, float)
    k, h = len(pts), depth / 2
    vs, ns, uvs, fs = [], [], [], []
    run = 0.0
    for i in range(k):
        a, b = pts[i], pts[(i + 1) % k]
        e = b - a
        length = np.linalg.norm(e)
        nrm = np.array([e[1], -e[0], 0.0]) / max(length, 1e-12)
        j = len(vs)
        vs += [(a[0], a[1], h), (b[0], b[1], h), (b[0], b[1], -h), (a[0], a[1], -h)]
        ns += [nrm] * 4
        uvs += [(run, 0), (run + length, 0), (run + length, depth), (run, depth)]
        fs += [(j, j + 1, j + 2), (j, j + 2, j + 3)]
        run += length
    for z, sign in ((h, 1.0), (-h, -1.0)):
        j = len(vs)
        vs += [(x, y, z) for x, y in pts]
        ns += [(0, 0, sign)] * k
        uvs += [(x * cap_uv * sign, -y * cap_uv) for x, y in pts]
        if centre is None:
            fs += [(j, j + i, j + i + 1) for i in range(1, k - 1)]
        else:
            vs.append((centre[0], centre[1], z))
            ns.append((0, 0, sign))
            uvs.append((centre[0] * cap_uv * sign, -centre[1] * cap_uv))
            fs += [(j + k, j + i, j + (i + 1) % k) for i in range(k)]
    v, n = np.array(vs, float), np.array(ns, float)
    return Mesh(v, _orient(v, np.array(fs), n), n, np.array(uvs, float))


def bevel_box(sx, sy, sz, bevel=0.03):
    """A cuboid centred on the origin with every edge chamfered by `bevel` metres: 44 triangles,
    flat-shaded. Its flat faces still reach the full size, so pieces stack flush. Each face's
    UVs span 0..1; the chamfers take the UVs of the face they lean toward most."""
    h = np.array([sx, sy, sz]) / 2
    b = min(bevel, h.min() * 0.49)
    polys = []
    for i in range(3):                                           # six faces
        j, k = (i + 1) % 3, (i + 2) % 3
        for si in (1, -1):
            q = []
            for dj, dk in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = np.zeros(3); p[i] = si * h[i]; p[j] = dj * (h[j] - b); p[k] = dk * (h[k] - b)
                q.append(p)
            polys.append(q)
    for i in range(3):                                           # twelve edge chamfers
        j, k = (i + 1) % 3, (i + 2) % 3
        for si in (1, -1):
            for sj in (1, -1):
                q = []
                for (ci, cj), dk in (((h[i], h[j] - b), -1), ((h[i], h[j] - b), 1),
                                     ((h[i] - b, h[j]), 1), ((h[i] - b, h[j]), -1)):
                    p = np.zeros(3); p[i] = si * ci; p[j] = sj * cj; p[k] = dk * (h[k] - b)
                    q.append(p)
                polys.append(q)
    for sx_ in (1, -1):                                          # eight corners
        for sy_ in (1, -1):
            for sz_ in (1, -1):
                s = np.array([sx_, sy_, sz_])
                polys.append([s * (h - b * np.array(m)) for m in ((0, 1, 1), (1, 0, 1), (1, 1, 0))])
    vs, ns, fs = [], [], []
    for q in polys:
        c = np.mean(q, axis=0)
        nrm = np.cross(q[1] - q[0], q[2] - q[0])
        nrm /= np.linalg.norm(nrm)
        if nrm @ c < 0:
            nrm = -nrm
        i0 = len(vs)
        vs += q
        ns += [nrm] * len(q)
        fs += [(i0, i0 + t, i0 + t + 1) for t in range(1, len(q) - 1)]
    v, n = np.array(vs), np.array(ns)
    ax = np.abs(n).argmax(1)
    uv = np.zeros((len(v), 2))
    for a, (iu, iv) in {0: (2, 1), 1: (0, 2), 2: (0, 1)}.items():
        m = ax == a
        uv[m, 0] = v[m, iu] / (2 * h[iu]) + 0.5
        uv[m, 1] = 0.5 - v[m, iv] / (2 * h[iv])
    return Mesh(v, _orient(v, np.array(fs), n), n, uv)


def wedge(sx, sy, sz):
    """A ramp: sx wide, rising from Y=0 at +Z to sy at -Z over sz (it climbs toward -Z, the way
    a player walks forward). Base on Y=0, centred in X and Z. Each face's UVs span 0..1."""
    tri = prism([(-sz / 2, 0), (sz / 2, 0), (sz / 2, sy)], sx)   # in (x=run, y=up), extruded along Z
    m = tri.rotated(90, "y")                                     # run x -> -z, extrusion z -> x
    lo, hi = m.bounds
    ax = np.abs(m.n).argmax(1)
    uv = np.zeros((len(m.v), 2))
    for a, (iu, iv) in {0: (2, 1), 1: (0, 2), 2: (0, 1)}.items():
        k = ax == a
        uv[k, 0] = (m.v[k, iu] - lo[iu]) / (hi[iu] - lo[iu])
        uv[k, 1] = 1 - (m.v[k, iv] - lo[iv]) / (hi[iv] - lo[iv])
    return m.with_uv(uv)


def block(sx, sy, sz, x=0.0, y=0.0, z=0.0):
    """A box standing on Y=y with its base centre at (x, y, z): the usual way to stack
    architecture. UVs per face; follow with `box_uv` for world-scale tiling."""
    return box(sx, sy, sz).moved(x, y + sy / 2, z)


def flat(mesh):
    """Hard-edge every face: one vertex per triangle corner, face normals."""
    v = mesh.v[mesh.f].reshape(-1, 3)
    uv = mesh.uv[mesh.f].reshape(-1, 2)
    f = np.arange(len(v)).reshape(-1, 3)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    return Mesh(v, f, np.repeat(fn, 3, 0), uv)


def box_uv(mesh, per_metre=1.0):
    """Project UVs along each vertex's dominant normal axis (use after `flat` or on hard-edged
    meshes). per_metre = texture repeats per metre."""
    ax = np.abs(mesh.n).argmax(1)
    uv = np.zeros((len(mesh.v), 2))
    for a, (i, j) in {0: (2, 1), 1: (0, 2), 2: (0, 1)}.items():
        m = ax == a
        uv[m, 0] = mesh.v[m, i] * per_metre
        uv[m, 1] = -mesh.v[m, j] * per_metre
    return mesh.with_uv(uv)


def to_game(part, scale=0.001, tolerance=0.05):
    """A build123d Part, manifold3d Manifold or trimesh mesh from the CAD kernels (mm, Z up)
    as a flat-shaded game Mesh (metres, Y up). UVs are box-projected at 1 repeat per metre."""
    from .. import mesh as cadmesh
    tm = cadmesh.to_trimesh(part, tolerance) if hasattr(cadmesh, "to_trimesh") else part
    v = np.asarray(tm.vertices, float) * scale
    v = np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)             # Z up -> Y up, right-handed
    return box_uv(flat(Mesh(v, np.asarray(tm.faces))))


def volume(mesh):
    """Signed volume; positive when the faces wind counter-clockwise seen from outside."""
    a, b, c = (mesh.v[mesh.f[:, k]] for k in range(3))
    return float((a * np.cross(b, c)).sum() / 6)


def ball(r=0.5, sides=12, rings=8):
    """A sphere centred on the origin (scale it for an ellipsoid)."""
    prof = [(r * np.sin(t), -r * np.cos(t)) for t in np.linspace(0, np.pi, rings + 1)]
    prof[0], prof[-1] = (0.0, -r), (0.0, r)
    return lathe(prof, sides)


def along(mesh, a, b):
    """Stand a mesh built along +Y from the origin so that its Y axis runs from point a toward b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    y = np.array([0.0, 1.0, 0.0])
    v = np.cross(y, d)
    s, c = np.linalg.norm(v), float(y @ d)
    if s < 1e-9:
        r = np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    else:
        k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        r = np.eye(3) + k + k @ k * ((1 - c) / s ** 2)
    return Mesh(mesh.v @ r.T + a, mesh.f, mesh.n @ r.T, mesh.uv)


def capsule(a, b, r0, r1=None, sides=12, rings=4):
    """A limb: a tube from point a to point b with radius r0 at a and r1 at b, rounded at both
    ends. Bodies for sculpting are built from these and `ball`s, then fused in Blender."""
    r1 = r0 if r1 is None else r1
    length = float(np.linalg.norm(np.asarray(b, float) - np.asarray(a, float)))
    quarter = np.linspace(0, np.pi / 2, rings + 1)
    prof = [(r0 * np.sin(t), -r0 * np.cos(t)) for t in quarter] + \
           [(r1 * np.cos(t), length + r1 * np.sin(t)) for t in quarter]
    prof[0], prof[-1] = (0.0, -r0), (0.0, length + r1)
    return along(lathe(prof, sides), a, b)


def wind_to_normals(mesh):
    """Turn round any triangle that winds against its own vertex normals (a decimated mesh can
    leave one or two): the engine culls by winding, so such a face would be a hole."""
    a, b, c = (mesh.v[mesh.f[:, k]] for k in range(3))
    back = (np.cross(b - a, c - a) * mesh.n[mesh.f].sum(1)).sum(1) < 0
    if not back.any():
        return mesh
    f = mesh.f.copy()
    f[back] = f[back][:, [0, 2, 1]]
    return Mesh(mesh.v, f, mesh.n, mesh.uv)
