"""`cad publish`: turn a built and sliced output folder into a shop-ready product.

Writes into output/<name>/:
    <name>_product.png      clean 1600 x 1600 iso render, white background
    <name>_hero.png         same, lower and more frontal camera
    <stem>_plate.png        the slicer's own plate picture per sliced 3MF
    <name>_print_notes.txt  what the buyer needs to know (deterministic bytes)
    <name>_preview.glb      low-poly, unit-scaled viewer mesh for the shop's 3D canvas
    manifest.json           schema cadkit-product/1, everything the shop ingests

A model can steer it with two optional constants:

    PRODUCT = dict(title="...", category="molds", tags=[...], printers=["a1", "a1mini"],
                   cast_material="cement", post_processing="...", sellable=None)
    LICENSE_NOTES = "..."   # replaces DEFAULT_LICENSE in the notes and manifest

`gate()` decides `sellable`: watertight single body, every check PASS, no warnings,
no fit interference, a fresh slice + 3MF per supported printer, product render and
notes present. A dirty git tree is a reason, not a block. PRODUCT["sellable"]=True
overrides (reasons stay as caveats); False blocks.
"""
import re
from pathlib import Path

from . import __version__
from . import outputs
from . import printers as printersmod

SCHEMA = "cadkit-product/1"
DEFAULT_PRINTERS = ["a1", "a1mini"]
FILE_ROLES = ("stl", "3mf", "step", "png", "txt", "glb")
GLB_FACES = (8000, 12000)   # face band for the viewer mesh; the hard cap is 15k
SPEC_KEYS = ("object", "overall", "mates_with", "orientation", "must_have", "tolerances",
             "casting", "material")

DEFAULT_LICENSE = (
    "Licensed, not sold. Personal licence: print as many copies as you like for yourself "
    "and as gifts; no selling prints or files, no sharing the files. Commercial licence: "
    "sell prints and castings made with this file, no file resale or redistribution. "
    "Either way the design stays the author's. No warranty: check the first print "
    "before casting."
)

MOLD_NOTES_DEFAULT = (
    "Print the mold opening-up as supplied, 2-3 walls, 15% infill is plenty. Wipe the "
    "cavity with a thin coat of release agent (mold release spray, a smear of petroleum "
    "jelly, or diluted dish soap left to dry) before every pour. Mix the casting "
    "material to a pourable, lump-free consistency, pour, then tap and shake the mold "
    "for a minute so bubbles rise off the detail. Let it cure fully (cement 24-48 h, "
    "plaster 1-2 h, resin per its instructions) before demolding: flex the walls and "
    "lift the mold off the casting rather than prying the casting out. Rinse and dry "
    "the mold between pours. PLA softens above ~55 C: keep it out of the sun and away "
    "from hot resin mixes."
)


# ---------------------------------------------------------------- model metadata

def parse_spec(doc):
    """Split a model docstring into the prose before `Spec:` and the Spec block as a
    dict of normalised keys ('mates with' -> 'mates_with'), continuation lines joined.
    Returns (description, spec)."""
    doc = (doc or "").replace("\r\n", "\n")
    m = re.search(r"^\s*Spec\b[^\n]*:\s*\n", doc, re.M)
    if not m:
        return doc.strip(), {}
    description = doc[:m.start()].strip()
    spec, key = {}, None
    for line in doc[m.end():].split("\n"):
        if not line.strip():
            if spec:
                break
            continue
        km = re.match(r"^\s*([A-Za-z][A-Za-z /-]*?):\s*(.*)$", line)
        indent = len(line) - len(line.lstrip())
        if km and (key is None or indent <= spec_indent[0]):
            key = re.sub(r"[ /-]+", "_", km.group(1).strip().lower())
            spec[key] = km.group(2).strip()
            spec_indent = [indent]
        elif key:
            spec[key] = (spec[key] + " " + line.strip()).strip()
    return description, spec


def slug_of(name):
    """Shop slug: lowercase kebab, `_` -> `-`, no leading/trailing or doubled dashes."""
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-") or "model"


def title_of(name, product=None):
    if product and product.get("title"):
        return product["title"]
    words = name.replace("-", "_").split("_")
    return " ".join(w.upper() if w in ("d20", "sd", "usb") else w.capitalize() for w in words if w)


def category_of(name, summary, product=None):
    if product and product.get("category"):
        return product["category"]
    text = f"{name} {summary}".lower()
    if "mold" in text or "mould" in text:
        return "molds"
    return "parts"


