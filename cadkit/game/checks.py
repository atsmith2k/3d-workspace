"""Checks for game assets. A model's `checks(p)` returns a list of these; the build fails
`ready` when one fails. `static_checks` are the ones every model gets without asking.

    def checks(p):
        return [size(x=1.0, y=1.0, z=1.0), tris(max=600), pivot("centre"), materials(1)]
"""
import re
from dataclasses import dataclass

import numpy as np

from .gltf import SUPPORTED_ATTRIBUTES, SUPPORTED_EXTENSIONS

MAX_TEXTURE = 8192                    # Cinder's MAX_COOKED_TEXTURE_SIZE


@dataclass
class Check:
    name: str
    fn: object

    def run(self, ctx):
        try:
            ok, detail = self.fn(ctx)
        except Exception as e:                      # a check that cannot run has failed
            ok, detail = False, f"{type(e).__name__}: {e}"
        return dict(name=self.name, ok=bool(ok), detail=detail)


def _span(spec, tol):
    return (spec[0], spec[1]) if isinstance(spec, (tuple, list)) else (spec - tol, spec + tol)


def size(x=None, y=None, z=None, tol=0.01):
    """Overall size in metres. A number is +-tol, a tuple is a range."""
    def fn(ctx):
        lo, hi = ctx.model.bounds
        got, bad = hi - lo, []
        for i, spec in enumerate((x, y, z)):
            if spec is not None:
                a, b = _span(spec, tol)
                if not a <= got[i] <= b:
                    bad.append(f"{'xyz'[i]} {got[i]:.3f} not in {a:.3f}..{b:.3f}")
        return not bad, "; ".join(bad) or f"{got[0]:.3f} x {got[1]:.3f} x {got[2]:.3f} m"
    return Check("size", fn)


def tris(max, min=0):
    def fn(ctx):
        n = ctx.model.triangles
        return min <= n <= max, f"{n} triangles (budget {min}..{max})"
    return Check("tris", fn)


def materials(max):
    def fn(ctx):
        n = len(ctx.model.parts)
        return n <= max, f"{n} material(s), one draw call each (budget {max})"
    return Check("materials", fn)


def texture_size(max=1024):
    """No texture larger than `max` a side."""
    def fn(ctx):
        sizes = [t.shape[:2] for m in ctx.model.materials for t in m.textures().values()]
        big = [s for s in sizes if s[0] > max or s[1] > max]
        return not big, f"{len(sizes)} texture(s), largest {np.max(sizes) if sizes else 0} px (budget {max})"
    return Check("texture_size", fn)


ANCHORS = dict(centre=(0.5, 0.5, 0.5), base=(0.5, 0.0, 0.5), top=(0.5, 1.0, 0.5), back=(0.5, 0.5, 1.0))


def pivot(kind="centre", tol=0.005):
    """Where the origin is in the bounds. "centre": dynamic props (the world kit centres box
    and sphere colliders on the entity). "base": static pieces and characters, standing on
    Y=0. "top": floor tiles, so their walking surface is Y=0. "back": wall-mounted pieces,
    which hang off the wall toward -Z. Or a tuple of fractions (fx, fy, fz) of the bounds;
    None in a tuple leaves that axis free."""
    anchor = ANCHORS[kind] if isinstance(kind, str) else kind
    label = kind if isinstance(kind, str) else f"anchor {kind}"

    def fn(ctx):
        lo, hi = ctx.model.bounds
        off = np.array([0.0 if a is None else abs(lo[i] + a * (hi[i] - lo[i])) for i, a in enumerate(anchor)])
        ok = bool((off <= tol).all())
        return ok, (f"origin is at the {label} of the bounds" if ok
                    else f"origin is {off[0]:.3f}, {off[1]:.3f}, {off[2]:.3f} m from the {label}")
    return Check(f"pivot {label}", fn)


def tiles(image_of, max_error=1.2, name="tiles"):
    """A texture repeats without a seam. image_of(model) returns the image."""
    from .texture import seam_error

    def fn(ctx):
        e = seam_error(image_of(ctx.model))
        return e <= max_error, f"seam error {e:.2f} (up to 1.0 the wrap is no worse than the image's own detail; limit {max_error})"
    return Check(name, fn)


