# ash10's Fantasy RPG Pack: inventory and plan

Status: planning, 2026-11-17. Nothing in this document is built except where "exists" is marked
(the Dungeon Kit and Sandbox Kit, `docs/game-assets-plan.md`). Name: **ash10's Fantasy RPG Pack**.
All twelve planning questions are answered (sections 1 and 12).

The aim: every asset a team needs to build a complete high-fantasy adventure RPG on Cinder,
from the title screen to the final boss, without making or buying anything else.

## 1. Decisions (yours, 2026-11-17)

| Decision | Choice | What it means for the pack |
|---|---|---|
| Art style | **Stylised mid-poly** | Chunky readable shapes, hand-painted-looking textures, one palette. Budgets in section 3. |
| Game types | **Third-person, top-down / isometric, and first-person, from one set** | Every environment works at eye level, from above (roofs and upper floors lift off) and from inside (ceilings, interior faces, door frames you walk through). First person adds hand-and-weapon view models. |
| Tone | **Dark fantasy throughout** | Blood, gore and grim props are part of the main pack, not an add-on (section 7.17). The shop listing carries a content label. |
| Peoples | **Five playable peoples** | Human, elf-like, dwarf-like, halfling-like, orc-like, on four body shapes; all armour fits all five. |
| First person | **Separate view models** | Dedicated arms and weapon meshes with their own camera and about 48 clips. |
| Terrain | **Modular ground pieces** | Tiles, slopes, cliffs and banks on the grid; no sculpted landscape chunks. |
| Licence | **Free in CinderCore, paid on the shop** | Bundled with CinderCore for games made on Cinder; a commercial licence on the shop for any engine. Not CC0. |
| Genre staples | **Redesigned as our own** | The biting chest, the slime cube and the owl-headed bear become three original creatures. |
| Voices | **Non-verbal only** | Effort, pain, laughter and creature voices; no spoken words. |
| First release | **A free starter slice** | A small complete slice released free first, leading to the sub-packs. |
| Packaging | **Modular sub-packs plus a complete bundle** | Sixteen sub-packs sharing one style guide; fourteen are usable and sellable alone, and two (the animation library, the sample worlds) ship inside others. CinderCore ships the bundle; the shop may sell both. |

## 2. Principles the whole pack holds

1. **One world, one ruler.** Metres, Y up. A person is 1.8 m; the grid is 2 m; walls are 3 m
   (4 m in halls); doors open 1.2 x 2.2 m; stairs rise 0.2 m per step. Everything in every
   sub-pack snaps to that, so a village house stands on a dungeon floor tile without adjustment.
2. **Three cameras.** Top-down: buildings split into foundation, storey and roof pieces that hide
   independently. First person: no missing back faces at eye level, ceilings exist, props are
   detailed where a hand reaches. Third person: silhouettes read at 10 m.
3. **Modular before unique.** A building is walls, corners, doors, windows, roofs; a hero is a
   body, armour pieces and a weapon; a dungeon room is tiles. Unique hero pieces come last.
4. **Ours to license.** Inspired by the genre, not by any product. Creatures come from folklore
   and from our own designs; no setting-specific monsters, names, deities, spells or art from
   Dungeons & Dragons or any other property (section 9). Licence: free with CinderCore for
   games made on Cinder, a paid commercial licence on the shop for any engine (the licence
   text is still to be written). The existing CC0 Dungeon Kit assets stay CC0 as published;
   their restyled successors in this pack take the new licence.
5. **Proven in the engine.** Every asset passes the pipeline's ladder (`ready YES`), every
   sub-pack has a demo world or scene, and the bundle has a playable slice (section 7.15).
6. **Honest about the engine.** Cinder 0.1.1 cannot yet draw skinned models in world files,
   honour alpha, draw UI images, play audio from a world file, or emit particles. Section 8 says
   what each gap blocks and how the pack is built so it is correct the day the gap closes.

## 3. Style guide (fixed in `fantasy-rpg-style-guide.md` and `assets/_frp.py`; summary here)

**Palette.** One master palette of about 48 colours, weighted dark: cold and soot-stained
stone, weathered and rotten wood, three metals (iron with rust, tarnished bronze, dull gold),
worn leather, cloth dyes in muted natural tones, foliage that leans autumn and blight, and
accents kept for things that matter: arcane blue, fel green, holy gold, and blood in three
states (fresh, dried, old stain).

**Tone.** Dark fantasy: a world past its best, with real menace. Stylised, not photoreal, so
gore reads as part of the style rather than as shock. Limits in section 7.17.

**Materials.** Metallic-roughness PBR. Painted base colour with ambient shading baked in
lightly; normal maps for surface form (planks, stone courses, cloth weave), not for
silhouette. Roughness carries the material read. Emissive only for light sources and magic.

**Budgets.**

| Class | Triangles | Textures | Materials |
|---|---|---|---|
| Hero or major NPC (body + default outfit) | 8,000-15,000 | 2k atlas | 1-2 |
| Armour or outfit piece | 500-2,500 | shares the set's atlas | 1 |
| Common monster | 3,000-8,000 | 1k-2k | 1 |
| Large monster or boss | 12,000-30,000 | 2k | 2-3 |
| Weapon or shield | 300-1,500 | 512-1k (set atlas) | 1 |
| First-person view model (arms + weapon) | 4,000-8,000 | 2k | 2 |
| Small prop | 100-800 | set atlas | 1 |
| Furniture, large prop | 500-3,000 | 1k | 1 |
| Modular building piece | 50-1,500 | tiling + trim sheet | 1-2 |
| Tree | 800-3,000 | 1k | 2 |
| Texel density | 512 px per metre; 1,024 for first-person held items and hero faces | | |

**Shared textures.** Per kit: two or three tiling materials (stone, wood, plaster), one trim
sheet, one prop atlas. Cinder uploads a texture once per model today (engine gap 9), so the
shared sheets are small and the manifest names them, ready for sharing when the engine can.

