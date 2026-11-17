"""Stone golem: a hulking rock creature with a molten sigil in its chest and glowing eyes.

The first character made by the high-to-low workflow. Its body is laid out as ellipsoids and
capsules along a skeleton, fused into one skin and sculpted in Blender (over 500,000
triangles: lumps, facets, grain, a sigil and eye sockets cut to an exact depth), baked onto a
game mesh, and skinned with Blender's automatic (bone heat) weights.

Spec:
  kind: character
  size: about 2.5 m across the fists x 2.4 m tall x 0.95 m deep
  pivot: feet at the origin, centred in X; faces +Z
  budget: 9,000 triangles, one material, 2048 px textures (four maps), 18 bones
  high poly: at least 500,000 triangles before baking
  proportions: a massive chest and shoulders, forearms thicker than the upper arms, fists at
               knee height, short legs set wide, a small head sunk between the shoulders
  bind pose: arms held out from the body and legs apart, so nothing fuses when the parts are
             joined and the skin weights separate cleanly
  materials: brown-grey rock, dark in the cracks, light on worn edges, moss on the shoulders
             and back of the head; a diamond sigil on the chest and two eyes, cut 40 mm deep,
             glowing orange (emissive, strength 1.5)
  clips: idle 3.2 s (slow breathing sway), walk 1.6 s (heavy, in place, left foot strikes at
         phase 0), smash 1.4 s (both fists raised and brought down; plays once)
  use: a boss or guardian in a dungeon; half as tall again as a 1.8 m player
  engine: no body (give it a capsule from game code); rest_y 0. Skinned: the world kit does
          not draw it; use it from a Mojo Game with an AnimatorRef
  needs: Blender 5.x (cadkit.game.blender); cached after the first build
"""
from cadkit.game import *
from cadkit.game import blender as B