def model_info(mod, path):
    """What `compose_manifest` needs from a loaded model module."""
    product = dict(getattr(mod, "PRODUCT", None) or {})
    description, spec = parse_spec(getattr(mod, "__doc__", "") or "")
    return dict(
        name=Path(path).stem,
        model=Path(path).name,
        model_sha256=outputs.sha256(path),
        summary=(getattr(mod, "DESCRIPTION", "") or "").strip(),
        description=description,
        spec=spec,
        product=product,
        license_notes=(getattr(mod, "LICENSE_NOTES", None) or "").strip() or None,
    )


# ---------------------------------------------------------------- viewer mesh

def preview_glb(meshes, path, faces=GLB_FACES):
    """Write a binary glTF preview of `meshes` (trimesh.Trimesh, print pose) for the
    shop's 3D viewer. Not printable on purpose: the parts are concatenated, simplified
    into the `faces` band (8-12k by default) and normalised to a unit bounding box
    centred on the origin, so the real millimetre size is not in the file. One neutral
    PBR material, no normals (the viewer computes them). Returns (faces, bytes).

    Simplification is manifold3d's tolerance-bounded edge collapse (every vertex stays
    within the tolerance of the original surface), which keeps 1.7 mm mold walls and
    relief lines intact where quadric decimators collapse them; the tolerance is
    searched so the count lands in the band."""
    import numpy as np
    import trimesh
    import manifold3d as m3
    tm = trimesh.util.concatenate([m.copy() for m in meshes]) if len(meshes) > 1 else meshes[0].copy()
    lo, hi = faces
    if len(tm.faces) > hi:
        man = m3.Manifold(m3.Mesh(np.ascontiguousarray(tm.vertices, np.float32),
                                  np.ascontiguousarray(tm.faces, np.uint32)))
        if man.status() == m3.Error.NoError and man.num_tri() > 0:
            best, t_lo, t_hi = None, 0.01, 4.0          # mm; bisect in log space
            for _ in range(14):
                tol = float(np.sqrt(t_lo * t_hi))
                n = man.simplify(tol).num_tri()
                if n > hi:
                    t_lo = tol
                else:
                    t_hi = tol
                    if n >= lo or best is None or n > best[1]:
                        best = (tol, n)
                    if n >= lo:
                        break
            mg = man.simplify(best[0] if best else t_hi).to_mesh()
            tm = trimesh.Trimesh(vertices=np.asarray(mg.vert_properties)[:, :3],
                                 faces=np.asarray(mg.tri_verts), process=False)
    tm.apply_translation(-tm.bounds.mean(axis=0))
    tm.apply_scale(1.0 / float(np.max(tm.extents)))
    tm = trimesh.Trimesh(vertices=np.asarray(tm.vertices, dtype=np.float32), faces=tm.faces, process=False)
    tm.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name="preview", baseColorFactor=[205, 205, 205, 255], metallicFactor=0.0, roughnessFactor=0.65))
    data = tm.export(file_type="glb")
    Path(path).write_bytes(data)
    return len(tm.faces), len(data)


# ---------------------------------------------------------------- printers and files

def fits_bed(size_mm, bed):
    return all(s <= b + 1e-6 for s, b in zip(sorted(size_mm), sorted(bed)))


def printers_for(info, build, requested=None):
    """(wanted, supported): the printers the product targets and those whose bed
    takes every part of this build."""
    wanted = list(requested or info.get("product", {}).get("printers") or DEFAULT_PRINTERS)
    wanted = [w.lower().replace("-", "").replace("_", "").replace(" ", "") for w in wanted]
    supported = []
    for key in wanted:
        pr = printersmod.PRINTERS.get(key)
        if not pr:
            continue
        if all(fits_bed(part["size_mm"], pr["bed"]) for part in build.get("parts", {}).values()):
            supported.append(key)
    return wanted, supported