**Naming.** `snake_case`, unique across the bundle, prefixed by sub-pack: `vil_`, `dun_`,
`cas_`, `nat_`, `int_`, `wpn_`, `arm_`, `itm_`, `mon_`, `npc_`, `hero_`, `fx_`, `ui_`, `sfx_`,
`mus_`. The existing Dungeon Kit keeps its names.

## 4. The sub-packs at a glance

| # | Sub-pack | What it is | Assets (est.) | Depends on |
|---|---|---|---|---|
| 1 | Heroes | Playable bodies, faces, hair, class outfits, view-model arms | 150 | Blender; engine gap 10 |
| 2 | Armour and outfits | Modular wearables in material tiers | 180 | Blender; sub-pack 1's rig |
| 3 | Weapons and shields | Melee, ranged, magic foci, ammunition | 140 | - |
| 4 | Townsfolk and NPCs | Villagers, guards, merchants, quest givers, mounts and pets | 70 | Blender; sub-pack 1's rig |
| 5 | Monsters | 63 creatures in 12 families, 8 bosses | 71 | Blender |
| 6 | Animation library | Shared clip sets for humanoids and each creature rig | 320 clips | sub-packs 1, 5 |
| 7 | Dungeons | Six dungeon themes on the grid, traps, puzzles (extends the Dungeon Kit) | 260 | exists in part |
| 8 | Village and town | Modular houses with interiors, shops, streets, market | 240 | - |
| 9 | Castle and fortress | Walls, towers, gatehouse, keep, siege props | 120 | - |
| 10 | Wilderness | Four biomes: terrain pieces, trees, rocks, plants, water, roads | 280 | alpha fix for foliage |
| 11 | Interiors and furniture | Tavern, smithy, shops, library, alchemist, temple, camp | 300 | - |
| 12 | Items and loot | World models and icons for everything in an inventory | 220 + 300 icons | - |
| 13 | Magic and effects | Spell meshes, auras, projectiles, hit and status effects | 90 | engine: particles, alpha |
| 14 | Interface | HUD, inventory, sheets, dialogue, map, shop, menus, fonts, cursors | 60 screens and sets | engine: UI images |
| 15 | Audio | Effects, ambience, music, UI sounds, creature and voice barks | 420 sounds, 24 tracks | - |
| 16 | Worlds and samples | Demo scenes per sub-pack, prefabs, a playable slice | 20 worlds, 80 prefabs | everything |

About **2,200 models, 320 animation clips, 300 icons, 60 interface pieces, 440 sounds and 20
worlds**, including roughly 100 dark-fantasy pieces spread through the sub-packs (section 7.17). Sub-packs 6 and 16 are not sold alone: 6 ships inside 1, 4 and 5; 16 inside the bundle.

## 5. What exists already

| Have | Count | Use in this pack |
|---|---|---|
| Dungeon Kit: floor, walls, doorway, corner, pillar, stairs, door, plate, torch, chest, gem, crate, barrel, lantern | 14 models | The seed of sub-pack 7 (stone dungeon theme) and of 11 and 12. Restyled to the new guide where needed. |
| `adventurer`, `robot_character` | 2 rigs | Proves the biped rig, skinning and clip pipeline. The adventurer is replaced by sub-pack 1's heroes. |
| 11 sounds | | Seed of sub-pack 15. |
| `dungeon_hud`, `pause_menu`, `title_screen`, `block_caps`, `hud_icons`, `ui_frames` | | Seed of sub-pack 14. |
| Sandbox Kit | 15 models | Separate product; shares scale and grid. |

## 6. Shared systems to design before any sub-pack

Status 2026-11-17: 1, 2, 4, 6, 7 are built and proven by `assets/hero_mannequin.py` (35 bones, eight
sockets, four shapes) and `packs/frp_style_test.py`; 3, 8 and 9 are specified in the style guide
(`SLOTS`, `SOUND_PEAK`, icon rules) with no fitted armour or sound family built yet; 5 is not started.

These are decisions more than assets; each is a short spec with a test asset.

1. **The humanoid rig.** One skeleton for every humanoid (heroes, NPCs, humanoid monsters):
   the current 18 bones plus fingers (3 per hand as mitten, thumb, index), toes, jaw, eyes,
   and attachment bones: `hand_r`, `hand_l`, `back`, `hip_l`, `hip_r`, `head_top`, `shield`,
   `quiver`. About 40 bones; Cinder's limit is 256.
2. **Body proportions.** Four body shapes on that one skeleton by bone scale and mesh:
   standard, stout (dwarf-like), slight (halfling-like), tall (orc-like). Armour is fitted
   per shape by the build, not modelled four times.
3. **Modular armour slots.** head, shoulders, chest, arms, hands, belt, legs, feet, cloak,
   plus full-body robes. Each piece hides the body region under it (no skin poking through).
4. **Sockets and grips.** Every weapon has a `grip` origin and a forward axis; every shield a
   `strap`; every wearable a slot. Checked by the build.
5. **First-person view models.** Separate arms-and-weapon meshes with their own closer camera
   (decided), each weapon class with first-person clips; bare and gloved arms per body shape.
6. **The building kit grammar.** Wall, corner, door, window, floor, ceiling, stair and roof
   pieces on the 2 m grid, each storey 3 m, with a rule for what hides in top-down view.
7. **Terrain.** Cinder has no terrain system: modular ground tiles (2 m and 8 m) with slope,
   cliff and bank pieces on the grid (decided). The spec fixes edge profiles so any tile meets any other.
8. **Icon style.** 128 px source, 64 px shown, the `hud_icons` construction: dark outline,
   one highlight, readable at 32 px. One generator per item family so icons match their models.
9. **Sound families.** A naming and loudness standard so any footstep works with any surface
   and any weapon with any hit: `sfx_<family>_<material>_<variant>`.

## 7. The inventory

Counts are distinct assets. "x3" means three variants of one design. **B** marks work that
needs the Blender integration (sculpted or organic forms, complex unwraps, skin weights on
organic bodies); unmarked work the present pipeline can do.

### 7.1 Heroes (150) B

The player character, any class, any of five peoples, both body presentations.

