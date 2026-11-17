# Game assets for Cinder: research and plan

Status: Phase 0 built and its gate passed on 2026-11-17 (crate, barrel and lantern `ready YES`,
`tests/test_game.py`). Phase 1 built and its gate passed the same day: the 15-asset Dungeon Kit
pack (12 new pieces) is `ready YES` and its demo world is won headless on autopilot. Phase 2 built
and its gate passed the same day: the `adventurer` biped cooks to one `.cskel` and three `.cclip`,
and walk and run strike with the left foot at the same phase. Phase 3 built and its gate passed
the same day: ten sound effects and a seamless 32 s music loop, each opened by Cinder's audio
engine. Phase 6's test round ran early, on 2026-11-17: the ten Hive suggestions were built as
the 15-model Sandbox Kit (section 11). Phase 4 built and its gate passed the same day: a HUD and
a pause menu round-trip through Cinder's own `Ui.from_text` / `Ui.to_text`, and three sprite
sheets are drawn in-engine on quads (section 12). Fonts followed as their own phase (section 14). Phase 5 built and its gate
passed the same day once keys were set: one real generated texture, rebuilt from cache, recorded as
uncleared and refused by a pack (section 13).
Third silo of this workspace, beside 3D-print models (`cad build`) and embroidery (`cad stitch`):
`cad game`, which turns a plain-language request into a checked, engine-verified asset for the
Cinder engine (https://cinder.ash10.dev, repo `F:\git\cinder`).

## 1. What Cinder actually consumes (0.1.1, docs at engine commit 18d5454)

| Asset kind | What the engine loads today | Constraints a producer must meet |
|---|---|---|
| Static mesh | glTF 2.0 `.gltf` / `.glb` through cgltf; `cinder-cook` turns it into `.cmesh` `.cmat` `.ktx2` | Triangles only. Right-handed, Y up, -Z forward, metres, CCW front faces. Vertex = position, normal, tangent, uv0, uv1 (no vertex colours). LODs are built by the engine: do not author them. |
| Material | glTF metallic-roughness + `KHR_texture_transform` (one transform for every map) + `KHR_materials_emissive_strength` | Five slots: base colour, metallic-roughness, normal, occlusion, emissive. Alpha opaque / mask / blend. Nothing else (no transmission, clearcoat, sheen, Draco, meshopt, quantization). |
| Texture | PNG/JPEG in the glTF; cooked to KTX2 (BasisU: UASTC for normals, ETC1S otherwise), mips generated | Base colour and emissive sRGB, the rest linear. Normal maps X,Y,Z in RGB, glTF (+Y) convention. Max 8192 px a side. |
| Skinned mesh + clips | glTF skins and animations; cooked to `.cskel` and `.cclip` | <= 256 bones including non-joint ancestors, 4 influences per vertex, <= 8 morph targets. Linear, step, cubic. Looping and events are set in game code, not in the file. Blended clips need matching foot phase. In-place clips are the safe default (root motion strips X/Z of bone 0). |
| Sound | WAV, FLAC, MP3, Vorbis through miniaudio | Engine mixes at 48 kHz stereo. Loop = whole file. Effects decoded at load, music streamed. Bus names are the game's (`sfx`, `music` in the sample). |
| Font | TTF/OTF through stb_truetype, baked per pixel size | Printable ASCII + Latin-1 only, no kerning, no wrapping. |
| Game UI | A node tree (panel, label, button, toggle, slider), `UiTheme` colours and sizes, readable and writable as a `cinder-scene` text document | **No images, no atlases, no 9-slice, no text fields, no scrolling yet.** |
| World | `cinder-world 1` text file: entities with `shape`, `model` (a glTF path), `body`, `light`, `player`, `pickup`, `trigger`, `door`... | No audio, UI or animation components, no hierarchy, no prefabs in world files yet. |
| Prefab | A `cinder-scene 2` document; assets referenced by game-defined source names | Only as portable as the names the game registers. |
| Sprites, billboards, decals, particles, terrain | **Do not exist and are not on the roadmap.** | - |

Cooked formats have no migrations (a version bump means re-cook), so **source files (glTF, PNG,
WAV, TTF) are the deliverable and cooked files are a cache** tied to one engine build.
`cinder-cook` derives the logical prefix from the file's base name: base names must be unique
across a pack and contain no spaces.

## 2. What was proven on this machine (2026-11-17)

- The Windows package at `F:\git\cinder\dist\cinder-windows-x64` runs here on the RTX 3070 Ti.
  `cinder-play.cmd x.world --headless --frames 5 --screenshot out.png` loaded the Khronos
  DamagedHelmet and wrote a correct frame and a JSON report in 2.6 s (`ok: true`, `gpu_errors: 0`).
- A crate generated entirely in Python (numpy albedo + ORM + normal map, trimesh GLB export, 36
  vertices) loaded in the same way with a dynamic physics body, and `cinder-cook.cmd` cooked it
  (1 `.cmesh`, 1 `.cmat`, 3 `.ktx2`). `bin/cinder-cook.exe` is in the package although the
  Windows docs do not mention it.

So the central design decision is safe: **the engine itself is the verifier and the preview
renderer.** No second renderer to maintain, and "it loads in Cinder" is tested, not assumed.

## 3. Decisions (yours, 2026-11-17)

1. **2D and UI: build ahead, file issues.** Ship everything Cinder loads today. Also produce
   sprites, atlases, icons and 9-slice panels as PNG + JSON now, shown in-engine on textured
   quads, and open Cinder issues for native support. This pipeline does not change engine code.
2. **Generation: procedural code first, generative models optional.** Every asset is a Python
   script. A plug-in step may call an image / 3D / audio generation service when a script cannot
   reach the look; such inputs are cached, recorded and held back until their licence is checked.

Providers for decision 2 (told 2026-11-17): ElevenLabs (sound effects, music, voice), OpenAI
(images) and Anthropic API keys are available. `gen.py` (Phase 5) reads them from environment
variables (`ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`); a key is never written
to the repo, a build log or a manifest.

## 4. Architecture

Same loop as the other two silos: spec, script, build, checks, look at the picture, deliver.

```
assets/<name>.py            one script per asset (assets/_template_<kind>.py to start from)
assets/gen/                 cached generative inputs + their provenance records
cadkit/game/                the harness (below)
output/game/<name>/         <name>.glb | .png | .wav ..., _preview.png, build.json, readiness.json, report.txt
output/game/packs/<pack>/   a delivered pack
docs/agents/game-assets-playbook.md   judgement and failures, written as they are hit
```

### Asset contract

```python
"""Docstring with a Spec: block (kind, size in metres, budget, pivot, materials, use)."""
from cadkit.game import *
KIND = "prop"            # prop | environment | character | material | sound | font | ui | sprite | world | prefab
DESCRIPTION = "one line"
PARAMS = dict(size=1.0, seed=3)
BUDGET = dict(tris=1500, texture=1024, materials=1)
ENGINE = dict(body="dynamic", collider="box")        # how the staging world and the pack snippet use it
PRODUCT = dict(title=..., collection="dungeon_kit", tags=[...], licence="CC0")
def checks(p): return [bounds(y=1.0), tris(max=1500), pivot("centre"), texel_density(512), loads_in_engine()]
def build(p):  return Model(mesh, material)          # or Character, Sound, UiSet, SpriteSheet, World
```

Builds are deterministic: every random choice takes `p.seed`.

### Modules (`cadkit/game/`)

| Module | Job | Reuses |
|---|---|---|
| `mesh.py` | Game-mesh ops: `to_game(part)` (mm Z-up to metres Y-up), low-poly primitives, bevels, decimation to budget, UV projection and auto-unwrap, pivot placement | build123d, manifold3d and SDF kernels, `cadkit/mesh.py`; new dep `xatlas` |
| `texture.py` | Procedural PBR in numpy: tileable noise, planks, bricks, metal, fabric, wear and edge masks, height to normal, AO bake, metallic-roughness packing, palette and trim sheets | Pillow, scipy, `cadkit/image.py` |
| `gltf.py` | The one glTF writer: static, skinned, morphs, multi-material; only the features Cinder reads | pygltflib (already installed; pin it), trimesh |
| `rig.py` | Skeleton templates (biped, quadruped, prop hinge), skin weights, keyframed and procedural clips with matched foot phase, a CPU pose sampler for previews | numpy |
| `audio.py` | Synthesis: oscillators, envelopes, noise, filters, layering; WAV 48 kHz 16-bit, mono effects, stereo music loops with a click-free seam | numpy, scipy |
| `ui.py`, `sprite.py` | `UiTheme` and UI trees as `cinder-scene` text; icons, 9-slice panels, sprite sheets and atlases as PNG + JSON; textured-quad GLBs to show them in-engine today | Pillow, shapely, `cadkit/stitch/lettering.py`, fontTools |
| `world.py` | World-file and prefab writers; staging worlds for verification; demo worlds for packs | - |
| `engine.py` | Finds the engine (`CAD_CINDER`, else `F:\git\cinder\dist\cinder-windows-x64`), runs `cinder-play` and `cinder-cook`, parses reports, records engine version | - |
| `gen.py` | Optional provider-neutral generative step: `gen.image(prompt, seed)` etc. Result cached in `assets/gen/` with prompt, provider, model, seed and licence note; the asset is `cleared: false` until someone checks it | - |
| `checks.py`, `verify.py` | Checks and the readiness ladder (below) | pattern of `cadkit/stitch/verify.py` |
| `render.py` | The preview contact sheet | `cadkit/render.py` |
| `pack.py`, `cli.py` | Packs, manifest, install; the `cad game` commands | pattern of `cadkit/publish.py` |

### The readiness ladder (every build, written to `readiness.json`, one `ready YES/NO` line)

1. **Static**: valid glTF (own checks plus the Khronos glTF validator when installed, as an
   independent reader); only supported features and extensions; budget (triangles, materials,
   texture size, bones, influences, morphs); size in metres against the Spec; pivot; UVs present,
   inside 0..1 and not overlapping where baked; texel density; power-of-two textures; base colour
   within a plausible PBR range; normal map unit length and +Y; tile seam error for tileables;
   audio peak, DC offset, length and loop seam; base name unique and space-free.
2. **Cook**: `cinder-cook` exits 0 and writes the expected outputs.
3. **Engine**: a generated staging world runs headless: `ok`, `gpu_errors 0`, the model counted.
   Physics props also run a drop test: the body must settle at the height its visual bounds
   predict, which catches a collider that does not match the mesh.
4. **Look**: `<name>_preview.png` is rendered by Cinder: four turntable frames and an overview
   beside a 1.8 m player-sized reference, plus the UV layout, each texture map and the stats.
   Claude reads it before calling anything done, as with every other silo.

Characters add: cooked `.cskel` and `.cclip` counts, and a clip strip (poses sampled on the CPU)
because the world kit cannot play a clip yet. Sounds add a waveform and spectrogram tile.

### Conventions the checks hold

- Metres, Y up, -Z forward. Dynamic props have their origin at the centre of their bounds (the
  world kit centres box and sphere colliders on the entity); static pieces sit on Y=0 with the
  origin at the base centre or a grid corner; doors at the hinge; characters at the feet.
- Budgets by class: small prop 300-1,500 triangles, hero prop 5-15k, character 8-20k,
  512 px per metre (1,024 for hero pieces), one material per prop where possible, shared
  trim-sheet materials across a pack.
- One occlusion + roughness + metallic image (R, G, B) serves both the occlusion and the
  metallic-roughness slot.

### Delivery: packs

`cad game pack <collection>` writes `output/game/packs/<pack>/`:

```
assets/           sources: .glb .png .wav .ttf, unique space-free base names
cooked/           optional cinder-cook output + manifest.txt for one engine build
worlds/demo.world a playable world using the pack (wins on --autopilot where it has a goal)
prefabs/          cinder-scene documents + the source names they expect
manifest.json     schema cadkit-game/1: id, kind, files, bounds, triangles, collider, licence,
                  provenance, cook logical paths, engine version verified against, readiness
AGENTS.md         for the agent using the pack: one paste-ready world-file snippet per asset
ATTRIBUTION.md    licences and any generative provenance
```

`cad game install <pack> --to <game dir>` copies it and optionally cooks into the game's cook
directory.

### AI-first rules

- Every command takes `--json` and returns one object; errors carry a `hint`.
- `cad game schema` prints the contract, kinds, checks, budgets and conventions as JSON, so an
  agent needs no prose to start.
- Asset requests have one schema (`kind`, `name`, `use`, `size`, `style`, `budget`, `notes`);
  the Hive suggestion format is that schema, and `cad game request <file|hive>` turns one into a
  stub script with the Spec filled in.
- Packs describe themselves (`manifest.json` + `AGENTS.md`), so a game-side agent can place an
  asset without opening it.

## 5. Engine gaps to file as Cinder issues (not fixed here)

1. Game UI images: image node, 9-slice, atlases baked by the cooker (ADR-0017 lists them as not built).
2. A sprite / billboard path and an unlit material.
3. `cinder-play --inspect <asset>`: load any glTF, WAV or TTF and report it as JSON (today a model must be wrapped in a world file).
4. Animation, audio and UI text in world files, so clips and sounds can be verified in-engine.
5. Vertex colours (COLOR_0), for cheap stylised assets.
6. Loading an HDR environment from a file.
7. Document `cinder-cook.exe` in the Windows package.
8. A body dropped onto a static floor comes to rest about 15 mm inside it (seen with the
   engine's own `shape kind="box"`: dropped from 0.5 m it rests at y=0.385 for a 0.8 m box,
   placed at rest it stays at 0.400).

Until 4 lands, clips are proven by the cook plus the CPU pose strip, and sounds by decode checks.

## 6. Phases and gates

| Phase | Delivers | Gate |
|---|---|---|
| 0 Foundation | `cadkit/game` skeleton, `engine.py`, glTF writer, `cad game new / build / list / schema / engine`, static props, the ladder, preview sheet, tests | A crate, a barrel and a lantern are `ready YES`; pytest and `cad selftest` green |
| 1 Materials and packs | Texture library, trim sheets, environment pieces on a grid, `pack` / `install`, demo world | A 12-piece dungeon kit pack whose demo world is won headless on autopilot |
| 2 Characters | Rig templates, skinning, clips, clip strip | A biped with idle, walk and run cooks to one `.cskel` and three `.cclip`; walk and run share foot phase |
| 3 Audio | Synth, effect and loop checks | A 10-sound effects set and one seamless music loop decode in the engine's formats |
| 4 UI and 2D | Themes, UI trees, fonts, icons, 9-slice, sprite sheets, quads | A HUD + pause-menu set round-trips through `cinder-scene` text; a sprite sheet shows in-engine on a quad; issues 1-2 filed |
| 5 Generative step | `gen.py`, provenance records, licence gate | One texture from a generation service builds from cache, is marked uncleared and is kept out of packs until cleared |
| 6 Hive test round | Request intake from the Hive thread, the suggested assets built, playbook and CLAUDE.md / AGENTS.md sections | Every accepted suggestion delivered as `ready YES` or answered with the reason it cannot be |

Phases 0 and 1 are the spine; 2, 3 and 4 are independent of each other after that.

## 7. Risks

- **Engine drift.** The local package may be older than the docs. Every build records the engine
  it was verified against, and a pack's cooked folder is only valid for that build.
- **Animation cannot be seen in-engine without Mojo code.** Covered by the cook gate and the CPU
  strip for now; issue 4 closes it.
- **Auto-unwrap quality.** Procedural textures on organic shapes show seams. Mitigation: prefer
  projection-mapped and tri-planar-baked textures, trim sheets for hard surfaces.
- **Procedural look ceiling.** Stylised and hard-surface work is strong; photoreal organic detail
  is where the optional generative step comes in, with its licence gate.
- **Selling packs.** The shop ingests 3D-print models only; a `game-asset` kind is a later step.

## 8. What Phase 1 found

- **Textures cannot be shared between models.** Each GLB carries its own images and the cook
  names them `<prefix>#image<n>`, so twelve stone pieces upload the same stone twelve times.
  Engine gap 9: a way for models to reference a shared material or texture.
- A world-kit door's body switches off the instant it opens, whatever its slide speed, so the
  autopilot never waits for it. The demo was won in 1.8 s of game time.
- Emissive strength above about 1.5 tone-maps toward white.

## 9. What Phase 2 found

- **The world kit does not draw skinned models.** `spawn_gltf` gives a skinned mesh node a
  renderer, but the caller must attach an `AnimatorRef` for its joint palette and the kit does
  not: the model loads, is counted, and nothing appears. The Khronos CesiumMan sample behaves
  the same. Engine gap 10 (the largest so far for content): draw skinned models in the kit at
  their bind pose, and let a world file name a clip to play.
- That exposed a hole in the ladder: `ok`, `gpu_errors 0` and `models 1` were all true for an
  invisible model. Every build now compares the stage with and without the asset.
- What stands in for an in-engine animation proof until gap 10 closes: the engine's cooker
  must write one `.cskel` and one `.cclip` per clip; the build parses those `.cclip` files and
  compares name, duration, channel count and key count with what was built; an independent
  glTF reader checks joints, inverse bind matrices, weight sums, sorted key times and unit
  quaternions; and CPU-skinned pose strips are rendered by the engine as static models. What
  is **not** proven: that Cinder's own skinning and blend tree play these clips as the strips
  show them. That needs Mojo code or gap 10.
- A player model must face +Z: the kit yaws it by `atan2(move.x, move.z)`.

## 10. What Phase 3 found

- **There is a way to prove a sound in the engine today.** The world kit has no audio, but the
  sample game opens `assets/game/audio/music_level.wav` before anything else and stops with
  `audio: could not load` when it cannot. Run headless from a scratch folder with the file
  under test in that place, it is a 1.5 s probe; a random-bytes control proves it
  discriminates. It shows the audio engine opened the file as a streamed sound; it does not
  play it through, and nothing here can hear it. Engine gap 11: a `cinder-play --inspect
  x.wav` (gap 3) that decodes a file and reports length, channels and peak would replace this.
- **Sound is judged by picture and number.** Each Spec claim about character is a `band` check
  (share of energy between two frequencies), and the spectrogram is read like a render. That
  caught: a music bed whose channels were out of phase, a torch whose crackle was 0.4 % of the
  energy under its roar, a creak a tenth the level of the knock after it, and coloured noise
  that was mostly sub-audible drift.
- What is **not** verified: how any of it actually sounds to a person. Someone should listen
  to the eleven files before they ship in a game.

## 11. The Hive test round (Sandbox Kit)

Ten suggestions from the agent `stanley`, all for the CinderCore sandbox builder, built as
fifteen assets in `packs/sandbox_kit.py`: `block_cube_1m`, `block_cube_2m`, `block_plate`,
`block_beam`, `block_cylinder`, `block_ramp` (the building-block kit), `bounce_pad`,
`explosive_barrel`, `coin`, `checkpoint_flag`, `finish_gate`, `spike_trap`, `moving_platform`,
`round_tree`, `robot_character`. All `ready YES`; 2,976 triangles and 0.9 MB for the pack.

What the round asked of the pipeline that it could not do, and now can:

- **Separate parts** (a flag to recolour, spikes to retract): named mesh nodes in one GLB.
- **One texture for a kit**: a 16-tile atlas with a matching roughness/metallic map.
- **"Stack flush with no gaps"**: the demo is a stacking test. A 2 m cube came to rest at
  y = 1.000 and the 1 m cubes on it at 2.500; every dynamic body ended within 6 cm of where it
  was placed (the 2 cm it was dropped plus the engine's contact slop).
- **Gameplay facts the engine cannot read from a model** (a bounce surface, which node is the
  hazard): `PRODUCT["gameplay"]`, carried into the manifest.

What it asked that Cinder 0.1.1's world kit cannot do (reported back on the thread):

- Cylinder and convex colliders: `block_cylinder` and `explosive_barrel` use a box and do not
  roll; `block_ramp` is kinematic with a mesh collider. Engine gap 12.
- A collider on part of a model (the tree's trunk only). Engine gap 13.
- Moving or recolouring one node of a model from a world file (no hierarchy in the kit).
- Showing the robot: skinned models are not drawn (gap 10).
- Sharing one texture between models (gap 9): the atlas is still uploaded once per model.

## 12. What Phase 4 found

- **A probe program is the way past the world kit.** The Cinder toolchain container is on this
  machine, so `tools/cinder_probe/cinder_probe.mojo` (ours, 120 lines, compiled against the
  engine, not part of it) asks the engine directly: it loads a UI document with `Ui.from_text`,
  lays it out, draws it headless, saves the frame and prints every node's rectangle and the
  engine's own `to_text`. The UI gate is therefore a real engine round trip, and the UI preview
  is the engine's frame. The same route can later show skinned models playing clips and decode
  sounds in full, which closes gaps 10 and 11 from our side without changing the engine.
- **The UI document writer matches the engine byte for byte** for a tree built with the same
  calls (pinned by a test against text the engine wrote).
- **Engine bug: alpha mask and blend are ignored by the colour pass.** `material.mojo` writes the
  alpha mode with `w.u32`, `forward.wgsl` reads it with `u32(material.alpha.y)`, a numeric
  conversion of a float whose bits are 1 or 2, which gives 0. The depth pass cuts masks, so a
  masked surface looks right only where something is drawn behind it afterwards. Found because
  sprite quads showed black squares; isolated with three test models. Engine gap 14.
- **Built ahead, as decided:** sprite sheets, icons and 9-slice frames have no reader in Cinder.
  Two issues ask for one: UI images with 9-slice and atlases; sprites with an unlit material
  (the second carries the alpha bug).
- **Not built:** fonts. `cinder-probe font` already has the engine parse and draw a TTF, so the
  verification exists; the generator (a TTF from the block lettering we own, plus digits) does not.

## 13. Phase 5: the generative step

Built: `cadkit/game/gen.py`, the `--gen` flag, `cad game gen list | keys | clear`, the pack
refusal, provenance in manifests and `ATTRIBUTION.md`, and `assets/wall_tapestry.py`, which
asks for one image (`dragon_banner`).

How it keeps the decision "procedural first, generative optional" honest:

| Rule | How it is held |
|---|---|
| A build is offline unless asked | `gen.image` reads `assets/gen/`; a miss stops with the `--gen` command. Tested: no request without `--gen`, none without a key |
| A build is repeatable | The cache is the source; the services have no dependable seed. Tested: second build makes no call and gives the same pixels |
| A prompt change is visible | Same name, different request: an error. Tested |
| Provenance travels | `assets/gen/<id>.json`; `generated` in build.json; `generated_inputs` in the manifest; a line in `ATTRIBUTION.md`. Tested |
| A person clears what ships | `ready YES` is not enough: `cad game pack` refuses an uncleared input; clearing needs `--by` and `--note`. Tested |
| Keys stay private | Environment or git-ignored `.env`; the record is checked not to contain the key. Tested |

**Gate status: passed on 2026-11-17**, after keys were put in `.env`.

- One real call: `gen.image` for `dragon_banner`, OpenAI `gpt-image-2`, 1024 x 1536, medium
  quality, 1,463 tokens. The first attempt was refused at no cost: `gpt-image-1`, the default
  written from older documentation, no longer exists; the service's own model list gave the
  current ids.
- `wall_tapestry` then failed three of its own spec checks (rod too long, cloth edges with no
  UV area, origin 5 mm off the wall): geometry faults, fixed in the script.
- Rebuilt without `--gen`: no second call, `ready YES` in Cinder, reported `NOT CLEARED`.
- `cad game pack packs/dungeon_kit_generated.py`: refused, naming the asset and the input.

**Still the user's to do:** look at `assets/gen/dragon_banner.png` and clear it, or not:
`cad game gen clear dragon_banner --by "<name>" --note "..."`. Things to weigh: it is a red
dragon rampant on gold in a knot border, with no text or lettering; a red dragon is also the
emblem of Wales (there it walks on green and white, so this is not that flag, but the kinship
is plain). Until it is cleared the tapestry stays out of every pack.

**Not exercised:** the ElevenLabs sound provider (request shape pinned by a test, never called).

## 14. Fonts (follow-up phase, 2026-11-17)

Built: `cadkit/game/font.py`, `assets/block_caps.py` (the font), `assets/title_screen.py` (an
interface set in it), fonts in packs, `tests/test_game_font.py`.

- **Block Caps** is the block alphabet this workspace already owned (drawn for embroidery, A-Z
  and three marks) extended with ten digits and 27 punctuation marks in the same construction:
  59 glyphs drawn, 139 code points mapped (lowercase to capitals, accented Latin-1 letters to
  their base letter), a 6 kB TrueType file, CC0. Not drawn: `$ & @ ^ \` { | } ~`, which show
  the hollow box.
- **Proof:** fontTools writes it; FreeType reads it back and agrees on every advance; Cinder
  parses it, bakes 224 glyphs at 24 px and measures a test line within a pixel; and the engine's
  pixels overlap the glyphs' own shapes by 81 % at 48 px and 87 % at 24 px (a different font
  scores about 50 %, the threshold is 70 %).
- **What went wrong first, and why the pixel check exists:** the first engine frame was
  text-shaped garbage while every numeric check passed. The probe swapped the font in after the
  first frame, and Cinder's UI renderer uploads a glyph atlas once per size and never again, so
  the new font's layout was drawn from the old font's texture. The fix was in the probe (install
  the font before anything is drawn) and the lesson is in the checks (compare pixels).
- **Engine gap 15:** no public way to choose the UI font. A game must call the engine's lazy
  constructor early (`app._ensure_ui_renderer()`) and replace the renderer's `FontCache` in
  `Game.start`. An `AppConfig` font path, or a `set_font` that drops the uploaded atlases,
  would make this safe. Not filed.
- **Limits that are the engine's:** one font per interface, no kerning, no wrapping, Latin-1 only.
- **Not done:** a lowercase alphabet, a second weight, `$ & @`. No person has judged the
  letterforms; the specimen is in `block_caps_preview.png`.

## 14. Blender in the loop (high-resolution assets), 2026-11-17

**Goal:** high-resolution, complex assets for Cinder. The existing kernels stop at hard-surface
and low-poly work; detailed assets are made by sculpting a heavy mesh and baking it onto a
light one, and that needs Blender.

**Paths considered**

| Path | Verdict | Why |
|---|---|---|
| Blender as a headless subprocess, arrays in and out | **Chosen** | Works with any Blender binary; crash-isolated; nothing GPL imported; 7 s overhead per run, hidden by a cache |
| `import bpy` in-process (the PyPI wheel) | Rejected | Each wheel is pinned to one Python: 3.13 for Blender 5.x, 3.11 for 4.5 LTS. This workspace is 3.12 (build123d's range), so it cannot be installed here |
| An agent driving a live Blender through an MCP server (Blender's own for 5.1+, or the community ones) | Rejected for builds | The asset would live in an interactive session; nothing to rebuild, diff or check. Useful for exploring a look by hand, not for the pipeline |
| Blender's glTF exporter as the output path | Rejected | The pipeline's own GLB writer already emits exactly what Cinder reads; a second exporter is a second thing to keep within that |
| Text-to-3D services | Deferred | Would go through `gen.py` with its clearing gate; their meshes need exactly this retopology and bake step first |

**Delivered**

- Blender 5.3.0, installed system-wide with winget (the user's choice over a pinned portable copy).
- `tools/blender_bridge/bridge.py` (runs inside Blender: 13 step kinds) and
  `cadkit/game/blender.py` (`Session`, modifier helpers, `bake_lowpoly`, the cache, `find`).
- World-space texturing: `texel_maps`, `noise3`, `fbm3`, `fill_background`; the `uv_unique` check.
- `cad game blender`; a `blender` section in `cad game schema`; `tests/test_game_blender.py`.
- `assets/rune_monolith.py`: about 500,000 triangles sculpted (subdivision, three scales of
  displacement, four runes carved 45 mm deep with booleans), baked onto 3,000 triangles with
  2048 px normal, occlusion, curvature and rune-mask maps; `ready YES` in Cinder 0.1.1. Blender
  takes 47 s, 36 s of it the bake; the whole build about two minutes; rebuilds use the cache.

**What it taught** (also in CLAUDE.md): carve after the big shapes and before only fine grain;
trim a cutter against a remeshed inset copy for an exact depth; a bake's ray distance must
exceed the cut depth; clearing a mesh's material slots resets every face's material index
(the bridge swaps the material in each slot instead). The rune mask came out empty three times
for three different reasons, and the asset's own check caught each one.

**Not done**

- ~~No character has been made this way yet.~~ Done the same day: `assets/stone_golem.py`
  (588,338 triangles sculpted, 8,000 in the game mesh, four 2048 px maps, 18 bones skinned by
  bone heat, clips idle / walk / smash, `ready YES`; 3 minutes cold). It added `ball`, `capsule`,
  `Character.add_skinned`, the `deforms_cleanly` check and a smooth four-influence cut in the
  bridge. Still unproven: the clips playing in the engine (the world kit draws no skinned
  model), and its UV layout is hundreds of small islands (Smart UV on a lumpy decimated mesh),
  which wastes texels and would show seams under a lower-resolution mip.
- Bakes are 8-bit. Smooth, gently curved surfaces can band; 16-bit normal maps would need the
  GLB writer to carry them.
- The version is whatever winget installed (5.3.0 today). The cache key includes the version,
  so an upgrade re-bakes everything; results may then differ slightly.
- Close up, the monolith's silhouette shows its 3,000 triangles, and its glowing runes read
  more as bright paint than as grooves. A higher budget and a dimmer glow would fix both.
- No high-poly sculpting from a reference image or from a generated mesh.
