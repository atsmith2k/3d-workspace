"""Rune monolith: a weathered standing stone with four glowing runes carved down its face.

The first asset made by the high-to-low workflow. A 330,000-triangle stone is sculpted in
Blender (subdivision, three scales of displacement, runes cut with a boolean), and its detail
is baked onto a 3,000-triangle game mesh as 2048 px normal, occlusion, curvature and rune-mask
maps. The colour is then painted from those maps and from each texel's place on the stone.

Spec:
  kind: environment
  size: about 1.0 x 2.4 x 0.85 m
  pivot: base on Y=0, the stone's axis at the origin; the runes face -Z
  budget: 3,500 triangles, one material, 2048 px textures (four maps)
  high poly: at least 300,000 triangles before baking
  materials: grey granite, darker in the cracks and lighter on worn edges (from the baked
             occlusion and curvature); moss on upward faces and low in the crevices; rune
             grooves dark with a cyan glow (emissive, strength 1.5)
  features: four angular runes, each about 0.32 x 0.34 m, strokes 35 mm wide, cut exactly 45 mm
            deep into the weathered stone (the cutter is trimmed by an inset copy of it); lumps of 0.5 m, cracks of 0.15 m and grain of 25 mm, all in the normal map
  use: a landmark or objective marker in a dungeon or outdoor level; over head height beside
       a 1.8 m player
  engine: body static, auto collider (triangle mesh of the 3,000-triangle game mesh)
  needs: Blender 5.x (cadkit.game.blender); cached after the first build
"""
from cadkit.game import *
from cadkit.game import blender as B

KIND = "environment"
DESCRIPTION = "weathered standing stone with glowing carved runes (baked from high-poly)"
PARAMS = dict(height=2.4, tris=3000, texture=2048, glow=1.5, rune_depth=0.045, seed=7)
BUDGET = dict(tris=3500, texture=2048, materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = dict(collection="hero_props", licence="CC0-1.0", tags=["monolith", "runes", "stone", "landmark", "baked"])

RUNES = [   # strokes in a unit cell: x -0.5..0.5, y 0..1
    [((0, 0), (0, 1)), ((0, 0.62), (0.38, 0.92)), ((0, 0.30), (0.38, 0.60))],
    [((0, 0.08), (0.36, 0.5)), ((0.36, 0.5), (0, 0.92)), ((0, 0.92), (-0.36, 0.5)), ((-0.36, 0.5), (0, 0.08))],
    [((0, 0), (0, 1)), ((0, 1), (-0.36, 0.64)), ((0, 1), (0.36, 0.64))],
    [((-0.32, 0.08), (0.32, 0.92)), ((0.32, 0.08), (-0.32, 0.92))],
]
PROFILE = [(0.50, 0.0), (0.52, 0.5), (0.46, 1.2), (0.40, 1.9), (0.30, 2.3), (0.0, 2.42)]
DEPTH = 0.8                       # the stone is 0.8 as deep as it is wide


def checks(p):
    def baked(ctx):
        meta = ctx.model.meta
        return meta["high_tris"] >= 300_000, (f"{meta['high_tris']:,} triangles sculpted, baked onto "
                                              f"{ctx.model.triangles:,} (Blender {meta['blender']})")

    def detail(ctx):
        n = np.asarray(ctx.model.materials[0].normal)[ctx.model.meta["mask"]] * 2 - 1
        tilt = float(np.degrees(np.arccos(np.clip(n[:, 2], -1, 1))).mean())
        return 3.0 < tilt < 35.0, f"the baked normals lean {tilt:.1f} degrees from flat on average: detail, not noise"

    def runes(ctx):
        share = ctx.model.meta["rune_share"]
        return 0.004 < share < 0.08, f"the rune mask covers {share:.1%} of the stone's texels"
    return [size(x=(0.85, 1.25), y=(p.height - 0.15, p.height + 0.2), z=(0.65, 1.05)), tris(max=3500),
            pivot((None, 0.0, None)), materials(1), texture_size(2048), uv_unique(),
            custom("high poly", baked), custom("normal detail", detail), custom("runes baked", runes)]


def radius(y):
    ys = [q[1] for q in PROFILE]
    return float(np.interp(y, ys, [q[0] for q in PROFILE]))


def rune_cutter(p):
    """Boxes that cut the four runes into the -Z face, as one mesh."""
    strokes = []
    w, h, width = 0.32, 0.34, 0.035
    for k, glyph in enumerate(RUNES):
        base = 1.82 - 0.46 * k
        z = -DEPTH * radius(base + h / 2)
        for (x0, y0), (x1, y1) in glyph:
            a, b = np.array([x0 * w, base + y0 * h]), np.array([x1 * w, base + y1 * h])
            length = float(np.linalg.norm(b - a))
            angle = float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0])))
            mid = (a + b) / 2
            strokes.append(box(length + width, width, 0.5).rotated(angle, "z").moved(mid[0], mid[1], z))    # deep: the inset stone trims it
    return merge(*strokes)


