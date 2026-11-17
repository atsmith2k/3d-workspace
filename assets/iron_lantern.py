"""Iron lantern: a square cage with a pitched roof and a carrying ring round a glowing core.

Spec:
  kind: prop
  size: 0.18 x 0.43 x 0.18 m (ring included)
  pivot: base centre on Y=0 (static piece: it stands on tables, floors and wall brackets)
  budget: 400 triangles, two materials, no textures
  materials: iron (dark, metallic, rough 0.55); glow (emissive warm orange, strength 1.8, blooms)
  features: base and top plates 0.18 m square; four 16 mm corner posts; glass core 0.12 m square
            x 0.19 m; four-sided roof 80 mm high; ring of 34 mm radius standing upright on the cap
  use: light-source dressing for dungeon and tavern scenes; pair it with a point light in the world
  engine: body static, auto collider (triangle mesh)
"""
from cadkit.game import *

KIND = "prop"
DESCRIPTION = "iron lantern with a glowing core"
PARAMS = dict(width=0.18, plate=0.025, cage=0.20, post=0.016, core=0.12, roof=0.08, ring=0.034,
              ring_tube=0.006, glow=1.8)
BUDGET = dict(tris=400, materials=2)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["lantern", "light", "prop"])


def checks(p):
    total = 2 * p.plate + p.cage + p.roof + 0.02 + 2 * p.ring + p.ring_tube
    return [size(x=p.width, y=total, z=p.width, tol=0.005), tris(max=400), pivot("base"), materials(2),
            custom("glow is emissive", lambda ctx: (
                any(m.emissive_strength >= 1 and any(m.emissive) for m in ctx.model.materials),
                "one material emits, with strength over 1 so it blooms"))]


def build(p):
    w, t = p.width, p.plate
    iron = Material("lantern_iron", color=(0.09, 0.09, 0.10), metallic=1.0, roughness=0.55)
    glow = Material("lantern_glow", color=(1.0, 0.72, 0.38), roughness=0.3,
                    emissive=(1.0, 0.42, 0.10), emissive_strength=p.glow)

    y = 0.0
    parts = [box(w, t, w).moved(0, y + t / 2, 0)]                       # base plate
    y += t
    e = w / 2 - p.post / 2 - 0.004
    for sx in (-e, e):
        for sz in (-e, e):
            parts.append(box(p.post, p.cage + 0.002, p.post).moved(sx, y + p.cage / 2, sz))
    core = box(p.core, p.cage - 0.01, p.core).moved(0, y + p.cage / 2, 0)
    y += p.cage
    parts.append(box(w, t, w).moved(0, y + t / 2, 0))                   # top plate
    y += t
    r = w / 2 * 2 ** 0.5                                                # corner radius of a square
    parts.append(flat(lathe([(r, y - 0.001), (0.03, y + p.roof)], sides=4, phase=45)))
    y += p.roof
    parts.append(box(0.045, 0.02 + 0.002, 0.045).moved(0, y + 0.01 - 0.001, 0))   # cap
    y += 0.02
    ring = torus(p.ring, p.ring_tube, segments=14, sides=6).rotated(90, "x")
    parts.append(ring.moved(0, y + p.ring - 0.002, 0))
    return Model((merge(*parts), iron), (core, glow))
