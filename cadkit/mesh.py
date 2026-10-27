"""Turn whatever a model returns into one clean, checked triangle mesh."""
from dataclasses import dataclass, field

import numpy as np
import trimesh
from manifold3d import Manifold
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
        obj = drop_crumbs(obj)
        # booleans can leave microscopic slivers that collapse when rounded to STL's
        # float32; simplify first, then weld. Big meshes (lattices) get one pass.
        big = obj.num_tri() > 400_000
        best = None
        for k, tol in enumerate((0.05,) if big else (0.01, 0.02, 0.005, 0.03)):
            m = obj.simplify(tol).to_mesh()
            v, f = np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts)
            # manifold3d may leave the solid touching itself at a vertex (two indices,
            # one position). Slicers weld by position and then see a non-manifold
            # pinch ("reversed faces" in Bambu Studio), so pull such vertices apart.
            v, pinched = unpinch(v, f)
            if pinched and k == 0:
                print(f"  note: separated {pinched} self-touching vertices by {UNPINCH_MM} mm")
            # thin geometry can lose watertightness to vertex welding; the un-welded
            # mesh (float32-rounded only) is often sound, and cheaper to test first
            raw = trimesh.Trimesh(v.astype(np.float32).astype(np.float64), f, process=False)
            if sound_as_sliced(raw):
                return raw
            tm = clean(v, f)
            if sound_as_sliced(tm):
                return tm
            best = best or tm
        return best
    elif hasattr(obj, "tessellate"):
        verts, tris = obj.tessellate(tolerance, angular_tolerance)
        v = np.array([(p.X, p.Y, p.Z) for p in verts])
        f = np.array(tris, dtype=np.int64)
    else:
        raise TypeError(f"build() returned {type(obj).__name__}; expected a build123d "
                        "Part/Solid, manifold3d.Manifold or trimesh.Trimesh")
    return clean(np.asarray(v, float), np.asarray(f))


def drop_crumbs(manifold, min_volume_mm3=1.0):
    """Remove disconnected fragments smaller than a grain of filament (lattice
    meshing and tight booleans leave them); says so when it does."""
    parts = manifold.decompose()
    if len(parts) <= 1:
        return manifold
    crumbs = [p for p in parts if 0 < p.volume() < min_volume_mm3]   # voids have negative volume
    if not crumbs:
        return manifold
    print(f"  note: dropped {len(crumbs)} floating crumbs under {min_volume_mm3} mm3")
    # subtract rather than recompose: recomposing loses enclosed voids
    return manifold - Manifold.compose(crumbs)


UNPINCH_MM = 0.004   # how far self-touching vertices are pulled apart (invisible on a print)


def unpinch(v, f, step=UNPINCH_MM):
    """Separate vertices that share a float32 position but not an index: a solid that
    touches itself at a point or edge. Each extra vertex moves `step` toward the mean
    of its own incident face centres, i.e. into its own surface, so the two sheets
    no longer coincide and position-welding (what every slicer does) stays manifold.
    Returns (vertices, number moved)."""
    v = np.array(v, float)
    moved = 0
    for attempt in range(3):
        key = v.astype(np.float32)
        _, first, inv, cnt = np.unique(key, axis=0, return_index=True,
                                       return_inverse=True, return_counts=True)
        inv = inv.ravel()
        extra = np.where(cnt[inv] > 1)[0]
        extra = extra[extra != first[inv[extra]]]      # keep one vertex of each group in place
        if len(extra) == 0:
            break
        centres = v[f].mean(axis=1)
        for vi in extra:
            fi = np.where((f == vi).any(axis=1))[0]
            d = centres[fi].mean(axis=0) - v[vi] if len(fi) else np.zeros(3)
            n = np.linalg.norm(d)
            if n < 1e-12:
                d = np.array([1.0, 0, 0]) * (attempt + 1)
                n = np.linalg.norm(d)
            v[vi] += d / n * step * (attempt + 1)
        moved += len(extra)
    return v, moved