def build(p):
    k = p.height / 2.42
    stone = merge(lathe([(r, y * k) for r, y in PROFILE], 8), disc(PROFILE[0][0], 0, 8, up=False)).scaled(1, 1, DEPTH)
    s = B.Session()
    hi = s.add(stone, "high")
    grain = B.displace("CLOUDS", scale=0.025, strength=0.006)
    s.modify(hi, B.subsurf(1, simple=True), B.subsurf(5),
             B.displace("CLOUDS", scale=0.5, strength=0.16),          # lumps
             B.displace("VORONOI", scale=0.15, strength=0.035))       # cracks and facets
    lo = s.copy(hi, "low")                                           # the game mesh comes from the uncarved stone
    s.modify(lo, grain)
    # Carve after the big shapes, never before: displacing a carved mesh moves each groove wall
    # along its own normal and smears the strokes shut. Depth is exact: the cutter is trimmed by
    # a copy of the stone inset by the groove depth, so it only ever removes the outer skin.
    cut = s.add(rune_cutter(p), "runes", emit=1.0)                   # emissive: the cut faces bake as a mask
    s.remesh(cut, 0.012)
    inner = s.copy(hi, "inner")
    s.modify(inner, B.inflate(-p.rune_depth))
    s.remesh(inner, 0.02)                                            # an inset rough surface crosses itself: make it one skin
    s.boolean(cut, inner, materials="INDEX")
    s.boolean(hi, cut)
    s.modify(hi, grain)                                              # 6 mm of grain is safe over the grooves
    s.decimate(lo, p.tris)
    s.shade(lo, sharp_angle=50)
    s.unwrap(lo, margin=0.006)
    s.bake([hi], lo, size=p.texture, maps=("normal", "ao", "curvature", "emit"), cage=0.05, ray=0.2, samples=64)
    r = s.run()
    low = r.mesh(lo)
    low = low.moved(0, -low.bounds[0][1], 0)                          # stand it on Y=0

    n = p.texture
    pos, nrm, mask = texel_maps(low, n)
    ao, curv = r.image("ao"), r.image("curvature")
    rune = np.clip(blur(r.image("emit"), 1) * 1.6, 0, 1) * mask
    # granite: two greys mixed by 3D noise (no UV seams), speckled, dark in cracks, light on edges
    rock = tint(fbm3(pos, 0.45, seed=p.seed), (0.30, 0.31, 0.33), (0.56, 0.55, 0.53))
    rock *= (0.86 + 0.28 * noise3(pos, 0.012, p.seed + 1))[..., None]
    rock *= (0.45 + 0.55 * ao)[..., None]
    rock = np.clip(rock + 0.35 * np.clip(curv - 0.52, 0, 0.3)[..., None], 0, 1)
    # moss: on faces that look up, and low in the crevices
    up = np.clip((nrm[..., 1] - 0.15) / 0.5, 0, 1)
    low_damp = np.clip(1 - pos[..., 1] / 0.9, 0, 1) * np.clip((0.75 - ao) / 0.4, 0, 1)
    moss = np.clip(np.maximum(up, low_damp) * 1.6 * fbm3(pos, 0.2, seed=p.seed + 2) - 0.15, 0, 1) * (1 - rune)
    green = tint(noise3(pos, 0.04, p.seed + 3), (0.13, 0.20, 0.07), (0.27, 0.36, 0.13))
    base = rock * (1 - moss[..., None]) + green * moss[..., None]
    base = base * (1 - 0.8 * rune[..., None])                        # the grooves are dark; the glow lights them
    rough = np.clip(0.86 + 0.08 * moss - 0.3 * rune, 0, 1)
    emission = rune[..., None] * np.array([0.15, 0.85, 1.0])

    flat = np.zeros((n, n, 3)) + [0.5, 0.5, 1.0]
    normal = np.where(mask[..., None], r.image("normal"), flat)
    mat = Material("monolith_stone", base=fill_background(base, mask),
                   orm=fill_background(orm(ao, rough, 0.0), mask), normal=fill_background(normal, mask),
                   emission=fill_background(emission, mask), emissive=(1.0, 1.0, 1.0), emissive_strength=p.glow,
                   metallic=1.0, roughness=1.0)
    model = Model((low, mat))
    model.meta = dict(high_tris=r.step("modify", 3)["triangles"], blender=r.info["blender"], mask=mask,
                      rune_share=float((rune > 0.5).sum() / max(mask.sum(), 1)), bake_seconds=r.seconds, cached=r.cached)
    return model
