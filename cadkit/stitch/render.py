"""Preview sheet for a stitch plan:

  sewn      thread-by-thread render on fabric, hoop field dashed, overall size
  detail    a 24 mm window at thread scale (where the density peaks, or `detail=(x, y)`):
            row texture, satin edges, corners, travel left on top
  path      sewing order: thin stitches in thread colour, jump threads red dashed
            (grey when trimmed), block numbers where each colour starts
  density   thread layers per mm2: green normal, yellow dense, red too dense
  bottom    colour swatches (with the nearest Brother thread) and the report lines
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .threads import rgb, thread_label

TILE = 800
SS = 2
FABRIC = (238, 233, 222)
THREAD = 0.45       # mm a 40 wt thread covers once sewn; 0.4 mm rows close up (files
                    # snap to 0.1 mm, so real rows sit 0.35-0.42 apart)


def _xf(bounds, tile, margin=40):
    x0, y0, x1, y1 = bounds
    s = (tile - 2 * margin) / max(x1 - x0, y1 - y0, 1e-6)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def f(p):
        p = np.asarray(p, float)
        return np.c_[(p[..., 0] - cx) * s + tile / 2, tile / 2 - (p[..., 1] - cy) * s]
    return f, s


def _shade(c, k):
    return tuple(int(max(0, min(255, v * k if k < 1 else v + (255 - v) * (k - 1)))) for v in c)


def _fabric(T):
    rng = np.random.default_rng(1)
    noise = rng.normal(0, 4, (T // 4, T // 4)).astype(np.float32)
    base = np.clip(np.array(FABRIC, np.float32)[None, None, :] + noise[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(base).resize((T, T), Image.BILINEAR)


def _threads(im, plan, f, s):
    """Draw every stitch in sewing order at the thread's real width: later stitches
    cover earlier ones, so underlay and buried travel disappear as they do on fabric.
    PIL measures a line's width along its major axis, so a 45 deg stitch would come out
    1/sqrt(2) too thin (fabric shows between rows as moire): widths are corrected per
    stitch."""
    d = ImageDraw.Draw(im)
    w0 = THREAD * s
    for block, r in plan.runs:
        if len(r) < 2:
            continue
        c = rgb(plan.colors[block])
        dark, light = _shade(c, 0.70), _shade(c, 1.25)
        pts = f(r)
        v = np.diff(pts, axis=0)
        L = np.linalg.norm(v, axis=1)
        k = L / np.maximum(np.abs(v).max(1), 1e-9)          # 1 .. sqrt(2)
        for a, b, kk in zip(pts[:-1], pts[1:], k):
            w = max(1, int(np.ceil(w0 * kk)))
            seg = [tuple(a), tuple(b)]
            if w < 6:
                d.line(seg, fill=c, width=w)
                continue
            d.line(seg, fill=dark, width=w)                   # shaded edges, sheen
            d.line(seg, fill=c, width=max(1, int(w * 0.7)))
            d.line(seg, fill=light, width=max(1, w // 4))


def _sewn(plan, hoop_wh, font, box=None):
    T = TILE * SS
    im = _fabric(T)
    d = ImageDraw.Draw(im)
    b = plan.bounds
    W, H = hoop_wh
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    view = (min(b[0], cx - W / 2), min(b[1], cy - H / 2), max(b[2], cx + W / 2), max(b[3], cy + H / 2))
    f, s = _xf(view, T, 40 * SS)
    hx = f(np.array([[cx - W / 2, cy + H / 2], [cx + W / 2, cy - H / 2]]))
    _dashed_rect(d, hx, (170, 165, 155), 2 * SS)
    _threads(im, plan, f, s)
    if box is not None:
        (x0, y0), (x1, y1) = f(np.array([[box[0], box[3]], [box[2], box[1]]]))
        d.rectangle([x0, y0, x1, y1], outline=(200, 40, 40), width=2 * SS)
    im = im.resize((TILE, TILE), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    sw, sh = plan.size
    d.text((12, 10), "sewn", fill=(60, 60, 60), font=font)
    d.text((12, TILE - 28), f"{sw:.1f} x {sh:.1f} mm   (dashed: hoop {W:g} x {H:g})",
           fill=(60, 60, 60), font=font)
    return im


DETAIL = 24.0       # mm across the detail tile


def _detail(plan, centre, font):
    T = TILE * SS
    im = _fabric(T)
    x, y = centre
    box = (x - DETAIL / 2, y - DETAIL / 2, x + DETAIL / 2, y + DETAIL / 2)
    f, s = _xf(box, T, 0)
    _threads(im, plan, f, s)
    d = ImageDraw.Draw(im)
    bar = f(np.array([[box[0] + 1, box[1] + 1.5], [box[0] + 6, box[1] + 1.5]]))
    d.line([tuple(bar[0]), tuple(bar[1])], fill=(30, 30, 30), width=3 * SS)
    im = im.resize((TILE, TILE), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, TILE, 34], fill=(250, 250, 250))
    d.text((12, 10), f"detail  {DETAIL:g} mm at ({x:.0f}, {y:.0f}), red box on 'sewn'   bar 5 mm",
           fill=(60, 60, 60), font=font)
    return im, box


def _dashed_rect(d, corners, color, width, dash=14):
    (x0, y0), (x1, y1) = corners
    for (ax, ay), (bx, by) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                               ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        _dashed(d, (ax, ay), (bx, by), color, width, dash)


def _dashed(d, a, b, color, width, dash=10):
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = np.linalg.norm(b - a)
    n = max(1, int(L / dash))
    for i in range(0, n, 2):
        p, q = a + (b - a) * i / n, a + (b - a) * min(n, i + 1) / n
        d.line([tuple(p), tuple(q)], fill=color, width=width)


def _path(plan, font):
    T = TILE * SS
    im = Image.new("RGB", (T, T), (255, 255, 255))
    d = ImageDraw.Draw(im)
    f, s = _xf(plan.bounds, T, 40 * SS)
    for block, r in plan.runs:
        if len(r) > 1:
            d.line([tuple(p) for p in f(r)], fill=rgb(plan.colors[block]), width=SS)
    for block, a, b, trimmed in plan.jumps:
        pa, pb = f(np.array([a, b]))
        _dashed(d, pa, pb, (150, 150, 150) if trimmed else (220, 30, 30), SS, 8 * SS)
    big = ImageFont.load_default(size=15 * SS)
    seen = set()
    for block, r in plan.runs:
        if block in seen:
            continue
        seen.add(block)
        x, y = f(r[:1])[0]
        d.ellipse([x - 9 * SS, y - 9 * SS, x + 9 * SS, y + 9 * SS], fill=(30, 30, 30))
        lab = str(block + 1)
        d.text((x - d.textlength(lab, font=big) / 2, y - 8 * SS), lab, fill=(255, 255, 255), font=big)
    im = im.resize((TILE, TILE), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.text((12, 10), "sewing order   (red dashed: untrimmed jump, grey: trimmed)",
           fill=(60, 60, 60), font=font)
    return im


DENSITY_STOPS = [(0.0, (255, 255, 255)), (0.6, (205, 235, 200)), (1.5, (120, 200, 110)),
                 (2.5, (245, 215, 70)), (3.5, (235, 120, 40)), (4.5, (200, 20, 20))]


def _cmap(g):
    xs = [s for s, _ in DENSITY_STOPS]
    cols = np.array([c for _, c in DENSITY_STOPS], float)
    out = np.stack([np.interp(g, xs, cols[:, i]) for i in range(3)], -1)
    return out.astype(np.uint8)


def _density(plan, density, font):
    g, (gx0, gy0), cell = density
    T = TILE
    f, s = _xf(plan.bounds, T, 40)
    img = Image.fromarray(_cmap(g[::-1]))       # row 0 = top (max y)
    ny, nx = g.shape
    tl = f(np.array([[gx0, gy0 + ny * cell]]))[0]
    br = f(np.array([[gx0 + nx * cell, gy0]]))[0]
    w, h = int(round(br[0] - tl[0])), int(round(br[1] - tl[1]))
    im = Image.new("RGB", (T, T), (255, 255, 255))
    im.paste(img.resize((max(1, w), max(1, h)), Image.BILINEAR), (int(round(tl[0])), int(round(tl[1]))))
    d = ImageDraw.Draw(im)
    d.text((12, 10), f"density   max {g.max():.1f} thread layers", fill=(60, 60, 60), font=font)
    x = 12
    for v, c in DENSITY_STOPS[1:]:
        d.rectangle([x, T - 30, x + 22, T - 12], fill=c, outline=(120, 120, 120))
        d.text((x + 28, T - 30), f"{v:g}", fill=(60, 60, 60), font=font)
        x += 70
    return im


def densest(plan, density):
    """(x, y) of the densest cell: where a detail view is most worth having."""
    g, (gx0, gy0), cell = density
    iy, ix = np.unravel_index(int(np.argmax(g)), g.shape)
    return gx0 + (ix + 0.5) * cell, gy0 + (iy + 0.5) * cell


def render_sheet(plan, density, path, title, info_lines, hoop_wh, block_stitches=None,
                 detail=None):
    font = ImageFont.load_default(size=15)
    small = ImageFont.load_default(size=14)
    det, box = _detail(plan, detail or densest(plan, density), font)
    tiles = [_sewn(plan, hoop_wh, font, box), det, _path(plan, font), _density(plan, density, font)]
    n_col = len(plan.colors)
    band = 60 + max(22 * n_col, 18 * min(len(info_lines), 40)) + 20
    sheet = Image.new("RGB", (TILE * 4 + 50, TILE + 70 + band), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    d.text((14, 12), title, fill=(20, 20, 20), font=ImageFont.load_default(size=19))
    for i, t in enumerate(tiles):
        sheet.paste(t, (10 + i * (TILE + 10), 50))
        d.rectangle([10 + i * (TILE + 10), 50, 10 + i * (TILE + 10) + TILE - 1, 50 + TILE - 1],
                    outline=(200, 200, 200))
    y0 = TILE + 70
    d.text((14, y0), "threads (sewing order)", fill=(20, 20, 20), font=font)
    for i, c in enumerate(plan.colors):
        y = y0 + 26 + 22 * i
        d.rectangle([14, y, 34, y + 16], fill=rgb(c), outline=(90, 90, 90))
        st = f"  {block_stitches[i]:,} st" if block_stitches else ""
        d.text((42, y), f"{i + 1}. {c}{st}  {thread_label(c)}", fill=(40, 40, 40), font=small)
    x0 = 640
    for j, line in enumerate(info_lines[:40]):
        warn = line.startswith("WARNING") or " FAIL " in line
        d.text((x0, y0 + 18 * j), line[:200], fill=(180, 60, 20) if warn else (50, 50, 50), font=small)
    sheet.save(path)
    return path