def collect_files(out, name, parts, printers):
    """The whitelist of deliverable files present in `out`, each with role, size and
    sha256. G-code, report, JSON and ad-hoc pictures are never included."""
    out = Path(out)
    files = []

    def add(path, role, **extra):
        if path.exists():
            files.append(dict(role=role, **extra, path=path.name, bytes=path.stat().st_size,
                              sha256=outputs.sha256(path)))

    for fname, data in parts.items():
        part = data.get("part", fname)
        add(out / f"{fname}.stl", "stl", part=part)
        add(out / f"{fname}.step", "step", part=part)
        for key in printers:
            add(out / f"{fname}_{key}.3mf", "3mf", part=part, printer=key)
    add(out / f"{name}_product.png", "png", kind="product")
    add(out / f"{name}_hero.png", "png", kind="hero")
    add(out / f"{name}_preview.png", "png", kind="check_sheet")
    for fname in parts:
        for key in printers:
            add(out / f"{fname}_{key}_plate.png", "png", kind="plate", part=parts[fname].get("part", fname), printer=key)
    add(out / f"{name}_print_notes.txt", "txt", kind="print_notes")
    add(out / f"{name}_preview.glb", "glb", kind="viewer")
    return files


# ---------------------------------------------------------------- manifest

def compose_manifest(out, build, slices, info, printers=None, git=None, generated_at=None):
    """The cadkit-product/1 manifest for one output folder. `build` and `slices` are
    the build.json / slice.json contents, `info` comes from model_info(). Stale
    slices (STL changed since) are left out. Pure apart from reading the files it
    lists, so it runs the same on synthetic folders."""
    out = Path(out)
    name = build.get("name") or info["name"]
    product = info.get("product", {})
    wanted, supported = printers_for(info, build, printers)
    parts = []
    stl_sha = {}
    for fname, data in build.get("parts", {}).items():
        stl_sha[fname] = data.get("stl_sha256")
        parts.append(dict(
            name=fname, part=data.get("part", fname),
            size_mm=data.get("size_mm"), size_in=data.get("size_in"),
            volume_cm3=data.get("volume_cm3"), est_grams_pla=data.get("est_grams_pla"),
            triangles=data.get("triangles"), watertight=data.get("watertight"),
            bodies=data.get("bodies"), flat_base_mm2=data.get("flat_base_mm2"),
            overhang_mm2=data.get("overhang_mm2"), thinnest_wall_mm=data.get("thinnest_wall_mm"),
            checks=list(data.get("checks", [])), checks_ok=bool(data.get("checks_ok", False)),
            warnings=list(data.get("warnings", [])),
            files=dict(stl=data.get("stl"), step=data.get("step")),
        ))
    fit = [dict(a=q["a"], b=q["b"], interference_mm3=q["interference_mm3"],
                clearance_mm=q["clearance_mm"], ok=q["ok"])
           for q in ((build.get("fit") or {}).get("pairs") or [])]
    out_slices = []
    for stem, s in slices.items():
        fresh = s.get("stl") in {p["files"]["stl"] for p in parts} and \
            s.get("stl_sha256") == stl_sha.get(Path(s["stl"]).stem)
        if not fresh:
            continue
        out_slices.append(dict(
            part=Path(s["stl"]).stem, printer=s.get("printer"), printer_name=s.get("printer_name"),
            slicer=s.get("slicer"), filament_preset=s.get("filament_preset"), material=s.get("material"),
            layer_height_mm=s.get("layer_height_mm"), infill_pct=s.get("infill_pct"),
            supports=s.get("supports", dict(enabled=False, generated=False)),
            print_time_s=s.get("print_time_s"), print_time_text=s.get("print_time_text"),
            layers=s.get("layers"), filament_g=s.get("filament_g"), filament_m=s.get("filament_m"),
            file=s.get("file"),
        ))
    files = collect_files(out, name, build.get("parts", {}), supported)
    by_kind = {f.get("kind"): f["path"] for f in files if f["role"] == "png"}
    images = dict(product=by_kind.get("product"), hero=by_kind.get("hero"),
                  check_sheet=by_kind.get("check_sheet"),
                  thumbnails=[f["path"] for f in files if f.get("kind") == "plate"])
    git = git or outputs.git_info()
    manifest = dict(
        schema=SCHEMA,
        name=name,
        slug=slug_of(name),
        title=title_of(name, product),
        summary=info.get("summary", ""),
        description=info.get("description", ""),
        category=category_of(name, info.get("summary", ""), product),
        tags=list(product.get("tags") or [category_of(name, info.get("summary", ""), product)]),
        spec=dict(info.get("spec", {})),
        params=dict(build.get("params", {})),
        printer=build.get("printer"),
        printers_supported=supported,
        printers_requested=wanted,
        cast_material=product.get("cast_material"),
        post_processing=product.get("post_processing"),
        parts=parts,
        fit=fit,
        slices=out_slices,
        files=files,
        images=images,
        sellable=False,
        sellable_override=product.get("sellable"),
        reasons=[],
        license=info.get("license_notes") or DEFAULT_LICENSE,
        license_custom=bool(info.get("license_notes")),
        generated_at=generated_at or outputs.now_iso(),
        cadkit_version=__version__,
        git_commit=git.get("commit"),
        git_dirty=bool(git.get("dirty")),
        model=info.get("model"),
        model_sha256=info.get("model_sha256") or build.get("model_sha256"),
    )
    manifest["sellable"], manifest["reasons"] = gate(manifest)
    return manifest


