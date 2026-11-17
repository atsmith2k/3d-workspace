# ash10's Fantasy RPG Pack: style guide

The rules every asset in every sub-pack follows. The same rules are code in `assets/_frp.py`
(ruler, palette, materials, budgets, slots, sound levels) and `cadkit/game/rig.py` (the humanoid
and its sockets): an asset script starts with `from _frp import *` and takes its numbers from
there. When this page and the code disagree, the code is right and this page is the bug.

Judged by one scene: `cad game pack packs/frp_style_test.py` (a timber hut on open ground, seen
third-person, first-person and top-down) and one figure: `cad game build assets/hero_mannequin.py`
(`--set shape=standard|stout|slight|tall`). Inventory and order of work: `fantasy-rpg-pack-plan.md`.

## 1. Tone

Dark fantasy throughout: a world past its best, with real menace. Stylised mid-poly, not
photoreal. Stone is cold and soot-stained, wood weathered or rotten, iron rusted, plaster
water-stained, grass dying. Colour is kept for what matters: magic, blood, potions, cloth of rank.
A surface that looks new is wrong unless the Spec says why.

## 2. Ruler

Metres, Y up, -Z forward; characters face +Z.

| Thing | Size | Constant |
|---|---|---|
| A person (standard shape) | 1.80 m | `PERSON` |
| Grid cell | 2.0 m | `GRID` |
| Storey, floor to floor | 3.0 m | `STOREY` |
| Door opening | 1.2 x 2.2 m | `DOOR_W`, `DOOR_H` |
| Window opening, sill height | 0.8 x 1.0 m, 1.1 m | `WINDOW_W`, `WINDOW_H`, `WINDOW_SILL` |
| Step rise | 0.2 m | `STEP_RISE` |
| Village and interior wall thickness | 0.3 m (dungeon and castle 0.4 and up) | `WALL_T` |
| Texel density | 512 px per metre; 1,024 for held items and faces | `TEXEL` |
| One repeat of a tiling material | 2 m; ground 4 m | `TILE`, `GROUND_TILE` |

Grid pieces are exact to 2 mm (`piece_checks`). Walls stand centred on cell edges; a post
(`vil_corner`) stands on every corner where walls meet; floors walk at Y = 0 of their storey.

## 3. Palette

About sixty colours in `PALETTE` (`P["stone_dark"]`), weighted dark. Families: stone (5 + moss,
soot), wood (5, rot to pale), plaster and thatch, cloth dyes (muted: red, blue, green, ochre,
undyed, black), metal (iron, steel, rust, bronze, dull gold, silver), leather and bone, ground and
growth (autumn and blight), and the accents: blood in three states (fresh, dried, old stain),
arcane blue, fel green, holy gold, ember, potion red and blue, glass.

- Take colours from the palette by name. A new colour is added to the palette, not to an asset.
- Accents cover little: under a tenth of an asset's surface unless it is a magic item.
- Emissive strength stays at or under 1.5 (Cinder tone-maps more toward white). Light comes from
  a point light placed in the world, colour from the emissive.

## 4. Materials

Metallic-roughness PBR, textures procedural and seeded, tileable, cached. With an ORM map the
factors are 1.0.

| Material | Use | Notes |
|---|---|---|
| `stone()` | walls | dressed blocks 1.0 x 0.5 m, soot and runs |
| `paving()` | stone floors | flags, four to the tile each way |
| `timber()` | frames, posts, beams, doors | grain along u; `grain_up(mesh)` for uprights |
| `boards()` | timber floors | eight boards to the tile |
| `plaster()` | infill panels | a few broken hairline cracks, stains from the top |
| `thatch()` | roofs | strands run down the slope (v) |
| `ground()`, `earth()` | top and sides of ground tiles | ground repeats every 4 m |
| `iron_rusted()`, `steel_blade()` | fittings; blades | |
| `flat_material(name, colour)` | small single-colour parts | no texture, no sampler |

Rules learned on the style test:

- **World-scale UVs** (`tiled(mesh)`): courses and boards run on across neighbouring pieces.
  Never stretch a tiling material to fit a piece.
- **Grain follows the timber**: horizontals `tiled`, uprights `grain_up`.
- **Thin edges**: a custom mapping on the show faces collapses on the edges; use
  `directed_uv(mesh, uv, axis)`, which box-maps the rest.
- **Stains are soft and wide**, never column stripes; **cracks start and stop**, never contour lines.
- **Ground must not read as a grid**: broad low-contrast drifts, a 4 m repeat, and 8 m tiles
  for open land.
- **Never two surfaces in one plane**: a ground-floor piece is placed 20 mm above the ground.
- Normal maps carry surface form (boards, courses), never the silhouette.

