# Enhancement roadmap: intricate, accurate, prompt-driven models

Research date: 2026-10-24. Everything marked **verified** was run on this machine
against the current `.venv` (build123d 0.13.0, manifold3d 3.5.4, trimesh 5.2.0).

## Where we stand

The harness is ~700 lines: two kernels, a mesh checker (watertight, bodies, flat base,
overhang area, bed fit), a 5-view software renderer, and one worked example. Claude's
only feedback after a build is the stats block and the preview PNG.

The 2026 text-to-CAD benchmarks all point the same way: models that *run code and
check geometry as they go* beat models that write a script blind. build123d-mcp reports
a CADGenBench score jump from 0.360 to 0.457 and validity from 88% to 100% from feedback
alone (self-reported). Text2CAD-Bench finds that scripts which execute still often
produce the wrong shape, and that sweep/loft/shell are where LLMs fail most. CADTestBench
shows executable per-model tests both grade and *guide* generation.

So the highest-leverage work is not a new kernel. It is making every build tell Claude
more, earlier, and letting the model script declare what "correct" means.

## Tier 1: close the feedback loop (do first)

### 1. Measurement API and spec checks in the model script (**done in Sprint 2**: `cadkit/measure.py`, `cadkit/checks.py`, `cad measure`)
- Add `cadkit.measure`: bounding box, volume, centroid, distance between two faces or
  points, hole finder (cylindrical faces: diameter, axis, depth), thickness at a point,
  min/max Z of a selection. Works on build123d shapes and on the final trimesh.
- Add an optional `CHECKS` list to the model contract, run by `cad build` after
  `build()`, failing the build with a plain-language message:
  ```python
  CHECKS = [
      dims(x=(119, 121), y=(119, 121), z=(29, 31)),
      hole(d=6.4, tol=0.2, count=4),
      wall_min(1.2),
      flat_base(min_area=2000),
      fits_bed(),
  ]
  ```
  This is the CADTestBench idea applied locally: the prompt's requirements become
  assertions, and a passing build means the geometry matches intent, not just that
  the code ran.
- Print the measurements in `report.txt` so the model sees numbers, not just a picture.

### 2. Wall thickness and minimum feature check (**verified**, **done in Sprint 1**)
- `trimesh.proximity.thickness` (ray method) on 3000 sampled points took 1.4 s on the
  butterfly mold once `rtree` is installed. Add `rtree==1.4.1` to `requirements.txt`.
- Report min and 5th-percentile thickness; warn below 1.2 mm; list the worst locations
  so Claude knows *where* the wall is thin. Paint thin regions yellow in the preview.

### 3. Richer previews (**sections, dimensions and tinting done in Sprint 1**; custom view angles, zoom and the HTML viewer remain)
- Dimension overlays on Top and Front tiles (overall X/Y/Z, plus any dimensions a
  model names via `ANNOTATE`).
- Cross-section tiles: `tm.section()` is sub-second (**verified**). Default to one
  section through the centroid on each axis for anything with internal cavities
  (molds, enclosures, holes), plus `--section y=0` on the CLI.
- Colour overhang faces red and thin faces yellow instead of only reporting areas.
- `--view az,el` and `--zoom x,y,z,r` so Claude can ask for a specific angle or a
  close-up of a detail it cannot confirm from the sheet.
- Optional: a single-file three.js viewer written next to the STL
  (`<name>_view.html`) so the user can orbit it in the browser pane, and Claude can
  screenshot arbitrary angles there.

### 4. Slicer integration (**verified**, **`cad slice` done in Sprint 1**; 3MF export remains)
- PrusaSlicer's console binary slices headlessly in about 5 s and the G-code header
  carries the key numbers:
  ```
  "C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe" --export-gcode --layer-height 0.2 --fill-density 15% --support-material --output out.gcode model.stl
  ```
  gave `estimated printing time = 7h 22m 26s`, `filament used [mm] = 32709.53`
  for the butterfly mold. `--info model.stl` also reports `manifold = yes` and
  part count, a free second opinion on our watertight check.
- Add `cad slice models/x.py [--profile <ini>]`: print time, filament mm/g (grams need
  a filament profile with density), support volume, layer count, and a warning when
  support is generated at all. Put a one-line summary in `report.txt`.
