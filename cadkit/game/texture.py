"""Procedural PBR textures in numpy. Everything is tileable and seeded.

Images are float arrays in 0..1 with row 0 at the top. Base colour is authored in sRGB
(what a paint program shows); height, roughness, metallic and occlusion are linear.
"""
import numpy as np


def noise(size, cells=8, seed=0):
    """Tileable value noise, (size, size) in 0..1, `cells` lattice cells across."""
    rng = np.random.default_rng(seed)
    g = rng.random((cells, cells))
    t = np.arange(size) * cells / size
    i0 = np.floor(t).astype(int) % cells
    i1 = (i0 + 1) % cells
    fr = t - np.floor(t)
    fr = fr * fr * (3 - 2 * fr)
    top = g[np.ix_(i0, i0)] * (1 - fr)[None, :] + g[np.ix_(i0, i1)] * fr[None, :]
    bot = g[np.ix_(i1, i0)] * (1 - fr)[None, :] + g[np.ix_(i1, i1)] * fr[None, :]
    return top * (1 - fr)[:, None] + bot * fr[:, None]


def fbm(size, cells=4, octaves=5, seed=0, gain=0.5):
    """Fractal noise: tileable, 0..1."""
    out, amp, total = np.zeros((size, size)), 1.0, 0.0
    for o in range(octaves):
        c = min(cells * 2 ** o, size)
        out += amp * noise(size, c, seed + 31 * o)
        total += amp
        amp *= gain
    return out / total