- **Bodies (10):** five peoples x two builds (masculine, feminine), all on the shared rig:
  human, elf-like (tall, slight, pointed ears), dwarf-like (stout), halfling-like (slight,
  small), orc-like (tall, heavy, tusks). Own names for the peoples (section 9).
- **Heads and faces (30):** three face shapes per people; five skin tone sets as palette swaps;
  expressions through jaw and eye bones plus four morph targets (blink, smile, frown, shout:
  Cinder allows 8).
- **Hair and beards (36):** 20 hair styles, 10 beards and moustaches, 6 brows; colour by
  palette. Built as solid sculpted shapes, not alpha cards, because Cinder ignores alpha.
- **Underclothes (4):** the body is never bare: tunic and trousers, two sets, two builds.
- **Class starter outfits (40):** eight classes x five pieces (head, chest, arms, legs, feet),
  one distinctive look each: warrior, rogue, ranger, wizard, cleric, paladin, bard, druid.
  These are the tier-1 items of sub-pack 2 in class colours.
- **First-person view models (16):** bare arms and gloved arms x four body shapes, two builds.
- **Portrait renders (10):** a bust render per body for menus (an image, built ahead).
- **Character creator data (4):** the manifest of what combines with what, as JSON.

### 7.2 Armour and outfits (180) B

- **Material tiers (5):** cloth, leather, chain, plate, and a rare "runed" tier.
- **Slots per tier (9):** head, shoulders, chest, arms, hands, belt, legs, feet, cloak.
- **Sets:** cloth x3 looks (apprentice, mage, noble), leather x3 (scout, rogue, hunter),
  chain x2 (guard, mercenary), plate x3 (knight, paladin, dark knight), runed x2. That is 13
  sets x 9 = 117 pieces.
- **Robes and full-body garments (12):** wizard robe x3, priest vestment x3, peasant dress x2,
  noble gown x2, monk habit, hooded traveller.
- **Headwear (20):** hoods x4, wizard hats x3, circlets x3, crowns x2, helms beyond the sets
  x6 (horned, winged, great helm, kettle, barbute, skull), masks x2.
- **Cloaks and capes (10):** solid meshes with four spine-driven bones for motion.
- **Accessories (21):** belts and pouches x6, quivers x3, backpacks x3, bedroll, amulets x4
  (visible on chest), bracers x2, sashes x2.

### 7.3 Weapons and shields (140)

Each family in three visual tiers (common iron, fine steel, legendary with emissive detail),
with a grip socket and, where it applies, a sheath or back position.

- **Swords (18):** dagger, short sword, long sword, greatsword, scimitar, rapier x3 tiers.
- **Axes and hammers (18):** hand axe, battle axe, great axe, mace, war hammer, maul x3.
- **Polearms (12):** spear, halberd, glaive, quarterstaff x3.
- **Ranged (15):** short bow, long bow, crossbow, hand crossbow, sling x3; strings are thin
  geometry with a bone for the draw.
- **Ammunition (8):** arrows x3, bolts x2, sling stones, quiver fill, throwing knives.
- **Magic foci (18):** staves x6, wands x6, orbs x3, tomes x3 (open and closed poses).
- **Shields (15):** buckler, round, heater, kite, tower x3.
- **Improvised and tools as weapons (10):** club, pitchfork, sickle, torch (held), pickaxe,
  shovel, woodcutter's axe, fishing rod, lute (bard), holy symbol.
- **Monster weapons (14):** crude cleavers, bone clubs, rusted blades, spiked shields, shaman
  staff, giant's tree club.
- **Sheaths and holders (12):** scabbards x4, bow case, back harness, belt loops.

### 7.4 Townsfolk and NPCs (70) B

Bodies come from sub-pack 1; these are outfits, heads and props that make people.

- **Villagers (18):** farmer, farmhand, miller, baker, fisher, shepherd, child x2, elder x2,
  beggar, washerwoman, woodcutter, hunter, miner, stable hand, drunk, traveller.
- **Trades (14):** blacksmith, innkeeper, barmaid or barman, merchant x3 (general, arms,
  exotic), alchemist, herbalist, librarian, tailor, jeweller, cartwright, scribe, healer.
- **Authority (10):** town guard x3, captain, noble x2, mayor, tax collector, herald, executioner.
- **Faith and magic (8):** priest x2, acolyte, monk, hedge wizard, court mage, fortune teller, hermit.
- **Underworld (6):** thief, fence, smuggler, assassin, bandit recruiter, cultist.
- **Mounts and animals (14):** horse x3 coats (with saddle and tack as separate pieces), pony,
  mule with packs, ox and cart, dog x2, cat, chicken, pig, sheep, cow, goat. Quadruped rig.

### 7.5 Monsters (71) B

Twelve families, each with a weak, a standard and an elite form where that makes sense, so a
game has enemies for every level. All from folklore or our own design (section 9).

| Family | Creatures | Rig |
|---|---|---|
| Goblinoids | goblin grunt, goblin archer, goblin shaman, hobgoblin-like soldier, brute | humanoid |
| Orc-kin raiders | raider, berserker, warlord, drummer | humanoid |
| Undead | skeleton warrior, skeleton archer, skeleton mage, zombie, ghoul, wraith, mummy, death knight | humanoid; wraith has no legs |
| Beasts | wolf, dire wolf, bear, boar, giant rat, giant bat, giant spider x2 sizes, snake, giant scorpion | quadruped, spider, serpent, flyer |
| Vermin and oozes | slime x3 colours and sizes, carrion beetle, swarm of rats (as one mesh) | blob (morphs), insect |
| Giants | ogre, troll, hill giant, cyclops | large humanoid |
| Constructs | stone golem, iron golem, animated armour, clockwork sentinel, living statue | humanoid, rigid parts |
| Elementals | fire, water, earth, air (mesh bodies with emissive and morph motion) | custom |
| Fey and plant | sprite, dryad-like spirit, treefolk, mushroom folk x2, vine horror | humanoid, plant |
| Mythic beasts | griffin, harpy, minotaur, basilisk, manticore, chimera, hydra | mixed |
| Dark folk | bandit x3, cultist x3, dark mage, vampire, werewolf (two forms), necromancer | humanoid |
| Dragons | wyvern, drake, young dragon, ancient dragon x3 colours by material | dragon (wings, neck, tail) |