def uv_unique(max_overlap=0.01, part=0):
    """Every face owns its place in the texture (no overlapping UVs): what a baked map needs."""
    from .texture import uv_overlap

    def fn(ctx):
        m = ctx.model.parts[part][0]
        lo, hi = m.uv.min(0), m.uv.max(0)
        if lo.min() < -1e-4 or hi.max() > 1 + 1e-4:
            return False, f"UVs run outside 0..1 ({lo.round(3)} .. {hi.round(3)})"
        o = uv_overlap(m, 1024)
        return o <= max_overlap, f"{o:.1%} of the used texels are claimed by more than one face (limit {max_overlap:.0%})"
    return Check("uv unique", fn)


def custom(name, fn):
    """fn(ctx) -> (ok, detail). ctx has .model, .summary (the GLB read back), .params, .name."""
    return Check(name, fn)


# ---------------------------------------------------------------- always run

def _name_ok(ctx):
    ok = bool(re.fullmatch(r"[a-z][a-z0-9_]*", ctx.name))
    return ok, (f"'{ctx.name}' is a unique-able, space-free cook prefix" if ok else
                f"'{ctx.name}': use snake_case (cinder-cook derives the prefix from the base name)")


def _readback(ctx):
    s, m = ctx.summary, ctx.model
    lo, hi = m.bounds
    bad = []
    if s["triangles"] != m.triangles:
        bad.append(f"triangles {s['triangles']} != {m.triangles}")
    if s["vertices"] != m.vertices:
        bad.append(f"vertices {s['vertices']} != {m.vertices}")
    if not (np.allclose(s["bounds"][0], lo, atol=1e-4) and np.allclose(s["bounds"][1], hi, atol=1e-4)):
        bad.append("bounds differ")
    if s["materials"] != len(m.parts):
        bad.append(f"materials {s['materials']} != {len(m.parts)}")
    return not bad, "; ".join(bad) or "GLB reads back as built (pygltflib)"


def _features(ctx):
    s = ctx.summary
    bad = []
    if s["modes"] != [4]:
        bad.append(f"primitive modes {s['modes']} (Cinder keeps triangles only)")
    extra = set(s["attributes"]) - SUPPORTED_ATTRIBUTES
    if extra:
        bad.append(f"attributes Cinder ignores: {sorted(extra)}")
    ext = set(s["extensions"]) - SUPPORTED_EXTENSIONS
    if ext:
        bad.append(f"extensions Cinder does not read: {sorted(ext)}")
    return not bad, "; ".join(bad) or "only features Cinder reads"


def _geometry(ctx):
    bad = []
    for i, (m, _) in enumerate(ctx.model.parts):
        if not (np.isfinite(m.v).all() and np.isfinite(m.uv).all() and np.isfinite(m.n).all()):
            bad.append(f"part {i}: non-finite values")
            continue
        a, b, c = (m.v[m.f[:, k]] for k in range(3))
        fn = np.cross(b - a, c - a)
        area = np.linalg.norm(fn, axis=1) / 2
        if (area < 1e-10).any():
            bad.append(f"part {i}: {int((area < 1e-10).sum())} degenerate triangles")
        if np.abs(np.linalg.norm(m.n, axis=1) - 1).max() > 0.01:
            bad.append(f"part {i}: normals are not unit length")
        back = ((fn * m.n[m.f].sum(1)).sum(1) < 0).sum()
        if back:
            bad.append(f"part {i}: {int(back)} triangles wind against their normals (culled)")
    return not bad, "; ".join(bad) or "finite, no degenerate triangles, unit normals, winding matches"


def _uvs(ctx):
    bad = []
    for i, (m, mat) in enumerate(ctx.model.parts):
        if not mat.textures() or mat.flat_uv:
            continue
        ua, ub, uc = (m.uv[m.f[:, k]] for k in range(3))
        d1, d2 = ub - ua, uc - ua
        if (np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) < 1e-12).mean() > 0.02:
            bad.append(f"part {i} ({mat.name}): textured but over 2% of its triangles have no UV area")
    return not bad, "; ".join(bad) or "every textured triangle has UV area"