def sound_as_sliced(tm):
    """Watertight and consistently wound after welding vertices by position, which is
    how slicers read an STL (an index-level check alone misses self-touching solids)."""
    if not (tm.is_watertight and tm.is_winding_consistent):
        return False
    if len(tm.vertices) == len(np.unique(tm.vertices.astype(np.float32), axis=0)):
        return True
    w = tm.copy()
    w.merge_vertices()
    return bool(w.is_watertight and w.is_winding_consistent)


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
    """(bodies, voids): connected surface shells with positive volume are separate
    pieces; negative-volume shells are enclosed cavities (lattice infill, sealed
    pockets), which slicers handle as part of the solid."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = len(tm.vertices)
    e = tm.edges_unique
    graph = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    _, labels = connected_components(graph, directed=False)
    comp = labels[tm.faces[:, 0]]
    # signed volume per component from the divergence theorem (tetrahedra to origin)
    t = tm.triangles
    signed = np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])) / 6
    bodies = voids = 0
    void_faces = np.zeros(len(tm.faces), bool)
    for c in np.unique(comp):
        sel = comp == c
        if signed[sel].sum() > 0:
            bodies += 1
        else:
            voids += 1
            void_faces |= sel
    return bodies, voids, void_faces


def wall_thickness(tm, samples=4000, seed=0, face_weight=None):
    """Local wall thickness at area-weighted random surface points: the distance a ray
    travels through the material from each point along the inward normal, until it
    leaves through a face roughly parallel to the entry face. Samples whose ray exits
    through a steeply angled face (the feather edge of a countersink, chamfer or
    fillet, a wedge) are dropped: that is an edge, not a wall.
    Returns (points, face_index, thickness_mm). `face_weight` (per-face, 0 to skip)
    restricts where samples land; rays still see the whole mesh, so skin over a
    lattice measures as the skin."""
    pts, fi = sample.sample_surface(tm, samples, face_weight=face_weight, seed=seed)
    n = tm.face_normals[fi]
    origins = pts - n * 1e-3
    loc, ray_id, hit_face = tm.ray.intersects_location(origins, -n, multiple_hits=True)
    th = np.full(len(pts), np.nan)
    if len(loc):
        dist = np.linalg.norm(loc - origins[ray_id], axis=1)
        order = np.lexsort((dist, ray_id))             # per ray, first exit hit first
        ray_sorted, dist_sorted, face_sorted = ray_id[order], dist[order], hit_face[order]
        first = np.r_[True, ray_sorted[1:] != ray_sorted[:-1]]
        rays, d, f = ray_sorted[first], dist_sorted[first], face_sorted[first]
        parallel = np.einsum("ij,ij->i", n[rays], tm.face_normals[f]) < -0.5
        th[rays[parallel]] = d[parallel]
    keep = ~np.isnan(th)
    return pts[keep], fi[keep], th[keep]


NARROW_OVERHANG_MM = 4.0   # strips narrower than this (lips, groove roofs, short bridges, ceilings of holes up to ~8 mm) print fine


def overhang_regions(tm, mask):
    """Split overhang faces into connected regions and estimate each one's width as
    2*area/perimeter (exact for a long strip). Returns a per-face width array."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    width = np.zeros(len(tm.faces))
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return width
    adj = tm.face_adjacency
    both = mask[adj[:, 0]] & mask[adj[:, 1]]
    remap = -np.ones(len(tm.faces), int)
    remap[idx] = np.arange(len(idx))
    e = remap[adj[both]]
    g = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(idx), len(idx)))
    _, lab = connected_components(g, directed=False)
    # region perimeter: adjacency edges with exactly one overhang face (plus open edges)
    one = mask[adj[:, 0]] ^ mask[adj[:, 1]]
    edge_len = np.linalg.norm(tm.vertices[tm.face_adjacency_edges[:, 0]] - tm.vertices[tm.face_adjacency_edges[:, 1]], axis=1)
    region_of_face = np.full(len(tm.faces), -1)
    region_of_face[idx] = lab
    per = np.zeros(lab.max() + 1)
    for k in np.flatnonzero(one):
        a, b = adj[k]
        r = region_of_face[a] if mask[a] else region_of_face[b]
        per[r] += edge_len[k]
    area = np.bincount(lab, weights=tm.area_faces[idx], minlength=len(per))
    w = np.where(per > 0, 2 * area / np.maximum(per, 1e-9), 1e9)
    width[idx] = w[lab]
    return width