- **Bosses (8, part of the count):** goblin king, lich, ancient dragon, demon lord of our own
  design, spider queen, giant king, vampire lord, corrupted treefolk elder.
- **Three originals in place of single-origin staples (3, decided):** the *hoardling*, a
  strongbox that stands up on jointed iron legs and snaps its lid; the *amber glut*, a rolling
  mass of translucent resin with the remains of its meals held inside; the *hornbear*, a
  heavy bear-beast with a ram's horns and a boar's bristled back. They fill the same roles
  (the trap in the treasure room, the corridor blocker, the forest brute) with our own designs.

### 7.6 Animation library (about 320 clips) B

Clips are authored once per rig and shared by everything on it. All loop or return to idle,
all in place, gaits phase-matched (left foot strikes at phase 0).

- **Humanoid locomotion (22):** idle x3, walk, run, sprint, strafe left and right, walk
  back, crouch idle, crouch walk, jump start, in air, land, roll, climb ladder, swim,
  turn in place x2, sit, stand up, fall.
- **Humanoid combat, per weapon class (8 classes x 9 = 72):** ready stance, attack x3 combo,
  heavy attack, block, block hit, parry, draw and sheathe. Classes: unarmed, one-handed, sword
  and shield, two-handed, dual wield, polearm, bow, crossbow.
- **Casting (12):** cast forward, cast up, cast ground, channel loop, two-handed cast, staff
  cast, wand flick, summon, buff self, heal, fail, counter.
- **Reactions (14):** hit light x4 directions, hit heavy, stagger, knockdown, get up, death
  x3, stun loop, frozen, burning.
- **Interaction (24):** pick up, use, open door, open chest, pull lever, push, talk x3,
  listen, wave, bow, cheer, point, shrug, eat, drink, read, write, hammer (smith), sweep,
  dig, mine, chop.
- **First person (48):** per weapon class: idle, walk bob, attack x3, block, draw, sheathe;
  plus cast, interact, torch.
- **NPC ambient (16):** lean, sit on bench, sit at table, sleep, pray, guard stand, patrol
  look, argue, laugh, beg, dance, play lute, tend bar, serve, cower, flee.
- **Creature sets:** quadruped (idle, walk, run, attack x2, hit, death, howl: 8 each for
  wolf, bear, boar, horse-type); spider (7); flyer (8); serpent (6); dragon (16: includes
  breath, fly, land, take off); slime (5, by morph targets); large humanoid reuses the
  humanoid set with three unique attacks. About 110 clips.

### 7.7 Dungeons (260)

Six themes, each a complete kit on the 2 m grid with the same piece list, so a level made in
one theme can be re-skinned in another.

- **Per theme, structural (26):** floor x3 variants, wall, wall half, wall with torch niche,
  doorway, archway, corner inner and outer, pillar, half pillar, column broken, stairs up,
  stairs spiral, ramp, ledge, railing, ceiling flat, ceiling vault, ceiling beam, window
  slit, grate floor, pit edge, secret door wall, collapsed wall, rubble pile.
- **Themes (6 x 26 = 156):** stone dungeon (exists in part), crypt and catacomb, natural
  cave (irregular pieces: B), mine (timber shoring, rails), sewer (channels, pipes, water
  planes), ruined temple (carved, overgrown).
- **Doors and gates (14):** wooden door, reinforced door, iron door, double door, portcullis,
  jail door, secret door, trapdoor, each with frame; locked variants by a visible lock.
- **Traps and mechanisms (24):** pressure plate (exists), spike trap, arrow wall, swinging
  blade, falling ceiling, pit cover, flame jet, poison vent, rolling boulder and track,
  lever x2, wheel, chain and winch, floor switch, rune plate, tripwire, crushing wall, dart
  statue, counterweight, pulley, cage on chain, drawbridge small, sluice gate, timed gate.
- **Dungeon dressing (46):** torch (exists), brazier, standing candelabra, chain x3, shackles,
  skeleton remains x4, coffin, sarcophagus x2, urn x3, altar x2, statue x4, idol, cobweb x3
  (geometry), bones pile, treasure pile x3, cell cot, bucket, crate and barrel (exist), mine
  cart, rail pieces x4, ore veins x3, crystal clusters x3, stalagmites x4, rope bridge, planks.
- **Puzzle pieces (20):** rotating statue, mirror and light beam source, rune pillars x4,
  weighted blocks x2, pedestal, key slots x3, coloured braziers x4, sliding wall, riddle
  plaque, constellation floor.

### 7.8 Village and town (240)

Buildings are kits, not blocks: every house has an interior, and roofs and storeys lift off.

- **Wall system, three styles (3 x 22 = 66):** timber frame and plaster, stone, wooden plank.
  Each: wall, wall half, wall with window x2, wall with door, corner, gable end x2 pitches,
  jetty overhang, interior wall, interior doorway, floor, ceiling with beams, stair straight,
  stair turning, chimney breast, foundation, porch post, balcony, shutter, door, window frame.
- **Roofs, three coverings (3 x 12 = 36):** thatch, clay tile, wood shingle: slope, ridge, end,
  hip, valley, dormer, chimney x2, eave, corner, tower cone, lean-to.
- **Ready-made buildings as prefabs (16, built from the kit):** cottage x3, farmhouse, inn
  and tavern, smithy, general store, bakery, mill (wind or water), chapel, town hall, guard
  post, stable, barn, market stall hall, wizard's tower.
- **Street and yard (48):** cobble road straight, corner, T, cross, end; dirt path set x5;
  kerb, steps, bridge stone x3 pieces, bridge wood, well, fountain, market stalls x4, awnings
  x3, signposts x2, hanging shop signs x10 (blank board plus ten trade emblems), street lamp,
  notice board, stocks, gallows, statue, bench, trough, hitching post, cart, wagon, wheelbarrow,
  hay bale, woodpile, fence wood, fence stone, gate, garden bed, scarecrow.
