# 3D workspace: generative models for 3D printing

The user describes an object; Claude writes it as a Python model script, builds it,
looks at the renders, iterates, and hands back an STL. Modeling is fully generative:
the user does not model by hand here. If they want to tweak something themselves they
import the STL into Tinkercad (or any slicer/CAD app), so every STL must import cleanly.

## Workflow

1. Clarify only what changes the geometry (size, what it attaches to, print vs cast,
   printer bed). Otherwise pick sensible defaults and state them.
2. `cad new <name> "<one-line description>"` creates `models/<name>.py` from the template.
3. Write the model (see "Model contract" below).
4. `cad build models/<name>.py` builds it, checks it, and writes to `output/<name>/`:
   - `<name>.stl` (binary, mm, the deliverable)
   - `<name>.step` (build123d models only; editable in Fusion/FreeCAD/Onshape)
   - `<name>_preview.png` (Iso / Top / Front / Right / Iso-from-below + stats)
   - `report.txt`
5. **Read the preview PNG and look at it** before calling a model done. Check proportions,
   that details actually show, nothing is floating, and the print orientation is sane.
   Fix and rebuild until it looks right; the build must report `watertight, 1 body`.
6. Deliver: send the preview PNG and the STL to the user (SendUserFile), and summarize
   size, print orientation, supports needed, and anything they should know.

Variants: `cad build models/x.py --set style=square --set thickness=30` writes to
`output/x_square_30/`. Use `--name` to pick the folder name, `--fast` for a quick coarse
iteration (skips STEP), `--bed X Y Z` for a different printer (default 256 mm cube).

`cad` is `cad.cmd` in the repo root (Windows) and wraps `.venv/Scripts/python -m cadkit`.
From Git Bash use `./cad.cmd ...` or `.venv/Scripts/python -m cadkit ...`.

## Model contract

```python
"""Docstring: what it is, how it's oriented, anything non-obvious."""
DESCRIPTION = "one line"
PARAMS = dict(width=40.0, style="a")   # every tunable dimension; types drive --set parsing
def build(p):                          # p.width, p.style ...
    return part                        # or {"lid": a, "base": b} for multi-part prints
```

`build` may return a build123d Part/Solid, a manifold3d `Manifold`, or a `trimesh.Trimesh`.
A dict exports each part as its own STL (`<name>-<part>.stl`).

## Which kernel

| Kernel | Use for | Helpers |
|---|---|---|
| **build123d** (OpenCascade B-rep) | Engineered parts: enclosures, brackets, adapters, anything with fillets, chamfers, holes, threads, exact fits. Exports STEP too. | `from cadkit.cad import *`: `closed_spline`, `clip`, `draft_extrude`, `faces_of` |
| **manifold3d** (mesh CSG) | Decorative and organic work: reliefs, molds with artwork, patterns, lots of strokes/spots, lattices. Fast and never fails on intricate booleans. STL only. | `from cadkit.relief import *`: `smooth_shape`, `stroke`, `bezier`, `circle`, `ellipse`, `mirror_x`, `grow`, `extrude`, `drafted`, `draft_offset` |

`models/butterfly_paver_mold.py` is the worked manifold example; `models/_template.py` is
the build123d starting point.

## Design rules (3D printing)

- Units are millimetres. Z is up. The part sits on Z=0 **in the orientation it prints**,
  with a flat base. The build reports flat base area and overhang area; aim for 0 overhang.
- Minimum wall 1.2 mm (2+ mm for anything structural); minimum embossed detail 0.8 mm wide.
- Fits: 0.2 mm clearance per side for sliding fits, 0.1 mm for press fits. Holes print
  ~0.2 mm undersize.
- Molds for cement/plaster/resin are cast face-down: a rib on the mold floor becomes a
  groove in the casting, a pocket becomes a raised area. Draft every wall the casting
  touches: about 2° on walls and 8-10° on ribs. Mirror any text or asymmetric art, since
  the casting is the mirror image of the mold floor.
- Keep STLs under 25 MB (Tinkercad's import limit). Under 300k triangles keeps Tinkercad
  responsive; use `--fast` or coarser curves if a model gets heavier.

## Gotchas (learned the hard way)

- **Never leave coplanar faces in a union.** A rib that sits exactly on a floor leaves
  zero-area slivers and a non-watertight STL. Sink it 0.1 mm into the surface it stands on.
  Same for clip boundaries in stacked/drafted slices: move the clip region with the draft
  so slice end faces don't coincide.
- build123d 0.13: `Sketch & Sketch` returns empty; use `clip(a, b)`.
- build123d: `extrude(taper>0)` goes through LocOpe_DPrism and can **segfault** on thin or
  traced shapes; use `draft_extrude` from `cadkit.cad`. Spline faces built from clockwise
  points face -Z and won't fuse with other faces; `closed_spline` fixes that.
- build123d tapers on large, intricate art (many joined strokes) are slow (minutes) and
  fail often. Do that kind of work in manifold3d instead.
- Mesh cleanup and float32 rounding are handled in `cadkit/mesh.py`; if a build reports
  NOT watertight, look for coplanar or touching geometry in the model first.

## Layout

```
cadkit/        harness: __main__ (CLI), mesh (convert/clean/check), render (preview), cad + relief helpers
models/        one script per object (_template.py is the starting point)
output/        generated files, safe to delete; rebuilt from models/
cad.cmd        CLI wrapper
```

Setup on a new machine: `py -3.12 -m venv .venv` then
`.venv\Scripts\python -m pip install -r requirements.txt`.
