# Game assets playbook

Judgement for `cad game`, and the failures already hit. The reference is CLAUDE.md ("Game
assets for Cinder"); the plan is `docs/game-assets-plan.md`. Add to this file when a build
teaches something.

## Before writing

- Run `cad game engine`. No engine means no `ready YES`: fix that first (`CAD_CINDER`).
- Ask what the asset stands next to. Scale errors are the commonest fault in generated
  assets, and the preview's 1.8 m orange figure is there to catch them: look at it.
- Decide dynamic or static before modelling. It sets the pivot, and the pivot cannot be
  moved later without breaking every world that placed the asset.

## Modelling

- Spend triangles on the silhouette, texture the rest. The crate's frame is geometry
  (it changes the outline and catches light); its plank gaps are normal map only.
- Match geometry to texture counts: the barrel has 20 staves on 20 sides, so every stave joint
  lies on an edge.
- Sink parts 1-2 mm into each other instead of leaving coplanar faces: two faces in one plane
  flicker. Where bars meet at a corner, let one run through and butt the others against it.
- Hard edges are duplicated vertices. `box` and `flat` give them; `lathe(smooth=False)` gives
  hard rings; a four-sided `lathe` needs `flat()` or its faces shade as a cone.

## Texturing

- One atlas per prop: side wrap in one band, caps in a strip. Paint unused atlas area in a
  neighbouring colour so the mips do not bleed black.
- A wrapped texture (round a barrel) needs its seam on a feature that is already a line.
- Roughness variation sells a surface more than colour variation. Metal: metallic 1, roughness
  0.35-0.6, dark base. Wood: metallic 0, roughness 0.6-0.9.
- Emissive strength over about 3 tone-maps to near white in Cinder; keep the colour saturated
  and the strength low, and put a point light beside it in the world for the cast light.

## Failures hit

| Symptom | Cause | Fix |
|---|---|---|
| `physics: rests -250 mm from where its bounds say` | Dynamic prop with its origin at the base; the box collider is centred on the entity | Origin at the centre of the bounds |
| A rim or inner wall invisible from one side | `lathe` profile travelling the wrong way: the surface faces to the right of travel | Reverse the profile for surfaces that face the axis |
| `seam` check failed on a correct wrap | The check compared the wrap with the image's average step, not with its other joints | Compare like with like: the wrap step against the other stave joints |
| Every dropped body rests 15 mm low | Engine behaviour in Cinder 0.1.1, primitives included | Tolerance floor of 30 mm in the drop test; reported as an engine gap |
| `TypeError: bool is not JSON serializable` | A numpy bool in a result dict | Wrap comparisons of numpy values in `bool()` |
| `TypeError: 'module' object is not callable` in every asset | A new module `materials.py` shadowed the exported check `materials` | Renamed the library to `matlib`; never name a module after an exported function |
| Red gem renders pink, flames white | Emissive strength 2.5-6 tone-maps toward white | Strength 0.6-1.8 with a saturated colour; point lights do the lighting |
| Stone looked like leopard skin | Pitting mask too dense and too dark | Sparse, small, shallow pits (`matlib.stone_blocks`) |
| Demo screenshot showed the player's back in a corner | The run continues after the win and the follow camera pulls in | `SHOTS`: frames from placed cameras in the world without its player |
| Door failed `pivot base` | Its ring pull on one face shifts the bounds in Z | `pivot((0.5, 0.0, None))`: leave the axis a detail offsets free |

## Kits

- Put what the pieces share in `assets/_<kit>.py`: grid, wall height, the materials, a
  `kit_checks` helper, `PRODUCT` and the static `ENGINE`. Each piece file is then its Spec,
  its sizes and ten lines of geometry (`assets/_dungeon.py`).
- Review a kit in its demo world, not piece by piece: joints, course alignment and scale only
  show when pieces stand together. Read `<pack>_contents.png` for the single pieces.
- Use every asset of a pack in its demo; the demo is also the proof that they all load together.

## Characters

- Bind in a relaxed A-pose, not a T-pose: wherever the asset is shown unanimated it still
  looks like a person.
- One tube per limb, weighted across the joint (`bind=[upper, lower]`), with a ring of
  vertices just before, at and just after the joint. Separate rigid segments open a gap when
  the joint bends.
- Clothing that hangs over a joint (a tunic skirt over the thighs) needs clearance: the skirt
  and the leg tops intersected until the skirt was deepened and the thighs slimmed.
- Write gaits as a function of phase with the left foot striking at phase 0, and derive walk
  and run from the same function with different amplitudes: they then share foot phase by
  construction, and the `phase_matched` check proves it.
- Judge a clip from its strip, then measure: a bent elbow seen from the front looks straight.
  `bone_positions(sk, clip, t)` gives joint positions; compare the angle you meant.

| Symptom | Cause | Fix |
|---|---|---|
| `ready YES` with an empty frame | The world kit loads skinned models and draws nothing; no check looked at pixels | Visibility test on every build; static bakes for skinned frames |
| The GLB was never written, a file named `translation` appeared | A loop variable `path` shadowed the output path | Renamed; do not shadow arguments |
| Jagged patches of tunic colour on the thighs | Skirt and leg surfaces almost coincident | Give overlapping clothing 20 mm or more of clearance |

## Sound

- Write the Spec's "character" as things a check can hold: where the energy sits, how long,
  how loud, what happens in what order. "Dull thud" is `band(40, 800, at_least=0.5)` and
  `band(6000, 20000, at_most=0.1)`.
- Build a sound from events: a transient (filtered noise burst, 5-30 ms), a body (`modes` for
  anything struck: wood is a few partials dying in 0.1-0.25 s, metal rings longer and higher),
  a tail. Layer them with `place` at their times.
- Look at relative levels in the waveform: a layer a tenth the height of its neighbour will
  not be heard.
- A `pass` that only just passes (0.4 % against a 0.4 % floor) means the threshold was fitted
  to the sound. Fix the sound, then set the threshold where the Spec says it should be.

| Symptom | Cause | Fix |
|---|---|---|
| `edges` failed on every sharp transient | The test looked at the first 16 samples, not at whether the sound starts at zero | A click is a non-zero first or last sample; a fast attack is not |
| Quiet sound flagged for trailing silence | Silence threshold was an absolute level | 60 dB under the sound's own peak |
| Music left and right correlated -0.3 | A stereo reverb on the steady drone gave each channel its own phase | Reverb on the events only; bed dry; a correlation check |
| Brown noise had 3 % of its energy in 20-200 Hz | 1/f shaping from 1 Hz up: mostly drift below hearing | No energy below 20 Hz in coloured noise |
| Pack notes loaded a loop as streamed and the music as not looping | `SoundDesc` is (path, bus, streamed, looping, spatial); I had looping first | Read the engine source for every signature a snippet uses; a test now pins the order |

## Taking a request

- Read the notes line twice: it is where the real requirement is ("the flag should be a
  separate part", "collider on the trunk only"). Where the engine cannot do what a note asks,
  build the nearest thing that works today, put what was wanted in `PRODUCT["gameplay"]`, and
  say so in the reply. Never quietly deliver less.
- A "kit" in a request is several assets: one script per piece, a shared `_<kit>.py`.
- Hold the request's numbers as checks (size to 2 mm for grid pieces, triangle budget, the
  opening of a gate). Six of nine props failed their own spec on the first build: a bung 12 mm
  too tall, plinths in a doorway, an arrow 3 mm proud.
- Prove fit in the demo, not on paper: stack the pieces and let the settle check measure it.

## UI and sprites

- Lay an interface out for 1280 x 720 and read the right half of the preview: the outlined
  rectangles are the engine's layout, not ours. A node that is wider than expected is text
  measured in the engine's font.
- Name every node the game will touch; the `.mojo` file's `find` lines are generated from the names.
- `cinder.ui` has no wrapping, scrolling or images: keep a menu to one column that fits, and
  say counts in words until images exist.
- Icons: a dark outline of about 6 % of the size and one highlight; fill over 60 % of the
  frame; check them at a third of their size in your head (24 px for a 64 px icon).
- 9-slice: the centre must be one flat colour or stretching shows; put all the character in
  the corners and edges.
- When a render looks wrong, find out whose fault it is before changing the asset: render a
  Khronos sample the same way, then reduce to the smallest model that shows it. The alpha bug
  took three quads to pin to one line of the engine's shader.

## Generated inputs

- Reach for one only when a script cannot make the look: painted pictures, organic photographic
  texture. Stone, wood, metal, icons and UI are better drawn: smaller, tileable by construction,
  and nobody has to clear them.
- Generate the flat picture, build everything else. The tapestry's cloth shape, rod, UVs and
  normal map are code; only the picture is generated.
- A generated image is not tileable and not square: `gen.tileable`, `gen.material` (which
  resizes to a power of two).
- Clearing is the user's decision, with their name on it. Show them the image and say what to
  look for: text or lettering, a logo or trademark, a real person's likeness, a real house's or
  nation's arms, anything that copies a known work.
- A provider's model ids go stale faster than documentation. Before the first real call, list
  the service's models; do not trust an id from memory or from a third-party page.
- After generating, the asset's own spec checks still decide: the tapestry's picture was right
  first time and its geometry failed three checks.

## Fonts

- Build glyphs from one stroke weight on a grid, and clip every corner the same way at the end:
  the family look comes from the shared construction, not from each glyph.
- Design the confusable pairs on purpose and check them: 0 and O (a bar in the zero), 1 and I
  (a flag and a foot), 5 and S, 8 and B, 2 and Z.
- The smallest size decides the weight: at the HUD's smallest size the thinnest stroke must
  still be about 1.5 px.
- Map what you did not draw to something sensible (lowercase to capitals, accents to the base
  letter) and say plainly what falls through to the box.
- Read the specimen at every size, then read the engine's frame. They are different renderers
  and the engine's is the one that ships.

## High-resolution assets (Blender)

- Reach for Blender when the asset needs surface detail finer than its triangle budget can
  hold, or a shape that is carved, eroded or organic. A crate does not; a weathered stone does.
- Think in three scales when sculpting by displacement: lumps about a fifth of the object,
  cracks about a twentieth, grain about a hundredth, each with about a third of the strength of
  the one before.
- The game mesh comes from the uncarved high mesh; the carving goes only into the maps.
- Read the maps as well as the render: the UV layout tile, then base, ORM and normal. A rune
  mask that is empty or a normal map that is flat blue is visible at a glance.
- When a baked feature looks wrong, plot where its mask lands on the mesh (`texel_maps` gives
  each texel's position) beside where the cutter was. That is how the smeared runes were found.
- Budget: 2048 px maps on a 2.4 m object are about 800 px per metre; a four-map GLB is about
  7 MB. Go to 4096 only for something the camera rests on.

## Sculpted characters

- Proportions carry a creature more than detail does. The golem reads as heavy because its
  forearms are thicker than its upper arms, its fists hang at knee height and its head is
  sunk between the shoulders; the rock texture came second.
- Bind pose: arms 35-40 deg out from the body, feet apart by more than a leg's width. Check the
  joined blobs before sculpting: anything that touches will be one lump with shared weights.
- When `deforms_cleanly` fails, print the worst edges with the bones and weights of both ends
  before touching the pose. Same lead bone but a different fourth bone is a truncation tear
  (fixed in the bridge); different lead bones far apart is fused geometry; a smooth ramp of
  stretch near a joint is the pose asking too much.
- Glowing eyes and a chest mark give a silhouette-coloured creature a face and a front.