- **Harbour and river (20):** dock pieces x5, pilings, rowboat, fishing boat, net rack, crane,
  crates of fish, barrels, rope coils, buoy, lighthouse (prefab), water plane tiles x3.
- **Farm (18):** field strip crops x4 (wheat, cabbage, pumpkin, grapes: geometry plants), plough,
  beehive, chicken coop, pig pen fence, feeding trough, orchard tree x2, haystack, windmill
  sails, water wheel, silo, vegetable crates x2.
- **Tents and camps (16):** tent x3, pavilion, bedroll, campfire lit and out, cooking pot and
  tripod, log seat, banner pole x3 heraldry of our own, weapon rack, supply crates, wagon camp.
- **Graveyard (20):** headstone x6, crypt entrance, mausoleum, iron fence, gate, dead tree,
  open grave, coffin, shovel, lantern post, angel statue, crow (static), mound, wreath, bench.

### 7.9 Castle and fortress (120)

- **Curtain wall (16):** wall section, wall with walkway, crenellation, stair to walkway,
  wall corner, wall end, breach (ruined), arrow loop, machicolation, buttress, postern door,
  drain, hoarding, banner mount, torch bracket, foundation slope.
- **Towers (14):** round and square tower in three storeys each, roof cone, roof flat, spiral
  stair core, tower door, tower window.
- **Gatehouse (10):** gate arch, portcullis, great doors, drawbridge, winch room, murder
  holes, flanking tower join, bridge pier, chain, guard room.
- **Keep (22):** great hall walls, columns, dais, throne x2, long table and benches, hearth
  great, gallery, stained window frames x3 (coloured solid panes), tapestry (generated art:
  each needs clearing), banner x4, chandelier, minstrel balcony, royal bed, war table with map.
- **Yards and works (20):** training dummy x2, archery butt, weapon racks x3, armour stand,
  forge and anvil, smith's tools, stables stalls, kennel, well covered, chapel altar, cistern.
- **Dungeon below (10):** cells, rack, stocks, iron maiden, brazier with irons, warden's
  desk, keys ring, oubliette grate, chains, straw. More in section 7.17.
- **Siege (12):** catapult, ballista, battering ram, siege tower, mantlet, stake wall, trench
  planks, pitch cauldron, boulder pile, ladder, palisade x2.
- **Ruined variants (16):** broken versions of the eight most-used wall and tower pieces, with
  rubble and ivy geometry.

### 7.10 Wilderness (280)

Four biomes sharing one piece list where possible: **temperate forest**, **mountain and
snow**, **swamp**, **arid badlands**. Foliage is built as geometry, because alpha-cut leaf
cards do not render in Cinder today; alpha-card versions are planned for after the fix.

- **Ground and terrain (per biome 12 = 48):** ground tile flat x3, slope, cliff face x3,
  cliff corner, ledge, path overlay x2, bank to water. Modular, on the grid (decided).
- **Trees (40):** per biome 8: three species in two or three sizes, a dead tree, a stump, a
  fallen log. B for trunks and canopy forms.
- **Rocks (32):** boulder x4, rock cluster x3, standing stone, per biome material.
- **Plants and undergrowth (56):** bushes x3, ferns, tall grass clump, flowers x4, mushrooms
  x4, reeds, lily pads, cactus x3, thorn bush, vines hanging x3, roots, moss patch, berry
  bush, herb plants x8 (gatherable, each matches an item in sub-pack 12).
- **Water (14):** river straight, bend, fork, waterfall (mesh with scrolling-ready UVs),
  pond, lake edge x3, stepping stones, ford, swamp pool x2, ice sheet, hot spring.
- **Roads and travel (22):** dirt road set x6, milestone, waymark cairn, wooden bridge x3,
  rope bridge, fallen-tree bridge, signpost, shrine roadside x2, abandoned cart, campsite
  ring, toll gate, ruined wall x3.
- **Landmarks (28):** standing stone circle, ancient ruin pieces x8, giant skeleton, cave
  mouth x3 (joins sub-pack 7 caves), abandoned tower, obelisk x2, fairy ring, world tree
  stump, crashed meteor, dragon nest, bandit palisade x4, hermit hut, wizard's stone, altar.
- **Gatherables and nodes (20):** ore nodes x5 (iron, copper, silver, gold, crystal), herb
  nodes x8, wood pile, fishing spot marker, bird nest, beehive wild, treasure dig spot, bones.
- **Sky and weather (20):** these are data and textures: sky colour presets x8 (dawn, day,
  dusk, night, overcast, storm, fog, eerie), sun and moon settings, fog presets, plus
  rain and snow as effects that wait for particles (section 8).

### 7.11 Interiors and furniture (300)

Each room type is a complete set, sized for first-person play (things at hand height carry
the detail).

- **Common furniture (60):** tables x6, chairs x5, stools x3, benches x3, beds x5 (straw,
  cot, common, fine, royal), wardrobes x3, chests x4 (chest exists), shelves x5, cupboards
  x3, desks x3, cabinets x3, rugs x6 (solid, patterned by code), curtains x3, room dividers,
  ladders x2, coat rack, mirror, washstand, bathtub, chamber pot.
- **Lighting (20):** candle x3, candlestick x3, candelabra x2, lantern (exists), hanging
  lantern, oil lamp, chandelier x3, wall sconce x2, torch (exists), brazier, fireplace x3.
- **Tavern (30):** bar counter pieces x4, kegs x3, tankards x3, bottles x6, plates and bowls
  x4, food x8 (bread, cheese, roast, stew, pie, fruit, fish, sausage), dartboard, card table,
  notice board, stage, trophy head (our own beast), mop and bucket.
- **Kitchen (20):** hearth with spit, oven, cauldron x2, pots x3, pans x2, knives, cutting
  board, sacks x3, hanging herbs, hanging game, water barrel, butter churn, pantry shelf.
- **Smithy (20):** forge, bellows, anvil, quench trough, grindstone, tool rack, tongs x2,
  hammers x3, ingots x4, half-made sword, horseshoes, coal pile, armour stand, workbench.
