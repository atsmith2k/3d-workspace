# 3D workspace: generative models for 3D printing

The user describes an object; Claude writes it as a Python model script, builds it,
looks at the renders, iterates, and hands back an STL. Modeling is fully generative:
the user does not model by hand here. If they want to tweak something themselves they
import the STL into Tinkercad (or any slicer/CAD app), so every STL must import cleanly.

## Session start

- If `.venv` is missing, or `cad selftest` fails, run setup first (README, "For Claude:
  setting up this project"): `py scripts/setup.py` on Windows, `python3 scripts/setup.py`
  elsewhere, and wait for `READY`.
- If the user opens with no specific request ("set up", "what can this do", a greeting),
  confirm it's ready, mention any existing models (`cad list`), and invite them:
  **"Give me instructions for the model you want to make."** Ask for the object, rough
  size, and whether it's printed directly or used as a mold.
- If they open with a model request, just start the workflow below.

## Workflow

1. Clarify only what changes the geometry (size, what it attaches to, print vs cast,
   A1 or A1 mini). Otherwise pick sensible defaults and state them.
2. `cad new <name> "<one-line description>"` creates `models/<name>.py` from the template.
3. **Write the spec before the code.** Fill in the `Spec` block in the docstring: what it
   is, overall size, what it mates with and the exact dimensions used (with clearances),
   print orientation, every feature the user asked for with a size, tolerances. Then turn
   each line into a check in `checks(p)` (see "Model contract"): `dims`, `hole`, `solid`,
   `empty`, `thickness_at`, `flat_base`, `no_overhang`... The build fails when a check
   fails, which catches "the code ran but the shape is wrong" before you look at a picture.
4. Write `build(p)`.
5. `cad build models/<name>.py` builds it, checks it, and writes to `output/<name>/`:
   - `<name>.stl` (binary, mm, the deliverable)
   - `<name>.step` (build123d models only; editable in Fusion/FreeCAD/Onshape)
   - `<name>_preview.png`: Iso, Top/Front/Right with overall dimensions, Iso-from-below,
     two section views (cut through the centre, or `--section y=10 --section x=0`), and
     the stats. Faces are tinted **red** where they overhang and **yellow** where the
     wall is under 1.2 mm; section tiles show cut material in **orange**.
   - `report.txt`
6. **Read the preview PNG and look at it** before calling a model done. Check proportions,
   that details actually show, nothing is floating, and the print orientation is sane.
   Use the section tiles to confirm floor and wall thickness, cavities and hidden holes;
   add a `--section` through any feature you cannot see. Fix and rebuild until it looks
   right; the build must report `watertight, 1 body`, and the `wall` line should show
   0% under 1.2 mm unless the thin spots are intentional fine detail (the warning says
   where they are). Every `check` line must say PASS. When something in the picture is
   unclear, measure it instead of guessing: `cad measure models/<name>.py --probe x,y,z`
   says whether a point is inside, how far from the surface, and how thick the material
   is there; `--hole x,y[,axis]` measures a hole's diameter.
7. `cad slice models/<name>.py` (or `cad build ... --slice`) slices with Bambu Studio for
   the target printer (see "Printers") and reports print time, filament grams and metres,
   layer count, whether supports were generated, and writes the sliced project 3MF.
   Options: `--printer a1mini`, `--layer-height 0.28`, `--infill 20`, `--supports`,
   `--filament "Bambu PETG Basic"`. Tell the user the print time and filament on delivery.
8. Deliver: send the preview PNG, the STL and the `_<printer>.3mf` project to the user
   (SendUserFile), and summarize size, print orientation, print time, supports needed,
   and anything they should know.

Variants: `cad build models/x.py --set style=square --set thickness=30` writes to
`output/x_square_30/`. Use `--name` to pick the folder name, `--fast` for a quick coarse
iteration (skips STEP), `--printer a1mini` for the smaller printer, `--bed X Y Z` for
any other bed size. `--sweep thickness=2,3,4` builds every value and writes one
comparison sheet (`output/x_sweep_thickness/sweep.png`) to choose from.
`cad lint models/x.py` flags known pitfalls (taper extrudes, sketch `&`, missing
PARAMS/checks/Spec) before building; run it on any model that fails oddly.

Run `cad` from the repo root: `cad.cmd` on Windows (cmd/PowerShell), `./cad` on macOS,
Linux and Git Bash. Both wrap `.venv` Python `-m cadkit`. Other commands: `cad list`
(models and build status), `cad selftest` (regression suite: builds every model in
`tests/expected.json` and compares size, volume and checks with the recorded values;
also says which slicers were found; set `CAD_BAMBU` / `CAD_SLICER` for unusual installs).
After changing anything in `cadkit/` run `cad selftest`. After finishing a new model,
or deliberately changing an existing one, add or refresh its entry with
`cad selftest --update` (add the model's key, file and `--set` list to the JSON first)
so later helper changes cannot silently break it.

When a request is a variation of an existing model, add a parameter or style to that
model rather than copying it. Name new models in snake_case after the object.

## Model contract

```python
"""Docstring: what it is, how it's oriented, the Spec block (see the template)."""
from cadkit.checks import *
DESCRIPTION = "one line"
PARAMS = dict(width=40.0, style="a")   # every tunable dimension; types drive --set parsing
def checks(p):                         # or a static CHECKS = [...] list
    return [dims(x=p.width), hole(6.4, at=(10, 10)), solid((0, 0, 1)), no_overhang()]
def build(p):                          # p.width, p.style ...
    return part                        # or {"lid": a, "base": b} for multi-part prints
```

`build` may return a build123d Part/Solid, a manifold3d `Manifold`, or a `trimesh.Trimesh`.
A dict exports each part as its own STL (`<name>-<part>.stl`); then `checks` may return
a dict of part name to list (a plain list applies to every part).

Checks (`cadkit/checks.py`) run on the exported mesh, so they work for either kernel:
`dims(x=, y=, z=)` (number = +-0.5 mm, tuple = range), `volume(lo, hi)` cm3,
`hole(d, at=(a, b), axis="z", span=(lo, hi), tol=0.2)` (through hole unless `span`),
`solid(*points)`, `empty(*points)`, `thickness_at(point, min_mm)`, `wall_min(mm)`,
`flat_base(mm2)`, `no_overhang()`, `single_body()`, `fits_bed()`, and
`custom(name, fn)` with `fn(ctx)` seeing `ctx.tm`, `ctx.report`, `ctx.params`.
The same measurements are available in `cadkit/measure.py` and from `cad measure`.

## Which kernel

| Kernel | Use for | Helpers |
|---|---|---|
| **build123d** (OpenCascade B-rep) | Engineered parts: enclosures, brackets, adapters, anything with fillets, chamfers, holes, threads, exact fits. Exports STEP too. | `from cadkit.cad import *`: `closed_spline`, `clip`, `draft_extrude`, `faces_of` |
| **manifold3d** (mesh CSG) | Decorative and organic work: reliefs, molds with artwork, patterns, lots of strokes/spots. Fast and never fails on intricate booleans. STL only. | `from cadkit.relief import *`: `smooth_shape`, `stroke`, `bezier`, `circle`, `ellipse`, `mirror_x`, `grow`, `extrude`, `drafted`, `draft_offset`, `text` |
| **SDF** (implicit, meshed by manifold) | Blends, lattices and gyroid infill, shells, twists, repeats: `smooth_union` instead of fillets, `lattice_fill` to lighten a part. Returns a Manifold, so it combines with relief shapes and `text`. | `from cadkit.sdf import *`: `sphere`, `box`, `cylinder`, `capsule`, `torus`, `plane`, `union`, `intersect`, `subtract`, `smooth_*`, `twist`, `bend`, `repeat`, `shell`, `gyroid`, `schwarz_p`, `diamond`, `lattice_fill`, `build_sdf`, `to_sdf` |

Worked examples: `models/butterfly_paver_mold.py` (manifold relief mold),
`models/insert_test_block.py` (build123d + hardware table + embossed text),
`models/lattice_coaster.py` (SDF lattice + mesh text), `models/_template.py` (build123d start).

**Hardware and standard parts.** Never guess a fastener, insert, magnet, bearing, port or
board dimension: `from cadkit.hardware import *` has `clearance("M3")`, `insert("M3")`
(hole, depth, boss), `nut_pocket`, `head_pocket`, `magnet_pocket(6, 3)`, `bearing("608")`,
`dowel_hole("1/2")`, `board("pi4")`, `port("usb_c")` and the raw tables (`HEAT_SET`,
`CLEARANCE`, `BOARDS`, `BATTERIES`, `LUMBER`...). Helper results already include the
0.2 mm print allowance. For real thread geometry, screws, nuts, washers, bearings and
gears use `bd_warehouse` (`from bd_warehouse.thread import IsoThread`,
`from bd_warehouse.fastener import SocketHeadCapScrew, HexNut, HeatSetNut, ClearanceHole,
InsertHole`; heat-set sizes are like `"M3-0.5-Standard"`, type `"McMaster-Carr"`).

**Recipes** (`from cadkit.recipes import *`, build123d): `rounded_box`, `shell_box` (open
box), `lid` (plate with inner lip, returned in print pose), `boss` / `add_bosses` /
`boss_corners` (insert standoffs), `screw_holes` (clearance, countersunk or counterbored),
`slot`, `hex_pocket`, `chamfer_bottom`. `models/enclosure_box.py` shows them together.
Reach for these before building a box or standoff from primitives.

**Images and SVGs** (`from cadkit.image import *`): `trace("logo.png", width=60)` turns a
logo, sketch or photo silhouette into a CrossSection (holes kept); `svg_shape("x.svg",
width=80)` loads an SVG's paths; `heightmap("photo.jpg", width=100, height=3, base=1)`
makes a relief slab or lithophane (`invert=True`) as a Manifold. When the user gives an
image, run `cad trace image.png --width 60` first and look at the outline preview it
writes before modeling with it. build123d models can also use `import_svg`.

**Multi-part fit.** For a dict return, define `assembly(p)` giving each part's move from
print pose to assembled pose, `{"lid": (dx, dy, dz, rx, ry, rz)}` (degrees, rotation about
the part's own origin first). The build then reports interference volume or the smallest
gap for every pair, and fails on overlap. Model lids and covers in their print pose and
let `assembly` flip them.

**Text.** build123d: `emboss_text(part, "M3", size, depth, at=(x, y, z_top), engrave=False,
mirror=False)` from `cadkit.cad`, or `text_solid(...)` to place yourself. manifold:
`text("Mold 7", size, bold=True, mirror=True)` from `cadkit.relief` gives a CrossSection
for `extrude`/`grow`/`drafted`. Cap height >= 5 mm, raised 0.6 mm (3 layers), bold for
small sizes; mirror text on mold floors.

## Printers

The user prints on a **Bambu Lab A1** (default, 256 x 256 x 256 mm bed) and an
**A1 mini** (180 x 180 x 180 mm). Pass `--printer a1mini` to build, slice and measure
when a part is for the mini; it sets the bed check and the Bambu Studio presets.
Definitions live in `cadkit/printers.py`. When the user doesn't say which printer, use
the A1 and keep parts under 175 mm so they also fit the mini when possible.

`cad slice` uses Bambu Studio's own CLI and system presets, so the time and filament are
what Bambu Studio will show, and it writes `output/<name>/<name>_<printer>.3mf`: a sliced
project the user opens in Bambu Studio and sends to the printer as is. Hand that 3MF to
the user along with the STL. `--filament "Bambu PETG Basic"` picks another Bambu filament
preset; `--layer-height` picks the matching Bambu quality preset (0.08 Extra Fine, 0.12
Fine, 0.16 Optimal, 0.20 Standard, 0.24 Draft, 0.28 Extra Draft).

Bambu A1 series design notes (0.4 mm nozzle, 0.42 mm line width, 0.2 mm layers):
- Wall thicknesses at multiples of 0.42 mm print cleanest: 0.84, 1.26, 1.68, 2.10.
  Heights at multiples of 0.2 mm; put fine horizontal detail on top faces.
- Textured PEI plate: the bed face comes out matte-textured; it is not a show face.
  Elephant's foot compensation (0.075 mm) is on, so no need to chamfer the bottom edge
  for that reason alone.
- No enclosure: design for PLA/PETG/TPU; ABS/ASA warp over ~100 mm.
- Bambu's default 15% sparse infill, 2 walls, 3 top/bottom layers. Structural parts:
  raise `--infill` or design thicker walls rather than relying on infill.

## Design rules (3D printing)

- Units are millimetres. Z is up. The part sits on Z=0 **in the orientation it prints**,
  with a flat base. The build reports flat base area and overhang area; aim for 0 overhang.
- Minimum wall 1.2 mm (2+ mm for anything structural); minimum embossed detail 0.8 mm wide.
  The build samples wall thickness over the surface and reports the thinnest spots;
  drafted ribs get thinner toward the tip, so check the rib width at the top, not the base.
- Fits: 0.2 mm clearance per side for sliding fits, 0.1 mm for press fits. Holes print
  ~0.2 mm undersize.
- Molds for cement/plaster/resin are cast face-down: a rib on the mold floor becomes a
  groove in the casting, a pocket becomes a raised area. Draft every wall the casting
  touches: about 2° on walls and 8-10° on ribs. Mirror any text or asymmetric art, since
  the casting is the mirror image of the mold floor.
- Keep STLs under 25 MB (Tinkercad's import limit). Under 300k triangles keeps Tinkercad
  responsive; use `--fast` or coarser curves if a model gets heavier. Lattice-filled
  parts are inherently heavy (hundreds of thousands of triangles); Bambu Studio copes,
  Tinkercad may not.
- The report's `enclosed voids` (sealed pockets, lattice cells) are fine: slicers print
  them hollow. `bodies` > 1 means genuinely separate pieces.

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
- SDF: write functions with numpy ufuncs (`np.sqrt`, `np.maximum`...) so the grid is
  evaluated at once; `math` functions force a slow point-by-point path. An open lattice
  band thinner than ~2 cells breaks into pieces; closed-skin `lattice_fill` is robust.
  `from build123d import *` shadows single-letter names like `M` (it is a unit).
- Mesh cleanup and float32 rounding are handled in `cadkit/mesh.py`; if a build reports
  NOT watertight, look for coplanar or touching geometry in the model first.

## Layout

```
cadkit/          harness: __main__ (CLI), mesh (convert/clean/check), render (preview), cad + relief helpers
models/          one script per object (_template.py is the starting point); commit these
output/          generated files (gitignored); rebuilt from models/
scripts/setup.py one-step install + self-test
cad, cad.cmd     CLI wrappers (macOS/Linux/Git Bash, Windows)
docs/            README images
```

Python 3.12-3.14 (numpy 2.5 needs >=3.12, build123d needs <3.15). Dependencies are
pinned in `requirements.txt`; when upgrading, re-run `cad selftest` and update the pins.