def gate(m):
    """(sellable, reasons) for a manifest; see the module docstring for the rules."""
    reasons = []
    if not m.get("parts"):
        reasons.append("no parts built")
    for p in m.get("parts", []):
        tag = p["name"]
        if not p.get("watertight"):
            reasons.append(f"{tag}: not watertight")
        if p.get("bodies") != 1:
            reasons.append(f"{tag}: {p.get('bodies')} bodies")
        failed = [c["name"] for c in p.get("checks", []) if not c.get("ok")]
        if failed or not p.get("checks_ok"):
            reasons.append(f"{tag}: checks failed ({', '.join(failed) or 'unknown'})")
        for w in p.get("warnings", []):
            reasons.append(f"{tag}: {w}")
    for q in m.get("fit", []):
        if not q.get("ok"):
            reasons.append(f"fit: {q['a']} vs {q['b']} interfere by {q['interference_mm3']} mm3")
    if not m.get("printers_supported"):
        reasons.append("no supported printer: the part is larger than every requested bed")
    have_3mf = {(f.get("part"), f.get("printer")) for f in m.get("files", []) if f["role"] == "3mf"}
    have_slice = {(s["part"], s["printer"]) for s in m.get("slices", [])}
    for p in m.get("parts", []):
        for key in m.get("printers_supported", []):
            if (p["name"], key) not in have_slice:
                reasons.append(f"{p['name']}: no fresh slice for {key}")
            if (p["part"], key) not in have_3mf:
                reasons.append(f"{p['name']}: no {key} 3MF")
    roles = {f["role"] for f in m.get("files", [])}
    if "stl" not in roles:
        reasons.append("no STL in the folder")
    if not (m.get("images") or {}).get("product"):
        reasons.append("no product render")
    if not any(f.get("kind") == "print_notes" for f in m.get("files", [])):
        reasons.append("no print notes")
    blocking = list(reasons)
    if m.get("git_dirty"):
        reasons.append("built from an uncommitted working tree")
    override = m.get("sellable_override")
    if override is False:
        return False, ["PRODUCT sellable=False"] + reasons
    if override is True:
        return True, reasons
    return not blocking, reasons


# ---------------------------------------------------------------- print notes

def _hm(seconds):
    if not seconds:
        return "?"
    h, rem = divmod(int(seconds), 3600)
    return (f"{h}h " if h else "") + f"{rem // 60}m"


def _size_text(size_mm, size_in):
    if not size_mm:
        return "?"
    mm = " x ".join(f"{v:.1f}" for v in size_mm)
    inch = " x ".join(f"{v:.2f}" for v in (size_in or [v / 25.4 for v in size_mm]))
    return f"{mm} mm ({inch} in)"


