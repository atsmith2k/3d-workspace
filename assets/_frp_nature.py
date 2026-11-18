"""Wilderness: what trees, rocks and plants share.

Cinder 0.1.1 draws alpha-masked materials opaque, so nothing here is a leaf card. Foliage is
solid, faceted geometry in flat palette colours (no texture, no sampler): a canopy is a few
lumpy masses, a grass clump a fan of two-sided blades. Trunks and rocks carry the two textured
materials, `bark()` and `rock()`.

Growth leans autumn and blight: rust and dark green, never a fresh green. Trees have no body in
a kit world (any kit collider would make the canopy solid); each says the collider it wants.
"""
from _frp import *


def lumpy(mesh, amount, scale=1.0, seed=0, centre=None):
    """Push each vertex in or out from `centre` by smooth noise of its position (so seam
    vertices that share a position move together), up to `amount` of its distance."""
    c = mesh.v.mean(0) if centre is None else np.asarray(centre, float)
    d = mesh.v - c
    k = 1 + amount * (2 * fbm3(mesh.v, scale, 3, seed) - 1)        # scale: metres across one lump
    return Mesh(c + d * k[:, None], mesh.f, None, mesh.uv)


def blob(r, seed, squash=0.8, sides=8, rings=5, amount=0.28):
    """A faceted, lumpy mass centred on the origin: a canopy clump, a bush, the start of a rock."""
    m = lumpy(ball(r, sides, rings), amount, 0.9 * r, seed, centre=(0, 0, 0)).scaled(1.0, squash, 1.0)
    return flat(m)


def stem(points, radii, sides=7, u_repeat=1.0, per_metre=0.5):
    """A trunk or branch through a list of points with a radius at each: a tube with rings at
    the points, UVs running round (u) and along its length in metres (v), open at both ends."""
    pts, radii = np.asarray(points, float), np.asarray(radii, float)
    seg = np.diff(pts, axis=0)
    length = np.concatenate([[0], np.cumsum(np.linalg.norm(seg, axis=1))])
    tang = np.vstack([seg[:1], (seg[:-1] + seg[1:]) / 2, seg[-1:]])
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    ref = np.array([0.0, 0.0, 1.0])
    ang = np.linspace(0, 2 * np.pi, sides + 1)
    vs, ns, uvs, fs = [], [], [], []
    for i, (p, t, r) in enumerate(zip(pts, tang, radii)):
        a = np.cross(t, ref if abs(t @ ref) < 0.9 else np.array([1.0, 0.0, 0.0]))
        a /= np.linalg.norm(a)
        b = np.cross(t, a)
        ring = np.outer(np.cos(ang), a) + np.outer(np.sin(ang), b)
        vs.append(p + r * ring)
        ns.append(ring)
        uvs.append(np.c_[np.linspace(0, u_repeat, sides + 1), np.full(sides + 1, -length[i] * per_metre)])
    w = sides + 1
    for i in range(len(pts) - 1):
        for k in range(sides):
            q, s_, t_, u_ = i * w + k, i * w + k + 1, (i + 1) * w + k + 1, (i + 1) * w + k
            fs += [(q, s_, t_), (q, t_, u_)]
    v, nrm, f = np.vstack(vs), np.vstack(ns), np.array(fs)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    keep = np.linalg.norm(fn, axis=1) > 1e-12
    f, fn = f[keep], fn[keep]
    back = (fn * nrm[f].sum(1)).sum(1) < 0
    f[back] = f[back][:, ::-1]
    return Mesh(v, f, nrm, np.vstack(uvs))


def two_sided(mesh):
    """The mesh and its back: for blades and fronds, which are seen from both sides."""
    return merge(mesh, Mesh(mesh.v, mesh.f[:, ::-1], -mesh.n, mesh.uv))