def _textures(ctx):
    bad, n = [], 0
    for mat in ctx.model.materials:
        for slot, img in mat.textures().items():
            n += 1
            h, w = img.shape[:2]
            if max(h, w) > MAX_TEXTURE:
                bad.append(f"{mat.name}.{slot} is {w}x{h}: over Cinder's {MAX_TEXTURE} px")
            if (h & (h - 1)) or (w & (w - 1)):
                bad.append(f"{mat.name}.{slot} is {w}x{h}: not a power of two (mips, tiling)")
            a = np.asarray(img, float)
            if slot == "base":
                lum = a[..., :3].mean()
                if not 0.04 <= lum <= 0.94:
                    bad.append(f"{mat.name}.base mean {lum:.2f}: outside a plausible albedo (0.04..0.94)")
            if slot == "normal":
                v = a[..., :3] * 2 - 1
                # a baked map may have a few texels facing away (the wall of a deep cut); a map
                # that is wrong (object space, wrong channel order) has many
                inward = float((v[..., 2] <= 0).mean())
                if np.abs(np.linalg.norm(v, axis=2) - 1).mean() > 0.05 or inward > 0.01:
                    bad.append(f"{mat.name}.normal: not a tangent-space map (length off, or {inward:.1%} of "
                               "texels point inward)")
        if mat.orm is not None and (mat.metallic != 1.0 or mat.roughness != 1.0):
            bad.append(f"{mat.name}: orm texture with factors {mat.metallic}/{mat.roughness}; "
                       "they multiply the texture, set both to 1.0")
    return not bad, "; ".join(bad) or f"{n} texture(s): size, power of two, albedo range, normals"


def _budget(ctx):
    b, m, bad = ctx.budget or {}, ctx.model, []
    if "tris" in b and m.triangles > b["tris"]:
        bad.append(f"{m.triangles} triangles over BUDGET {b['tris']}")
    if "materials" in b and len(m.parts) > b["materials"]:
        bad.append(f"{len(m.parts)} materials over BUDGET {b['materials']}")
    if "texture" in b:
        for mat in m.materials:
            for slot, img in mat.textures().items():
                if max(img.shape[:2]) > b["texture"]:
                    bad.append(f"{mat.name}.{slot} {max(img.shape[:2])} px over BUDGET {b['texture']}")
    return not bad, "; ".join(bad) or f"within BUDGET {b}" if b else "no BUDGET declared"


def _skin(ctx):
    from .rig import MAX_BONES
    sk, s, bad = ctx.model.skeleton, ctx.summary["skin"], []
    if s is None:
        return False, "the GLB has no skin"
    if not 1 <= len(sk) <= MAX_BONES:
        bad.append(f"{len(sk)} bones (Cinder allows 1..{MAX_BONES})")
    if s["joints"] != len(sk) or s["inverse_bind"] != len(sk):
        bad.append(f"file has {s['joints']} joints and {s['inverse_bind']} inverse bind matrices for {len(sk)} bones")
    if s["weight_sum_error"] > 1e-4:
        bad.append(f"weights do not sum to 1 (off by {s['weight_sum_error']:.4f})")
    if s["joint_index_max"] >= len(sk):
        bad.append("a vertex names a joint that does not exist")
    for i, b in enumerate(sk.bones):
        if b.parent >= i:
            bad.append(f"bone {b.name} comes before its parent")
    used = set()
    for j, w in ctx.model.skins:
        used |= set(np.unique(j[w > 0]).tolist())
    idle = [b.name for i, b in enumerate(sk.bones) if i not in used and b.name != "root"
            and not any(c.parent == i for c in sk.bones)]
    if idle:
        bad.append(f"leaf bones move nothing: {idle}")
    return not bad, "; ".join(bad) or f"{len(sk)} bones, 4 influences, weights sum to 1, parents first"


