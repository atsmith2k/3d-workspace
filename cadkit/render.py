"""Software renderer: a contact sheet of shaded views, so the model can be inspected
without a GUI. Z-buffered, so concave parts (molds, pockets) draw correctly.

Sheet layout (4 x 2 tiles):
  Iso | Top (dims) | Front (dims) | Right (dims)
  Iso from below | Section front | Section right | stats + legend
Faces are tinted red where they overhang and yellow where the wall is thin; section
tiles show cut material in orange."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIEWS = [
    ("Iso", (1, -1, 0.9)),
    ("Top", (0, 0, 1)),
    ("Front", (0, -1, 0)),
    ("Right", (1, 0, 0)),
    ("Iso from below", (-1, 1, -0.8)),
]
# (label, cut axis, camera): the camera looks along the cut axis and everything
# between it and the cut plane is clipped away
SECTIONS = [("Section front", 1, (0, -1, 0)), ("Section right", 0, (1, 0, 0))]
TILE = 480
SS = 2  # supersampling
BG = (246, 247, 249)
BASE = np.array([74, 144, 217], float)
OVERHANG = np.array([225, 70, 60], float)
THIN = np.array([235, 190, 40], float)
CUT = np.array([240, 150, 95], float)
AXES = "XYZ"


def _basis(cam):
    c = np.asarray(cam, float)
    c /= np.linalg.norm(c)
    up = np.array([0, 1.0, 0]) if abs(c[2]) > 0.99 else np.array([0, 0, 1.0])
    r = np.cross(up, c)
    r /= np.linalg.norm(r)
    return r, np.cross(c, r), c


def _project(v, cam, scale, size, center):
    r, u, c = _basis(cam)
    v = v - center
    return v @ r * scale + size / 2, size / 2 - v @ u * scale, v @ c


SHADE = (0.28, 0.55, 0.22)   # ambient, key light, camera fill
EDGE = 0.35                  # how dark silhouette/crease lines are drawn (1 = none)


def _render_view(tm, cam, scale, size, center, tint=None, cut=None, marks=None,
                 bg=BG, shade=SHADE, edge=EDGE):
    """Returns the RGB tile as a float array. `tint` is an (F, 3) per-face colour or
    one RGB for every face. `cut` is a view-space depth: everything nearer the camera
    than that plane is clipped away per pixel, back faces are drawn too, and wherever
    the nearest surviving face is a back face the ray entered material at the cut, so
    that pixel is painted flat orange. The camera must look straight along the cut
    normal. `bg` is the background colour, `shade` the (ambient, key, fill) light
    weights and `edge` the darkening factor for depth-jump lines."""
    r, u, c = _basis(cam)
    sx, sy, sz = _project(tm.vertices, cam, scale, size, center)
    n = tm.face_normals
    facing = n @ c
    vis = np.abs(facing) > 1e-6 if cut is not None else facing > 1e-6
    key = np.array([0.4, -0.3, 0.85]) + c
    key /= np.linalg.norm(key)
    amb, kw, fw = shade
    shade = amb + kw * np.clip(n @ key, 0, 1) + fw * np.clip(n @ c, 0, 1)

    zb = np.full((size, size), -np.inf)
    fid = np.full((size, size), -1, np.int64)
    ids = np.flatnonzero(vis)
    X, Y, Z = sx[tm.faces[ids]], sy[tm.faces[ids]], sz[tm.faces[ids]]
    for k, i in enumerate(ids):
        xs, ys, zs = X[k], Y[k], Z[k]
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
        if cut is not None:
            hit &= z <= cut
        sub[hit] = z[hit]
        fid[y0:y1 + 1, x0:x1 + 1][hit] = i

    empty = fid < 0
    img = np.empty((size, size, 3))
    img[:] = bg
    f = fid[~empty]
    if tint is None:
        colour = BASE * 1.25
    else:
        tint = np.asarray(tint, float)
        colour = (tint[f] if tint.ndim == 2 else tint) * 1.25
    px = np.clip(shade[f, None] * colour, 0, 255)
    if cut is not None:
        px[facing[f] < 0] = CUT
    img[~empty] = px
    # dark silhouette/crease lines where depth jumps
    z = np.where(empty, zb[~empty].min() - 1 if (~empty).any() else 0, zb)
    lines = np.zeros_like(empty)
    jump = 4 / scale  # depth step bigger than ~4 pixels' worth of mm
    lines[:-1] |= np.abs(np.diff(z, axis=0)) > jump
    lines[:, :-1] |= np.abs(np.diff(z, axis=1)) > jump
    lines[:-1] |= empty[:-1] != empty[1:]
    lines[:, :-1] |= empty[:, :-1] != empty[:, 1:]
    img[lines] = img[lines] * edge
    if marks is not None and len(marks):
        # yellow dots at sample points that are visible in this view (depth test)
        mx, my, mz = _project(np.asarray(marks, float), cam, scale, size, center)
        rad = max(2, SS * 2)
        for x, y, zm in zip(mx, my, mz):
            xi, yi = int(x), int(y)
            if 0 <= xi < size and 0 <= yi < size and zm >= zb[yi, xi] - 0.6:
                img[max(yi - rad, 0):yi + rad + 1, max(xi - rad, 0):xi + rad + 1] = THIN
    return img


SECTION_DEPTH = 10.0   # mm of enclosed-void geometry kept behind a cut plane


def _subset(tm, keep):
    """Mesh of the kept faces; same vertices, so projections stay identical."""
    import trimesh
    return trimesh.Trimesh(tm.vertices, tm.faces[keep], face_normals=tm.face_normals[keep], process=False)


def _view(tm, cam, scale, size, center, tint=None, cut=None, hidden=None, marks=None):
    """Faces of enclosed voids (`hidden`) can never be seen from outside, so they are
    dropped from exterior views (a lattice-filled part is 98% void faces). Section
    views keep the ones just behind the cut, where the lattice shows."""
    if hidden is not None and hidden.any():
        keep = ~hidden
        if cut is not None:
            depth = _project(tm.vertices, cam, scale, size, center)[2][tm.faces].max(axis=1)
            keep |= (depth <= cut) & (depth >= cut - SECTION_DEPTH * scale)
        tm = _subset(tm, keep)
        tint = tint[keep] if tint is not None else None
    return _render_view(tm, cam, scale, size, center, tint, cut, marks)


def _tile(img):
    return Image.fromarray(img.astype(np.uint8)).resize((TILE, TILE), Image.LANCZOS)


def _draw_dims(im, tm, cam, scale, center, font):
    """Overall extents along the two screen axes, drawn just outside the silhouette."""
    r, u, _ = _basis(cam)
    lo, hi = tm.bounds
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    sx, sy, _ = _project(corners, cam, scale / SS, TILE, center)
    x0, x1, y0, y1 = sx.min(), sx.max(), sy.min(), sy.max()
    ext = hi - lo
    h_axis, v_axis = int(np.argmax(np.abs(r))), int(np.argmax(np.abs(u)))
    d = ImageDraw.Draw(im)
    grey, dark = (120, 125, 135), (40, 40, 40)
    # horizontal dimension under the part
    yl = min(y1 + 16, TILE - 14)
    d.line([(x0, yl), (x1, yl)], fill=grey, width=1)
    d.line([(x0, yl - 5), (x0, yl + 5)], fill=grey)
    d.line([(x1, yl - 5), (x1, yl + 5)], fill=grey)
    label = f"{AXES[h_axis]} {ext[h_axis]:.1f}"
    w = d.textlength(label, font=font)
    d.rectangle([(x0 + x1) / 2 - w / 2 - 3, yl - 8, (x0 + x1) / 2 + w / 2 + 3, yl + 8], fill=BG)
    d.text(((x0 + x1) / 2 - w / 2, yl - 7), label, fill=dark, font=font)
    # vertical dimension to the right of the part
    xl = min(x1 + 16, TILE - 4)
    d.line([(xl, y0), (xl, y1)], fill=grey, width=1)
    d.line([(xl - 5, y0), (xl + 5, y0)], fill=grey)
    d.line([(xl - 5, y1), (xl + 5, y1)], fill=grey)
    label = f"{AXES[v_axis]} {ext[v_axis]:.1f}"
    w = d.textlength(label, font=font)
    tx = min(xl + 6, TILE - w - 2)
    d.rectangle([tx - 2, (y0 + y1) / 2 - 8, tx + w + 2, (y0 + y1) / 2 + 8], fill=BG)
    d.text((tx, (y0 + y1) / 2 - 7), label, fill=dark, font=font)


def render_sheet(tm, path, title, info_lines, overhang_faces=None, thin_faces=None,
                 sections=None, hidden_faces=None, thin_points=None):
    """`sections`: list of (axis_index, position_mm) cuts; default both through the
    bounding-box centre."""
    size = TILE * SS
    center = tm.bounds.mean(axis=0)
    radius = np.linalg.norm(tm.extents) / 2
    scale = size * 0.44 / radius
    font = ImageFont.load_default(size=15)
    small = ImageFont.load_default(size=13)
    tint = np.tile(BASE, (len(tm.faces), 1))
    if overhang_faces is not None:
        tint[overhang_faces] = OVERHANG
    # thin walls are marked at the sample points rather than by tinting faces: one
    # thin spot on a large flat facet would otherwise paint the whole facet yellow

    tiles = []
    for name, cam in VIEWS:
        im = _tile(_view(tm, cam, scale, size, center, tint, hidden=hidden_faces, marks=thin_points))
        if name in ("Top", "Front", "Right"):
            _draw_dims(im, tm, cam, scale, center, small)
        tiles.append((name, im))
    cuts = dict(sections or [])
    for label, axis, cam in SECTIONS:
        pos = cuts.get(axis, center[axis])
        origin = center.copy()
        origin[axis] = pos
        depth = float((origin - center) @ _basis(cam)[2])
        im = _tile(_view(tm, cam, scale, size, center, cut=depth, hidden=hidden_faces))
        tiles.append((f"{label} at {AXES[axis]}={pos:.1f}", im))

    sheet = Image.new("RGB", (TILE * 4, TILE * 2), BG)
    for k, (name, im) in enumerate(tiles):
        ImageDraw.Draw(im).text((10, 8), name, fill=(60, 60, 60), font=font)
        sheet.paste(im, ((k % 4) * TILE, (k // 4) * TILE))
    d = ImageDraw.Draw(sheet)
    x0, y0 = 3 * TILE + 16, TILE + 16
    d.text((x0, y0), title, fill=(20, 20, 20), font=ImageFont.load_default(size=19))
    y = y0 + 34
    passed = [l for l in info_lines if l.startswith("check    PASS")]
    shown = [l for l in info_lines if not l.startswith("check    PASS")]
    if passed:
        shown.append(f"checks   {len(passed)} passed" + (", failures above" if any("FAIL" in l for l in shown) else ""))
    y_max = 2 * TILE - 24 - 3 * 18 - 10   # keep clear of the legend
    for line in shown:
        warn = line.startswith("WARNING") or "FAIL" in line
        for chunk in _wrap(line, 62):
            if y > y_max:
                d.text((x0, y), "...", font=small, fill=(50, 50, 50))
                break
            d.text((x0, y), chunk, font=small, fill=(180, 60, 20) if warn else (50, 50, 50))
            y += 18
        if y > y_max:
            break
    legend = [(OVERHANG, "overhang > 45 deg"), (THIN, "thin wall spot (< 1.2 mm)"), (CUT, "cut material")]
    y = 2 * TILE - 24
    for col, text in legend:
        d.rectangle([x0, y, x0 + 12, y + 12], fill=tuple(int(c) for c in col))
        d.text((x0 + 18, y - 2), text, font=small, fill=(80, 80, 80))
        y -= 18
    for k in range(1, 4):
        d.line([(k * TILE, 0), (k * TILE, 2 * TILE)], fill=(220, 222, 226))
    d.line([(0, TILE), (4 * TILE, TILE)], fill=(220, 222, 226))
    sheet.save(path)


def _wrap(line, width):
    out, cur = [], ""
    for w in line.split(" "):
        if cur and len(cur) + len(w) + 1 > width:
            out.append(cur)
            cur = "         " + w
        else:
            cur = f"{cur} {w}" if cur else w
    return out + [cur]


# ---------------------------------------------------------------- product render

PRODUCT_CAM = (1, -1, 0.9)          # the preview's iso view
HERO_CAM = (0.55, -1, 0.42)         # lower and more frontal, for the shop hero image
PRODUCT_BG = (255, 255, 255)
PRODUCT_TINT = np.array([186, 188, 192], float)   # neutral light grey, x1.25 in the shader
CAST_TINT = np.array([176, 170, 160], float)      # warm cement grey, for the cast render
PRODUCT_SHADE = (0.36, 0.5, 0.2)
PRODUCT_EDGE = 0.55
PRODUCT_SS = 2


def render_product(tm, path, cam=PRODUCT_CAM, size=1600, ss=PRODUCT_SS, fill=0.80, tint=PRODUCT_TINT):
    """A clean single-view product picture: square `size` px, white background, one
    neutral tint, soft edge lines, no overlays, dimensions or marks. `tm` may be a
    list of meshes (a multi-part model), drawn together in print pose. Renders at
    `ss` x supersampling and downsamples; returns the time it took in seconds.
    `tint` is the surface colour (CAST_TINT for a mold's casting)."""
    import time
    import trimesh
    t0 = time.time()
    if isinstance(tm, (list, tuple)):
        tm = tm[0] if len(tm) == 1 else trimesh.util.concatenate(list(tm))
    px = int(size * ss)
    # frame by the projected silhouette, not the bounding sphere, so the part fills
    # `fill` of the picture whichever way it is viewed
    center = tm.bounds.mean(axis=0)
    r, u, _ = _basis(cam)
    sx, sy, _ = _project(tm.vertices, cam, 1.0, 0, center)
    w, h = sx.max() - sx.min(), sy.max() - sy.min()
    scale = px * fill / max(w, h, 1e-6)
    center = center + r * (sx.max() + sx.min()) / 2 - u * (sy.max() + sy.min()) / 2
    img = _render_view(tm, cam, scale, px, center, tint=tint, bg=PRODUCT_BG,
                       shade=PRODUCT_SHADE, edge=PRODUCT_EDGE)
    im = Image.fromarray(img.astype(np.uint8))
    if px != size:
        im = im.resize((size, size), Image.LANCZOS)
    im.save(path)
    return time.time() - t0