def blade(base, tip, width, lean=(0, 0, 0)):
    """One grass blade or frond leaflet: a two-sided triangle from a base of `width` to a tip."""
    base, tip = np.asarray(base, float), np.asarray(tip, float)
    side = np.cross(tip - base, [0, 1, 0])
    if np.linalg.norm(side) < 1e-6:
        side = np.array([1.0, 0, 0])
    side = side / np.linalg.norm(side) * width / 2
    mid = (base + tip) / 2 + np.asarray(lean, float)
    v = np.array([base - side, base + side, mid + side * 0.6, mid - side * 0.6, tip])
    return two_sided(Mesh(v, [(0, 1, 2), (0, 2, 3), (3, 2, 4)]))


def plant_checks(x, y, z, kind, mats, anchor="base"):
    b = BUDGET_OF[kind]
    return [size(x=x, y=y, z=z), tris(max=b["tris"]), pivot(anchor, tol=0.03), materials(mats), texture_size(b["texture"])]


def on_ground(tol=0.004):
    """Nothing below the ground, and it touches it."""
    def fn(ctx):
        lo = ctx.model.bounds[0][1]
        return abs(lo) <= tol, f"lowest point {lo * 1000:+.0f} mm from the ground"
    return custom("stands on the ground", fn)


# ---------------------------------------------------------------- sculpted and baked (needs Blender)
# A rock or a canopy drawn as a few hundred flat facets reads as a paper model. These are made
# the way such assets are made by hand: a heavy mesh is sculpted (lumps, facets, grain), a light
# one is cut from it, and the difference is baked into a normal map, an occlusion map and a
# curvature map. The colour is then painted in world space from those maps, so crevices are dark
# and edges worn because the shape says so. Nothing here is generated: it needs nobody's clearing.

def sculpt(shape, tris, size, lumps=(0.5, 0.2), facets=(0.18, 0.05), grain=(0.03, 0.005), fuse=None, ground=True,
           levels=5, sharp=60):
    """Sculpt `shape` in Blender and bake it onto a game mesh of `tris` triangles with `size` px
    maps. lumps, facets, grain: (feature size in metres, strength in metres) of three scales of
    displacement; the grain goes into the bake only. fuse: a voxel size, to join overlapping
    parts into one skin first. ground: cut flat at Y=0. Returns (low Mesh, Result)."""
    from cadkit.game import blender as B
    from cadkit.game.mesh import wind_to_normals
    s = B.Session()
    hi = s.add(shape, "high")
    if fuse:
        s.remesh(hi, fuse)
        s.modify(hi, B.smooth(0.5, 3), B.subsurf(1))
    else:
        s.modify(hi, B.subsurf(levels))
    s.modify(hi, B.displace("CLOUDS", scale=lumps[0], strength=lumps[1]),
             B.displace("VORONOI", scale=facets[0], strength=facets[1]))
    if ground:
        s.boolean(hi, s.add(box(40, 2, 40).moved(0, -1.0, 0), "ground"))
    lo = s.copy(hi, "low")
    s.modify(hi, B.displace("CLOUDS", scale=grain[0], strength=grain[1]))
    s.decimate(lo, tris)
    s.shade(lo, sharp_angle=sharp)
    s.unwrap(lo, margin=0.006)
    reach = max(lumps[1], facets[1])
    s.bake([hi], lo, size=size, maps=("normal", "ao", "curvature"), cage=0.25 * reach + 0.02, ray=reach + 0.06, samples=48)
    r = s.run()
    low = wind_to_normals(r.mesh(lo))
    if ground:                                                   # the face it stands on is never seen: do not draw it
        under = (low.v[low.f][:, :, 1] < 2e-3).all(1)
        idx = np.unique(low.f[~under])
        remap = -np.ones(len(low.v), int)
        remap[idx] = np.arange(len(idx))
        low = Mesh(low.v[idx], remap[low.f[~under]], low.n[idx], low.uv[idx])
    return low, r