KIND = "character"
DESCRIPTION = "stone golem with a glowing chest sigil: idle, walk, smash (baked from high-poly)"
PARAMS = dict(tris=8000, texture=2048, glow=1.5, cut=0.04, seed=11)
BUDGET = dict(tris=9000, texture=2048, materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = dict(collection="hero_props", licence="CC0-1.0", tags=["character", "golem", "boss", "rigged", "baked"],
               notes="Skinned. Cinder 0.1.1's world kit loads a skinned model but draws nothing: use it from a "
                     "Mojo Game that gives the spawned mesh an AnimatorRef. Clips by index: 0 idle (loops), "
                     "1 walk (loops), 2 smash (plays once). Front is +Z.")

GLOW = (1.0, 0.42, 0.08)


def checks(p):
    def baked(ctx):
        meta = ctx.model.meta
        return meta["high_tris"] >= 500_000, (f"{meta['high_tris']:,} triangles sculpted, baked onto "
                                              f"{ctx.model.triangles:,} (Blender {meta['blender']})")

    def glow(ctx):
        share = ctx.model.meta["glow_share"]
        return 0.002 < share < 0.06, f"the sigil and eyes cover {share:.1%} of the body's texels"

    def influences(ctx):
        """Every vertex is led by a bone it lies near: a fist is not driven by a leg."""
        from cadkit.game.rig import MAX_INFLUENCES
        sk, (mesh, _), (j, w) = ctx.model.skeleton, ctx.model.parts[0], ctx.model.skins[0]
        lead = j[np.arange(len(j)), w.argmax(1)]
        far = 0.0
        for b in np.unique(lead):
            a, t = sk.bones[b].head, sk.tail(b)
            ab = t - a
            v = mesh.v[lead == b]
            u = np.clip(((v - a) @ ab) / max(float(ab @ ab), 1e-9), 0, 1)
            far = max(far, float(np.linalg.norm(v - (a + u[:, None] * ab), axis=1).max()))
        used = len(np.unique(j[w > 0]))
        return far < 0.75 and used >= len(sk) - 1, (f"no vertex is more than {far:.2f} m from the bone that leads it; "
                                                    f"{used} of {len(sk)} bones carry weight; {MAX_INFLUENCES} per vertex")
    return [size(x=(2.1, 2.9), y=(2.25, 2.6), z=(0.7, 1.2)), tris(max=9000), pivot((0.5, 0.0, None), tol=0.06),
            materials(1), texture_size(2048), uv_unique(), clips("idle", "walk", "smash"),
            custom("high poly", baked), custom("glow baked", glow), custom("weights are local", influences),
            deforms_cleanly()]


# ---------------------------------------------------------------- skeleton and body

def skeleton():
    """The biped's bone names (so biped_gait drives it), in a golem's proportions."""
    sk = Skeleton()
    sk.add("root", None, (0, 0, 0))
    sk.add("hips", "root", (0, 1.00, 0))
    sk.add("spine", "hips", (0, 1.25, 0.02))
    sk.add("chest", "spine", (0, 1.52, 0.03))
    sk.add("neck", "chest", (0, 1.98, 0.08))
    sk.add("head", "neck", (0, 2.05, 0.10), tail=(0, 2.38, 0.12))
    for s, side in ((1, "L"), (-1, "R")):                  # left is +X when it faces +Z
        sk.add(f"upper_arm.{side}", "chest", (s * 0.60, 1.88, 0.0))
        sk.add(f"lower_arm.{side}", f"upper_arm.{side}", (s * 0.98, 1.36, 0.03))
        sk.add(f"hand.{side}", f"lower_arm.{side}", (s * 1.14, 0.80, 0.08), tail=(s * 1.18, 0.46, 0.10))
    for s, side in ((1, "L"), (-1, "R")):
        sk.add(f"upper_leg.{side}", "hips", (s * 0.30, 0.96, 0.0))
        sk.add(f"lower_leg.{side}", f"upper_leg.{side}", (s * 0.33, 0.52, 0.03))
        sk.add(f"foot.{side}", f"lower_leg.{side}", (s * 0.34, 0.13, 0.0), tail=(s * 0.34, 0.04, 0.28))
    return sk


def blob(centre, radii, sides=14, rings=10):
    return ball(1.0, sides, rings).scaled(*radii).moved(*centre)


def body(sk):
    """Overlapping round shapes along the bones. Blender fuses them into one skin."""
    h = sk.head
    parts = [blob((0, 1.00, 0.0), (0.40, 0.28, 0.30)),                # pelvis
             blob((0, 1.30, 0.03), (0.44, 0.32, 0.34)),               # belly
             blob((0, 1.66, 0.03), (0.60, 0.40, 0.42)),               # chest
             blob((0, 2.14, 0.11), (0.21, 0.24, 0.23)),               # head
             blob((0, 2.22, 0.20), (0.19, 0.07, 0.10))]               # brow ridge
    for side in ("L", "R"):
        s = 1 if side == "L" else -1
        sh, el, wr = h(f"upper_arm.{side}"), h(f"lower_arm.{side}"), h(f"hand.{side}")
        parts += [blob(sh, (0.27, 0.25, 0.26)),                       # shoulder boulder
                  capsule(sh, el, 0.18, 0.15), capsule(el, wr, 0.17, 0.22),
                  blob(wr + [s * 0.03, -0.17, 0.02], (0.21, 0.24, 0.22))]          # fist
        hp, kn, an = h(f"upper_leg.{side}"), h(f"lower_leg.{side}"), h(f"foot.{side}")
        parts += [capsule(hp, kn, 0.21, 0.17), capsule(kn, an, 0.17, 0.19),
                  blob(an + [0.0, -0.03, 0.10], (0.20, 0.11, 0.30))]               # foot
    return merge(*parts)


def cutters():
    """What is cut out to glow: a diamond sigil on the chest and two eyes. Deep shapes: the
    inset copy of the body trims them to the cut depth."""
    strokes = []
    c, w, hgt, t = np.array([0.0, 1.70]), 0.17, 0.22, 0.04
    corners = [c + [0, -hgt], c + [w, 0], c + [0, hgt], c + [-w, 0]]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        length = float(np.linalg.norm(b - a))
        angle = float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0])))
        mid = (a + b) / 2
        strokes.append(box(length + t, t, 0.6).rotated(angle, "z").moved(mid[0], mid[1], 0.42))
    strokes.append(box(0.05, 0.05, 0.6).rotated(45, "z").moved(c[0], c[1], 0.42))          # a point in the middle
    for x in (-0.085, 0.085):
        strokes.append(capsule((x, 2.14, 0.15), (x, 2.14, 0.5), 0.042))                    # eyes
    return merge(*strokes)


# ---------------------------------------------------------------- clips

def walk():
    return Clip.cycle("walk", 1.6, lambda ph: biped_gait(ph, stride=20, knee=34, arm=13, elbow=10, lean=7,
                                                          bob=0.035, twist=7, drop=6), keys=16)


def idle():
    def pose(ph):
        s, s2 = np.sin(2 * np.pi * ph), np.sin(4 * np.pi * ph)
        out = {"hips:move": (0, -0.012 - 0.012 * s, 0), "spine": euler(x=1.5 * s, z=1.0 * s2),
               "chest": euler(x=2.0 * s), "head": euler(x=-2.0 * s, y=6 * np.sin(2 * np.pi * ph + 0.8)),
               "upper_leg.L": euler(x=-2 - 2 * s), "upper_leg.R": euler(x=-2 - 2 * s),
               "lower_leg.L": euler(x=4 + 4 * s), "lower_leg.R": euler(x=4 + 4 * s)}
        for side, sign in (("L", 1.0), ("R", -1.0)):
            out[f"upper_arm.{side}"] = euler(x=2 * s2, z=-sign * (6 + 2 * s))
            out[f"lower_arm.{side}"] = euler(x=-8 - 3 * s)
        return out
    return Clip.cycle("idle", 3.2, pose, keys=12)


