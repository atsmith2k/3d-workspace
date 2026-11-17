"""ash10's Fantasy RPG Pack: what every asset in every sub-pack shares.

The style guide in code (docs/game-asset-packs/fantasy-rpg-style-guide.md is the prose): one
ruler, one palette, one set of materials, one set of budgets. An asset script starts with
`from _frp import *` and takes its sizes, colours and surfaces from here, so a village wall
stands on a dungeon floor and a potion sits on a tavern table without adjustment.

Ruler: metres, Y up. A person is 1.8 m. The grid is 2 m. A storey is 3 m. Doors open
1.2 x 2.2 m. Steps rise 0.2 m. Walls stand on cell edges, centred. Floors walk at Y = 0.
Tone: dark fantasy. Stone is cold and stained, wood weathered, iron rusted; colour is kept
for what matters.
"""
from functools import lru_cache

from cadkit.game import *
from cadkit.game.texture import blur

# ---------------------------------------------------------------- ruler
PERSON, GRID, STOREY = 1.8, 2.0, 3.0
DOOR_W, DOOR_H = 1.2, 2.2
WINDOW_W, WINDOW_H, WINDOW_SILL = 0.8, 1.0, 1.1
STEP_RISE = 0.2
WALL_T = 0.3                       # village and interior walls; dungeon and castle walls are 0.4 and up
TEXEL = 512                        # texture pixels per metre (1024 for held items and faces)
TILE = 2.0                         # metres one repeat of a tiling material covers

LICENCE = "ash10 Fantasy RPG Pack licence (free with CinderCore; commercial on shop.ash10.dev; text pending)"
PREFIX = dict(heroes="hero_", armour="arm_", weapons="wpn_", npcs="npc_", monsters="mon_", dungeons="dun_",
              village="vil_", castle="cas_", wilderness="nat_", interiors="int_", items="itm_", effects="fx_",
              interface="ui_", sounds="sfx_", music="mus_")
BUDGET_OF = dict(hero=dict(tris=15000, texture=2048, materials=2), armour=dict(tris=2500, texture=2048, materials=1),
                 monster=dict(tris=8000, texture=2048, materials=1), boss=dict(tris=30000, texture=2048, materials=3),
                 weapon=dict(tris=1500, texture=1024, materials=3), viewmodel=dict(tris=8000, texture=2048, materials=2),
                 small_prop=dict(tris=800, texture=1024, materials=2), large_prop=dict(tris=3000, texture=1024, materials=2),
                 building=dict(tris=1500, texture=1024, materials=3), tree=dict(tris=3000, texture=1024, materials=2),
                 terrain=dict(tris=600, texture=1024, materials=2))


def product(subpack, *tags, **more):
    """PRODUCT for an asset of a sub-pack: its collection, the licence and tags."""
    return dict(collection=f"frp_{subpack}", licence=LICENCE, tags=["fantasy", "rpg", "dark", subpack, *tags], **more)


# ---------------------------------------------------------------- palette (sRGB 0..1), weighted dark
PALETTE = dict(
    # stone
    stone_shadow=(0.16, 0.16, 0.17), stone_dark=(0.24, 0.24, 0.25), stone_mid=(0.36, 0.35, 0.35),
    stone_light=(0.50, 0.49, 0.47), mortar=(0.13, 0.12, 0.12), moss=(0.22, 0.28, 0.16), soot=(0.07, 0.07, 0.07),
    # wood
    wood_rot=(0.13, 0.10, 0.08), wood_dark=(0.21, 0.14, 0.09), wood_mid=(0.34, 0.23, 0.14),
    wood_light=(0.48, 0.35, 0.22), wood_pale=(0.60, 0.50, 0.36),
    # plaster, thatch, cloth
    plaster_stain=(0.40, 0.35, 0.28), plaster=(0.62, 0.57, 0.48), plaster_light=(0.72, 0.68, 0.60),
    thatch_dark=(0.26, 0.21, 0.12), thatch=(0.47, 0.40, 0.23), thatch_light=(0.60, 0.53, 0.33),
    cloth_red=(0.45, 0.10, 0.09), cloth_blue=(0.14, 0.20, 0.36), cloth_green=(0.17, 0.28, 0.17),
    cloth_ochre=(0.58, 0.42, 0.14), cloth_undyed=(0.56, 0.51, 0.42), cloth_black=(0.09, 0.09, 0.10),
    # metal
    iron_dark=(0.10, 0.10, 0.11), iron=(0.22, 0.22, 0.23), steel=(0.50, 0.52, 0.55), rust=(0.34, 0.16, 0.08),
    bronze=(0.50, 0.33, 0.14), gold_dull=(0.66, 0.50, 0.18), silver=(0.68, 0.69, 0.72),
    # leather, bone, skin
    leather_dark=(0.17, 0.11, 0.07), leather=(0.33, 0.21, 0.12), bone=(0.72, 0.68, 0.56), bone_old=(0.52, 0.47, 0.36),
    # ground and growth
    dirt_dark=(0.15, 0.12, 0.09), dirt=(0.27, 0.21, 0.15), mud=(0.20, 0.17, 0.13), grass_dead=(0.36, 0.33, 0.18),
    grass=(0.22, 0.31, 0.14), grass_dark=(0.13, 0.20, 0.10), leaf_autumn=(0.50, 0.28, 0.10), blight=(0.30, 0.28, 0.20),
    # accents: kept for things that matter
    blood_fresh=(0.48, 0.03, 0.03), blood_dried=(0.25, 0.04, 0.03), blood_stain=(0.17, 0.07, 0.06),
    arcane=(0.20, 0.45, 0.95), fel=(0.35, 0.80, 0.20), holy=(0.95, 0.80, 0.35), ember=(1.0, 0.42, 0.08),
    potion_red=(0.70, 0.06, 0.08), potion_blue=(0.12, 0.30, 0.80), glass=(0.55, 0.68, 0.66))
