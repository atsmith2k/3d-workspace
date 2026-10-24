"""Turn whatever a model returns into one clean, checked triangle mesh."""
from dataclasses import dataclass, field

import numpy as np
import trimesh
from trimesh import proximity, sample

PLA_DENSITY = 1.24          # g/cm3
TINKERCAD_MAX_BYTES = 25e6  # Tinkercad's STL import limit
OVERHANG_DEG = 45           # faces steeper than this below horizontal need support
MIN_WALL = 1.2              # mm; thinner walls drop out or print as single fragile lines


def to_trimesh(obj, tolerance=0.01, angular_tolerance=0.1):
    """Accepts a build123d Shape, a manifold3d.Manifold or a trimesh.Trimesh."""
    if isinstance(obj, trimesh.Trimesh):
        v, f = obj.vertices, obj.faces
    elif type(obj).__module__.startswith("manifold3d"):
        # booleans can leave microscopic slivers that collapse when rounded to STL's
        # float32; try a few simplify tolerances until the result is a clean solid
        for tol in (0.01, 0.02, 0.005, 0.03):
            m = obj.simplify(tol).to_mesh()
            tm = clean(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts))
            if tm.is_watertight and tm.is_winding_consistent:
                return tm
        return tm
    elif hasattr(obj, "tessellate"):
        verts, tris = obj.tessellate(tolerance, angular_tolerance)
        v = np.array([(p.X, p.Y, p.Z) for p in verts])
        f = np.array(tris, dtype=np.int64)
    else:
        raise TypeError(f"build() returned {type(obj).__name__}; expected a build123d "
                        "Part/Solid, manifold3d.Manifold or trimesh.Trimesh")
    return clean(np.asarray(v, float), np.asarray(f))


def clean(v, f):
    """STL stores float32, so round to it first, then weld and drop zero-area slivers."""
    v = v.astype(np.float32).astype(np.float64)
    tm = trimesh.Trimesh(v, f, process=False)
    tm.merge_vertices(digits_vertex=4)
    tm.update_faces(tm.nondegenerate_faces(height=1e-6))
    tm.remove_unreferenced_vertices()
    if tm.volume < 0:
        tm.invert()
    return tm


def body_count(tm):
    """Connected pieces, via union-find over face edges (no scipy needed)."""
    parent = np.arange(len(tm.vertices))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in tm.edges_unique:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(i) for i in np.unique(tm.faces)})


def wall_thickness(tm, samples=4000, seed=0):
    """Local wall thickness at area-weighted random surface points: the distance a ray
    travels through the material from each point along the inward normal.
    Returns (points, face_index, thickness_mm). About 1-2 s on a 60k-triangle mesh."""
    pts, fi = sample.sample_surface(tm, samples, seed=seed)
    th = proximity.thickness(tm, pts, exterior=False, normals=tm.face_normals[fi], method="ray")
    return pts, fi, np.asarray(th)


def _grow_faces(tm, mask):
    """One ring of adjacent faces, so flagged spots are visible in the preview."""
    out = mask.copy()
    adj = tm.face_adjacency
    hit = mask[adj[:, 0]] | mask[adj[:, 1]]
    out[adj[hit].ravel()] = True
    return out


@dataclass
class Report:
    size: np.ndarray
    volume_cm3: float
    triangles: int
    watertight: bool
    bodies: int
    base_area_mm2: float
    overhang_area_mm2: float
    wall_thin_mm: float = 0.0        # ~1st percentile of sampled thickness
    wall_median_mm: float = 0.0
    thin_fraction: float = 0.0       # share of surface samples under MIN_WALL
    thin_points: list = field(default_factory=list)
    stl_bytes: int = 0
    warnings: list = field(default_factory=list)
    overhang_faces: np.ndarray = field(default=None, repr=False)
    thin_faces: np.ndarray = field(default=None, repr=False)

    @property
    def ok(self):
        return self.watertight and self.bodies >= 1

    def lines(self):
        x, y, z = self.size
        out = [
            f"size     {x:.1f} x {y:.1f} x {z:.1f} mm  ({x/25.4:.2f} x {y/25.4:.2f} x {z/25.4:.2f} in)",
            f"volume   {self.volume_cm3:.1f} cm3  (~{self.volume_cm3 * PLA_DENSITY:.0f} g PLA if solid)",
            f"mesh     {self.triangles} triangles, {'watertight' if self.watertight else 'NOT watertight'}, "
            f"{self.bodies} bod{'y' if self.bodies == 1 else 'ies'}",
            f"base     {self.base_area_mm2:.0f} mm2 flat on the bed",
            f"overhang {self.overhang_area_mm2:.0f} mm2 steeper than {OVERHANG_DEG} deg",
        ]
        if self.wall_median_mm:
            out.append(f"wall     thinnest ~{self.wall_thin_mm:.1f} mm, median {self.wall_median_mm:.1f} mm, "
                       f"{100 * self.thin_fraction:.1f}% of surface under {MIN_WALL} mm")
        if self.stl_bytes:
            out.append(f"stl      {self.stl_bytes / 1e6:.1f} MB")
        return out + [f"WARNING  {w}" for w in self.warnings]