def streaks(size, along="x", cells=64, stretch=24, seed=0):
    """Noise stretched along one axis (wood grain, brushed metal). Tileable, 0..1."""
    rng = np.random.default_rng(seed)
    lines = max(2, size // max(1, size // cells))
    g = rng.random((lines, max(2, lines // stretch)))
    yi = (np.arange(size) * lines // size) % lines
    t = np.arange(size) * g.shape[1] / size
    x0 = np.floor(t).astype(int) % g.shape[1]
    x1 = (x0 + 1) % g.shape[1]
    fr = t - np.floor(t)
    img = g[np.ix_(yi, x0)] * (1 - fr) + g[np.ix_(yi, x1)] * fr
    return img if along == "x" else img.T


def blur(img, radius):
    """Tileable box blur applied three times (close to a Gaussian)."""
    r = int(round(radius))
    if r <= 0:
        return img
    out = img.astype(float)
    for _ in range(3):
        for axis in (0, 1):
            acc = np.zeros_like(out)
            for d in range(-r, r + 1):
                acc += np.roll(out, d, axis)
            out = acc / (2 * r + 1)
    return out


def normal_from_height(height, strength=1.0):
    """Tangent-space normal map (glTF convention: +X right, +Y up the image, +Z out) from a
    height field. `strength` is the height range in texels."""
    h = height.astype(float) * strength
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2            # +row is down the image
    n = np.dstack([-dx, dy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def occlusion_from_height(height, radius=6, strength=1.0):
    """Cheap cavity occlusion: texels below their surroundings darken. 0..1, 1 = open."""
    return np.clip(1 - strength * np.clip(blur(height, radius) - height, 0, None) * 2, 0, 1)


def orm(occlusion=1.0, roughness=0.6, metallic=0.0, size=None):
    """Pack occlusion (R), roughness (G), metallic (B) into one linear image."""
    parts = [np.asarray(x, float) for x in (occlusion, roughness, metallic)]
    shape = next((p.shape for p in parts if p.ndim == 2), (size or 4, size or 4))
    return np.dstack([np.broadcast_to(p, shape) for p in parts]).clip(0, 1)


def tint(value, dark, light):
    """Map a 0..1 field onto a colour ramp between two sRGB colours."""
    v = np.clip(value, 0, 1)[..., None]
    return np.asarray(dark, float) * (1 - v) + np.asarray(light, float) * v


def to_u8(img):
    return (np.clip(np.asarray(img, float), 0, 1) * 255 + 0.5).astype(np.uint8)


def seam_error(img):
    """How badly an image fails to tile: the step across each wrap edge relative to the
    largest step between neighbouring rows (or columns) inside the image. Up to about 1.0
    the wrap is no worse than the image's own detail; well above 1 shows a seam."""
    a = np.asarray(img, float)
    if a.ndim == 2:
        a = a[..., None]
    worst = 0.0
    for axis in (0, 1):
        m = np.moveaxis(a, axis, 0)
        inner = np.abs(np.diff(m, axis=0)).reshape(len(m) - 1, -1).mean(1).max()
        worst = max(worst, float(np.abs(m[0] - m[-1]).mean() / max(inner, 1e-6)))
    return worst


# ---------------------------------------------------------------- texturing an unwrapped mesh in world space

def noise3(p, scale=1.0, seed=0):
    """Value noise at 3D points p (..., 3), 0..1, features about `scale` metres across. Sampled
    at each texel's position on the mesh it has no UV seams, unlike a 2D texture."""
    q = np.asarray(p, float) / scale
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)

    def h(dx, dy, dz):
        n = (i[..., 0] + dx) * 73856093 ^ (i[..., 1] + dy) * 19349663 ^ (i[..., 2] + dz) * 83492791 ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0

    x0 = h(0, 0, 0) * (1 - f[..., 0]) + h(1, 0, 0) * f[..., 0]
    x1 = h(0, 1, 0) * (1 - f[..., 0]) + h(1, 1, 0) * f[..., 0]
    x2 = h(0, 0, 1) * (1 - f[..., 0]) + h(1, 0, 1) * f[..., 0]
    x3 = h(0, 1, 1) * (1 - f[..., 0]) + h(1, 1, 1) * f[..., 0]
    return (x0 * (1 - f[..., 1]) + x1 * f[..., 1]) * (1 - f[..., 2]) + (x2 * (1 - f[..., 1]) + x3 * f[..., 1]) * f[..., 2]


def fbm3(p, scale=1.0, octaves=4, seed=0, gain=0.5):
    """Fractal 3D noise, 0..1."""
    out, amp, total = 0.0, 1.0, 0.0
    for o in range(octaves):
        out = out + amp * noise3(p, scale / 2 ** o, seed + 17 * o)
        total += amp
        amp *= gain
    return out / total


def texel_maps(mesh, size):
    """For an unwrapped mesh: what each texel of a size x size texture lies on.
    Returns (position HxWx3, normal HxWx3, mask HxW bool). Texels outside every UV island are
    False in the mask and zero elsewhere. This is how a texture is painted in world space
    (moss on upward faces, dirt near the ground) instead of in UV space."""
    pos = np.zeros((size, size, 3))
    nrm = np.zeros((size, size, 3))
    mask = np.zeros((size, size), bool)
    uv = mesh.uv * size
    for a, b, c in mesh.f:
        p0, p1, p2 = uv[a], uv[b], uv[c]
        x0, x1 = int(max(np.floor(min(p0[0], p1[0], p2[0])), 0)), int(min(np.ceil(max(p0[0], p1[0], p2[0])), size - 1))
        y0, y1 = int(max(np.floor(min(p0[1], p1[1], p2[1])), 0)), int(min(np.ceil(max(p0[1], p1[1], p2[1])), size - 1))
        if x1 < x0 or y1 < y0:
            continue
        det = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(det) < 1e-12:
            continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px, py = xs + 0.5, ys + 0.5
        w0 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) / det
        w1 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) / det
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not inside.any():
            continue
        yy, xx = ys[inside], xs[inside]
        w = np.stack([w0[inside], w1[inside], w2[inside]], 1)
        pos[yy, xx] = w @ mesh.v[[a, b, c]]
        nrm[yy, xx] = w @ mesh.n[[a, b, c]]
        mask[yy, xx] = True
    length = np.linalg.norm(nrm, axis=2, keepdims=True)
    return pos, nrm / np.maximum(length, 1e-9), mask


def fill_background(img, mask):
    """Carry each UV island's edge colour out over the empty texels around it, so mip-mapping
    and filtering never pull in the background. `mask` is True on the islands."""
    from scipy import ndimage
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return np.asarray(img)[idx[0], idx[1]]


def uv_overlap(mesh, size=1024):
    """Share of the covered texels whose centre lies inside more than one triangle: 0 for a
    clean unwrap. A baked map needs every face to own its texels."""
    count = np.zeros((size, size), np.int32)
    uv = mesh.uv * size
    for a, b, c in mesh.f:
        p0, p1, p2 = uv[a], uv[b], uv[c]
        x0, x1 = int(max(np.floor(min(p0[0], p1[0], p2[0])), 0)), int(min(np.ceil(max(p0[0], p1[0], p2[0])), size - 1))
        y0, y1 = int(max(np.floor(min(p0[1], p1[1], p2[1])), 0)), int(min(np.ceil(max(p0[1], p1[1], p2[1])), size - 1))
        det = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if x1 < x0 or y1 < y0 or abs(det) < 1e-12:
            continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px, py = xs + 0.5, ys + 0.5
        w0 = ((p1[1] - p2[1]) * (px - p2[0]) + (p2[0] - p1[0]) * (py - p2[1])) / det
        w1 = ((p2[1] - p0[1]) * (px - p2[0]) + (p0[0] - p2[0]) * (py - p2[1])) / det
        inside = (w0 > 1e-6) & (w1 > 1e-6) & (1 - w0 - w1 > 1e-6)      # strictly inside: shared edges are nobody's
        count[ys[inside], xs[inside]] += 1
    covered = count > 0
    return float((count > 1).sum() / max(covered.sum(), 1))
