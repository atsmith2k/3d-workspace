# 3D workspace: generative models for 3D printing

The user describes an object; Claude writes it as a Python model script, builds it,
looks at the renders, iterates, and hands back an STL. Modeling is fully generative:
the user does not model by hand here. If they want to tweak something themselves they
import the STL into Tinkercad (or any slicer/CAD app), so every STL must import cleanly.

Agents other than Claude Code: start at `AGENTS.md` (tool-neutral). Embroidery design
judgement and the failures already hit are in `docs/agents/embroidery-playbook.md`; taking
a design or model live on the shop is `docs/agents/shop-publishing.md`.

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
     the stats. Faces are tinted **red** where they overhang; **yellow dots** mark spots
     where the wall is under 1.2 mm; section tiles show cut material in **orange**.
   - `build.json` (every number above, structured) and `report.txt` (composed from it)
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
   Each slice is recorded in `output/<name>/slice.json` (keyed by the 3MF stem, so A1
   and A1 mini slices coexist) and `report.txt` is recomposed from `build.json` +
   `slice.json`; a slice whose STL has since changed is marked STALE there.
8. Deliver: send the preview PNG, the STL and the `_<printer>.3mf` project to the user
   (SendUserFile), and summarize size, print orientation, print time, supports needed,
   and anything they should know.

Selling a model: `cad publish models/<name>.py --refresh` rebuilds it in full, slices
it for every printer in `PRODUCT["printers"]` whose bed it fits, renders a clean
`<name>_product.png` and `<name>_hero.png` (1600 px, white, no overlays), pulls the
slicer's plate pictures out of the 3MFs, writes `<name>_print_notes.txt` and a
`manifest.json` (schema `cadkit-product/1`) the shop ingests. The manifest's `sellable`
gate wants: watertight single body, every check PASS, no WARNING lines, no fit
interference, a fresh 3MF per supported printer, the product render and notes.
Without `--refresh` it reuses the existing build and slices and only re-slices what
is missing or stale.

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
After changing anything in `cadkit/` run `cad selftest` and
`.venv/Scripts/python -m pytest tests -q`. After finishing a new model,
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
PRODUCT = dict(title="...", category="molds", tags=[...], printers=["a1", "a1mini"],
               cast_material="cement", post_processing=None, sellable=None)  # optional
LICENSE_NOTES = "..."                  # optional; replaces the default licence text
MIN_WALL = 0.4                         # optional; thin-wall warning floor (blades); dict per part ok
SLICE = dict(supports=True, rotate=-90, process=dict(seam_position="back"))  # optional
def checks(p):                         # or a static CHECKS = [...] list
    return [dims(x=p.width), hole(6.4, at=(10, 10)), solid((0, 0, 1)), no_overhang()]
def build(p):                          # p.width, p.style ...
    return part                        # or {"lid": a, "base": b} for multi-part prints