**Generated surfaces** (for sculpted, baked assets: rocks, trees, statues, monsters' hides):
`gen.surface_image` + `gen.pbr`, projected onto the bake with `Surface.sample` (CLAUDE.md,
"Generated surfaces on baked models"; `assets/nat_boulder_mossy.py`). The picture gives texture,
the palette gives colour, the bake gives shading. Generated inputs are named `frp_<material>`
and shared across assets: one granite for every boulder. None ships uncleared.

## 5. Budgets

`BUDGET_OF[kind]` (triangles, largest texture, materials = draw calls):

| Kind | Triangles | Texture | Materials |
|---|---|---|---|
| `hero` | 15,000 | 2048 | 2 |
| `armour` | 2,500 | 2048 | 1 |
| `monster` | 8,000 | 2048 | 1 |
| `boss` | 30,000 | 2048 | 3 |
| `weapon` | 1,500 | 1024 | 3 |
| `viewmodel` | 8,000 | 2048 | 2 |
| `small_prop` | 800 | 1024 | 2 |
| `large_prop` | 3,000 | 1024 | 2 |
| `building` | 1,500 | 1024 | 3 |
| `tree` | 3,000 | 1024 | 2 |
| `terrain` | 600 | 1024 | 2 |

**The world budget is textures, not triangles.** Cinder 0.1.1 has 256 sampler slots and the
world kit takes one per texture per placed copy of a model, so a world holds about 250 textures
counting every copy: 83 pieces of one textured material (three maps), 41 of two. `cad game pack`
counts them and refuses a demo over 245. So: flat materials where a texture adds nothing, large
tiles for ground, one atlas per prop, and scenes built from fewer, larger pieces.

## 6. Naming

`snake_case`, unique across the bundle, prefixed by sub-pack (`PREFIX`): `hero_ arm_ wpn_ npc_
mon_ dun_ vil_ cas_ nat_ int_ itm_ fx_ ui_ sfx_ mus_`. `PRODUCT = product("village", "wall")`
sets the collection (`frp_village`), licence and tags. Material names start `frp_`.

## 7. Buildings

- Pieces: wall, wall with door, wall with window, corner post, floor, roof slope, gable, door
  leaf; each one cell (2 m) wide, one storey (3 m) high, origin at the base centre (floors: on
  the walking surface; door leaf: at the hinge).
- A wall is plaster panels between timbers that stand 20 mm proud; openings are framed.
  Windows carry bars, not glass (Cinder draws no transparency yet).
- **Roofs and upper storeys are separate entities with names starting `roof_`, `gable_`,
  `upper_`**: a top-down camera hides them by prefix (`SHOTS[...]["hide"]`), a game by name.
- Check all three cameras for every kit: street level, inside at 1.6 m eye height with a
  70 degree view, and above at 15 m with the roof hidden.

## 8. Ground

Modular tiles on the grid: 2 m and 8 m flats, slopes rising one metre over a cell, top face at
Y = 0 (`pivot("top")`), earth sides 0.5 m deep so a raised tile shows a bank. Any tile meets any
other on a straight edge at the same height.

## 9. The humanoid

`humanoid(shape)` in `cadkit.game.rig`: one skeleton of 35 bones for every hero, townsperson and
humanoid monster. The 18 bones of `biped` plus `jaw`, `eye.L/R`, `fingers.L/R` (a mitten),
`thumb.L/R`, `toe.L/R` and eight sockets. Bone names never change between shapes, so a clip made
once plays on all four.

| Shape | Height | Width | For |
|---|---|---|---|
| `standard` | 1.80 m | 1.00 | humans, elves, most undead |
| `stout` | 1.35 m | 1.30 | dwarf-like |
| `slight` | 1.10 m | 0.92 | halfling- and goblin-like |
| `tall` | 2.05 m | 1.16 | orc-like, large humanoids |

Rest pose: a relaxed A-pose, feet at the origin, facing +Z, left is +X. Phase 0 of every gait is
the left foot's strike.

**Sockets** (`SOCKETS`): bones that deform nothing. A game parents an item's entity to one; a
build binds an item to one with `attach(character, parts, socket)`.

| Socket | Parent | Holds |
|---|---|---|
| `socket_hand.R` | `hand.R` | main-hand weapon or tool |
| `socket_hand.L` | `hand.L` | off-hand weapon, torch, focus |
| `socket_shield` | `lower_arm.L` | shield strap, outside of the forearm |
| `socket_back` | `chest` | two-handed weapon, bow or staff |
| `socket_quiver` | `chest` | quiver, behind the right shoulder |
| `socket_hip.L` | `hips` | sheathed sword |
| `socket_hip.R` | `hips` | dagger, pouch or potion |
| `socket_head` | `head` | helmet, hat, crown |

**Held-item convention.** A weapon or tool is modelled with the grip at its origin and the blade
or shaft along +Y (it stands upright in a world). A shield is modelled as a disc in the XZ plane
with its face toward +Y and its strap point at the origin. `attach` applies the socket's `turn`:
in the hand, +Y becomes +Z, so the blade points where the figure faces. Every character that
holds something carries a check that the item is bound to its socket and points the right way
(the mannequin's `held item points forward`).

**Armour slots** (`SLOTS`): each piece belongs to one slot, is bound to that slot's bones and
hides the body under it, so the build drops the covered body region instead of letting skin
show through.

| Slot | Bones | Hides |
|---|---|---|
| `head` | head | scalp (never the face unless the helm is closed) |
| `shoulders` | chest, upper_arm | nothing |
| `chest` | spine, chest | torso |
| `arms` | upper_arm, lower_arm | arms |
| `hands` | hand, fingers, thumb | hands |
| `belt` | hips | nothing |
| `legs` | hips, upper_leg, lower_leg | legs |
| `feet` | foot, toe | feet |
| `cloak` | chest, spine | nothing |
| `robe` | spine, chest, hips, upper_leg | torso and legs (takes the chest and legs slots) |

A piece is drawn from the joints of the skeleton it is built for (`assets/_frp_body.py`:
`armour(sk, shape, slots)`), so one piece fits all four shapes; `dress(...)` leaves out the body
regions its slot hides (`HIDES`: chest hides the torso, legs the hips and legs, and so on).
Every armour asset carries three checks: each piece is bound to its slot's bones; what a piece
hides lies inside it (run each limb plate all the way to its joint); limb plates stand at least
6 mm off the body. Plate is `plate_worn()`: dull steel with hammer marks and rust in spots, never
the blotched `iron_rusted()` over a whole harness. Reference: `assets/arm_footman_iron.py`.

**First-person view models** are separate assets with the camera at the origin, looking down -Z
(70 degrees, 16:9, near plane 5 cm): forearm from an elbow that is out of frame, the world
weapon's own meshes in `socket_hand.R`, clips `idle` and an attack. Checks: nothing nearer than
the near plane, the whole weapon in frame at rest, the arm leaving by the bottom or right edge,
the attack crossing the centre line. Reference: `assets/wpn_longsword_iron_fp.py`.

## 10. Weapons, items, icons

- Weapons: `BUDGET_OF["weapon"]`, held-item convention, 1,024 px per metre. Blade `steel_blade`,
  fittings `iron_rusted` or a flat metal, grip leather. First-person view models are separate
  assets (`viewmodel`).
- Items lie or stand as they would be found; dynamic ones have the origin at the centre of
  their bounds (the world kit centres colliders on the entity).
- Icons: 128 px source shown at 64, readable at 32: a dark outline, one highlight, a
  silhouette that matches the model. One generator per item family, on one sheet per family
  (`ui_item_icons`). Cinder's UI draws no images yet: icons are built ahead.

## 11. Sound

Names: `sfx_<family>_<material or source>_<variant>`, for example `sfx_step_stone_03`,
`sfx_hit_blade_flesh_02`, `mus_village_dusk`. Variants are numbered from 01; a family ships at
least four of anything heard repeatedly, so a game can avoid playing the same one twice running.

`SOUND_PEAK[family]` (dBFS) keeps any footstep usable with any surface and any weapon with any hit:

| Family | Peak | Form |
|---|---|---|
| `step`, `ui`, `cloth` | -8 | mono, spatial (ui: not spatial) |
| `swing`, `foley`, `door` | -6 | mono, spatial |
| `hit`, `spell`, `voice`, `creature` | -3 | mono, spatial |
| `ambience`, `music` | -8 | stereo, not spatial, streamed, loops whole |

A family is one recipe in `assets/_frp_sound.py` and one small asset script per variant
(`write_family("stone", "assets")`). Family checks: variants within 3 dB RMS of each other, and
no two more than 0.6 alike by cross-correlation. Sounds a synthesiser does badly (throats, voices,
animals) come from `gen.sound` and are only trimmed and levelled here; they stay uncleared until
a person has listened. Voices are non-verbal only (grunts, breaths, cries). Every claim a Spec makes about a sound has
a `band` check; nobody in the pipeline can listen.

## 12. Before an asset is done

1. Spec written first; every line a check.
2. `ready YES`; the preview read, beside the 1.8 m figure.
3. Colours from the palette, sizes from the ruler, budget from `BUDGET_OF`.
4. For kit pieces: placed in a scene and looked at from all three cameras.
5. For anything worn or held: built on the mannequin in all four shapes.
6. Nothing generated ships uncleared; no real person, brand, or another game's design.