- **Shops (30):** counters x3, display cases x3, weapon wall rack, armour mannequin x2,
  shelves stocked x6 (general, potions, books, cloth, food, curios), scales, coin trays,
  till box, crates open x4, cloth bolts x4, shop sign interior, strongbox.
- **Library and study (26):** bookshelf x4, book stacks x5, open book x3, scrolls x4, scroll
  rack, lectern, globe, astrolabe, telescope, map table, inkwell and quill, writing desk,
  candle clock, hourglass, skull on desk, chalkboard with our own diagrams.
- **Alchemist and mage (30):** alembic, retort, flasks x6, mortar and pestle, cauldron
  bubbling, ingredient jars x8, herb drying rack, crystal ball, summoning circle (floor
  decal as geometry), spell focus stand, caged familiar, potion rack, ritual candles,
  enchanting table, rune stones x4, bone charms.
- **Temple and shrine (24):** altar x3, pews, font, incense burner, holy symbols x6 of our own
  pantheon, statue of a deity x3, offering bowl, prayer mat, reliquary, bell, candle rack,
  tomb effigy, stained panel frames x3.
- **Barracks and jail (20):** bunk, footlocker, weapon rack x3, armour rack, guard desk,
  wanted posters x4 (generated or drawn art), keys, cell bars, cot, manacles, duty roster.
- **Clutter (20):** the small things that make a room lived in: coins, dice, cards, pipe,
  cup, spilled wine, crumbs plate, letter x3, quill, sewing kit, toy x2, boots, hat, broom,
  bucket, rope coil, rag.

### 7.12 Items and loot (220 world models + 300 icons)

Everything that can be in an inventory, as a world model (lying on a table, dropped on the
ground) and as an icon. Weapons and armour take their icons from sub-packs 2 and 3.

- **Potions (24):** health, mana, stamina in three sizes; antidote, fire resist, frost
  resist, strength, speed, invisibility, water breathing, night sight, poison x3, elixir,
  holy water, oil flask, acid flask, empty bottles x3.
- **Food and drink (24):** the eight tavern foods plus raw meat, cooked meat, fish x2, apple,
  berries, carrot, mushroom, honey, egg, cheese wheel, trail ration, waterskin, ale, wine, tea.
- **Ingredients (30):** eight herbs, monster parts x10 (fang, claw, hide, wing, eye, venom
  sac, bone, horn, scale, ectoplasm), minerals x6, salts and powders x6.
- **Crafting materials (24):** ore x5, ingots x5, leather x3, cloth x3, wood x3, gems x5.
- **Valuables (22):** coin x3 metals, coin pile x3, purse, gems cut x6, ring x3, necklace
  x2, goblet, crown, idol, pearl.
- **Keys and quest items (24):** keys x6, lockpick, letter sealed, map fragment x3, journal,
  ancient tablet, holy relic, orb of power, dragon egg, signet ring, wanted poster, deed,
  crystal shard x3, music box, broken sword hilt, compass, spyglass.
- **Scrolls and books (18):** scroll x6 colours, spell tome x6 schools, recipe, skill book
  x3, bestiary, ledger.
- **Tools (20):** torch, lantern, rope, grappling hook, pickaxe, shovel, fishing rod,
  bedroll, tent pack, tinderbox, bandage, trap kit, crowbar, hammer, saw, sickle, bucket,
  whetstone, repair kit, cooking pot.
- **Containers and loot sources (14):** chest x4 tiers (exists x1), barrel and crate (exist),
  sack, urn, strongbox, corpse marker bag, treasure pile x3, buried cache.
- **Icons (300):** one per inventory item across sub-packs 2, 3 and 12, plus 60 skill and
  spell icons, 30 status effect icons, 20 map markers. Built ahead (engine gap: UI images).

### 7.13 Magic and effects (90)

Cinder has no particle system, so effects are built as meshes with emissive materials,
morph targets and UV-scroll-ready strips, designed to gain particles later.

- **Projectiles (16):** fire bolt, fireball, ice shard, frost orb, lightning bolt (mesh
  strip), arcane missile, poison glob, shadow bolt, holy bolt, rock throw, arrow trail,
  magic arrow x3 elements, wind slash, thrown potion.
- **Area and ground (18):** summoning circle x4 schools, fire patch, ice patch, poison
  cloud volume, healing circle, consecrated ground, web, entangling roots, earthquake
  cracks, wall of fire, wall of ice, wall of stone, gravity well, shield dome, portal.
- **Auras and buffs (14):** shield bubble, haste streaks, strength glow, stealth shimmer,
  regeneration, burning, frozen, poisoned, stunned stars, cursed, blessed halo, enraged,
  levitate, mana shield.
- **Impacts (14):** hit spark, blood spray x3 (light, heavy, arterial), block spark, magic
  impact x4 elements, explosion, shatter, splash, dust puff, critical burst.
- **Summons and transformations (10):** spirit weapon, spectral hand, familiar x3, skeleton
  rising pieces, treant sprout, portal frame, teleport flash, polymorph puff.
- **World effects (18):** fire for torches and braziers x3 sizes (replaces the static flame),
  smoke column, chimney smoke, waterfall mist, fountain water, magic crystal glow, lava
  surface, glowing mushrooms, fireflies (geometry), god rays plane, treasure sparkle,
  quest marker beam, save point crystal, level-up burst, loot beam x3 rarities.

### 7.14 Interface (about 60 screens and sets)

UI documents for what Cinder can draw today (text, panels, buttons, toggles, sliders), with
the art sets built ahead for when it can draw images.