- Bambu Studio is also installed and reads 3MF with per-object filament settings.
  trimesh exports 3MF (**verified**), so multi-part dicts can ship as one 3MF with
  parts pre-arranged and coloured. Make `--3mf` an export option.

## Tier 2: expand what can be modeled accurately

### 5. SDF / implicit kernel via manifold3d `level_set` (**verified**)
- A 40 mm gyroid lattice (half-mm edge length, 518k triangles) built in 3.1 s and
  came out as a valid manifold. No new dependency.
- Add `cadkit.sdf`: sphere/box/capsule/torus primitives, smooth union/subtract/
  intersect, twist/bend/repeat, gyroid/Schwarz/diamond lattices, shell, and
  `lattice_fill(solid, cell, wall)` to replace a solid's interior with a lattice.
  This covers organic blends, grips, vases, lattice infill, and "make it lighter"
  requests the B-rep kernel struggles with.
- Keep the triangle budget in check: resolution parameter defaults to the Tinkercad
  300k-triangle guideline, and `--fast` coarsens it.

### 6. Standard parts and hardware tables
- Pin `bd_warehouse` (ISO/Acme/trapezoidal/bottle threads, nuts, screws, washers,
  bearings, gears, O-rings, pipes, flanges) and `gggears` (helical, bevel, planetary,
  cycloid, rack and pinion). Tapped threads and real hardware fits are the most
  common "accuracy" complaint and should never be hand-modeled.
- Add `cadkit/hardware.py`: a plain dict of dimensions Claude otherwise guesses:
  heat-set inserts (M2-M5 hole and depth), screw clearance and tap drill sizes,
  magnets (common disc sizes), 608 bearings, USB-C/USB-A/HDMI cutouts, Pi and
  Arduino board outlines and hole patterns, imperial dowels and lumber, standard
  bottle and jar threads. Each entry carries its printing allowance.
- Pin `gridfinity_build123d` for bins, baseplates and lips; Gridfinity requests are
  frequent and the spec is finicky.

### 7. Image and SVG input
- `import_svg` already works in build123d 0.13 (**verified**), and `svgpathtools` is
  installed. Add `cadkit.image`: `trace(png) -> CrossSection` via `vtracer` (handles
  colour and photos) with a Potrace fallback, and `heightmap(png, height) -> Manifold`
  for lithophanes and stamped reliefs. Users can then hand over a logo, a sketch, or a
  photo and get a faithful outline instead of a guessed one.
- `cad trace image.png --threshold 50` writes the SVG and a preview of the outline so
  Claude can confirm the trace before modeling.

### 8. Text and fonts for both kernels
- build123d `Text` works today. Add `relief.text(string, font, size)` for manifold:
  rasterise with Pillow, trace, mirror automatically for molds. Engraved and
  embossed text is the second most common decorative request.

### 9. Multi-part fit and assembly checks
- For dict returns, compute pairwise intersection volume (manifold `^`) and minimum
  clearance between parts, render an assembled and an exploded view, and fail the
  build on interference. Lids, hinges, snap fits, and sliding drawers stop relying on
  the user to discover a mis-fit after printing.

## Tier 3: prompting and workflow

### 10. Spec sheet before code (**done in Sprint 2**: template docstring + CLAUDE.md step 3)
- Extend `CLAUDE.md` with a short spec template Claude fills in *before* writing the
  script: object, overall dims, mating parts and their exact dims, print orientation,
  tolerances, material, acceptance checks. The checks become `CHECKS`; the spec goes in
  the docstring. This is cheap and directly attacks "code ran, shape is wrong".

### 11. Recipe library
- Ship 8-10 worked models that cover the common shapes and the hard operations:
  enclosure with snap lid, wall bracket with ribs, hook, knob with D-shaft, cable
  clip, mold with draft and relief, lofted handle, swept channel, threaded cap,
  gridfinity bin. Each is parametric, reviewed, and annotated with why it is built
  that way. They are few-shot examples for Claude and base classes in
  `cadkit.recipes` for reuse. Text2CAD-Bench says loft/sweep/shell are where LLMs
  fail, so those recipes matter most.

