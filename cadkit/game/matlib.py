"""A small library of tileable PBR materials, built from cadkit.game.texture.

Each function returns a Material whose three maps (base, orm, normal) tile in both
directions, and is cached per argument set so every part of a model shares one object
(one material = one primitive = one draw call).

    stone = stone_blocks(rows=4, cols=2, seed=1)          # 1024 px over a 2 m tile
    wall = box_uv(box(2, 3, 0.4), per_metre=0.5)           # one repeat every 2 m
"""
from functools import lru_cache

import numpy as np

from .model import Material
from .texture import blur, fbm, normal_from_height, occlusion_from_height, orm, streaks, tint


def _blocks(n, rows, cols, stagger, mortar, bevel, seed):
    """Running-bond block layout. Returns (block id, 0..1 height with bevelled edges,
    mortar mask). Tiles when rows is even or stagger is 0."""
    y, x = np.mgrid[:n, :n] / n
    row = np.floor(y * rows).astype(int)
    xs = x * cols + stagger * (row % 2)
    col = np.floor(xs).astype(int) % cols
    fx, fy = xs - np.floor(xs), y * rows - row
    # distance to the nearest block edge, in fractions of the tile
    d = np.minimum(np.minimum(fx, 1 - fx) / cols, np.minimum(fy, 1 - fy) / rows)
    wobble = (fbm(n, 6, 3, seed + 11) - 0.5) * mortar * 0.8          # ragged edges
    d = d + wobble
    t = np.clip((d - mortar / 2) / max(bevel, 1e-6), 0, 1)
    return row * cols + col, t * t * (3 - 2 * t), d < mortar / 2


@lru_cache(maxsize=None)
def stone_blocks(size=1024, rows=4, cols=2, stagger=0.5, mortar=0.012, bevel=0.02, seed=1,
                 dark=(0.30, 0.29, 0.28), light=(0.52, 0.50, 0.47), mortar_color=(0.17, 0.16, 0.15),
                 name="stone_blocks"):
    """Dressed stone blocks in running bond. `mortar` and `bevel` are fractions of the tile."""
    ids, height, gap = _blocks(size, rows, cols, stagger, mortar, bevel, seed)
    rng = np.random.default_rng(seed)
    tone = rng.random(rows * cols)[ids]
    grain = fbm(size, 8, 5, seed + 1)
    pits = np.clip((fbm(size, 48, 3, seed + 2) - 0.68) * 5, 0, 1)        # sparse small pitting
    base = tint(0.55 * tone + 0.45 * grain, dark, light)
    base *= (1 - 0.18 * pits)[..., None]
    base[gap] = np.asarray(mortar_color) * (0.8 + 0.4 * grain[gap, None])
    h = height * (0.75 + 0.25 * tone) + 0.12 * grain - 0.08 * pits
    rough = np.clip(0.78 + 0.15 * grain + 0.1 * gap, 0, 1)
    return Material(name, base=base, orm=orm(occlusion_from_height(h, max(2, size // 128), 1.6), rough, 0.0),
                    normal=normal_from_height(h, size / 128), metallic=1.0, roughness=1.0)


@lru_cache(maxsize=None)
def flagstones(size=1024, rows=4, cols=4, seed=2, dark=(0.27, 0.27, 0.28), light=(0.47, 0.46, 0.45)):
    """Worn square paving, for floors: flatter and smoother than wall blocks."""
    return stone_blocks(size, rows, cols, 0.5, 0.010, 0.012, seed, dark, light, (0.13, 0.13, 0.13),
                        "flagstones")


@lru_cache(maxsize=None)
def planks(size=512, count=4, seed=3, dark=(0.30, 0.19, 0.10), light=(0.55, 0.38, 0.21), along="x"):
    """Boards running along u ("x") or v ("y"), a dark gap between them."""
    rng = np.random.default_rng(seed)
    grain = 0.6 * streaks(size, along, cells=128, stretch=10, seed=seed) + 0.4 * fbm(size, 8, seed=seed + 1)
    shade = np.ones((size, size))
    height = np.ones((size, size))
    for i in range(count):
        a, b = i * size // count, (i + 1) * size // count
        sl = (slice(a, b), slice(None)) if along == "x" else (slice(None), slice(a, b))
        gp = (slice(a, a + max(2, size // 170)), slice(None)) if along == "x" else (
            slice(None), slice(a, a + max(2, size // 170)))
        shade[sl] = 0.82 + 0.22 * rng.random()
        height[gp] = 0.0
    base = tint(grain, dark, light) * shade[..., None]
    base[height < 0.5] *= 0.35
    return Material("planks", base=base,
                    orm=orm(occlusion_from_height(height, 4, 1.2), np.clip(0.62 + 0.25 * grain, 0, 1), 0.0),
                    normal=normal_from_height(height + 0.5 * grain, size / 128),
                    metallic=1.0, roughness=1.0)


@lru_cache(maxsize=None)
def iron(size=256, seed=4, dark=(0.10, 0.10, 0.11), light=(0.24, 0.24, 0.25), name="iron"):
    """Dark forged iron: metallic, uneven roughness, faint hammer dimples."""
    dimples = blur(fbm(size, 16, 3, seed), 2)
    scratch = streaks(size, "x", cells=128, stretch=6, seed=seed + 1)
    return Material(name, base=tint(0.6 * dimples + 0.4 * scratch, dark, light),
                    orm=orm(1.0, np.clip(0.42 + 0.3 * scratch + 0.1 * dimples, 0, 1), 1.0),
                    normal=normal_from_height(dimples, size / 64), metallic=1.0, roughness=1.0)


def palette(name, colors, roughness=0.75, metallic=0.0, swatch=16):
    """A flat-colour material: sRGB colours as swatches in one small strip texture, so a whole
    stylised character is one material and one draw call. Colour a mesh with `swatch_uv`."""
    slots = 1
    while slots < len(colors):
        slots *= 2
    img = np.zeros((swatch, slots * swatch, 3))
    for i in range(slots):
        img[:, i * swatch:(i + 1) * swatch] = colors[min(i, len(colors) - 1)]
    return Material(name, base=img, roughness=roughness, metallic=metallic, flat_uv=True)


def swatch_uv(mesh, index, material):
    """Point every UV of a mesh at swatch `index` of a palette material."""
    slots = material.base.shape[1] // material.base.shape[0]
    uv = np.tile([(index + 0.5) / slots, 0.5], (len(mesh.v), 1))
    return mesh.with_uv(uv)
