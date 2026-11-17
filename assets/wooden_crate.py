"""Wooden crate: plank panels inside a raised frame, a pushable physics prop.

Spec:
  kind: prop
  size: 0.8 x 0.8 x 0.8 m
  pivot: centre of bounds (dynamic prop; the box collider is centred on the entity)
  budget: 200 triangles, one material, 512 px textures
  materials: one atlas: planks in the top half, darker frame timber in the bottom half
  features: 12 frame bars 70 mm wide standing 15 mm proud of the panels; 4 planks per panel
  use: stackable, pushable crate for sandbox and platform levels; waist-high beside a 1.8 m player
  engine: body dynamic, box collider
"""
from cadkit.game import *

KIND = "prop"
DESCRIPTION = "wooden crate with a raised frame, pushable"
PARAMS = dict(size=0.8, bar=0.07, proud=0.015, planks=4, seed=3)
BUDGET = dict(tris=200, texture=512, materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["crate", "prop"])


def checks(p):
    return [size(x=p.size, y=p.size, z=p.size), tris(max=200), pivot("centre"), materials(1),
            texture_size(512)]


def atlas(p, n=512):
    """Top half: planks running along u. Bottom half: frame timber running along u."""
    half = n // 2
    rng = np.random.default_rng(p.seed)
    grain = 0.6 * streaks(n, "x", cells=128, stretch=10, seed=p.seed) + 0.4 * fbm(n, 8, seed=p.seed + 1)
    height = np.ones((n, n))
    shade = np.ones((n, n))
    for i in range(p.planks):                                   # planks: tone per board, dark gaps
        y0, y1 = i * half // p.planks, (i + 1) * half // p.planks
        shade[y0:y1] = 0.82 + 0.22 * rng.random()
        height[y0:y0 + 3] = 0.0
    base = tint(grain, (0.46, 0.30, 0.17), (0.72, 0.52, 0.31)) * shade[..., None]
    base[half:] = tint(grain[half:], (0.25, 0.16, 0.09), (0.40, 0.27, 0.16))
    gap = height < 0.5
    base[gap] *= 0.35
    relief = height * 1.0 + 0.5 * grain
    rough = np.clip(0.62 + 0.25 * grain, 0, 1)
    return Material("crate_wood", base=base, orm=orm(occlusion_from_height(height, 4, 1.2), rough, 0.0),
                    normal=normal_from_height(relief, 4.0), metallic=1.0, roughness=1.0)


def build(p):
    s, t = p.size, p.bar
    inner = s - 2 * p.proud
    panels = box(inner, inner, inner)
    panels = panels.with_uv(panels.uv * [1.0, 0.5])             # top half of the atlas

    def bar(length):
        b = box(length, t, t)
        return b.with_uv(b.uv * [length / s, 0.4] + [0.0, 0.55])   # bottom half

    e = s / 2 - t / 2
    bars = []
    for a in (-e, e):
        for b in (-e, e):
            bars.append(bar(s).moved(0, a, b))                              # along X, full length
            bars.append(bar(s - 2 * t).rotated(90, "z").moved(a, 0, b))     # along Y, between
            bars.append(bar(s - 2 * t).rotated(90, "y").moved(a, b, 0))     # along Z, between
    return Model((merge(panels, *bars), atlas(p)))