### 12. Faster iteration
- `--sweep thickness=2,3,4` builds variants in parallel and writes one comparison
  sheet.
- Cache builds by (script hash, params) so re-rendering or re-slicing skips the build.
- `cad lint`: static checks for the gotchas list (coplanar unions, `extrude(taper=)`,
  `Sketch & Sketch`, missing `align`, parts not on Z=0).

### 13. Regression suite and a local benchmark (**regression suite done in Sprint 2**: `tests/expected.json`, `cad selftest --update`; the prompt benchmark remains)
- `tests/`: every recipe and every user model with expected volume, dims, and check
  results, run by `cad selftest`. Helper changes then cannot silently break models.
- Keep a small prompt-to-model benchmark (20 prompts with checks) to measure whether
  CLAUDE.md or helper changes actually improve first-build success.

## Tier 4: external and AI integrations (opt-in)

| Integration | What it adds | Cost / caveat |
|---|---|---|
| build123d-mcp | Reference design for feedback tools (`find_candidates`, `edit_feature`, `compare`) | We run in-process; borrow ideas, do not add the dependency |
| Zoo Text-to-CAD API | STEP from a prompt as a starting point, refined locally via `import_step` | Paid cloud API, mixed quality on complex parts |
| TRELLIS.2 / Hunyuan3D | Organic figurines from a photo ("a model of my dog") that CAD cannot do | 16 GB+ GPU locally or a hosted API; mesh needs cleanup and a flat base |
| Bambu / PrusaLink | Send the 3MF or G-code straight to the printer | Needs printer network setup |
| Tinkercad | No API; keep the clean-STL path | n/a |

## Suggested order and effort

| Step | Items | Effort |
|---|---|---|
| Sprint 1 | 2 thickness, 4 slicer, 3 sections and dimension overlays | done 2026-10-24 |
| Sprint 2 | 1 measure + CHECKS, 10 spec sheet, 13 regression suite | done 2026-10-24 |
| Sprint 3 | 5 SDF kernel, 6 hardware tables + bd_warehouse, 8 text | 2-3 days |
| Sprint 4 | 7 image input, 9 fit checks, 11 recipes, 12 sweep/lint | 3-4 days |
| Later | Tier 4 as demand appears | |

Dependency status: build123d 0.13.0 is the latest release (verified on GitHub), so no
kernel upgrade is pending. New pins proposed: `rtree`, `bd_warehouse`, `gggears`,
`gridfinity_build123d`, `vtracer`.

## Sources

- [build123d-mcp on PyPI](https://pypi.org/project/build123d-mcp/) (feedback-loop tools, CADGenBench claim)
- [Text2CAD-Bench, arXiv 2605.18430](https://arxiv.org/pdf/2605.18430)
- [CADTestBench, NeurIPS 2026](https://neurips.cc/virtual/2026/poster/139514)
- [MUSE benchmark](https://arxiv.org/pdf/2605.28579)
- [Foundation Models for Automatic CAD Generation, arXiv 2607.05573](https://arxiv.org/abs/2607.05573)
- [bd_warehouse docs](https://bd-warehouse.readthedocs.io/en/latest/)
- [gridfinity_build123d docs](https://gridfinity-build123d.readthedocs.io/)
- [build123d external libraries](https://build123d.readthedocs.io/en/v0.10.0/external.html)
- [build123d releases](https://github.com/gumyr/build123d/releases)
- [Manifold samples (gyroid module)](https://manifoldcad.org/docs/html/group___samples.html)
- [VTracer](https://github.com/visioncortex/vtracer)
- [PrusaSlicer CLI thread](https://forum.prusa3d.com/forum/prusaslicer/how-to-get-duration-and-filament-usage-on-cli/)
- [OrcaSlicer MCP](https://glama.ai/mcp/servers/xtblmkh9kb)
- [Zoo Text-to-CAD tutorial](https://zoo.dev/docs/developer-tools/tutorials/text-to-cad)
- [TRELLIS.2 vs Hunyuan3D](https://www.3daistudio.com/blog/trellis-2-vs-hunyuan-3d-differences-explained)