def smash():
    """Both fists up over the head, then down hard. Plays once: 0-45 % wind-up, 45-60 % the
    blow, 60-100 % recovery to the bind pose."""
    def ease(x):
        x = float(np.clip(x, 0, 1))
        return x * x * (3 - 2 * x)

    def pose(ph):
        up = ease(ph / 0.45) if ph < 0.45 else 1 - ease((ph - 0.45) / 0.15) if ph < 0.6 else 0.0
        hit = ease((ph - 0.45) / 0.15) * (1 - ease((ph - 0.62) / 0.38)) if ph >= 0.45 else 0.0
        out = {"hips:move": (0, -0.10 * hit, 0), "spine": euler(x=-13 * up + 16 * hit),
               "chest": euler(x=-18 * up + 20 * hit), "head": euler(x=10 * up - 12 * hit),
               "upper_leg.L": euler(x=-14 * hit), "upper_leg.R": euler(x=-14 * hit),
               "lower_leg.L": euler(x=28 * hit), "lower_leg.R": euler(x=28 * hit)}
        for side, sign in (("L", 1.0), ("R", -1.0)):
            out[f"upper_arm.{side}"] = euler(x=-122 * up - 55 * hit, z=-sign * (10 * up + 14 * hit))
            out[f"lower_arm.{side}"] = euler(x=-50 * up - 18 * hit)
        return out
    return Clip.cycle("smash", 1.4, pose, keys=20, looping=False)


# ---------------------------------------------------------------- build

def build(p):
    sk = skeleton()
    s = B.Session()
    hi = s.add(body(sk), "high", weld=False)
    s.remesh(hi, 0.03)                                               # one closed skin from the overlapping parts
    s.modify(hi, B.smooth(0.6, 6), B.subsurf(2),
             B.displace("CLOUDS", scale=0.32, strength=0.09),         # lumps
             B.displace("VORONOI", scale=0.11, strength=0.035))       # facets and cracks
    lo = s.copy(hi, "low")                                           # the game mesh: the uncarved shape
    grain = B.displace("CLOUDS", scale=0.02, strength=0.005)
    s.modify(lo, grain)
    cut = s.add(cutters(), "glow", emit=1.0)
    s.remesh(cut, 0.012)
    inner = s.copy(hi, "inner")
    s.modify(inner, B.inflate(-p.cut))
    s.remesh(inner, 0.02)
    s.boolean(cut, inner, materials="INDEX")                         # exact depth: only the outer 40 mm is cut
    s.boolean(hi, cut)
    s.modify(hi, grain)
    s.decimate(lo, p.tris)
    s.shade(lo, sharp_angle=60)
    s.unwrap(lo, margin=0.005)
    s.bake([hi], lo, size=p.texture, maps=("normal", "ao", "curvature", "emit"), cage=0.04, ray=0.15, samples=48)
    s.weights(lo, sk)                                                # bone heat, on the mesh the game will draw
    r = s.run()
    low = r.mesh(lo)
    joints, weights = r.skin(lo)
    drop = low.bounds[0][1]
    low = low.moved(0, -drop, 0)                                     # stand it on Y=0

    n = p.texture
    pos, nrm, mask = texel_maps(low, n)
    ao, curv = r.image("ao"), r.image("curvature")
    glow = np.clip(blur(r.image("emit"), 1) * 1.6, 0, 1) * mask
    rock = tint(fbm3(pos, 0.4, seed=p.seed), (0.26, 0.23, 0.21), (0.52, 0.47, 0.41))
    rock *= (0.85 + 0.3 * noise3(pos, 0.012, p.seed + 1))[..., None]
    rock *= (0.42 + 0.58 * ao)[..., None]
    rock = np.clip(rock + 0.4 * np.clip(curv - 0.52, 0, 0.3)[..., None], 0, 1)
    up = np.clip((nrm[..., 1] - 0.35) / 0.45, 0, 1) * np.clip((pos[..., 1] - 1.2) / 0.5, 0, 1)   # shoulders, head
    moss = np.clip(up * 1.7 * fbm3(pos, 0.18, seed=p.seed + 2) - 0.2, 0, 1) * (1 - glow)
    green = tint(noise3(pos, 0.04, p.seed + 3), (0.12, 0.18, 0.06), (0.25, 0.33, 0.12))
    base = rock * (1 - moss[..., None]) + green * moss[..., None]
    base = base * (1 - 0.85 * glow[..., None])
    rough = np.clip(0.88 + 0.07 * moss - 0.35 * glow, 0, 1)
    flat = np.zeros((n, n, 3)) + [0.5, 0.5, 1.0]
    mat = Material("golem_rock", base=fill_background(base, mask), orm=fill_background(orm(ao, rough, 0.0), mask),
                   normal=fill_background(np.where(mask[..., None], r.image("normal"), flat), mask),
                   emission=fill_background(glow[..., None] * np.array(GLOW), mask), emissive=(1.0, 1.0, 1.0),
                   emissive_strength=p.glow, metallic=1.0, roughness=1.0)

    ch = Character(sk)
    ch.add_skinned(low, mat, joints, weights)
    ch.clips = [idle(), walk(), smash()]
    ch.meta = dict(high_tris=r.step("modify", 3)["triangles"], blender=r.info["blender"],
                   glow_share=float((glow > 0.5).sum() / max(mask.sum(), 1)), bake_seconds=r.seconds, cached=r.cached)
    return ch
