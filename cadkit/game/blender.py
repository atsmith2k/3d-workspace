"""Blender in the loop, headless: the kernel for high-resolution, complex assets.

The game-asset kernels draw hard-surface and low-poly shapes well. What they cannot do is the
high-to-low workflow that detailed assets are made with: build a shape of hundreds of
thousands of triangles (subdivide, displace, carve with booleans, fuse parts), derive a
light mesh from it, unwrap that, and bake the detail into normal, occlusion and mask maps.
Blender does all of it; this module drives it as a subprocess and brings the result back as
an ordinary `Mesh` and images, so the asset is still a script, the build is still repeatable
and the same checks and the same engine ladder decide whether it is ready.

    from cadkit.game import blender as B
    s = B.Session()
    hi = s.add(rough_mesh, "high")
    s.modify(hi, B.subsurf(5), B.displace("CLOUDS", scale=0.6, strength=0.12))
    lo = s.copy(hi, "low")
    s.decimate(lo, 3000); s.shade(lo, sharp_angle=40); s.unwrap(lo)
    s.bake([hi], lo, size=2048, maps=("normal", "ao", "curvature"))
    r = s.run()
    mesh, normal, ao = r.mesh(lo), r.image("normal"), r.image("ao")

Why a subprocess and not `import bpy`: the bpy wheel is pinned to one Python (3.13 for
Blender 5.x; this workspace runs 3.12), a crash in Blender cannot take the build down, and
nothing GPL is imported into cadkit. Why not an agent driving a live Blender session (the MCP
servers): the asset would live in a session nobody can rebuild.

Results are cached under output/game/.blender/ by a hash of the steps, the input meshes, the
bridge script and the Blender version: an unchanged asset does not start Blender again.
Blender is found at CAD_BLENDER, else the newest under Program Files, else on PATH.
"""
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
from PIL import Image

from .model import Mesh

ROOT = Path(__file__).resolve().parent.parent.parent
BRIDGE = ROOT / "tools" / "blender_bridge" / "bridge.py"
CACHE = ROOT / "output" / "game" / ".blender"
_version = {}


class BlenderMissing(SystemExit):
    pass


def find():
    """Path of the Blender executable, or None."""
    env = os.environ.get("CAD_BLENDER")
    if env and Path(env).exists():
        return Path(env)
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramW6432")):
        if base:
            hits = sorted(Path(base).glob("Blender Foundation/Blender */blender.exe"),
                          key=lambda p: [int(x) if x.isdigit() else 0 for x in p.parent.name.split()[-1].split(".")])
            if hits:
                return hits[-1]
    which = shutil.which("blender")
    return Path(which) if which else None


def version(exe=None):
    """Blender's version string ("5.3.0"), or None when there is no Blender."""
    exe = exe or find()
    if exe is None:
        return None
    if exe not in _version:
        try:
            out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60).stdout
            _version[exe] = out.split()[1] if out.startswith("Blender") else out.strip().splitlines()[0]
        except (OSError, subprocess.SubprocessError, IndexError):
            _version[exe] = "unknown"
    return _version[exe]


def info():
    exe = find()
    return dict(blender=str(exe) if exe else None, version=version(exe),
                hint=None if exe else "install Blender 5.x (winget install BlenderFoundation.Blender) or set CAD_BLENDER")


# ---------------------------------------------------------------- modifier specs (Blender's own names)

def subsurf(levels=2, simple=False):
    """Subdivide: each level quadruples the faces. simple=True keeps the shape (no smoothing)."""
    return dict(type="SUBSURF", levels=levels, render_levels=levels,
                subdivision_type="SIMPLE" if simple else "CATMULL_CLARK")


def displace(texture="CLOUDS", scale=0.25, strength=0.05, mid_level=0.5, **texture_props):
    """Push the surface along its normals by a procedural texture: CLOUDS (soft lumps), VORONOI
    (cells, cracks), MUSGRAVE, STUCCI (grain), WOOD, MARBLE. scale is the feature size in metres."""
    return dict(type="DISPLACE", strength=strength, mid_level=mid_level, texture_coords="GLOBAL",
                texture=dict(type=texture, noise_scale=scale, **texture_props))


def inflate(distance):
    """Move the whole surface along its normals by a distance in metres (negative: an inset
    copy, which is how a cut is given an exact depth: trim the cutter against it)."""
    return dict(type="DISPLACE", strength=float(distance), mid_level=0.0)


