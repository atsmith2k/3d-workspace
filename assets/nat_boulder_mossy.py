"""Mossy boulder: a sculpted rock whose surface is a generated granite, projected onto the bake.

The first asset that joins the two deep ends of the pipeline. Blender sculpts a 400,000-triangle
boulder and bakes its shape onto a 2,500-triangle game mesh (normal, occlusion, curvature). Two
generated pictures, granite and moss, are turned into PBR surfaces and projected onto that mesh
in world space, so the stone has the look of real rock at 2048 px with no UV seams, while the
cracks stay dark and the edges worn because the bake says where they are.

Spec:
  kind: environment
  size: about 1.7 x 1.0 x 1.3 m; chest height beside a 1.8 m figure
  pivot: flat base on Y=0, centred
  budget: 3,000 triangles, one material, 2048 px textures (three maps)
  high poly: at least 300,000 triangles before baking
  materials: generated weathered granite (assets/gen/frp_granite), dark in the crevices and paler
             on worn edges from the bake; generated moss (assets/gen/frp_moss) on faces that look
             up and low in the damp; both darkened to the pack's palette
  features: lumps of 0.6 m and facets of 0.2 m sculpted; grain and lichen from the generated
            surface as colour and as a detail normal laid over the baked one; moss covers
            12-45 % of the stone, thickest on top and ragged at its edge
  use: wilderness dressing, cover, a landmark by a path
  engine: body static, auto collider
  needs: Blender 5.x; two generated inputs (`--gen`, OpenAI images), not cleared: not for sale
         until a person clears them
"""
from _frp import *
from cadkit.game import blender as B
from cadkit.game import gen
from cadkit.game.mesh import wind_to_normals