def _finish(name, low, r, size, base, rough, height, mask, relief):
    """A baked material: colour and roughness as painted, the baked normal with a fine detail
    normal from `height` (0..1, `relief` metres deep) laid over it."""
    from cadkit.game import gen                                    # numpy helpers only: nothing is generated
    flat_n = np.zeros((size, size, 3)) + [0.5, 0.5, 1.0]
    baked = np.where(mask[..., None], r.image("normal"), flat_n) * 2 - 1
    # between fused lobes a bake ray can find the wrong surface and a texel comes back leaning
    # into the mesh; such a texel would shade black, so it is stood up to at most 80 degrees
    baked[..., 2] = np.maximum(baked[..., 2], 0.17)
    baked = baked / np.linalg.norm(baked, axis=2, keepdims=True) * 0.5 + 0.5
    detail = gen.slope_normal(height * relief, 1.0 / gen.texel_metres(low, mask), mask=mask)
    normal = gen.combine_normals(baked, np.where(mask[..., None], detail, flat_n))
    return Material(name, base=fill_background(np.clip(base, 0, 1), mask), orm=fill_background(orm(r.image("ao"), rough, 0.0), mask),
                    normal=fill_background(normal, mask), metallic=1.0, roughness=1.0)


def paint_rock(low, r, size, seed=0, moss=1.0, name="frp_fieldstone"):
    """Field stone painted from the bake: cold grey that drifts in tone, dark in the crevices,
    worn pale on the edges, moss where faces look up. Returns (Material, facts for checks)."""
    pos, nrm, mask = texel_maps(low, size)
    ao, curv = r.image("ao"), r.image("curvature")
    tone = 0.5 * fbm3(pos, 0.4, 4, seed) + 0.3 * fbm3(pos, 0.07, 3, seed + 1) + 0.2 * fbm3(pos, 0.012, 2, seed + 2)
    stone_c = tint(np.clip((tone - 0.25) * 1.8, 0, 1), P["stone_shadow"], P["stone_light"])
    speck = np.clip((fbm3(pos, 0.006, 2, seed + 3) - 0.68) * 6, 0, 1)                        # pale flecks in the stone
    stone_c = stone_c * (1 + 0.35 * speck[..., None])
    stone_c = stone_c * (0.38 + 0.62 * ao)[..., None] * (1 + 1.3 * np.clip(curv - 0.52, 0, 0.3))[..., None]
    up = np.clip((nrm[..., 1] - 0.25) / 0.6, 0, 1)
    patch = 0.6 * fbm3(pos, 0.3, 4, seed + 4) + 0.4 * fbm3(pos, 0.05, 3, seed + 5)
    damp = np.clip(1 - pos[..., 1] / 0.25, 0, 1) * np.clip((0.85 - ao) / 0.4, 0, 1)          # low down, in the creases
    cover = np.clip((np.maximum(up, 0.7 * damp) * patch * 2.0 * moss - 0.98) * 6, 0, 1) * mask   # in drifts, never a cap
    fronds = fbm3(pos, 0.01, 3, seed + 6)
    dying = np.clip((fbm3(pos, 0.15, 3, seed + 7) - 0.55) * 4, 0, 1)[..., None]
    hue = np.array(P["grass_dark"]) * 0.5 + np.array(P["moss"]) * 0.5
    moss_c = (0.55 + 0.9 * fronds)[..., None] * (hue * (1 - dying) + np.array(P["blight"]) * 0.7 * dying) * (0.55 + 0.45 * ao)[..., None]
    base = stone_c * (1 - cover[..., None]) + moss_c * cover[..., None]
    rough = np.clip(0.8 + 0.1 * tone, 0, 1) * (1 - cover) + 0.97 * cover
    height = 0.6 * fbm3(pos, 0.012, 3, seed + 2) * (1 - cover) + (0.5 + 0.5 * fronds) * cover
    facts = dict(mask=mask, moss_share=float(cover[mask].mean()), mean=float(np.clip(base, 0, 1)[mask].mean()),
                 used=float(mask.mean()), moss_up=float(cover[mask & (nrm[..., 1] > 0.7)].mean()),
                 moss_side=float(cover[mask & (np.abs(nrm[..., 1]) < 0.3)].mean()))
    return _finish(name, low, r, size, base, rough, height, mask, 0.004), facts