def print_notes_text(m):
    """The buyer-facing notes. No timestamps: identical inputs give identical bytes."""
    lines = [m["title"], m.get("summary", ""), ""]
    slices = m.get("slices", [])
    names = {s["printer"]: s.get("printer_name") or s["printer"] for s in slices}
    for key in m.get("printers_supported", []):
        names.setdefault(key, printersmod.PRINTERS.get(key, {}).get("name", key))
    materials = sorted({s.get("material") for s in slices if s.get("material")})
    presets = sorted({s.get("filament_preset") for s in slices if s.get("filament_preset")})
    lh = sorted({s.get("layer_height_mm") for s in slices if s.get("layer_height_mm")})
    infill = sorted({s.get("infill_pct") for s in slices if s.get("infill_pct") is not None})
    sup = "none needed" if not any((s.get("supports") or {}).get("generated") for s in slices) else "yes, included in the 3MF"
    lines += ["PRINTING",
              "  printers:     " + (", ".join(names[k] for k in names) or "any 0.4 mm nozzle FDM printer"),
              "  material:     " + (", ".join(materials) or "PLA") + (f" ({', '.join(presets)})" if presets else ""),
              "  layer height: " + (", ".join(f"{v:g} mm" for v in lh) or "0.2 mm")
              + "; infill " + (", ".join(f"{v:g}%" for v in infill) or "15%")
              + "; supports " + sup,
              "  orientation:  " + (m.get("spec", {}).get("orientation") or "as supplied, flat base on the bed")]
    parts = m.get("parts", [])
    if len(parts) == 1:
        lines.append("  size:         " + _size_text(parts[0].get("size_mm"), parts[0].get("size_in")))
    else:
        lines.append(f"  parts:        {len(parts)}")
        for p in parts:
            lines.append(f"    {p['part']}: {_size_text(p.get('size_mm'), p.get('size_in'))}")
    if slices:
        lines.append("  estimates:")
        for s in slices:
            who = f"{s.get('printer_name') or s['printer']}" + (f", {s['part']}" if len(parts) > 1 else "")
            lines.append(f"    {who}: {_hm(s.get('print_time_s'))}, {s.get('filament_g', 0):.0f} g / "
                         f"{s.get('filament_m', 0):.1f} m {s.get('material') or ''}, {s.get('layers', 0)} layers".rstrip())
    else:
        lines.append("  estimates:    not sliced yet")
    lines.append("  files:")
    for f in m.get("files", []):
        what = {"stl": "mesh for any slicer", "3mf": f"sliced Bambu Studio project for the {names.get(f.get('printer'), f.get('printer'))}, open and print",
                "step": "editable CAD (Fusion, FreeCAD, Onshape)", "txt": "these notes",
                "glb": "low-poly preview for the shop's 3D viewer (not printable)",
                "png": {"product": "product picture", "hero": "product picture", "check_sheet": "engineering check sheet",
                        "plate": "slicer plate preview"}.get(f.get("kind"), "picture")}[f["role"]]
        lines.append(f"    {f['path']}  ({what})")
    lines.append("")
    if m.get("category") == "molds":
        text = m.get("post_processing") or MOLD_NOTES_DEFAULT
        cast = m.get("cast_material")
        lines += ["USING THE MOLD"] + (["  cast material: " + cast] if cast else []) + _wrap(text) + [""]
    elif m.get("post_processing"):
        lines += ["FINISHING"] + _wrap(m["post_processing"]) + [""]
    notes = []
    for p in parts:
        notes += [f"{p['part']}: {w}" if len(parts) > 1 else w for w in p.get("warnings", [])]
    pipeline = ("uncommitted", "no print notes", "no product render", "PRODUCT sellable")
    notes += [r for r in m.get("reasons", [])
              if not any(k in r for k in pipeline) and not any(r.endswith(w) for w in notes)]
    spec = m.get("spec", {})
    for k in ("must_have", "tolerances"):
        if spec.get(k):
            notes.append(f"{k.replace('_', ' ')}: {spec[k]}")
    lines += ["NOTES"] + (_wrap_list(notes) if notes else ["  none"]) + [""]
    lines += ["LICENSE"] + _wrap(m.get("license") or DEFAULT_LICENSE) + [""]
    lines.append(f"Generated by cadkit {m.get('cadkit_version', __version__)} from {m.get('model')}"
                 + (f" at commit {m['git_commit'][:12]}" if m.get("git_commit") else ""))
    return "\n".join(lines) + "\n"


def _wrap(text, width=78, indent="  "):
    import textwrap
    return textwrap.wrap(text, width=width, initial_indent=indent, subsequent_indent=indent)


def _wrap_list(items, width=78):
    out = []
    for it in items:
        out += _wrap(it, width, "  - ")[:1] + [l.replace("  - ", "    ", 1) for l in _wrap(it, width, "  - ")[1:]]
    return out


# ---------------------------------------------------------------- validation