def _grow_faces(tm, mask):
    """One ring of adjacent faces, so flagged spots are visible in the preview."""
    out = mask.copy()
    adj = tm.face_adjacency
    small = tm.area_faces < 4.0   # never spill onto a big flat facet next to fine detail
    hit = (mask[adj[:, 0]] | mask[adj[:, 1]]) & small[adj[:, 0]] & small[adj[:, 1]]
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
    voids: int = 0
    overhang_minor_mm2: float = 0.0   # narrow strips (lips, bridges) that print without support
    wall_thin_mm: float = 0.0        # ~1st percentile of sampled thickness
    wall_median_mm: float = 0.0
    thin_fraction: float = 0.0       # share of surface samples under MIN_WALL
    thin_points: list = field(default_factory=list)
    thin_samples: np.ndarray = field(default=None, repr=False)   # every thin sample, for the preview
    stl_bytes: int = 0
    warnings: list = field(default_factory=list)
    overhang_faces: np.ndarray = field(default=None, repr=False)
    thin_faces: np.ndarray = field(default=None, repr=False)
    void_faces: np.ndarray = field(default=None, repr=False)

    @property
    def ok(self):
        return self.watertight and self.bodies >= 1

    def lines(self):
        x, y, z = self.size
        out = [
            f"size     {x:.1f} x {y:.1f} x {z:.1f} mm  ({x/25.4:.2f} x {y/25.4:.2f} x {z/25.4:.2f} in)",
            f"volume   {self.volume_cm3:.1f} cm3  (~{self.volume_cm3 * PLA_DENSITY:.0f} g PLA if solid)",
            f"mesh     {self.triangles} triangles, {'watertight' if self.watertight else 'NOT watertight'}, "
            f"{self.bodies} bod{'y' if self.bodies == 1 else 'ies'}"
            + (f", {self.voids} enclosed void{'s' if self.voids > 1 else ''}" if self.voids else ""),
            f"base     {self.base_area_mm2:.0f} mm2 flat on the bed",
            f"overhang {self.overhang_area_mm2:.0f} mm2 steeper than {OVERHANG_DEG} deg"
            + (f" (plus {self.overhang_minor_mm2:.0f} mm2 of strips under {NARROW_OVERHANG_MM} mm wide, fine)"
               if self.overhang_minor_mm2 else ""),
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
    zmin_face = tm.triangles[:, :, 2].max(axis=1) <= lo[2] + 0.05   # level-set bottoms wobble ~0.01
    down = n[:, 2] < -np.cos(np.radians(90 - OVERHANG_DEG)) - 1e-3   # exactly 45 deg (countersinks) is fine
    bodies, voids, void_faces = body_count(tm)
    # faces of enclosed voids (lattice infill, sealed pockets) are not printed surfaces
    overhang_all = down & ~zmin_face & ~void_faces
    width = overhang_regions(tm, overhang_all)
    overhang = overhang_all & (width >= NARROW_OVERHANG_MM)
    rep = Report(
        size=size,
        volume_cm3=abs(tm.volume) / 1000,
        triangles=len(tm.faces),
        watertight=sound_as_sliced(tm),
        bodies=bodies,
        voids=voids,
        base_area_mm2=float(area[zmin_face & (n[:, 2] < -0.999)].sum()),
        overhang_area_mm2=float(area[overhang].sum()),
        overhang_minor_mm2=float(area[overhang_all & ~overhang].sum()),
        overhang_faces=overhang,
        void_faces=void_faces,
    )
    if thickness_samples and rep.watertight:
        weight = area * ~void_faces if voids else None
        pts, fi, th = wall_thickness(tm, thickness_samples, face_weight=weight)
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
        rep.thin_samples = pts[thin]
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