- **Fonts (4):** Block Caps (exists) for titles; a readable text face with lowercase for
  dialogue and descriptions (needed: the engine's Roboto is the only body font today); a
  runic or blackletter display face for the title and chapter headings; a numeral face for damage.
- **HUD (10):** health, mana and stamina bars; action bar with ten slots; minimap frame;
  compass strip; quest tracker; target frame; party frames; buff and debuff row; interaction
  prompt; damage numbers style; boss health bar.
- **Core screens (16):** title, new game, load and save slots, options (video, audio,
  controls, gameplay: four screens), pause (exists), character creation (four steps),
  loading with tip, death and game over, credits.
- **Character screens (12):** inventory grid, equipment paper doll, character sheet
  (attributes, skills), skill tree, spell book, quest journal, map and fast travel,
  bestiary, crafting, alchemy, enchanting, party management.
- **World interaction (10):** dialogue with choices, barter and shop, container loot,
  lockpick minigame, rest and wait, level up, notification toasts, tutorial pop-up,
  confirmation dialog, tooltip styles (item, skill, compare).
- **Art sets, built ahead (12):** 9-slice frames in four styles (parchment, wood, stone,
  metal: `ui_frames` is the seed), button sets x3, bar fills x6, slot frames by rarity x5,
  cursors x8 (default, attack, talk, loot, locked, use, spell target, move), ornaments and
  dividers, map tiles and icons, portrait frames, checkbox and slider art, scroll and
  banner headers.
- **Icons:** counted under 7.12.

### 7.15 Audio (about 420 sounds and 24 music tracks)

Synthesised where code does it well; generated (ElevenLabs) or recorded where it does not
(creature voices, human barks, realistic foley), each generated sound cleared by a person.

- **Footsteps (48):** six surfaces (stone, wood, dirt, grass, snow, water) x walk, run,
  jump land, x two to four variants.
- **Combat (72):** swings by weapon weight x3, hits on flesh, armour, wood, stone, shield
  blocks, parry, bow draw and release, crossbow, arrow fly-by and impact, critical hit,
  equip and unequip per material.
- **Magic (48):** cast, travel and impact for six schools (fire, frost, lightning, arcane,
  holy, shadow), heal, buff, debuff, summon, teleport, fizzle, enchant.
- **Creatures (80):** per family: idle, alert, attack, hurt, death (twelve families plus
  four animals), dragon set of eight. Mostly generated.
- **World and interaction (64):** doors x6, chests x3, levers, gates, traps x8, pickups by
  material x8, coins, crafting x6 trades, eating and drinking, fire, water, book and paper.
- **Ambience loops (32):** dungeon x4, cave, crypt, sewer, forest day and night, swamp,
  mountain wind, snowstorm, desert, village day and night, market, tavern, smithy, temple,
  castle hall, harbour, rain x2, thunder set, river, waterfall, campfire, magic hum.
- **Interface (28):** click, hover, confirm, cancel, open and close per screen family,
  equip, drop, buy and sell, level up, quest accepted and completed, error, notification.
- **Non-verbal voice (48, decided: no spoken words):** effort, attack shouts, pain, death,
  laughter, breath and fear in four voice types. Generated; each clip cleared by a person,
  using only stock voices licensed for commercial use.
- **Music (24 tracks, seamless loops with intros):** main theme, title, character creation,
  village x2, town, tavern x2, castle, temple, forest, mountain, swamp, desert, dungeon x3,
  combat x3, boss x2, victory sting, defeat sting, credits.

### 7.16 Worlds and samples (20 worlds, 80 prefabs)

- **A demo world per environment sub-pack (8):** each wins on the autopilot where it has a goal.
- **Prefabs (80):** furnished rooms, complete buildings, dungeon rooms, encounter groups,
  as `cinder-scene` documents with the source names they expect.
- **The playable slice (1):** a village, a road through the forest, a three-room dungeon and
  a boss, using at least one asset from every sub-pack. This is the bundle's proof and its
  shop trailer. It needs a Mojo `Game` (characters, combat and audio are not in the world kit).
- **Top-down, third-person and first-person camera presets** for the slice, to prove all three.

### 7.17 Dark fantasy content (about 100 pieces, counted in addition to the lists above)

The tone is dark throughout (decided), so these belong to the sub-packs they dress and are
listed together here so the scope and the limits are in one place.

- **Remains (18, in dungeons and wilderness):** skeletons in six poses (chained, slumped,
  crushed, impaled, fallen, seated), skull piles x3, rib cage, scattered bones x3, a corpse
  under a shroud, a hanged figure, a body in a gibbet, a mass grave pit, a burial pyre.
- **Torture and execution (16, castle and dungeon):** rack, iron maiden (open and closed),
  breaking wheel, pillory, gibbet cage, hanging cage, strappado frame, branding irons,
  thumbscrew table, executioner's block and axe, guillotine-style blade frame, gallows trap,
  spiked chair, wall manacles with remains, drain channel, tools tray.
- **Blood and gore dressing (20):** blood pools x4, drag trails x3, splatter x4, bloody
  hand prints, stained floor and wall variants of the six dungeon themes' commonest tiles,
  gore piles x3, a butchered carcass, hanging meat hooks, viscera on an altar.
  Built as thin geometry or as stained texture variants, because decals need alpha that
  Cinder does not honour yet.
- **Dark ritual (14):** sacrificial altar x2, blood-filled bowl, ritual circle drawn in
  blood, impaled effigy, bone totem x3, skull candles, flayed banner, cultist shrine,
  summoning pit, cursed idol, chained tome.
- **Blight and decay (12, wilderness and village):** plague cart, boarded-up house pieces,
  quarantine markings of our own design, withered crops, rotten trees x3, blighted ground
  tile, hanging corpse tree, burnt-out building shell pieces x2, carrion birds.
- **Creature variants (10):** flayed, rotting and battle-damaged skins for the commonest
  undead and humanoid enemies; dismemberment-ready splits (head, arm) for skeletons and zombies.
- **Effects and sound (10):** arterial spray, gore burst on death, blood drip loop, bone
  crack and wet impact sounds, a flesh-tear set, heartbeat and whisper ambience.

**Limits that hold even in a dark pack:** violence is fantasy violence against fantasy
creatures and adult combatants. No sexual violence, no harm to children, no real-world hate,
religious or extremist symbols (heraldry and ritual marks are our own and checked), and no
depiction modelled on a real person or a real atrocity. Stylised, never photoreal.

**Selling it:** the shop listing and the manifest carry a content label ("fantasy violence,
blood and gore, grim themes"). The manifest tags every dark piece `mature`, so a game that
wants the pack without them can filter by tag; the free starter slice ships with the tag
shown the same way.

## 8. Engine gaps that shape the pack

| Gap (plan section) | Blocks | How the pack is built meanwhile |
|---|---|---|
| World kit does not draw skinned models (9) | Seeing any character or monster in a kit world | Proven by cook, clip readback and pose strips; extend cinder-probe to render a skinned model playing a clip |
| Alpha mask and blend ignored (12, filed as cinder#45) | Foliage cards, hair cards, cloth edges, decals, water | Solid-geometry foliage and hair; alpha versions planned after the fix |
| No particles | Fire, smoke, weather, most spell effects | Mesh effects with emissive and morphs; particle specs written per effect |
| UI draws no images (filed as cinder#44) | Icons, framed panels, cursors, portraits, minimap | Screens as text-and-panel documents; all art built ahead as atlases |
| No audio in world files | Hearing a kit world | Sounds proven by the engine opening them; played from Mojo |
| Textures not shared between models | Memory of large kits | Small shared sheets; manifest names them for the day sharing lands |
| 256 samplers, one per texture per placed copy | Scenes over about 250 textures (83 one-material pieces) | Flat materials, 8 m ground tiles, atlases; the pack build counts samplers and refuses over 245 |
| No terrain system | Open landscapes | Modular ground and cliff pieces on the grid (decided) |
| No cylinder, convex or per-part colliders | Barrels that roll, trees with trunk-only collision | Collider wanted recorded in each manifest entry |
| No public UI font setting | Using our fonts | Documented recipe; installed in `Game.start` |

The pack is a strong argument for the engine roadmap: it gives every one of these gaps a
concrete body of assets waiting on it.

## 9. Rights

- **"Inspired by" means the genre, not the game.** No creature, place, deity, spell name,
  class feature or artwork that belongs to Dungeons & Dragons or another setting. Out by name:
  the eye tyrant with stalks, the tentacle-faced mind eater, the displacing cat, the
  serpent-folk and frog-folk races, named dragons and gods, and any class or spell name that
  is a product term. Classes use plain words (warrior, rogue, wizard).
- **Peoples have our own names.** "Elf", "dwarf", "orc", "goblin", "troll", "dragon" are
  folklore and free. "Hobbit" and "ent" are not; "halfling" and "treefolk" are used instead.
  Dragon-headed and horned-and-tailed humanoid peoples are designed fresh if wanted.
- **Generated inputs** (tapestries, posters, some voices and creature sounds) follow the
  pipeline's rule: cached, recorded, and out of every pack until a person clears each one.
- **Heraldry, holy symbols and scripts** are our own designs, checked against real-world
  national, religious and extremist symbols before use.
- A short rights review of the final creature list is a gate before production of sub-pack 5.

## 10. For the shop

- Each sub-pack is one product: a zip with `assets/`, `audio/`, `ui/`, `sprites/`, `fonts/`,
  `worlds/`, `manifest.json`, `AGENTS.md` and `ATTRIBUTION.md` (what `cad game pack` writes),
  plus cover images, a contents sheet and a turntable or slice video.
- Sources are glTF, PNG, WAV and TTF, so the products are usable in other engines too. That
  widens the market beyond Cinder and should be stated on the listing.
- The shop ingests 3D-print models and embroidery today; game assets need their own
  `kind: "game-asset-pack"` ingest step and product template (not built).
- **Licence (decided):** free with CinderCore for games made on Cinder; a paid commercial
  licence on the shop for use in any engine. The licence text, the price points and whether
  the shop sells per sub-pack, the bundle, or both at once are still to be set.
- **Content label:** every listing states "fantasy violence, blood and gore, grim themes".
- **Lead product (decided):** the free starter slice of section 11, step 2.

## 11. Order of work

1. **Style sheet and shared systems** (section 6): palette, rig, armour slots, building
   grammar, icon style. One test asset each.
2. **The free starter slice** (decided: the first release): one hero in one outfit with
   locomotion and one-handed combat, three monsters (goblin, skeleton, wolf), the stone dungeon
   theme completed in the dark style, one cottage with an interior, a forest clearing, twenty
   items, the HUD and inventory, thirty sounds and two music tracks. It proves the style across
   every kind before anything is made in volume, and is released free to lead to the sub-packs.
   The hero and monsters need the Blender integration, so the slice's environments, items,
   interface and audio can be built first and the slice completed when characters can be.
3. **Environment sub-packs** (7, 8, 11, 10, 9): the present pipeline can build most of these
   now, so they do not wait for Blender.
4. **Weapons, items and interface** (3, 12, 14): also buildable now.
5. **Characters, armour, monsters and animation** (1, 2, 4, 5, 6): when the Blender
   integration is ready.
6. **Effects and audio** (13, 15) alongside, then the playable slice and the bundle.

## 12. Answers and what is still open

Answered on 2026-11-17:

| # | Question | Answer |
|---|---|---|
| 1 | Name | ash10's Fantasy RPG Pack |
| 2 | Playable peoples | Five: human, elf-like, dwarf-like, halfling-like, orc-like |
| 3 | First person | Separate arms-and-weapon view models |
| 4 | Terrain | Modular ground pieces on the grid |
| 5 | Licence | Free in CinderCore, paid commercial licence on the shop |
| 6 | Single-origin genre staples | Redesigned as our own: hoardling, amber glut, hornbear |
| 7 | Voices | Non-verbal only |
| 8 | Tone | Dark fantasy throughout |
| 9 | First release | A free starter slice |

Still open (none blocks the style sheet or the environment sub-packs):

1. **Licence text and prices** for the shop, and whether sub-packs and the bundle go on sale together.
2. **Names for the five peoples** and for the pantheon, heraldry and script: ours, to be invented.
3. **A rights review of the final creature list** before the Monsters sub-pack is produced.
4. **The generation provider's terms for sold audio**: confirm that sound effects and non-verbal
   voice generated with the account in use may be sold inside an asset pack.
5. **Shop ingest**: the shop has no product kind for game-asset packs yet.
6. **Which engine gaps to press first.** The pack leans hardest on drawing skinned models in
   world files, alpha, and UI images.