P = PALETTE


# ---------------------------------------------------------------- materials (tileable, one repeat = 2 m)

def _stains(size, seed, amount=0.5):
    """Dirt that runs down a wall: darker low down and in streaks. 0 = clean, 1 = filthy."""
    run = blur(streaks(size, "y", cells=24, stretch=3, seed=seed), size // 60)       # soft, wide runs
    cloud = fbm(size, 3, 4, seed + 1)
    return np.clip((0.45 * run + 0.75 * cloud - 0.5) * 2.0 * amount, 0, 1)


@lru_cache(maxsize=None)
def stone(size=1024, seed=1):
    """Cold, soot-stained wall stone: dressed blocks 1.0 x 0.5 m."""
    m = stone_blocks(size, rows=4, cols=2, seed=seed, dark=P["stone_dark"], light=P["stone_light"],
                     mortar_color=P["mortar"], name="frp_stone")
    grime = _stains(size, seed + 20, 0.7)
    m.base = np.clip(m.base * (1 - 0.45 * grime[..., None]), 0, 1)
    return m


@lru_cache(maxsize=None)
def paving(size=1024, seed=2):
    return flagstones(size, rows=4, cols=4, seed=seed, dark=P["stone_shadow"], light=P["stone_mid"])


@lru_cache(maxsize=None)
def timber(size=512, seed=3):
    """Weathered structural timber and boards: dark, grain running along u."""
    return planks(size, count=4, seed=seed, dark=P["wood_rot"], light=P["wood_mid"], along="x")


@lru_cache(maxsize=None)
def boards(size=1024, seed=4):
    """Floor boards: eight to the tile, a little lighter where they are walked on."""
    return planks(size, count=8, seed=seed, dark=P["wood_dark"], light=P["wood_light"], along="x")


@lru_cache(maxsize=None)
def plaster(size=1024, seed=5):
    """Lime plaster gone grey-brown, cracked and water-stained."""
    grain = fbm(size, 24, 4, seed)
    patch = blur(fbm(size, 5, 3, seed + 1), 6)
    line = np.clip(1 - np.abs(fbm(size, 3, 6, seed + 2) - 0.5) * 60, 0, 1) ** 2        # hairlines where a slow field crosses 0.5
    broken = np.clip((fbm(size, 5, 3, seed + 9) - 0.52) * 6, 0, 1)                    # ...kept only in patches
    cracks = line * broken
    stain = _stains(size, seed + 3, 0.8)
    base = tint(0.35 * grain + 0.65 * patch, P["plaster_stain"], P["plaster_light"])
    base = base * (1 - 0.45 * stain[..., None]) * (1 - 0.5 * cracks[..., None])
    height = 0.5 + 0.2 * grain - 0.4 * cracks
    return Material("frp_plaster", base=np.clip(base, 0, 1),
                    orm=orm(1 - 0.4 * cracks, np.clip(0.86 + 0.1 * grain, 0, 1), 0.0),
                    normal=normal_from_height(height, size / 256), metallic=1.0, roughness=1.0)


@lru_cache(maxsize=None)
def thatch(size=1024, seed=6):
    """Old straw thatch: strands running down the slope (v), dark with damp."""
    strand = 0.7 * streaks(size, "y", cells=220, stretch=4, seed=seed) + 0.3 * streaks(size, "y", cells=90, stretch=3, seed=seed + 1)
    damp = blur(fbm(size, 4, 3, seed + 2), 8)
    rows = np.arange(size)[:, None] + (fbm(size, 6, 2, seed + 4) - 0.5) * size / 14   # course lines that wander
    layers = blur((rows % (size // 4) < size // 30).astype(float), 2)
    base = tint(np.clip(strand * 0.8 + 0.2 - 0.35 * damp, 0, 1), P["thatch_dark"], P["thatch_light"])
    base = base * (1 - 0.3 * layers[..., None])
    return Material("frp_thatch", base=np.clip(base, 0, 1), orm=orm(1 - 0.5 * layers, 0.95, 0.0),
                    normal=normal_from_height(strand * 0.8 - layers, size / 128), metallic=1.0, roughness=1.0)


@lru_cache(maxsize=None)
def ground(size=1024, seed=7):
    """Trodden earth with dying grass: the top of every outdoor ground tile."""
    tuft = np.clip((fbm(size, 4, 5, seed) - 0.40) * 2.2, 0, 1)                       # broad drifts, soft edges
    blades = 0.5 + 0.5 * streaks(size, "y", cells=300, stretch=2, seed=seed + 1)
    soil = fbm(size, 20, 4, seed + 2)
    grass = tint(blades * (0.6 + 0.4 * fbm(size, 9, 3, seed + 3)), P["grass_dark"], P["grass_dead"])
    earth = tint(soil, P["dirt_dark"], P["dirt"])
    base = earth * (1 - 0.75 * tuft[..., None]) + grass * 0.75 * tuft[..., None]
    return Material("frp_ground", base=np.clip(base, 0, 1), orm=orm(1.0, 0.94, 0.0),
                    normal=normal_from_height(0.5 * soil + 0.5 * tuft * blades, size / 200), metallic=1.0, roughness=1.0)


@lru_cache(maxsize=None)
def earth(size=512, seed=8):
    """Bare soil and stones: the cut sides of ground tiles, banks and paths."""
    soil = fbm(size, 10, 5, seed)
    pebbles = np.clip((fbm(size, 40, 2, seed + 1) - 0.66) * 7, 0, 1)
    base = tint(soil, P["dirt_dark"], P["dirt"]) * (1 - pebbles[..., None]) + np.asarray(P["stone_mid"]) * pebbles[..., None]
    return Material("frp_earth", base=np.clip(base, 0, 1), orm=orm(1.0, 0.92, 0.0),
                    normal=normal_from_height(soil + 0.6 * pebbles, size / 128), metallic=1.0, roughness=1.0)


@lru_cache(maxsize=None)
def iron_rusted(size=256, seed=9):
    """Forged iron with rust blooming in the hollows."""
    m = iron(size, seed, dark=P["iron_dark"], light=P["iron"], name="frp_iron")
    bloom = np.clip((fbm(size, 9, 4, seed + 5) - 0.5) * 4, 0, 1)
    m.base = np.clip(m.base * (1 - bloom[..., None]) + np.asarray(P["rust"]) * bloom[..., None], 0, 1)
    m.orm = orm(1.0, np.clip(m.orm[..., 1] + 0.4 * bloom, 0, 1), 1 - 0.85 * bloom)
    return m


@lru_cache(maxsize=None)
def steel_blade(size=256, seed=10):
    """A kept blade: bright steel, fine scratches along its length (v)."""
    scratch = streaks(size, "y", cells=200, stretch=10, seed=seed)
    return Material("frp_steel", base=tint(scratch, (0.40, 0.42, 0.45), (0.62, 0.64, 0.67)),
                    orm=orm(1.0, np.clip(0.28 + 0.2 * scratch, 0, 1), 1.0),
                    normal=normal_from_height(scratch, 1.0), metallic=1.0, roughness=1.0)


def flat_material(name, colour, roughness=0.7, metallic=0.0, emissive=None, strength=1.0):
    """A factor-only material in a palette colour (sRGB in, linear factor out)."""
    lin = tuple(((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92 for c in P[colour])
    kw = dict(emissive=tuple(((c + 0.055) / 1.055) ** 2.4 for c in P[emissive]), emissive_strength=strength) if emissive else {}
    return Material(name, color=lin + (1.0,), roughness=roughness, metallic=metallic, **kw)


GROUND_TILE = 4.0                  # ground repeats every 4 m: a 2 m repeat shows as a grid across open land


def tiled(mesh, every=TILE):
    """World-scale UVs for a tiling material: one repeat every 2 m (or `every`), so courses and
    boards run on across neighbouring pieces."""
    return box_uv(mesh, 1 / every)


def grain_up(mesh, every=TILE):
    """World-scale UVs turned a quarter: for upright timbers, so the grain runs up the post."""
    uv = box_uv(mesh, 1 / every).uv
    return mesh.with_uv(uv[:, ::-1].copy())


def directed_uv(mesh, uv, axis):
    """Use `uv` (an (N, 2) array) on the faces that look along `axis` ("x", "y", "z" or a vector),
    and world-scale box UVs on the rest: a custom mapping for the faces that show, without the
    thin edges collapsing to a line of texture."""
    d = dict(x=(1, 0, 0), y=(0, 1, 0), z=(0, 0, 1))[axis] if isinstance(axis, str) else axis
    d = np.asarray(d, float) / np.linalg.norm(d)
    main = np.abs(mesh.n @ d) > 0.5
    return mesh.with_uv(np.where(main[:, None], uv, tiled(mesh).uv))


def ccw(points):
    """A polygon's points in counter-clockwise order (what `prism` wants)."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
    return list(points) if area > 0 else list(points)[::-1]


def piece_checks(x, y, z, kind="building", anchor="base", mats=None, tol=0.002):
    """Checks for a grid piece: exact size (2 mm), the class budget, the pivot."""
    b = BUDGET_OF[kind]
    return [size(x=x, y=y, z=z, tol=tol), tris(max=b["tris"]), pivot(anchor), materials(mats or b["materials"]),
            texture_size(b["texture"])]
