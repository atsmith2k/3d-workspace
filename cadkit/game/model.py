"""Data model for game assets: Mesh, Material, Model.

Units are metres. Y is up, -Z is forward, right-handed, counter-clockwise front faces:
glTF's conventions and Cinder's. Texture arrays are HxWx3 (or HxW) floats in 0..1, row 0 at
the top, which is v=0 in glTF.
"""
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Mesh:
    v: np.ndarray                      # (N, 3) positions
    f: np.ndarray                      # (M, 3) triangle indices
    n: np.ndarray = None               # (N, 3) unit normals
    uv: np.ndarray = None              # (N, 2)

    def __post_init__(self):
        self.v = np.asarray(self.v, np.float64).reshape(-1, 3)
        self.f = np.asarray(self.f, np.int64).reshape(-1, 3)
        if self.uv is None:
            self.uv = np.zeros((len(self.v), 2))
        self.uv = np.asarray(self.uv, np.float64).reshape(-1, 2)
        if self.n is None:
            self.n = vertex_normals(self.v, self.f)
        self.n = np.asarray(self.n, np.float64).reshape(-1, 3)

    # ---- transforms (each returns a new Mesh) ----
    def moved(self, x=0.0, y=0.0, z=0.0):
        return Mesh(self.v + [x, y, z], self.f, self.n, self.uv)

    def scaled(self, sx, sy=None, sz=None):
        s = np.array([sx, sx if sy is None else sy, sx if sz is None else sz], float)
        n = self.n / s
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        f = self.f[:, ::-1] if np.prod(s) < 0 else self.f
        return Mesh(self.v * s, f, n, self.uv)

    def rotated(self, deg, axis="y"):
        a = np.radians(deg)
        c, s = np.cos(a), np.sin(a)
        r = dict(x=[[1, 0, 0], [0, c, -s], [0, s, c]],
                 y=[[c, 0, s], [0, 1, 0], [-s, 0, c]],
                 z=[[c, -s, 0], [s, c, 0], [0, 0, 1]])[axis]
        r = np.array(r)
        return Mesh(self.v @ r.T, self.f, self.n @ r.T, self.uv)

    def with_uv(self, uv):
        return Mesh(self.v, self.f, self.n, uv)

    def __add__(self, other):
        return merge(self, other)

    @property
    def bounds(self):
        return self.v.min(0), self.v.max(0)

    @property
    def triangles(self):
        return len(self.f)


def vertex_normals(v, f):
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    n = np.zeros_like(v)
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def merge(*meshes):
    meshes = [m for m in meshes if m is not None and len(m.f)]
    off, vs, fs, ns, uvs = 0, [], [], [], []
    for m in meshes:
        vs.append(m.v); ns.append(m.n); uvs.append(m.uv); fs.append(m.f + off)
        off += len(m.v)
    return Mesh(np.vstack(vs), np.vstack(fs), np.vstack(ns), np.vstack(uvs))


@dataclass
class Material:
    """glTF metallic-roughness, the part of it Cinder reads.

    `orm` is one image with occlusion in R, roughness in G, metallic in B; it fills both the
    occlusion and the metallic-roughness slot. With textures the factors multiply them, so
    leave metallic and roughness at 1.0 when `orm` is given.
    """
    name: str = "material"
    color: tuple = (0.8, 0.8, 0.8, 1.0)          # linear RGBA factor
    metallic: float = 0.0
    roughness: float = 0.6
    emissive: tuple = (0.0, 0.0, 0.0)
    emissive_strength: float = 1.0
    base: np.ndarray = None                      # sRGB base colour image
    orm: np.ndarray = None                       # linear
    normal: np.ndarray = None                    # linear, +Y (glTF)
    emission: np.ndarray = None                  # sRGB
    alpha: str = "opaque"                        # opaque | mask | blend
    alpha_cutoff: float = 0.5
    double_sided: bool = False
    flat_uv: bool = False                        # UVs collapse onto palette swatches on purpose

    def textures(self):
        return {k: getattr(self, k) for k in ("base", "orm", "normal", "emission")
                if getattr(self, k) is not None}


@dataclass
class Model:
    """A static model: one or more (Mesh, Material) parts. Parts that share a Material object
    are merged into one primitive when written.

    A part may name a node: Model((base, steel), (spikes, steel, "spikes")). Parts of one node
    become one mesh node of the glTF, so a game that spawns the file gets a separate entity it
    can move, hide or recolour (a flag on its pole, spikes in their base). Unnamed parts form
    the node named after the asset."""
    parts: list = field(default_factory=list)

    def __init__(self, *parts):
        self.parts = []
        self.nodes = []                           # node name per part, None = the asset's own node
        for p in parts:
            self.add(*p)

    def add(self, mesh, material, node=None):
        for i, (m, mat) in enumerate(self.parts):
            if mat is material and self.nodes[i] == node:
                self.parts[i] = (merge(m, mesh), mat)
                return self
        self.parts.append((mesh, material))
        self.nodes.append(node)
        return self

    @property
    def node_names(self):
        """Distinct node names in first-use order (None first when any part is unnamed)."""
        out = []
        for n in self.nodes:
            if n not in out:
                out.append(n)
        return sorted(out, key=lambda n: n is not None)

    @property
    def bounds(self):
        lo = np.min([m.bounds[0] for m, _ in self.parts], axis=0)
        hi = np.max([m.bounds[1] for m, _ in self.parts], axis=0)
        return lo, hi

    @property
    def triangles(self):
        return sum(m.triangles for m, _ in self.parts)

    @property
    def vertices(self):
        return sum(len(m.v) for m, _ in self.parts)

    @property
    def materials(self):
        return [mat for _, mat in self.parts]