def bevel(width=0.01, segments=2, angle=30.0):
    """Round every edge sharper than `angle` degrees."""
    return dict(type="BEVEL", width=width, segments=segments, limit_method="ANGLE", angle_limit=float(np.radians(angle)))


def smooth(factor=0.5, iterations=2):
    return dict(type="SMOOTH", factor=factor, iterations=iterations)


def solidify(thickness=0.02):
    return dict(type="SOLIDIFY", thickness=thickness)


# ---------------------------------------------------------------- a job

class Result:
    def __init__(self, folder, info, cached):
        self.folder, self.info, self.cached = Path(folder), info, cached

    def mesh(self, name):
        d = np.load(self.folder / f"out_{name}.npz")
        return Mesh(d["v"], d["f"], d["n"], d["uv"])

    def skin(self, name):
        """(joints Nx4, weights Nx4) of a mesh that went through `weights`."""
        d = np.load(self.folder / f"out_{name}.npz")
        return d["joints"].astype(np.int64), d["weights"]

    def image(self, kind, prefix="bake"):
        """A baked map as floats in 0..1, row 0 at the top (v=0): RGB for normal, grey otherwise."""
        with Image.open(self.folder / f"{prefix}_{kind}.png") as im:
            a = np.asarray(im.convert("RGB"), float) / 255
        return a if kind == "normal" else a.mean(2)

    @property
    def seconds(self):
        return self.info.get("seconds", 0.0)

    def step(self, op, index=0):
        """The bridge's report for the index-th step of a kind (triangles before and after, times)."""
        return [s for s in self.info["steps"] if s["op"] == op][index]