def check(tm, bed=(256, 256, 256), thickness_samples=4000, bed_name=None):
    lo, hi = tm.bounds
    size = hi - lo
    n = tm.face_normals
    area = tm.area_faces
    zmin_face = tm.triangles[:, :, 2].max(axis=1) <= lo[2] + 1e-3
    down = n[:, 2] < -np.cos(np.radians(90 - OVERHANG_DEG))
    overhang = down & ~zmin_face
    rep = Report(
        size=size,
        volume_cm3=abs(tm.volume) / 1000,
        triangles=len(tm.faces),
        watertight=bool(tm.is_watertight and tm.is_winding_consistent),
        bodies=body_count(tm),
        base_area_mm2=float(area[zmin_face & (n[:, 2] < -0.999)].sum()),
        overhang_area_mm2=float(area[overhang].sum()),
        overhang_faces=overhang,
    )
    if thickness_samples and rep.watertight:
        pts, fi, th = wall_thickness(tm, thickness_samples)
        # a sample sitting right on a convex edge exits through the neighbouring
        # face almost immediately; those sub-0.15 mm readings are noise, not walls
        keep = th >= 0.15
        pts, fi, th = pts[keep], fi[keep], th[keep]
        thin = th < MIN_WALL
        rep.wall_thin_mm = float(np.percentile(th, 1))
        rep.wall_median_mm = float(np.median(th))
        rep.thin_fraction = float(thin.mean())
        mask = np.zeros(len(tm.faces), bool)
        mask[fi[thin]] = True
        rep.thin_faces = _grow_faces(tm, mask)
        if thin.any():
            # group thin samples into spots 8 mm across, biggest first, so the model
            # knows where to look and how thin that region typically is
            tp, tt = pts[thin], th[thin]
            left = np.ones(len(tp), bool)
            spots = []
            while left.any():
                seed = np.flatnonzero(left)[0]
                near = left & (np.linalg.norm(tp - tp[seed], axis=1) < 8)
                spots.append((near.sum(), tp[near].mean(axis=0), np.median(tt[near])))
                left &= ~near
            spots.sort(key=lambda s: -s[0])
            rep.thin_points = [(tuple(np.round(q, 1)), round(float(t), 1)) for _, q, t in spots[:3]]
    if not rep.watertight:
        rep.warnings.append("mesh has holes or flipped faces; slicers may misprint it")
    if rep.bodies > 1:
        rep.warnings.append(f"{rep.bodies} separate pieces; intended?")
    if rep.base_area_mm2 < 1:
        rep.warnings.append("nothing sits flat at the lowest Z; rotate it or add a base")
    if rep.overhang_area_mm2 > 1:
        rep.warnings.append("overhangs present; needs supports or a different print orientation")
    if rep.thin_fraction > 0.003:
        where = ", ".join(f"({x}, {y}, {z}) {t} mm" for (x, y, z), t in rep.thin_points)
        rep.warnings.append(f"walls under {MIN_WALL} mm (yellow in preview) near {where}")
    if any(s > b for s, b in zip(sorted(size), sorted(bed))):
        rep.warnings.append(f"larger than the {bed_name + ' ' if bed_name else ''}bed "
                            f"({bed[0]:g} x {bed[1]:g} x {bed[2]:g} mm)")
    return rep
