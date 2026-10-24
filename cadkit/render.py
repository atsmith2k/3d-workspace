"""Software renderer: a contact sheet of shaded views, so the model can be inspected
without a GUI. Z-buffered, so concave parts (molds, pockets) draw correctly."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIEWS = [
    ("Iso", (1, -1, 0.9)),
    ("Top", (0, 0, 1)),
    ("Front", (0, -1, 0)),
    ("Right", (1, 0, 0)),
    ("Iso from below", (-1, 1, -0.8)),
]
TILE = 480
SS = 2  # supersampling
BG = (246, 247, 249)
BASE = np.array([74, 144, 217], float)


def _basis(cam):
    c = np.asarray(cam, float)
    c /= np.linalg.norm(c)
    up = np.array([0, 1.0, 0]) if abs(c[2]) > 0.99 else np.array([0, 0, 1.0])
    r = np.cross(up, c)
    r /= np.linalg.norm(r)
    return r, np.cross(c, r), c


def _render_view(tm, cam, scale, size):
    r, u, c = _basis(cam)
    center = tm.bounds.mean(axis=0)
    v = tm.vertices - center
    sx = v @ r * scale + size / 2
    sy = size / 2 - v @ u * scale
    sz = v @ c
    n = tm.face_normals
    vis = n @ c > 1e-6
    key = np.array([0.4, -0.3, 0.85]) + c
    key /= np.linalg.norm(key)
    shade = 0.28 + 0.55 * np.clip(n @ key, 0, 1) + 0.22 * np.clip(n @ c, 0, 1)

    zb = np.full((size, size), -np.inf)
    col = np.zeros((size, size))
    F = tm.faces[vis]
    sh = shade[vis]
    X, Y, Z = sx[F], sy[F], sz[F]
    for i in range(len(F)):
        xs, ys, zs = X[i], Y[i], Z[i]
        x0, x1 = max(int(xs.min()), 0), min(int(np.ceil(xs.max())), size - 1)
        y0, y1 = max(int(ys.min()), 0), min(int(np.ceil(ys.max())), size - 1)
        if x0 > x1 or y0 > y1:
            continue
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l1 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        l2 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        l3 = 1 - l1 - l2
        z = l1 * zs[0] + l2 * zs[1] + l3 * zs[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        hit = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4) & (z > sub)
        sub[hit] = z[hit]
        col[y0:y1 + 1, x0:x1 + 1][hit] = sh[i]

    empty = np.isinf(zb)
    img = np.empty((size, size, 3))
    img[:] = BG
    img[~empty] = np.clip(col[~empty, None] * BASE * 1.25, 0, 255)
    # dark silhouette/crease lines where depth jumps
    z = np.where(empty, zb[~empty].min() - 1 if (~empty).any() else 0, zb)
    edge = np.zeros_like(empty)
    jump = 4 / scale  # depth step bigger than ~4 pixels' worth of mm
    edge[:-1] |= np.abs(np.diff(z, axis=0)) > jump
    edge[:, :-1] |= np.abs(np.diff(z, axis=1)) > jump
    edge[:-1] |= empty[:-1] != empty[1:]
    edge[:, :-1] |= empty[:, :-1] != empty[:, 1:]
    img[edge] = img[edge] * 0.35
    return Image.fromarray(img.astype(np.uint8))


def render_sheet(tm, path, title, info_lines):
    size = TILE * SS
    radius = np.linalg.norm(tm.extents) / 2
    scale = size * 0.44 / radius
    font = ImageFont.load_default(size=15)
    small = ImageFont.load_default(size=13)
    sheet = Image.new("RGB", (TILE * 3, TILE * 2), BG)
    tiles = [(name, _render_view(tm, cam, scale, size)) for name, cam in VIEWS]
    for k, (name, im) in enumerate(tiles):
        im = im.resize((TILE, TILE), Image.LANCZOS)
        ImageDraw.Draw(im).text((10, 8), name, fill=(60, 60, 60), font=font)
        sheet.paste(im, ((k % 3) * TILE, (k // 3) * TILE))
    d = ImageDraw.Draw(sheet)
    x0, y0 = 2 * TILE + 16, TILE + 16
    d.text((x0, y0), title, fill=(20, 20, 20), font=ImageFont.load_default(size=19))
    for i, line in enumerate(info_lines):
        warn = line.startswith("WARNING")
        d.text((x0, y0 + 34 + i * 20), line, font=small,
               fill=(180, 60, 20) if warn else (50, 50, 50))
    for k in range(1, 3):
        d.line([(k * TILE, 0), (k * TILE, 2 * TILE)], fill=(220, 222, 226))
    d.line([(0, TILE), (3 * TILE, TILE)], fill=(220, 222, 226))
    sheet.save(path)