```

`PRODUCT`, `LICENSE_NOTES` and an optional `display(p)` (product-shot poses, like `assembly`;
otherwise overlapping parts are laid side by side) are read by `cad publish` only.
`SLICE` is the model's production print setup, used by every `cad slice`, `--slice` and
`cad publish` (so publish slices with supports when the model needs them): `supports`,
`rotate` (degrees about Z on the plate, e.g. to turn a flat back to the plate's back where
`seam_position: back` hides the seam) and `process` (any Bambu process key: `seam_position`,
`seam_slope_type`, `support_on_build_plate_only`, `wall_loops`...). `--process KEY=VALUE`
adds or overrides keys for one run; slice.json records them as `overrides` and the print
notes list them. Check where a seam really lands in the 3MF's G-code before claiming it.
`MIN_WALL` lowers the thin-wall warning threshold for walls that are thin on purpose
(cutter blade edges); the report still shows the share under 1.2 mm.
`PRODUCT["title"]` may use `{param}` placeholders so `--set` variants get their own titles.
Molds should also define `casting(p)` returning the piece the mold makes (usually
`cast_of(build(p))` from `cadkit.relief`; pass `minus=` a core, `flip=False` for upright
casts); `cad publish` renders it as `<name>_cast.png` in cement grey, since buyers judge
a mold by what comes out of it.
`sellable=None` lets the gate decide, `True` sells despite caveats (they stay listed
as reasons), `False` keeps the model off the shop. The `Spec:` block is parsed into the
manifest, so keep its `key: value` lines (`orientation` ends up in the print notes).
**Cite external dimension sources.** When a fit dimension comes from someone else's
published model, a datasheet or a teardown, say so in the Spec and in `LICENSE_NOTES`,
and set `sellable=False` until that source's licence has been checked
(`models/sequoia_ashtray_bin.py` is the pattern).

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
| **manifold3d** (mesh CSG) | Decorative and organic work: reliefs, molds with artwork, patterns, lots of strokes/spots. Fast and never fails on intricate booleans. STL only. | `from cadkit.relief import *`: `smooth_shape`, `stroke`, `bezier`, `circle`, `ellipse`, `mirror_x`, `grow`, `extrude`, `drafted`, `tapered`, `draft_offset`, `text`, `cast_of` |
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
`slot`, `hex_pocket`, `chamfer_bottom`, `j_hook` (coat/J hook lying on its side),
`knob` (scalloped grip, D-shaft socket or bolt + nut), `cable_clip` (press-in C-clips),
`lofted_bar` / `u_handle` (loft through sections; drawer pull), `swept_channel`
(U-channel along a spline). Worked models: `enclosure_box`, `coat_hook`, `shaft_knob`,
`cable_clip`, `drawer_pull`, `cable_raceway`. Reach for these before building a box,
standoff, hook, knob, clip, handle or channel from primitives, and copy their loft and
sweep setup (section planes from `Plane(origin, x_dir, z_dir)`, `path @ 0` / `path % 0`
for the sweep start) rather than improvising.

**Clay cutters** (`from cadkit.cutter import *`, manifold): `Art(outline, cutouts,
imprints, bars_x, bars_y)` plus `cutter_set(art, p)` gives a cutter and a pusher per size
in `p.sizes` (outline blade, cut-through inner blades, recessed imprint blades, support
bars, pusher prongs). Merge `CUTTER_PARAMS` into PARAMS, set `MIN_WALL = CUTTER_MIN_WALL`,
and use `cutter_checks(p)` / `cutter_assembly(p)` / `cutter_display(p)`. Worked model: `heart_hoop_clay_cutter`.

**Images and SVGs** (`from cadkit.image import *`): `trace("logo.png", width=60)` turns a
logo, sketch or photo silhouette into a CrossSection (holes kept); `svg_shape("x.svg",
width=80)` loads an SVG's paths; `heightmap("photo.jpg", width=100, height=3, base=1)`
makes a relief slab as a Manifold. When the user gives an
image, run `cad trace image.png --width 60` first and look at the outline preview it
writes before modeling with it. build123d models can also use `import_svg`.

**Lithophanes** (`cadkit/lithophane.py`): when the user wants a photo as a backlit print,
`cad litho new photo.jpg --width 100 [--shape flat|arc|cylinder] [--outline
rect|rounded|oval|heart|hexagon] [--set stand=30 ...] [--slice]` copies the photo to
`models/images/`, writes `models/lithophane_<stem>.py` from `models/_lithophane_template.py`
and builds it. Then tune with `cad build ... --set` like any model. Besides the usual
preview, the build writes `<name>_backlit.png`: the target tones beside a simulated
light-box view (Beer-Lambert through the wall plus light scatter). **Look at that one**
to judge tone and contrast; the regular preview is for the shape.
- Tone mapping is Cura's ImageReader lithophane model re-implemented (sRGB -> linear
  luminance, Beer-Lambert `transmittance` per mm, `model="transmittance"`). The default
  `model="perceptual"` spreads CIE lightness evenly over the printable lit range (~5:1
  at 0.6-3.0 mm), so shadows don't merge; `linear` is Cura's other option.
- `min_t`/`max_t` (0.6/3.0) set white/black wall; `gamma` lifts mid-tones; `levels`
  auto-stretches; `sharpen` pre-compensates the light diffusion; `nozzle` (0.4) flattens
  relief ridges and grooves narrower than an extrusion line; `mirror` when the relief side
  faces the viewer; `invert` for a negative.
- Shapes print upright (best detail: the wall traces the relief at nozzle resolution).
  The smooth face is the viewing side. The top frame band carries a 40 deg chamfer so it
  never overhangs; arcs and cylinders stand alone, a flat panel holds by its brim or
  `stand`. A cylinder's `width` is its circumference (diameter = width / pi).
- `SLICE = LITHO_SLICE`: 0.12 mm layers, 100% zig-zag infill (Bambu's default grid
  infill rejects 100%), 6 mm brim. A 100 x 80 panel is ~2 h and 18 g on the A1.
  `SLICE` may now set `layer_height` and `infill` for any model (CLI flags still win).
- `MIN_WALL = LITHO_MIN_WALL` (0.25): white areas are 0.6 mm on purpose, and the
  sampler reads crest shoulders thinner still. The `picture wall >= min_t` check holds
  the real minimum.
- Calibrate a filament: print `models/lithophane_calibration.py` (8 steps 0.6-3.4 mm),
  photograph it on a light box with fixed exposure, then run `cad litho calibrate photo.jpg
  [--crop x0,y0,x1,y1]`. It prints the transmittance to `--set`.
- Customer photos stay `sellable=False` (the template sets it). Models may define
  `extras(p, out, name) -> (files, lines)` for extra build outputs like this one.
  Reference model: `models/lithophane_test_card.py` (generated card,
  `scripts/make_litho_test_card.py`).

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

## Embroidery designs (`cad stitch`)

Same loop as models, for machine embroidery: the user describes a design, Claude writes
`designs/<name>.py`, builds it, looks at the preview, iterates, and hands back the PES
(and the Ink/Stitch SVG, so they can open and tweak it in Inkscape + Ink/Stitch, which
is how they validate and digitise by hand).

1. Clarify only what changes the stitching: finished size, hoop (default `4x4`, 100 x 100
   field; also 5x7, 6x10, 8x8, 8x12), what it sews on (knit/towel/cap/patch), number of
   colours, lettering. Their machine format is PES (Brother) unless they say otherwise.
2. `cad stitch new <name> "<description>"`, fill in the Spec (size, hoop, fabric and
   stabiliser, threads in sewing order, every feature with a size, density limit), turn
   it into `checks(p)`: `size`, `hoop`, `colors`, `max_density`, `long_stitches`,
   `min_feature`, `coverage`, `stitches`, `trims`, `jump_threads`, `short_stitches`,
   `custom`. Always include `coverage(1.0)`: it rasterises the delivered stitches and
   fails on bare fabric inside any fill, satin or outline band, or in a slot between
   elements (a broken border, a fill pulled back too far, a gap between fill sections).
3. Write `design(p)` returning a `Design` (`from cadkit.stitch import *`):
   `d.fill(shape, color, angle, spacing, underlay, method)`, `d.satin(path, width, color)`,
   `d.satin_rails(left, right, color)`, `d.run(path, color, bean=1)`,
   `d.outline(shape, color, width=None|mm)`, `d.text(string, size, color)`. Shapes are
   shapely: `circle`, `ellipse`, `rect`, `rounded_rect`, `poly`, `smooth`, `star`,
   `heart`, `ring`, `text_shape`, `svg("x.svg", width=)`, `trace("img.png", width=)`,
   and `a | b`, `a - b`, `a & b`. Paths: `line`, `arc`, `bezier`, `spline`,
   `circle_path`, `outline_paths`. Any other Ink/Stitch parameter passes through as a
   keyword (`fill_method="contour_fill"`, `stroke_method="ripple_stitch"`...).
4. `cad stitch build designs/<name>.py` writes `output/embroidery/<name>/`: `<name>.svg`,
   `.pes .dst .jef .exp .vp3 .xxx`, `_preview.png`, `build.json`, `report.txt`.
   `--engine inkstitch` (default when installed: Ink/Stitch 3 run headlessly on the SVG)
   or `native` (built-in); `--compare` runs both. `--hoop`, `--set`, `--formats pes,dst`.
5. Read the preview: the sewn render (does it read at size?), the **detail** tile (24 mm
   at thread scale, centred on the densest spot or `--detail x,y` / `DETAIL = (x, y)`:
   row texture, satin edges and corners, travel left on top), the sewing order (jump
   threads red, colour starts numbered), the density map (green fine, yellow dense,
   red too dense). Look at the detail tile on every border corner that worries you.
   Every check PASS, no WARNING lines; the `coverage` report line names the largest
   bare patch. `cad stitch sim <file.pes | designs/<name>.py>` opens the stitchsim
   viewer (`tools/stitchsim`, Rust/egui) to watch it sew stitch by stitch; add
   `--screenshot out.png --at 0.5` for a frame you can read without a window, or
   `--info` for its stats (they match pyembroidery's; `tests/test_stitch.py` checks).
   `--realistic --article tshirt|pants|cap|tote` stages a realistic render on a garment
   (folds, fabric grain, puckering; the cap three-quarter on with the design wrapped
   round its crown; the viewer also has these as a "Realistic" toggle and a "Stage on"
   panel).
   The viewer also flags problem areas (long / tiny stitches, density over 3.5, needle
   pile-ups, untrimmed jumps, missing tie-ins/offs, hoop overflow); `--info` lists
   them, so run `cad stitch sim <file> --info` on files the user brings in. `cad stitch inspect file.pes`
   reports on any stitch file, including ones the user made.
6. Deliver the PES (or their format), the SVG and the preview with SendUserFile; say the
   size, stitch count, colours in order with the nearest Brother thread, sew time, and
   the stabiliser.

Selling a design: `cad stitch publish designs/<name>.py` builds every size in
`SIZES` (label, hoop, longest side: re-stitched per size, never a scaled file) in eight
formats (PES PEC DST JEF EXP VP3 XXX U01), checks every one of them with stitchsim
(`problems 0` required in each, not just the PES), renders `<name>_product.png` (realistic, plain fabric) and garment mockups
(`PRODUCT["mockups"]`), a thread chart, buyer notes, `<slug>.zip` (one folder per size)
and `manifest.json` (schema `cadkit-embroidery/1`, `kind: "embroidery"`, attributes
`hoop_size`, `stitch_count`, `thread_colors`, `formats` for the shop's spec band, suggested
`shop` prices to confirm). `--no-refresh` reuses the size builds. `cad stitch bundle
<collection> --title ... --blurb ...` makes a bundle product (cover grid, contents,
zip of member zips, `bundle_of`) from every design whose `PRODUCT["collection"]` matches.
The shop's `publish-models.mts` only ingests 3D models today; embroidery needs its own
ingest step (and `--archive-pdfs` there would archive non-model products).

Machine readiness (no test sew-out per design; `docs/agents/stitch-reliability-roadmap.md`):
- **Fabric profile**: `FABRIC = "apparel"` (default; also woven, twill, knit, fleece,
  towel; `cadkit/stitch/fabrics.py`, `--fabric` on build) sets every element's pull
  compensation unless it passes `pull=` itself. Satins get it per side by width; fills
  get it in the shape (`fabrics.stretch` along the rows: Ink/Stitch 3.0 ignores fill
  pull compensation). The values are Wilcom's guidelines until calibrated.
- **Registration**: the build moves every stitch where the fabric's pull puts it
  (`fabrics.predict`) and re-runs coverage, joins between elements included; a gap that
  only opens once sewn is a `WARNING registration` line (overlap more: tuck/knockout).
- **Stray thread** (`checks.stray_stitches`): thread over 3 mm sewn outside every shape of
  its colour and not covered later is a `WARNING stray` line. **Lettering**: `d.text`
  under 6 mm is a `WARNING lettering` line.
- **Readiness** (`cadkit/stitch/verify.py`): every build writes `readiness.json` and a
  `ready YES/NO` line: each format read back against the design, checked by
  `cadkit/stitch/validate.py` (decoders and header checks written from the format specs,
  sharing no code with pyembroidery) and by stitchsim, plus the design's checks and
  warnings. `publish` sells only ready sizes (`--require-calibration` also wants a
  calibrated profile). `cad stitch verify designs/<name>.py` re-checks built folders.
- **Calibration**: build `designs/calibration_card.py`, sew that PES once per machine +
  fabric + stabiliser, photograph it flat from above, then
  `cad stitch calibrate photo.jpg --fabric knit --machine "Brother PE800" --stabiliser cut-away`
  (`--dry-run` first) writes `cadkit/stitch/profiles/knit.json`; every later build of that
  profile uses the measured pull and says so.

Collections: `designs/_fall.py` is the pattern (Harvest Hollow): one palette of exact
Brother threads shared by every design, `fit(d, size, hoop)` to draw once in a 100 mm
nominal space and rebuild per size (wide designs may use a hoop's long side: machines
rotate 90 deg, the hoop check accepts it and the buyer notes say so), and
`standard_checks()`. Reusable shapes are in `cadkit/stitch/motifs.py`: `maple_leaf`
(+ `maple_sectors`, `maple_veins`), `oak_leaf`, `leaf`, `acorn`, `pumpkin`, `wheat`,
`petal_ring`, `tendril`, `spiral`, `scallop`, `dots`, `blade`.

Lettering we own: `cadkit/stitch/lettering.py` `block_text("TEXAS", cap, stroke, tracking)`
is a squared athletic block alphabet (A-Z . ' -) drawn for embroidery, so a design needs
no third-party font licence and copies no school's typeface. `designs/_gameday.py` (Game
Day States) is the worked example: state or city name arched over a public-domain state
outline (`designs/_states.py`, Census boundaries), letters on one connected satin-edged
plate with a drop shadow, colourways named by colour only. Collegiate-style designs use
only state and city names: no school names, initials, nicknames, mascots, marks or school
wordmark styles, and no school or conference names in titles or tags (colour + school
references can infringe without any logo).

Digitising rules the checks enforce or the preview shows:
- Sewing order = the order elements are added: background fills first, details on top,
  outlines and lettering last. One colour change per colour where possible.
- Never stack fills: `knockout(lower, *upper)` cuts the lower fill out under everything
  sewn on top, keeping 0.4 mm overlap, and drops slivers. Density over ~3.5 thread
  layers (fill ~1, satin ~1.7) puckers and breaks needles.
- Satin columns 1-7 mm wide (wider snags: use a fill). `outline(shape, color, width=)`
  sews each ring as **one continuous satin column**: jags narrower than 0.4 x width are
  cleaned off first (a satin cannot follow them), corners up to 100 deg are mitred,
  sharper ones fan round a walking pivot. Never border a shape with separate satin
  pieces: every join is a visible break plus a tie-off and a trim. A closed path passed
  to `satin()` is treated as a ring too. (Ink/Stitch mis-sews closed rails, so the SVG
  writes a ring as two open columns meeting exactly at corners, with rungs.)
- A fill under a satin border stops under it: `fill(tuck(shape, border_width))` leaves
  0.6 mm overlap instead of doubling the thread under the whole border (dense corners,
  stiff edge). Fill row spacing 0.4 mm normal, 0.35 for lettering, 0.45-0.5 light.
  Vary fill angles between neighbouring areas so they read apart.
- Nothing narrower than 1 mm in a fill; lettering as fill needs >= 6 mm cap height
  (bold sans), smaller text needs satin lettering in Ink/Stitch.
- Towels: water-soluble topper; knits: cut-away stabiliser; wovens: tear-away.
- Lessons from the fall collection: start satin veins/stems clear of where other
  columns meet (five columns into one hole is a pile-up); keep runs (side veins, grass)
  2 mm inside an outline; never route a bean run back over its own holes (out-and-back
  piles 9 penetrations: zigzag forward or draw grass blades as slim Vs); runs closer than
  3 mm get joined by visible travel unless `trim_after=True`; back layers (petals) should
  be wide enough to fill behind the front layer; leave 1.5 mm between an inner shape
  and its parent's edge (thinner rims are dropped by knockout). The SVG sets Ink/Stitch's
  `min_stitch_len_mm` 0.4 and triangle lock stitches at 1 mm (its default locks are
  ~0.2 mm and the minimum length would merge them away).
- Machine files snap stitches to 0.1 mm, so 0.4 mm rows really sit 0.35-0.42 apart;
  thread spreads to ~0.45 mm and closes them. The preview draws thread at that width.
- Designs from a reference image (realistic animals, portraits): `cadkit.stitch.artwork`
  `Artwork(path, width).tones(k)` cuts the subject out, reduces it to k thread tones,
  merges specks and sub-`min_width` slivers into neighbours and vectorises each tone;
  `art.by_flow(shape, cell)` / `art.angle_in(shape)` give fill angles along the hair /
  grain read from the image. Fewer tones plus small patches at different angles keep the
  texture (a change of stitch direction reads as a change of shade in thread): 4 fur
  tones in ~10 mm patches looked like the 8-tone version at 30 % fewer stitches.
  `designs/grizzly_salmon.py` is the worked example.
- Machine efficiency: every jump that stays is cut, so `pattern.sew_short_jumps` sews
  jumps up to 3 mm (or `design.sew_jumps_mm`, e.g. 8 for many touching fur patches) as
  travel. Ties: the SVG asks Ink/Stitch for locks only where the thread is cut, and
  `pattern.tie_cuts` then checks every run end by stitchsim's own rules and adds a tie
  (0.4-0.8 mm inside the first/last stitch) only where none reads as tied, choosing a
  form that does not stack onto what is there (Ink/Stitch's triangle tie sometimes
  starts late or doesn't close). Run `cad stitch sim <file> --info` after a build:
  it flags missing tie-ins/offs, stacked locks and needle pile-ups.
- Every format must sew the same thing: `pattern.prepare` (run by `write_all`) puts an
  explicit TRIM before every jump that leaves sewn thread (only the PES/PEC writers cut
  jumps by themselves; VP3 has no jump and would sew the move as one long stitch), drops
  doubled penetrations, snaps to 0.1 mm (the VP3 writer drifts on fractional points) and
  sets the machine label. The build then reads every written file back
  (`pattern.verify_files`) and warns, failing the build, where a format differs from the
  design: colours, size, sewn length, stitches over 12.1 mm, untrimmed jumps, doubles.
- Buried travel: `design.hide_jumps_mm = 40` sews same-colour jumps as travel when a path
  between the two pieces lies under stitching sewn later in the same or a darker colour
  (a dark thread under a light fill shows through); `pattern.sew_hidden_jumps` finds that
  path (straight, else routed through covered ground) and keeps the trim otherwise.
  Design for it: lay pieces sewn later over the gaps (one plate under all the letters
  instead of an outline per letter took Game Day from 30-47 trims to 8-15).
- `d.satin(..., taper=True)` for columns that come to a point on purpose (claws, thorns,
  leaf tips): min_feature then only needs the body to be 1 mm wide.
- PES is written as version 6 so exact RGB travels; DST carries no colours, JEF snaps to
  Janome's palette. The `~Brother <name>` in the report is the nearest spool.

Worked examples: `designs/mountain_badge.py` (8-colour layered patch with knockouts and
banner lettering), `designs/monogram_patch.py` (fill, lettering, bean-stitch ring, satin
border), `designs/indiana_state.py` (map outline from public-domain boundary data,
continuous satin border over a tucked fill, script lettering with a knocked-out halo).
Code: `cadkit/stitch/` (`design`, `shapes`, `svg` writer, `engines`, `native`
engine, `pattern` reader/writers, `checks`, `render`, `cli`); tests in `tests/test_stitch.py`.

## Game assets for Cinder (`cad game`)

Third silo, same loop: the user (or a Hive suggestion) describes an asset, Claude writes
`assets/<name>.py`, builds it, reads the preview, iterates, and hands back a GLB that is proven
to load in the Cinder engine (https://cinder.ash10.dev; docs for agents at `/llms.txt`). Plan,
research and phases: `docs/game-assets-plan.md`; judgement and failures:
`docs/agents/game-assets-playbook.md`. Phases 0-4 are built: static props, environment
pieces, a material library, worlds and packs, skinned characters with clips, sound, game UI,
2D sprites, the optional generative step, fonts, and Blender in the loop for high-resolution
assets.

1. Clarify only what changes the asset: what it is for and what it stands next to, size in
   metres, style, whether it is pushed around (dynamic) or scenery (static).
2. `cad game new <name> "<description>"`, fill in the Spec (size, pivot, budget, materials,
   features, use, engine body and collider), turn it into `checks(p)`: `size`, `tris`,
   `materials`, `texture_size`, `pivot`, `tiles`, `custom`.
3. Write `build(p)` returning `Model((mesh, material), ...)` (`from cadkit.game import *`).
   Meshes: `box`, `lathe` (revolve a profile), `disc`, `cylinder`, `torus`, `flat` (hard edges),
   `block` (a box standing on a point), `bevel_box` (chamfered edges, flat faces at full size),
   `wedge` (a ramp), `prism` (extruded outline; `centre=` for stars and arrows), `box_uv`
   (world-scale tiling UVs), `ball`, `capsule` (a limb between two points), `merge`, `.moved/.rotated/.scaled/.with_uv`, and `to_game(part)` to bring a
   build123d / manifold / SDF part over (mm Z-up to metres Y-up). Textures (numpy, tileable,
   seeded): `noise`, `fbm`, `streaks`, `blur`, `tint`, `normal_from_height`,
   `occlusion_from_height`, `orm(occlusion, roughness, metallic)`. Library materials (cached,
   tileable): `stone_blocks`, `flagstones`, `planks`, `iron`. `Material(name, color,
   metallic, roughness, emissive, emissive_strength, base=, orm=, normal=, emission=, alpha=)`.
4. `cad game build assets/<name>.py` writes `output/game/<name>/`: `<name>.glb`,
   `<name>_preview.png`, `build.json` (with a paste-ready `world_snippet`), `readiness.json`,
   `report.txt`, `cooked/`. `--set`, `--json`, `--no-engine` (quick, never ready).
5. **Read the preview**: its four frames are rendered by Cinder itself, beside a 1.8 m orange
   figure for scale, with the UV layout and every texture map. Every check PASS and
   `ready YES`: static checks, `cinder-cook` accepts it, it draws headless with no GPU errors,
   and a solid prop dropped 0.5 m rests where its bounds say.
6. Deliver the GLB and the preview; say the size, triangles, materials, textures, how it is
   used (body, collider) and paste the world snippet.

**Mesh nodes.** `Model((base, mat), (spikes, mat, "spikes"))`: a third item names a node. Parts
of one node become one mesh node of the glTF, so a Mojo game gets a separate entity it can
move, hide or recolour (a flag on its pole, spikes in a trap). The world kit still draws the
file as one model. Each node is its own primitive: count it in `BUDGET["materials"]`.

**Characters** (`KIND = "character"`, `build(p)` returns a `Character`): `sk = biped(height)` is
an 18-bone humanoid (root at the feet as bone 0, relaxed A-pose, facing +Z) or build a
`Skeleton()` with `sk.add(name, parent, head, tail=)`. `ch = Character(sk)`;
`ch.add(mesh, material, bind="head")` binds rigidly, `bind=["upper_arm.L", "lower_arm.L"],
blend=0.045` weights one tube across a joint so it bends smoothly. `palette(name, colors)` +
`swatch_uv(mesh, i, pal)` give a whole character one flat-colour material.
`ch.clips = [Clip.cycle(name, seconds, pose_fn, keys=16)]` where `pose_fn(phase)` returns
`{bone: euler(x=, y=, z=)}` and `{"hips:move": (dx, dy, dz)}`; rest rotations are identity, so
a key is the bone's local rotation. Checks: `clips("idle", "walk", "run")`,
`phase_matched("walk", "run", "foot.L")`; every character also gets `skin` and `clip data`.
The cook must give one `.cskel` and one `.cclip` per clip, and the build **parses the engine's
`.cclip` files back** (name, duration, channels, keys) against what was built. The preview adds
one engine-rendered strip per clip: five moments of the cycle, skinned on the CPU and baked
static. Worked example: `assets/adventurer.py`.

**Sounds** (`KIND = "sound"`, `from cadkit.game.audio import *`, `build(p)` returns
`Sound(samples, loop=False, bus="sfx", spatial=True, streamed=False)`): synthesis at 48 kHz in
numpy. Sources `osc(freq, seconds, "sine"|"saw"|"square"|"tri")` (freq may be a per-sample
`glide(f0, f1, seconds)`), `noise(seconds, seed, "white"|"pink"|"brown")`, `modes(freqs, t60s,
amps, seconds)` (a struck object); envelopes `adsr`, `decay(seconds, t60)`, `fade`; filters
`lowpass`, `highpass`, `bandpass`, `swept_bandpass`; `reverb(x, seconds, mix, wrap=)`,
`place(dst, src, at, gain, wrap=)`, `stereo(x, pan)`, `normalize(x, peak_db)`; for loops
`fit(freq, seconds)` (a pitch that completes whole cycles) and `loop_blend`. Checks
(`from cadkit.game.sound import duration, band, peak, custom`): `duration(lo, hi)`,
`band(lo_hz, hi_hz, at_least=, at_most=)` (the share of energy in a band: how a thud is told
from a chime), `peak(lo_db, hi_db)`. Every sound also gets `format` (the WAV read back by
scipy), `level` (no clipping, not too quiet, no DC), `edges` (starts and ends at zero, no
trailing silence; for a loop, the seam), `channels` (spatial means mono) and `budget`.
The build writes `<name>.wav` (48 kHz 16-bit PCM) and `<name>_preview.png`: waveform and
spectrogram. **Nobody here can listen: read the spectrogram** and write a `band` check for
every claim the Spec makes about how it sounds. The engine step uses the sample game as a probe:
run headless from a scratch folder with the file standing in for its music, Cinder's audio
engine either opens it or reports `audio: could not load` (a garbage-file control runs once per
process). Worked examples: `assets/gem_pickup.py` (bell partials), `assets/chest_open.py`
(layered events), `assets/torch_crackle_loop.py` (a seamless texture loop),
`assets/dungeon_ambience_loop.py` (32 s stereo music loop).

**Game UI** (`KIND = "ui"`, `from cadkit.game.ui import *`, `build(p)` returns `UiSet(ui)`):
`ui = Ui(Theme(...))`, then the engine's own constructors with the engine's own defaults:
`ui.root(anchor, name, offset=)` (anchors `top_left` .. `bottom_right`, `centre`),
`ui.panel(parent, row=)`, `ui.label(parent, text, name=, size=, color=)`, `ui.button`,
`ui.toggle(parent, text, checked)`, `ui.slider(parent, text, value, lo, hi)`; any node field can
be passed or edited (`ui[id]["min_size"] = [260, 44]`). The build writes `<name>.ui.txt` (a
`cinder-scene 1` document, byte for byte what `Ui.to_text` writes), `<name>.theme.json` and
`<name>.mojo` (load code: `Ui.from_text`, the theme, `find` for every named node). Checks:
`has(name, kind)`, `node_at_least(name, w, h)`, `custom`; always: every control named, Latin-1
text with no quotes, and from the engine: the round trip, every node inside 1280 x 720, root
panels not overlapping. **cinder-probe** proves it: `tools/cinder_probe/cinder_probe.mojo` is
our Mojo program, compiled against the engine by `cad game probe build` (needs the Cinder
checkout at `../cinder` or `CAD_CINDER_SRC`, Docker and the `cinder-toolchain-windows` image);
it has Cinder read the document, lay it out, draw it headless and write it back, and reports
every node's rectangle. The preview is the engine's frame beside the same frame with each
rectangle outlined. Rebuild the probe when its source or the engine changes
(`cad game probe status`). Worked examples: `assets/dungeon_hud.py`, `assets/pause_menu.py`.

**Sprites** (`KIND = "sprite"`, `from cadkit.game.sprite import *`, `build(p)` returns
`SpriteSheet(frames, animations=, slices=)`): `Canvas(size)` draws anti-aliased shapes
(`circle`, `ellipse`, `rect(box, radius=)`, `polygon`, `line`) and `.image()` gives straight-alpha
RGBA. The build packs a power-of-two atlas and writes `<name>.png`, `<name>.json`
(`cadkit-sprites/1`: frames, animations with fps, 9-slice borders) and `<name>_quads.glb`, one
unlit quad per frame, which it cooks and draws in Cinder. Checks: `frames(*names)`,
`frame_size(w, h)`, `animation(name, count, fps)`, `nine_slice(name)`, `custom`. This is
**built ahead**: nothing in Cinder 0.1.1 reads a sprite sheet. Worked examples:
`assets/hud_icons.py`, `assets/ui_frames.py` (9-slice), `assets/coin_spin.py` (animation).

**Fonts** (`KIND = "font"`, `from cadkit.game.font import *`, `build(p)` returns
`FontFace(glyphs, family=, tracking=)`): glyphs are shapely shapes on a grid where the cap height
is 10 units and the baseline is y = 0, each with its advance. `block_glyphs(stroke)` is the
block alphabet this workspace owns (`cadkit.stitch.lettering`, A-Z) extended with digits and
punctuation in the same construction, so no third-party typeface is copied. The build writes
`<name>.ttf` (fontTools, 1000 units per em, cap height 700) and `<name>.json`. Lowercase maps
to the capitals and accented Latin-1 letters to their base letter (`unicase`, `fold_accents`),
because Cinder bakes code points 32..255 and anything else is a '?'. Checks: `covers(chars)`,
`stroke_at(px, min_px)` (the thinnest stroke at a size), `distinct("0", "O")` (confusable pairs);
always: valid outlines inside their advance, FreeType (Pillow) loads it and agrees on advances,
and from the engine through cinder-probe: Cinder parses it, bakes 224 glyphs, measures a test
line as expected, and **the engine's pixels match the glyphs** (`ink_match`, at least 70 %
overlap with FreeType's rendering; a different font scores about 50 %). A UI set in a font is
`UiSet(ui, font="block_caps")`: the font asset is built first, and a pack needs both.
Worked examples: `assets/block_caps.py`, `assets/title_screen.py`.

**High-resolution assets: Blender in the loop** (`from cadkit.game import blender as B`). The
other kernels draw hard-surface and low-poly shapes; this one does the high-to-low workflow that
detailed assets are made with. Blender runs headless as a subprocess (`blender -b
--factory-startup --python tools/blender_bridge/bridge.py -- <job>`); meshes cross as arrays
and come back as an ordinary `Mesh` and images, so the asset is still a script and the same
checks and Cinder ladder decide `ready`.
```python
s = B.Session()
hi = s.add(rough_mesh, "high")                       # weld=True joins a hard-edged mesh into one surface
s.modify(hi, B.subsurf(5), B.displace("CLOUDS", scale=0.5, strength=0.16))
lo = s.copy(hi, "low")                                # the game mesh comes from the high one...
s.decimate(lo, 3000); s.shade(lo, sharp_angle=50); s.unwrap(lo)
s.bake([hi], lo, size=2048, maps=("normal", "ao", "curvature", "emit"), cage=0.05, ray=0.2)
r = s.run()                                           # one Blender run, or the cache
low, normal, ao = r.mesh(lo), r.image("normal"), r.image("ao")
```
- Steps: `add(mesh, name, emit=)`, `modify(name, *modifiers)`, `boolean(a, b, operation, materials=)`,
  `join`, `copy`, `remesh(a, voxel_size)`, `decimate(a, tris)`, `shade(a, sharp_angle=)`,
  `unwrap(a)`, `bake(high, low, size, maps, cage, ray, samples)`, `weights(a, skeleton)` (bone-heat
  skin weights; `r.skin(name)` gives joints and weights), `get(a)`. Modifiers: `B.subsurf(levels)`,
  `B.displace(texture, scale, strength)` (CLOUDS, VORONOI, MUSGRAVE, STUCCI...), `B.inflate(d)`
  (move the surface along its normals), `B.bevel`, `B.smooth`, `B.solidify`, or any raw
  `dict(type="<BLENDER MODIFIER>", ...props)`. `B.bake_lowpoly(high, tris, size, maps)` is the
  whole workflow in one call.
- Maps: `normal` (tangent space, glTF's convention; Blender and Cinder both use MikkTSpace, and
  the mesh is triangulated before the bake so the tangents agree), `ao`, `curvature` (0.5 flat,
  bright on convex edges, dark in creases: drives edge wear), `emit` (the emission of the high
  mesh's materials: give a boolean cutter `emit=1.0` and the faces it cuts bake as a mask).
- Paint the colour in world space, not UV space: `texel_maps(mesh, size)` gives each texel's
  position and normal on the mesh and a mask of the UV islands; `noise3` / `fbm3` sampled at
  those positions have no seams; mix by the baked `ao` and `curvature`; `fill_background(img,
  mask)` carries island colours over the empty texels so mips do not bleed. Add `uv_unique()`
  to the checks of anything baked.
- Results are cached in `output/game/.blender/` by a hash of the steps, the input meshes, the
  bridge script and the Blender version: an unchanged asset does not start Blender again (the
  monolith is 47 s cold, instant after). `cad game blender` says which Blender is used
  (`CAD_BLENDER`, else the newest under Program Files, else PATH; installed here with winget).
- Why a subprocess: the `bpy` wheel is pinned to one Python (3.13 for Blender 5.x; this
  workspace is 3.12), a Blender crash cannot take the build down, and no GPL code is imported
  into cadkit. Why not an agent driving a live Blender (the MCP servers): the asset would live
  in a session nobody can rebuild.
- **Order matters.** Big shapes (subdivide, lumps, cracks), then carve, then only fine grain.
  Displacing after carving moves each groove wall along its own normal and smears the cut shut.
- **Exact cut depth**: trim the cutter against an inset copy of the surface
  (`s.modify(inner, B.inflate(-depth)); s.remesh(inner, 0.02); s.boolean(cut, inner,
  materials="INDEX"); s.boolean(hi, cut)`). The remesh matters: an inset rough surface crosses
  itself and the exact boolean returns nothing.
- `ray` must exceed the depth of what is carved, or the bake misses the floor of the cut;
  `cage` must clear the high mesh's bumps. Defaults in `bake_lowpoly` are 8 % and 2 % of the size.
- Have a check for every map (the monolith's rune mask baked empty three times, for three
  different reasons, and the check caught each): mask coverage, mean lean of the normals,
  high-poly triangle count from `r.step("modify", i)["triangles"]`.
- The cache folder is not source: the asset script is. Blender is needed to rebuild from
  nothing, so say `needs: Blender` in the Spec.
- **Sculpted characters.** Lay the body out as `ball`s (scale them for ellipsoids) and
  `capsule(a, b, r0, r1)`s along the bones of a `Skeleton`, in a wide A-pose (arms out, legs
  apart: parts that touch fuse, and bone heat then cannot tell them apart). `s.remesh(hi, 0.03)`
  makes the overlapping parts one closed skin; sculpt, bake, then `s.weights(lo, sk)` on the
  low mesh and `Character(sk).add_skinned(low, mat, *r.skin(lo))`. Add `deforms_cleanly()` to
  the checks: it poses every clip and fails when edges stretch (a vertex on the wrong bone).
  Bone heat spreads a vertex over five or more bones; the bridge takes the fifth-largest
  weight off the top four rather than just keeping them, or neighbouring vertices drop
  different bones and the skin tears (the golem's flank, 4.2x, when its arms went up). An arm
  raised more than about 120 deg at the shoulder stretches past the check: share the lift with
  the chest and elbow. Clips are not part of the Blender cache key: retiming one is instant.
Worked examples: `assets/rune_monolith.py` (500,000 triangles sculpted and carved, baked onto
3,000 with four 2048 px maps), `assets/stone_golem.py` (a 2.4 m character: 588,000 triangles
baked onto 8,000, automatic skin weights, three clips).

**Generated inputs** (`from cadkit.game import gen`): for a look a script cannot draw.
`gen.image(prompt, name="dragon_banner", size=(1024, 1536))` (OpenAI images) and
`gen.sound(prompt, name=, seconds=)` (ElevenLabs sound effects) return arrays;
`gen.material(img, name)` makes a PBR material from a picture, `gen.tileable(img)` makes it
repeat. Rules the code enforces:
- **A build never calls a service on its own.** Inputs are read from `assets/gen/<id>.png|.wav`
  (commit these, like `models/images/`). A miss stops the build with the command that would
  create it: `cad game build <asset> --gen`, one paid call. The services have no dependable
  seed, so the cache is what makes a build repeatable.
- Every input has a record, `assets/gen/<id>.json` (prompt, provider, model, parameters, when,
  `cleared: false`). Changing the prompt under the same name is an error, not a silent reuse.
- **Nothing generated ships until a person clears it.** The asset can be `ready YES`; `cad game
  pack` still refuses it. `cad game gen clear <id> --by NAME --note "what was checked"` is for
  the user, after looking at the picture and the provider's terms. **Claude never clears one.**
- Keys: `OPENAI_API_KEY`, `ELEVENLABS_API_KEY` in the environment or the git-ignored `.env` at
  the repo root (`cad game gen keys` says which are set). Never ask for a key in chat, never
  write one to a file that is committed, a log or a manifest.
- Write prompts that ask for what the mesh needs (front-on, evenly lit, edge to edge, no text)
  and that name no real person, brand, house or nation.
`cad game gen list` shows every input and whether it is cleared. Worked example:
`assets/wall_tapestry.py`.

**Packs.** `cad game pack packs/<name>.py [--refresh]` bundles every asset whose
`PRODUCT["collection"]` matches the script's `COLLECTION` into `output/game/packs/<name>/`:
`assets/*.glb`, `previews/`, `worlds/demo.world`, `manifest.json` (schema `cadkit-game/1`: per
asset bounds, triangles, textures, `engine_use`, `rest_y`, world snippet, cook logical paths,
licence, engine version verified against), `AGENTS.md` (a paste-ready snippet per asset) and
`ATTRIBUTION.md`. It rebuilds members that are missing, stale or not ready and refuses a pack
with a member that is not ready. The script's `demo(w)` builds the demo with
`cadkit.game.world.World`: `w.place(asset, at=(x, floor_y, z), yaw=, name=, body=, **components)`
stands a pack asset on a floor point using its `rest_y`, body and collider; `w.add(name,
light=dict(...), player=dict(...))` adds anything else. The pack is `ready` only when
`cinder-play --check` passes and the headless run loads every placed model with no GPU errors
(and is won, with `DEMO = dict(seconds=, autopilot=True, expect_won=True)`). `SHOTS = [dict(name,
position, target)]` adds beauty frames from placed cameras (the world without its player);
**read them and `<name>_contents.png`**. `cad game install <name> --to <game dir> [--cook]`
copies a ready pack into a game. `DEMO["settle"] = dict(max_move=0.25, free=[names])` makes the
demo a stacking test: every dynamic body must end the run within `max_move` metres of where it
was placed, and the manifest lists where each one ended. `PRODUCT["gameplay"]` (a dict: bounce
surface, hazard node, collider wanted) and `PRODUCT["notes"]` travel into the manifest and
`AGENTS.md`: that is how an asset tells a game what the engine cannot read from a model.
Worked examples: `packs/dungeon_kit.py` + `assets/_dungeon.py` (shared grid, stone and checks
for 12 pieces) and `packs/sandbox_kit.py` + `assets/_sandbox.py` (one 16-tile atlas for a whole
kit, `tile(mesh, T.RED)`; built from ten Hive suggestions).

`cad game list`, `cad game engine` (which Cinder package verifies; `CAD_CINDER`, else
`../cinder/dist/cinder-windows-x64`), `cad game schema` (contract, checks, conventions and the
request format as JSON: start there as an agent).

Rules the checks hold, and what the engine taught us:
- Metres, Y up, -Z forward, counter-clockwise front faces. Texture row 0 is the top (v=0).
- **Pivot**: a dynamic prop's origin is the centre of its bounds, because the world kit centres
  box and sphere colliders on the entity (an origin at the base sinks it half its height: the
  drop test fails). Static pieces sit on Y=0 with the origin at the base centre; floor tiles
  have it on the top face (`pivot("top")`, walking surface at Y=0); wall-mounted pieces on the
  back face (`pivot((0.5, None, 1.0))`, hanging toward -Z). `ENGINE["rest_y"]` is the origin's
  height when the asset is in place (default: standing on its lowest point).
- Kits: 2 m grid, walls centred on cell edges, one world-projected stone texture
  (`box_uv(mesh, 1 / GRID)`) so courses run on across neighbouring pieces.
- The autopilot walks straight lines: lay a demo's route down one axis and keep dressing off it.
- Emissive strength over about 1.5 tone-maps toward white (a red gem turns pink): keep the
  colour saturated, the strength low, and add a point light in the world for the cast light.
- Never name a module after a function the package exports (`materials` the check was
  shadowed by `materials` the module: the library is `matlib`).
- Cinder reads POSITION, NORMAL, TANGENT, TEXCOORD_0/1 and skin attributes; metallic-roughness
  with base, metallic-roughness, normal, occlusion and emissive maps; `KHR_texture_transform`
  and `KHR_materials_emissive_strength`. No vertex colours, no other extensions. It generates
  tangents and LODs itself: never author them.
- With an `orm` texture set `metallic=1.0, roughness=1.0` (factors multiply the texture).
- One material is one draw call: pack a prop into one atlas where you can (the crate and
  barrel do). Textures are powers of two; 512 px per metre is the default density.
- Base names are snake_case and unique: `cinder-cook` derives the cook prefix from them.
- Source files are the deliverable. `cooked/` is a cache for one engine build (cooked formats
  have no migrations).
- `lathe` faces to the right of travel: profile bottom-to-top faces outward, top-to-bottom
  faces the axis (a rim's inner wall).
- Cinder 0.1.1 leaves any dropped body about 15 mm inside the floor, its own primitives
  included; the drop test's tolerance allows for it.
- **`ok`, `gpu_errors 0` and a counted model do not mean anything was drawn.** Every build
  renders the stage with and without the asset and compares: a static asset that changes no
  pixels is a blocker.
- **Cinder 0.1.1's world kit does not draw skinned models** (it attaches no animator, so there
  is no joint palette; the Khronos CesiumMan is invisible too). A character's frames are
  therefore static bakes of its bind pose and clips, the report says so, and its pack notes
  tell a game to give the spawned mesh an `AnimatorRef` from Mojo. Never place a skinned asset
  in a world-kit demo.
- Characters face **+Z** (the kit turns a player model so +Z points where it walks), stand
  with their feet at the origin and animate in place. Left is +X. Phase 0 of every gait is the
  left foot's strike, so cycles blend on a shared phase.
- Rotating a leg about +X by a positive angle swings the foot to -Z (backward); knees bend
  with a positive X rotation of the lower leg, elbows with a negative one.
- A loop variable named `path` inside `write_glb` once redirected the output file: do not
  shadow arguments in long functions.
- The world kit's colliders are box, sphere and mesh, and a mesh cannot be dynamic. So a
  cylinder ships with a box collider (it stacks, it does not roll), a ramp ships kinematic with
  a mesh collider, and a tree ships with no body (any kit collider would make its canopy
  solid). Say what collider is wanted in `PRODUCT["gameplay"]` for Mojo games.
- A flat-colour kit fits one small atlas of tiles (512 px, sixteen 128 px tiles, 0.9 MB for 15
  models). Cinder still uploads it once per model.
- Sound: one-shots are mono and spatial; music and ambience are stereo, not spatial, streamed.
  A loop is the whole file (Cinder has no loop points): give every tone a `fit` pitch, place
  events with `wrap=True`, use `reverb(..., wrap=True)`, and shape noise in the frequency
  domain so it is periodic. Peaks: effects about -3 dBFS, things heard constantly (footsteps,
  UI ticks) -6 to -8, beds -8.
- Never put a steady tone through a stereo reverb: each channel gets an arbitrary phase and
  left and right cancel on a mono speaker (the music loop's drone measured -0.3 correlation).
  Send only the events through it and keep the bed dry; check `corrcoef(left, right) > 0.3`.
- `cinder.audio` `SoundDesc(path, bus, streamed, looping, spatial)`: streamed comes before
  looping. The world kit has no audio components: sounds are played from a Mojo `Game`.
- **Cinder 0.1.1 draws alpha-masked and alpha-blended materials opaque**: `forward.wgsl` reads
  the alpha mode with `u32()` where the material wrote integer bits, so it is always 0. Only the
  depth pass cuts the mask, which is why a masked quad looks right in front of something drawn
  later and wrong on its own. Do not rely on alpha in a model until the engine is fixed (it is
  in Cinder issue "Sprites: ..."); sprite proof quads show a black square behind the art.
- A UI theme is not in a UI document (the engine does not serialise it): node colours travel
  in the document, the theme's hover / pressed / accent / focus colours in `<name>.mojo`.
- Do not name a Mojo argument `out` (reserved); a docstring summary starts with a capital.
- An asset script's `from cadkit.game import *` brings names, not submodules (`__all__`): a
  script with no `checks()` once picked up the `checks` module and the build tried to call it.
- OpenAI image model ids change: `gpt-image-1` was gone by 2026-11 and `gpt-image-2` is the
  default here. When a call says the model does not exist, list `GET /v1/models` and set
  `CAD_GEN_OPENAI_MODEL` or the default in `gen.py`. A refused request costs nothing.
- **Installing a UI font in Cinder 0.1.1**: there is no public setting. The UI renderer uploads
  a glyph atlas the first time a size is drawn and never again, so a font swapped in after the
  first frame is laid out with the new metrics and drawn from the old texture: text-shaped
  garbage that measures correctly. Install it in `Game.start`, before anything is drawn:
  `app._ensure_ui_renderer()` then `app.ui_renderer.value().fonts = FontCache(font^)`.
- **Numbers that pass over a wrong picture** happened three times (a skinned model nobody drew,
  a font drawn from the wrong atlas, a tapestry whose picture was fine and whose mesh was not).
  Each time the fix was a check that looks at pixels. When adding a kind, add one.
- Text on a HUD or title needs its own ground: a panel behind it of alpha 120 or more. Pale
  text over an unknown scene disappeared on the first title screen.
- Not yet run against a real service: ElevenLabs sound in the generative
  step. Cinder has no sprites and its UI draws no images; see the plan for what is built ahead.

Worked examples: `assets/wooden_crate.py` (atlas, raised frame, dynamic), `assets/oak_barrel.py`
(lathe, hoops in geometry and texture, recessed heads), `assets/iron_lantern.py` (two
factor-only materials, emissive, static), `assets/spike_trap.py` (a named mesh node),
`assets/robot_character.py` (rigid parts on the shared biped). Code: `cadkit/game/` (`model`, `mesh`, `texture`,
`matlib`, `rig` (skeletons, skinning, clips, FK), `audio` (synthesis), `sound` (sound build, checks,
spectrogram), `ui` (UI documents, themes), `sprite` (drawing, atlases, 9-slice), `font` (glyphs, TTF writer),
`gen` (generated inputs), `blender` (headless Blender sessions; the bridge is
`tools/blender_bridge/bridge.py`), `gltf` writer + independent reader, `engine`, `checks`, `build` ladder, `world`,
`pack`, `render`, `cli`);
tests in `tests/test_game.py`, `tests/test_game_rig.py`, `tests/test_game_sound.py`,
`tests/test_game_ui.py`, `tests/test_game_font.py`, `tests/test_game_gen.py` and `tests/test_game_blender.py` (engine tests skip without a Cinder package, probe tests without the probe).
`tools/cinder_probe/` holds the Mojo probe.

## Printers

The user prints on a **Bambu Lab A1** (default, 256 x 256 x 256 mm bed) and an
**A1 mini** (180 x 180 x 180 mm). Pass `--printer a1mini` to build, slice and measure
when a part is for the mini; it sets the bed check and the Bambu Studio presets.
Definitions live in `cadkit/printers.py`. When the user doesn't say which printer, use
the A1 and keep parts under 175 mm so they also fit the mini when possible.

`cad slice` uses Bambu Studio's own CLI and system presets, so the time and filament are
what Bambu Studio will show (each preset goes in with its `inherits` chain and `include`
templates merged, `_flatten_preset`; passed raw, the CLI silently falls back to generic
G-code, a 200 mm bed and a 2 mm3/s flow limit), and it writes `output/<name>/<name>_<printer>.3mf`: a sliced
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
  Downward faces in strips under 2.5 mm wide (a groove roof, a lip over a slot, a short
  bridge) are reported separately as fine and do not fail `no_overhang()`.
- Minimum wall 1.2 mm (2+ mm for anything structural); minimum embossed detail 0.8 mm wide.
  The build samples wall thickness over the surface and reports the thinnest spots;
  drafted ribs get thinner toward the tip, so check the rib width at the top, not the base.
  Feather edges of countersinks, chamfers and fillets are not counted as walls. A lip
  left above a groove is `wall - groove_depth` thick: size the wall for it.
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
- build123d `Cone(bottom_radius, top_radius, height)`: bottom first. A countersink that
  opens at the top face is `Cone(shank_r, head_r, depth)`; swapping them makes an
  undercut the screw head cannot seat in, and a 90 deg cone sits just under the 45 deg
  overhang threshold so only `hole(..., csk=head_d)` catches it. Prefer
  `recipes.screw_holes(..., csk=True)`.
- build123d: `extrude(taper>0)` goes through LocOpe_DPrism and can **segfault** on thin or
  traced shapes; use `draft_extrude` from `cadkit.cad`. Spline faces built from clockwise
  points face -Z and won't fuse with other faces; `closed_spline` fixes that.
- manifold `drafted` stacks slices, so a tall drafted wall comes out as visible stair
  steps (and the casting copies them). Use `tapered` for body walls and round pins;
  keep `drafted` for spiky art and for domes (one slice per 0.2 mm layer).
- build123d tapers on large, intricate art (many joined strokes) are slow (minutes) and
  fail often. Do that kind of work in manifold3d instead.
- SDF: `build_sdf(..., snap=True)` moves every vertex onto the exact surface (level_set
  meshes a trilinear interpolation of the grid, leaving vertices up to ~0.2 mm off and a
  mottled skin). Features narrower than ~3 grid cells (grooves) alias into a rope texture
  along their length: give them a round-bottomed profile >= 1.6 mm wide at edge 0.6, or cut
  them as mesh sweeps. Dense capsule-swept rings (hundreds of hulls) leave sub-0.01 mm
  triangles that Bambu Studio welds into non-manifold edges: the build then says
  `bambu kept cadkit's STL` and the slice can come out ~10% slower. Treat that line as a
  defect, not a note.
- SDF: write functions with numpy ufuncs (`np.sqrt`, `np.maximum`...) so the grid is
  evaluated at once; `math` functions force a slow point-by-point path. An open lattice
  band thinner than ~2 cells breaks into pieces; closed-skin `lattice_fill` is robust.
  `from build123d import *` shadows single-letter names like `M` (it is a unit).
- Full builds re-export every STL through Bambu Studio's CLI (`slicer.bambu_export_stl`,
  `--arrange 0 --orient 0` so the pose and coordinates stay put): the shipped file is the
  mesh Bambu Studio itself loads and repairs, and the checks run on it. The build line
  `bambu    kept cadkit's STL: ...` means its export was rejected and why.
- Mesh cleanup and float32 rounding are handled in `cadkit/mesh.py`; if a build reports
  NOT watertight, look for coplanar or touching geometry in the model first.
- manifold3d can return a solid that touches itself at a vertex or edge (two indices,
  one position): valid for manifold, but slicers weld by position and then flag
  "reversed faces" / non-manifold edges. `mesh.unpinch` pulls such vertices 0.004 mm
  apart before export and the watertight check welds by position like a slicer; a
  `note: separated N self-touching vertices` line in the build output means it fired.

## Layout

```
cadkit/          harness: __main__ (CLI), mesh (convert/clean/check), render (preview + product),
                 outputs (build.json / slice.json / report.txt), publish (manifest, notes, gate)
models/          one script per object (_template.py is the starting point); commit these
assets/          one script per game asset (_template.py); `cad game build`
packs/           one script per asset pack (collection, demo world); `cad game pack`
cadkit/game/     game-asset harness (meshes, textures, glTF writer, Cinder engine adapter, ladder)
designs/         one script per embroidery design (_template.py); `cad stitch build`
cadkit/stitch/   embroidery harness (Design, stitch engines, PES/DST writers, checks, preview)
tools/stitchsim/ Rust embroidery simulator (PES/DST/EXP/JEF viewer); `cad stitch sim`
output/          generated files (gitignored); rebuilt from models/
tests/           expected.json (selftest) and pytest suite (`.venv/Scripts/python -m pytest tests -q`)
scripts/setup.py one-step install + self-test
cad, cad.cmd     CLI wrappers (macOS/Linux/Git Bash, Windows)
docs/            README images
```

Python 3.12-3.14 (numpy 2.5 needs >=3.12, build123d needs <3.15). Dependencies are
pinned in `requirements.txt`; when upgrading, re-run `cad selftest` and update the pins.