class Session:
    """Steps for one Blender run. Methods queue work and return the object's name; `run()`
    starts Blender once (or reads the cache) and returns a Result."""

    def __init__(self):
        self.steps, self.inputs, self.outputs = [], {}, []

    def add(self, mesh, name, weld=True, emit=0.0):
        """Send a Mesh. weld joins vertices at the same position (a hard-edged game mesh must be
        one surface before it is subdivided). emit > 0 gives it an emissive material, so the
        faces it leaves behind in a boolean can be baked as a mask with the "emit" map."""
        self.inputs[name] = mesh
        self.steps.append(dict(op="load", file=f"in_{name}.npz", name=name, weld=weld, emit=emit))
        return name

    def modify(self, target, *stack):
        self.steps.append(dict(op="modify", target=target, stack=list(stack)))
        return target

    def boolean(self, target, other, operation="DIFFERENCE", materials="TRANSFER"):
        """Cut `other` out of `target` (or "UNION", "INTERSECT"). materials="TRANSFER": the cut
        faces keep the cutter's material (bake them as a mask with an emissive cutter);
        "INDEX": they take the target's."""
        self.steps.append(dict(op="boolean", target=target, other=other, operation=operation.upper(),
                               materials=materials.upper()))
        return target

    def join(self, target, *others):
        self.steps.append(dict(op="join", target=target, others=list(others)))
        return target

    def copy(self, source, name):
        self.steps.append(dict(op="copy", source=source, name=name))
        return name

    def remesh(self, target, voxel_size):
        self.steps.append(dict(op="remesh", target=target, voxel_size=voxel_size))
        return target

    def decimate(self, target, tris):
        self.steps.append(dict(op="decimate", target=target, tris=int(tris)))
        return target

    def shade(self, target, smooth=True, sharp_angle=None):
        self.steps.append(dict(op="shade", target=target, smooth=smooth, sharp_angle=sharp_angle))
        return target

    def unwrap(self, target, angle=66.0, margin=0.01):
        self.steps.append(dict(op="triangulate", target=target))
        self.steps.append(dict(op="unwrap", target=target, angle=angle, margin=margin))
        return target

    def bake(self, high, low, size=1024, maps=("normal", "ao"), cage=0.02, ray=0.1, samples=32, margin=8):
        """Bake `high` (a name or a list) onto the unwrapped `low`. cage and ray are metres: how
        far outside the low mesh rays start and how far they may travel to find the high one.
        Too small and the bake has holes; too large and it picks up the wrong surface."""
        high = [high] if isinstance(high, str) else list(high)
        self.steps.append(dict(op="bake", high=high, low=low, size=int(size), maps=list(maps), cage=cage,
                               ray=ray, samples=samples, margin=margin))
        self.get(low)
        return low

    def weights(self, target, skeleton, skip=("root",)):
        """Automatic (bone heat) skin weights for a cadkit.game.rig.Skeleton. Bones named in
        `skip` take no weight: a root at the feet would otherwise claim the soles."""
        bones = [dict(name=b.name, parent=skeleton.bones[b.parent].name if b.parent >= 0 else None,
                      head=[float(x) for x in b.head], tail=[float(x) for x in skeleton.tail(i)],
                      deform=b.name not in skip)
                 for i, b in enumerate(skeleton.bones)]
        self.steps.append(dict(op="weights", target=target, bones=bones))
        self.get(target)
        return target

    def get(self, target):
        """Ask for an object's mesh back."""
        if target not in self.outputs:
            self.outputs.append(target)
        return target

    # ---- running

    def _key(self, steps, exe):
        h = hashlib.sha256()
        h.update(json.dumps(steps, sort_keys=True).encode())
        for name in sorted(self.inputs):
            m = self.inputs[name]
            h.update(name.encode() + np.ascontiguousarray(m.v, np.float32).tobytes()
                     + np.ascontiguousarray(m.f, np.int32).tobytes() + np.ascontiguousarray(m.uv, np.float32).tobytes())
        h.update(BRIDGE.read_bytes())
        h.update(str(version(exe)).encode())
        return h.hexdigest()[:20]

    def run(self, timeout=1800, cache=True):
        exe = find()
        if exe is None:
            raise BlenderMissing("this asset needs Blender: " + info()["hint"])
        steps = self.steps + [dict(op="save", target=t, file=f"out_{t}.npz") for t in self.outputs]
        folder = CACHE / self._key(steps, exe)
        done = folder / "result.json"
        if cache and done.exists():
            res = json.loads(done.read_text(encoding="utf-8"))
            if res.get("ok"):
                return Result(folder, res, cached=True)
        shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True)
        for name, m in self.inputs.items():
            np.savez(folder / f"in_{name}.npz", v=m.v, f=m.f, uv=m.uv)
        (folder / "job.json").write_text(json.dumps(dict(steps=steps), indent=1), encoding="utf-8")
        t0 = time.time()
        try:
            r = subprocess.run([str(exe), "-b", "--factory-startup", "--python-exit-code", "3",
                                "--python", str(BRIDGE), "--", str(folder)],
                               capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            raise SystemExit(f"Blender did not finish in {timeout} s")
        if not done.exists():
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-12:])
            raise SystemExit(f"Blender ended without a result (exit {r.returncode}):\n{tail}")
        res = json.loads(done.read_text(encoding="utf-8"))
        res["wall_seconds"] = round(time.time() - t0, 1)
        done.write_text(json.dumps(res, indent=1), encoding="utf-8")
        if not res.get("ok"):
            raise SystemExit("Blender step failed: " + res.get("error", "?") + "\n" + res.get("trace", ""))
        return Result(folder, res, cached=False)


# ---------------------------------------------------------------- the common workflow in one call

def bake_lowpoly(high, tris, size=2048, maps=("normal", "ao", "curvature"), sharp_angle=45.0, cage=None, ray=None,
                 samples=48, unwrap_angle=66.0, prepare=None):
    """High-poly in, game mesh and maps out.

    `high` is a Mesh already built (in Blender or not). The low mesh is the high one decimated
    to `tris` triangles, smooth-shaded with edges over `sharp_angle` kept hard, unwrapped, and
    baked. `prepare(session, name)` may add steps to the high mesh first. cage and ray default
    to 2 % and 8 % of the mesh's size. Returns (low Mesh with UVs, {map: image}, Result).
    """
    lo_, hi_ = high.bounds
    extent = float(np.linalg.norm(hi_ - lo_))
    s = Session()
    h = s.add(high, "high", weld=True)
    if prepare:
        prepare(s, h)
    low = s.copy(h, "low")
    s.decimate(low, tris)
    s.shade(low, sharp_angle=sharp_angle)
    s.unwrap(low, angle=unwrap_angle)
    s.bake([h], low, size=size, maps=maps, cage=cage or 0.02 * extent, ray=ray or 0.08 * extent, samples=samples)
    r = s.run()
    return r.mesh(low), {k: r.image(k) for k in maps}, r