def _clips(ctx):
    bad = []
    got = {c["name"]: c for c in ctx.summary["clips"]}
    for clip in ctx.model.clips:
        c = got.get(clip.name)
        if c is None:
            bad.append(f"clip {clip.name} is not in the file")
            continue
        if not c["times_sorted"]:
            bad.append(f"{clip.name}: key times are not increasing")
        if c["quaternion_error"] > 1e-3:
            bad.append(f"{clip.name}: rotations are not unit quaternions")
        if abs(c["duration"] - clip.duration) > 1e-3:
            bad.append(f"{clip.name}: duration {c['duration']} in the file, {clip.duration} built")
        if clip.looping:
            for bone, keys in clip.rotations.items():
                if 1 - abs(float(np.dot(keys[0][1], keys[-1][1]))) > 1e-4:
                    bad.append(f"{clip.name}: {bone} does not end where it starts (the loop pops)")
                    break
        unknown = [b for b in list(clip.rotations) + list(clip.translations) if b not in ctx.model.skeleton.names]
        if unknown:
            bad.append(f"{clip.name}: tracks for bones that do not exist: {unknown}")
    return not bad, "; ".join(bad) or (f"{len(got)} clip(s): " + ", ".join(
        f"{n} {c['duration']:g} s" for n, c in got.items()) + "; sorted keys, unit rotations, loops close")


def clips(*names):
    """The character has exactly these clips."""
    def fn(ctx):
        got = [c.name for c in ctx.model.clips]
        return sorted(got) == sorted(names), f"clips {got}"
    return Check("clips", fn)


def phase_matched(a, b, bone="foot.L", tol=1 / 16):
    """Two cycles strike with the same foot at the same phase, so Cinder can blend them on a
    shared phase (walk into run) without the feet sliding past each other."""
    def fn(ctx):
        from .rig import contact_phase
        sk = ctx.model.skeleton
        pa, pb = (contact_phase(sk, ctx.model.clip(n), bone) for n in (a, b))
        d = min(abs(pa - pb), 1 - abs(pa - pb))
        return d <= tol, f"{bone} strikes at phase {pa:.2f} in {a} and {pb:.2f} in {b}"
    return Check(f"phase {a}/{b}", fn)


def deforms_cleanly(typical=1.6, worst=4.0, samples=8):
    """Through every clip, edges keep roughly their length: a vertex bound to the wrong bone
    (a hand that follows a leg) stretches its edges many times over. `typical` bounds the
    99th-percentile stretch, `worst` the single worst edge."""
    def fn(ctx):
        m = ctx.model
        p99 = mx = 0.0
        where = ""
        for clip in m.clips:
            for k in range(samples):
                posed = m.posed(clip, clip.duration * k / samples)
                for (rest, _), (now, _) in zip(m.parts, posed.parts):
                    e = np.vstack([rest.f[:, [0, 1]], rest.f[:, [1, 2]], rest.f[:, [2, 0]]])
                    l0 = np.linalg.norm(rest.v[e[:, 0]] - rest.v[e[:, 1]], axis=1)
                    l1 = np.linalg.norm(now.v[e[:, 0]] - now.v[e[:, 1]], axis=1)
                    ratio = l1 / np.maximum(l0, 1e-6)
                    ratio = ratio[l0 > 1e-4]
                    p99 = max(p99, float(np.percentile(ratio, 99)))
                    if ratio.max() > mx:
                        mx, where = float(ratio.max()), f"{clip.name} at {k / samples:.2f}"
        ok = p99 <= typical and mx <= worst
        return ok, (f"edges stretch at most {mx:.2f}x (in {where}); 99 % stay under {p99:.2f}x"
                    + ("" if ok else f" (limits {worst}x and {typical}x): some vertices follow the wrong bone"))
    return Check("deforms cleanly", fn)


def static_checks(model=None):
    base = [Check("name", _name_ok), Check("readback", _readback), Check("features", _features),
            Check("geometry", _geometry), Check("uvs", _uvs), Check("textures", _textures),
            Check("budget", _budget)]
    if getattr(model, "skeleton", None) is not None:
        base += [Check("skin", _skin), Check("clip data", _clips)]
    return base