def validate_manifest(m):
    """Hand-rolled schema check for cadkit-product/1. Returns a list of problems;
    empty means valid."""
    bad = []

    def need(key, types, where=m, tag=""):
        if key not in where:
            bad.append(f"{tag}missing {key}")
            return False
        if not isinstance(where[key], types):
            bad.append(f"{tag}{key} is {type(where[key]).__name__}, want {types}")
            return False
        return True

    if m.get("schema") != SCHEMA:
        bad.append(f"schema is {m.get('schema')!r}, want {SCHEMA!r}")
    for key, types in (("name", str), ("slug", str), ("title", str), ("summary", str), ("description", str),
                       ("category", str), ("tags", list), ("spec", dict), ("params", dict), ("printer", str),
                       ("printers_supported", list), ("parts", list), ("fit", list), ("slices", list),
                       ("files", list), ("images", dict), ("sellable", bool), ("reasons", list),
                       ("license", str), ("generated_at", str), ("cadkit_version", str),
                       ("git_dirty", bool), ("model_sha256", str)):
        need(key, types)
    if "sellable_override" in m and m["sellable_override"] not in (None, True, False):
        bad.append("sellable_override must be null, true or false")
    if "git_commit" in m and m["git_commit"] is not None and not re.fullmatch(r"[0-9a-f]{40}", m["git_commit"]):
        bad.append("git_commit is not a 40-hex sha")
    if isinstance(m.get("slug"), str) and not re.fullmatch(r"[a-z0-9][a-z0-9-]*", m["slug"]):
        bad.append(f"slug {m['slug']!r} is not lowercase-kebab")
    if not m.get("parts"):
        bad.append("parts is empty")
    for i, p in enumerate(m.get("parts") or []):
        tag = f"parts[{i}] "
        for key, types in (("name", str), ("part", str), ("size_mm", list), ("size_in", list), ("volume_cm3", (int, float)),
                           ("est_grams_pla", (int, float)), ("triangles", int), ("watertight", bool), ("bodies", int),
                           ("flat_base_mm2", (int, float)), ("overhang_mm2", (int, float)),
                           ("thinnest_wall_mm", (int, float)), ("checks", list), ("checks_ok", bool),
                           ("warnings", list), ("files", dict)):
            need(key, types, p, tag)
        if len(p.get("size_mm") or []) != 3:
            bad.append(tag + "size_mm needs 3 numbers")
        for j, c in enumerate(p.get("checks") or []):
            for key, types in (("name", str), ("ok", bool), ("detail", str)):
                need(key, types, c, f"{tag}checks[{j}] ")
    paths = set()
    for i, f in enumerate(m.get("files") or []):
        tag = f"files[{i}] "
        for key, types in (("role", str), ("path", str), ("bytes", int), ("sha256", str)):
            need(key, types, f, tag)
        if f.get("role") not in FILE_ROLES:
            bad.append(f"{tag}role {f.get('role')!r} not in {FILE_ROLES}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(f.get("sha256", ""))):
            bad.append(tag + "sha256 is not 64 hex chars")
        if f.get("path") in paths:
            bad.append(f"{tag}duplicate path {f.get('path')}")
        if "/" in str(f.get("path", "")) or "\\" in str(f.get("path", "")):
            bad.append(f"{tag}path must be a bare file name")
        paths.add(f.get("path"))
        if f.get("role") == "3mf" and not f.get("printer"):
            bad.append(tag + "3mf without printer")
        if f.get("role") == "glb" and f.get("kind") != "viewer":
            bad.append(tag + "glb must be kind viewer")
    for i, s in enumerate(m.get("slices") or []):
        tag = f"slices[{i}] "
        for key, types in (("part", str), ("printer", str), ("printer_name", str), ("material", str),
                           ("print_time_s", int), ("layers", int), ("filament_g", (int, float)),
                           ("filament_m", (int, float)), ("supports", dict), ("file", str)):
            need(key, types, s, tag)
        if s.get("file") and s["file"] not in paths:
            bad.append(f"{tag}file {s['file']} is not in files[]")
    images = m.get("images") or {}
    for key in ("product", "hero", "check_sheet"):
        if key not in images:
            bad.append(f"images missing {key}")
        elif images[key] is not None and images[key] not in paths:
            bad.append(f"images.{key} {images[key]} is not in files[]")
    if not isinstance(images.get("thumbnails"), list):
        bad.append("images.thumbnails must be a list")
    if m.get("sellable") and not any(f.get("role") == "stl" for f in m.get("files") or []):
        bad.append("sellable without an STL")
    return bad


def _print_summary(m):
    print(f"\n== publish {m['name']}")
    print(f"  title     {m['title']}  [{m['category']}]  slug {m['slug']}")
    print(f"  printers  {', '.join(m['printers_supported']) or 'none fit'}")
    for s in m["slices"]:
        print(f"  slice     {s['printer']}: {s.get('print_time_text')}, {s.get('filament_g')} g {s.get('material')}, {s.get('file')}")
    print(f"  files     {len(m['files'])}: " + ", ".join(f['path'] for f in m['files']))
    print(f"  sellable  {m['sellable']}" + (f"  (override {m['sellable_override']})" if m['sellable_override'] is not None else ""))
    for r in m["reasons"]:
        print(f"            - {r}")