KIND = "environment"
DESCRIPTION = "sculpted boulder with a generated granite and moss surface projected onto the bake"
PARAMS = dict(width=1.7, tris=2500, texture=2048, seed=11, moss=1.0)
BUDGET = dict(tris=3000, texture=2048, materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("generated", "boulder", "rock", "moss", "baked", sellable=False)

GRANITE = "weathered dark grey granite rock face, fine speckled grain, hairline cracks, small patches of pale lichen"
MOSS = "thick damp dark green moss, dense tiny fronds, a few dead brown strands"


def checks(p):
    def baked(ctx):
        m = ctx.model.meta
        return m["high_tris"] >= 300_000, f"{m['high_tris']:,} triangles sculpted, baked onto {ctx.model.triangles:,}"

    def even(ctx):
        u = ctx.model.meta["unevenness"]
        return max(u.values()) < 0.06, "lighting left in the generated surfaces: " + ", ".join(f"{k} {v:.3f}" for k, v in u.items())

    def tiles(ctx):
        e = ctx.model.meta["seam"]
        return max(e.values()) < 1.6, "wrap error of the surfaces: " + ", ".join(f"{k} {v:.2f}" for k, v in e.items())

    def moss(ctx):
        share = ctx.model.meta["moss_share"]
        return 0.12 < share < 0.45, f"moss covers {share:.0%} of the stone"

    def moss_on_top(ctx):
        up, down = ctx.model.meta["moss_up"], ctx.model.meta["moss_side"]
        return up > 2 * down and up < 0.95, f"moss on {up:.0%} of upward texels and {down:.0%} of steep ones"

    def grain(ctx):
        m = ctx.model.meta
        return m["detail_lean"] > 1.5 and m["detail_lean"] < 20, (f"the generated grain adds {m['detail_lean']:.1f} degrees of "
                                                                 f"lean to the baked normals ({m['baked_lean']:.1f})")

    def dark(ctx):
        base = np.asarray(ctx.model.materials[0].base)[ctx.model.meta["mask"]]
        lum = float(base.mean())
        return 0.10 < lum < 0.36, f"mean base colour {lum:.2f}: dark-fantasy stone, not washed out and not black"
    return [size(x=(p.width - 0.25, p.width + 0.25), y=(0.75, 1.25), z=(1.0, 1.6)), tris(max=3000),
            pivot((None, 0.0, None)), materials(1), texture_size(2048), uv_unique(),
            custom("high poly", baked), custom("surfaces evenly lit", even), custom("surfaces tile", tiles),
            custom("moss cover", moss), custom("moss lies on top", moss_on_top), custom("generated grain", grain),
            custom("palette", dark)]


def lean(normal, mask):
    n = np.asarray(normal)[mask] * 2 - 1
    return float(np.degrees(np.arccos(np.clip(n[:, 2], -1, 1))).mean())


def build(p):
    k = p.width / 1.7
    rough_shape = ball(0.5, 12, 8).scaled(1.7 * k, 1.25 * k, 1.3 * k).moved(0, 0.42 * k, 0)
    s = B.Session()
    hi = s.add(rough_shape, "high")
    s.modify(hi, B.subsurf(6),
             B.displace("CLOUDS", scale=0.6, strength=0.22),          # lumps
             B.displace("VORONOI", scale=0.2, strength=0.05))         # facets
    under = s.add(box(4, 2, 4).moved(0, -1.0, 0), "ground")           # a flat base: it sits in the ground
    s.boolean(hi, under)
    lo = s.copy(hi, "low")
    s.modify(hi, B.displace("CLOUDS", scale=0.03, strength=0.005))    # grain, in the bake only
    s.decimate(lo, p.tris)
    s.shade(lo, sharp_angle=50)
    s.unwrap(lo, margin=0.006)
    s.bake([hi], lo, size=p.texture, maps=("normal", "ao", "curvature"), cage=0.05, ray=0.2, samples=64)
    r = s.run()
    low = wind_to_normals(r.mesh(lo))
    lo_b, hi_b = low.bounds
    low = low.moved(-(lo_b[0] + hi_b[0]) / 2, -lo_b[1], -(lo_b[2] + hi_b[2]) / 2)

    # the generated surfaces: one picture each, made into colour, height and roughness
    granite_img = gen.surface_image(GRANITE, "frp_granite", metres=1.5)
    moss_img = gen.surface_image(MOSS, "frp_moss", metres=1.0, quality="medium")
    granite = gen.pbr(granite_img, metres=1.5, relief=0.008, rough=(0.7, 0.95))
    green = gen.pbr(moss_img, metres=1.0, relief=0.012, rough=(0.9, 1.0))

    n = p.texture
    pos, nrm, mask = texel_maps(low, n)
    ao, curv = r.image("ao"), r.image("curvature")
    g_base, g_h, g_r = granite.sample(pos, nrm)
    m_base, m_h, m_r = green.sample(pos, nrm)
    # stone: the picture, pulled toward the palette, dark in crevices, paler on worn edges
    grey = g_base.mean(2, keepdims=True)
    rock = (0.55 * g_base + 0.45 * grey) * np.array(P["stone_light"]) / 0.5
    rock = rock * (0.4 + 0.6 * ao)[..., None]
    rock = np.clip(rock * (1 + 1.2 * np.clip(curv - 0.52, 0, 0.3))[..., None], 0, 1)
    # moss: where faces look up, and low in the damp crevices; it takes the hollows of the grain first
    up = np.clip((nrm[..., 1] - 0.2) / 0.7, 0, 1)
    damp = np.clip(1 - pos[..., 1] / 0.35, 0, 1) * np.clip((0.8 - ao) / 0.4, 0, 1)
    want = np.maximum(up, 0.8 * damp) * p.moss
    patch = 0.6 * fbm3(pos, 0.3, seed=p.seed) + 0.4 * fbm3(pos, 0.06, seed=p.seed + 1)     # drifts, with a ragged edge
    cover = np.clip((want * (0.3 + 1.5 * patch) + 0.6 * (0.5 - g_h) - 0.62) * 4, 0, 1) * mask
    # the picture gives the moss its texture; the palette gives it its colour (old, damp, half dead)
    tone = m_base.mean(2) / max(float(m_base.mean()), 1e-3)
    dying = np.clip((fbm3(pos, 0.12, seed=p.seed + 2) - 0.55) * 4, 0, 1)[..., None]
    hue = np.array(P["grass_dark"]) * 0.55 + np.array(P["moss"]) * 0.45
    moss_col = tone[..., None] * (hue * (1 - dying) + np.array(P["blight"]) * 0.7 * dying) * (0.6 + 0.4 * ao)[..., None]
    base = np.clip(rock * (1 - cover[..., None]) + moss_col * cover[..., None], 0, 1)
    rough_map = g_r * (1 - cover) + m_r * cover
    # the grain as a detail normal over the baked shape
    texel = gen.texel_metres(low, mask)
    height = g_h * granite.relief * (1 - cover) + (m_h * green.relief + 0.006) * cover       # metres; moss stands proud
    detail = gen.slope_normal(height, 1.0 / texel, mask=mask)
    flat = np.zeros((n, n, 3)) + [0.5, 0.5, 1.0]
    baked_n = np.where(mask[..., None], r.image("normal"), flat)
    normal = gen.combine_normals(baked_n, np.where(mask[..., None], detail, flat))

    mat = Material("frp_boulder_mossy", base=fill_background(base, mask), orm=fill_background(orm(ao, rough_map, 0.0), mask),
                   normal=fill_background(normal, mask), metallic=1.0, roughness=1.0)
    model = Model((low, mat))
    steep = mask & (np.abs(nrm[..., 1]) < 0.3)
    top = mask & (nrm[..., 1] > 0.7)
    model.meta = dict(high_tris=r.step("modify", 0)["triangles"], blender=r.info["blender"], mask=mask,
                      unevenness=dict(granite=gen.unevenness(granite.base), moss=gen.unevenness(green.base)),
                      seam=dict(granite=seam_error(granite.base), moss=seam_error(green.base)),
                      moss_share=float(cover[mask].mean()), moss_up=float(cover[top].mean()), moss_side=float(cover[steep].mean()),
                      baked_lean=lean(baked_n, mask), detail_lean=lean(normal, mask) - lean(baked_n, mask), texel_mm=texel * 1000)
    return model