def paint_foliage(low, r, size, seed=0, name="frp_foliage", turned=0.5):
    """A canopy painted from the bake: masses of leaves in drifts of dark green and rust
    (`turned`: the share that has turned), each leaf clump lit on top and dark underneath and
    inside. Returns (Material, facts for checks)."""
    pos, nrm, mask = texel_maps(low, size)
    ao, curv = r.image("ao"), r.image("curvature")
    drift = 0.65 * fbm3(pos, 1.3, 3, seed) + 0.35 * fbm3(pos, 0.25, 3, seed + 1)
    edge = float(np.quantile(drift[mask], 1 - turned))                                      # so `turned` of it has turned,
    leaves = fbm3(pos, 0.07, 3, seed + 2)                                                    # one leaf clump to the next
    # a soft edge, ragged by the clump: a hard one reads as camouflage paint, not as leaves turning
    rust = np.clip((drift - edge) * 3.5 + 0.5 + 1.1 * (leaves - 0.5), 0, 1)[..., None]
    fine = fbm3(pos, 0.018, 2, seed + 3)
    green = tint(np.clip(0.2 + 0.9 * leaves, 0, 1), P["grass_dark"], P["leaf_dark"]) * 1.25
    red = tint(np.clip(0.1 + 1.0 * leaves, 0, 1), P["leaf_rust"], 0.5 * (np.array(P["leaf_rust"]) + np.array(P["leaf_autumn"])))
    col = (green * (1 - rust) + red * rust) * (0.7 + 0.6 * fine)[..., None]
    sky = np.clip(0.5 + 0.5 * nrm[..., 1], 0, 1)                                             # lit from above, dark underneath
    # shade lightly: the engine lights the crown too, and a canopy seen from underneath that is
    # painted dark there as well comes out as a black, wet-looking mass
    col = col * (0.5 + 0.5 * ao)[..., None] * (0.82 + 0.3 * sky)[..., None] * (1 + 0.8 * np.clip(curv - 0.52, 0, 0.3))[..., None]
    rough = np.clip(0.9 + 0.08 * fine, 0, 1)
    facts = dict(mask=mask, turned=float(rust[..., 0][mask].mean()), mean=float(np.clip(col, 0, 1)[mask].mean()), used=float(mask.mean()))
    return _finish(name, low, r, size, col, rough, 0.6 * leaves + 0.4 * fine, mask, 0.004), facts


def baked_checks(high_min, used_min=0.3, part=0):
    """Checks every sculpted asset carries: how heavy the sculpt was, that the UV layout uses
    the texture, that no texel is shared."""
    def heavy(ctx):
        n = ctx.model.meta["high_tris"]
        return n >= high_min, f"{n:,} triangles sculpted, baked onto {ctx.model.triangles:,}"

    def used(ctx):
        u = ctx.model.meta["used"]
        return u >= used_min, f"UV islands cover {u:.0%} of the texture"
    return [uv_unique(part=part), custom("high poly", heavy), custom("texture used", used)]


def clumps(masses, seed=0, sub=7, share=0.5, squash=0.75):
    """The shape a canopy or thicket is sculpted from: for each (centre, radius) a core and
    `sub` smaller balls standing out of it, so the fused crown has a silhouette of leaf clumps
    rather than of a few smooth lumps."""
    rng = np.random.default_rng(seed)
    out = []
    for at, r in masses:
        out.append(ball(0.82 * r, 10, 7).scaled(1.0, squash, 1.0).moved(*at))
        for _ in range(sub):
            d = rng.normal(size=3)
            d[1] = abs(d[1]) * 0.8 - 0.25                                    # more on top and round the sides than beneath
            d /= np.linalg.norm(d)
            k = share * rng.uniform(0.75, 1.15)
            c = np.asarray(at, float) + d * [1.0, squash, 1.0] * r * 0.72
            out.append(ball(k * r, 8, 6).scaled(1.0, 0.85, 1.0).moved(*c))
    return merge(*out)
