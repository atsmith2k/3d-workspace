"""Measure a sewn calibration card from a photo and fit a fabric profile's pull numbers.

    cad stitch calibrate photo.jpg --fabric knit --machine "Brother PE800" \\
        --stabiliser cut-away [--fabric-detail "cotton jersey 180 gsm"] [--dry-run]

One sew-out per (machine, fabric, stabiliser) replaces per-design test sews: sew
designs/calibration_card.py (it is built with pull compensation OFF, so what it shows
is the fabric's raw pull), photograph it, run this. The fitted numbers go to
cadkit/stitch/profiles/<fabric>.json via fabrics.save_calibration, with provenance
(machine, stabiliser, photo and card stitch file with their sha256s, card version,
residual, date); every later build on that fabric uses them.

How to photograph the card
  - Sew it on the real fabric with the real stabiliser, then take it out of the hoop,
    tear/cut away the excess stabiliser and let it relax a few minutes. Do not press
    or stretch it; lay it flat on a plain, contrasting-free surface (a table, not a
    patterned cloth). Light fabric and a dark thread (the card's default black).
  - Shoot from straight above (phone parallel to the card; a little tilt is fine,
    the fiducials correct it), in even daylight or two lamps, no flash glare, no hard
    shadow across the card. Wrinkles in the fabric under the card spoil it.
  - Fill most of the frame with the card (it should be at least half the picture
    width; 10+ pixels per mm, i.e. any phone at 20-30 cm). All four corner squares
    and the small marker square beside the top-left one must be in the picture and
    not touch the edge. In focus: the satin stitches should be visible.
  - Use the original file (no filters, no "portrait" blur); JPEG or PNG.

Pipeline: greyscale -> lighting flattened (background estimated from the fabric
pixels only, divided out) -> Otsu threshold -> the four fiducials are the compact
square blobs of one size, the top-left one identified by the marker beside it ->
homography from their centres to the card's nominal positions (refined twice from the
centroids in the rectified frame) -> each feature resampled at 20 px/mm -> fill
square extents along/across the rows and satin bar widths from 50 % edge crossings
of the averaged profile, thread width from the running-stitch gauges (integrated
darkness).

The reference is not the card's nominal geometry but the same pipeline run on a perfect
synthetic photo of the card's actual stitch file (output/embroidery/calibration_card/
calibration_card.pes, the file the user sews) at zero pull: Ink/Stitch rows overshoot
the drawn edge (~0.14 mm a side) and the edge finder has its own small bias, and both
cancel. Per side, with d = baseline - sewn + (thread_sewn - thread_base):

    fill extent along the rows   d = 2 * pull_fill * |cos(row angle)|
    satin bar width              d = 2 * pull_satin(width)

(the model in fabrics.displace: satin edges move inward by the per-width pull, fill row
ends move back along the row). Extents across the rows are reported (across_fill) but
not fitted.
"""
import hashlib
import importlib.util
import sys
from datetime import date
from pathlib import Path

import numpy as np
from scipy import ndimage

from . import fabrics as F

ROOT = Path(__file__).resolve().parent.parent.parent
CARD = ROOT / "designs" / "calibration_card.py"
CARD_PES = ROOT / "output" / "embroidery" / "calibration_card" / "calibration_card.pes"
OUT = ROOT / "output" / "embroidery" / "calibration"
SCALE = 20.0                 # px per mm of the rectified measurement frame
THREAD_DEFAULT = 0.45        # mm, used when the gauges cannot be read
MAX_RESIDUAL = 0.25          # mm RMS of the width residuals before a fit is refused
PULL_RANGE = (-0.3, 1.0)     # plausible pull per side, mm


class CalibrationError(RuntimeError):
    """The photo cannot be measured (no fiducials, implausible result)."""


# ------------------------------------------------------------------ card

def load_card(card_module=None):
    """The calibration card module (designs/calibration_card.py by default); a module
    object or a path."""
    if card_module is not None and not isinstance(card_module, (str, Path)):
        return card_module
    path = Path(card_module or CARD)
    spec = importlib.util.spec_from_file_location("calibration_card_layout", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ image

def _otsu(v, bins=256):
    v = v[np.isfinite(v)]
    lo, hi = float(v.min()), float(v.max())
    if hi - lo < 1e-6:
        return lo
    h, e = np.histogram(v, bins, range=(lo, hi))
    c = (e[:-1] + e[1:]) / 2
    w0 = np.cumsum(h)
    w1 = w0[-1] - w0
    m0 = np.cumsum(h * c)
    mu0 = m0 / np.maximum(w0, 1)
    mu1 = (m0[-1] - m0) / np.maximum(w1, 1)
    between = w0 * w1 * (mu0 - mu1) ** 2
    return float(c[np.argmax(between)])


def _resize(a, shape, resample):
    from PIL import Image
    return np.asarray(Image.fromarray(a.astype(np.float32), mode="F")
                      .resize((shape[1], shape[0]), resample), dtype=np.float64)


def load_grey(path):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(path)).convert("L")
    return np.asarray(im, dtype=np.float64) / 255.0


def normalise(g):
    """Divide out uneven lighting: the fabric becomes ~1.0, thread darker. The
    background is a wide Gaussian of the fabric pixels only (thread masked out by a
    first Otsu pass), estimated at low resolution."""
    from PIL import Image
    H, W = g.shape
    k = min(1.0, 600.0 / max(H, W))
    small = _resize(g, (max(8, int(H * k)), max(8, int(W * k))), Image.BOX) if k < 1 else g
    t = _otsu(small)
    fabric = (small > t).astype(float)
    sigma = 0.06 * max(small.shape)
    num = ndimage.gaussian_filter(small * fabric, sigma)
    den = ndimage.gaussian_filter(fabric, sigma)
    bg = num / np.maximum(den, 1e-3)
    bg[den < 1e-3] = np.median(small[fabric > 0]) if fabric.any() else 1.0
    if k < 1:
        bg = _resize(bg, g.shape, Image.BILINEAR)
    return np.clip(g / np.maximum(bg, 1e-3), 0, 1.5)


# ------------------------------------------------------------------ fiducials

def _blobs(mask, min_area):
    lab, n = ndimage.label(mask)
    ys, xs = np.nonzero(lab)
    lbl = lab[ys, xs]
    A = np.bincount(lbl, minlength=n + 1).astype(float)
    sx = np.bincount(lbl, xs, n + 1)
    sy = np.bincount(lbl, ys, n + 1)
    sxx = np.bincount(lbl, xs.astype(float) ** 2, n + 1)
    syy = np.bincount(lbl, ys.astype(float) ** 2, n + 1)
    sxy = np.bincount(lbl, xs.astype(float) * ys, n + 1)
    out = []
    for i in range(1, n + 1):
        a = A[i]
        if a < min_area:
            continue
        cx, cy = sx[i] / a, sy[i] / a
        cxx = sxx[i] / a - cx ** 2
        cyy = syy[i] / a - cy ** 2
        cxy = sxy[i] / a - cx * cy
        l1, l2 = np.linalg.eigvalsh([[cxx, cxy], [cxy, cyy]])[::-1]
        if l2 <= 0:
            continue
        aspect = np.sqrt(l1 / l2)
        fill = a / (12 * np.sqrt(l1 * l2))          # 1.0 for a solid square
        out.append(dict(area=a, c=np.array([cx, cy]), aspect=aspect, fill=fill))
    return out


def _quad_area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _inside(P, q):
    """q inside the convex polygon P (any winding)."""
    def cross(a, b):
        return a[0] * b[1] - a[1] * b[0]
    s = [cross(P[(i + 1) % len(P)] - P[i], q - P[i]) for i in range(len(P))]
    return all(v > 0 for v in s) or all(v < 0 for v in s)


def find_fiducials(n):
    """Image positions (x, y px) of the four fiducial centres, ordered TL, BL, BR, TR
    as on the card (counter-clockwise from the marked one). Raises CalibrationError."""
    from itertools import combinations
    mask = n < _otsu(n)
    mask = ndimage.binary_opening(mask, iterations=1)
    # blobs cut by the photo edge are not whole squares: drop everything touching it
    lab, _ = ndimage.label(mask)
    edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    mask &= ~np.isin(lab, edge[edge > 0])
    D = min(n.shape)
    squares = [b for b in _blobs(mask, (0.004 * D) ** 2)
               if b["aspect"] < 1.5 and 0.75 < b["fill"] < 1.25]
    best = None
    for f in squares:
        side = np.sqrt(f["area"])
        if side < 0.015 * D:
            continue
        marks = [m for m in squares if 0.04 < m["area"] / f["area"] < 0.4
                 and 0.9 < np.linalg.norm(m["c"] - f["c"]) / side < 2.1]
        if len(marks) != 1:
            continue
        similar = [s for s in squares if s is not f and 0.6 < s["area"] / f["area"] < 1.6]
        if len(similar) < 3:
            continue
        similar = sorted(similar, key=lambda s: -np.linalg.norm(s["c"] - f["c"]))[:8]
        for trio in combinations(similar, 3):
            P = np.array([f["c"]] + [t["c"] for t in trio])
            # order counter-clockwise in a y-up frame, starting at f
            ctr = P.mean(0)
            ang = np.degrees(np.arctan2(-(P[:, 1] - ctr[1]), P[:, 0] - ctr[0]))
            P = P[np.argsort((ang - ang[0]) % 360)]
            if not _inside(P, marks[0]["c"]):
                continue
            area = _quad_area(P)
            if best is None or area > best[0]:
                best = (area, P, side)
    if best is None:
        raise CalibrationError(
            "calibration card not found: need four solid corner squares of one size and "
            "the small marker square beside the top-left one, all inside the photo. "
            "Photograph the whole card flat from above in even light (see "
            "cadkit/stitch/calibrate.py).")
    return best[1], best[2]


# ------------------------------------------------------------------ geometry

def homography(src, dst):
    """3x3 H with dst ~ H @ src (DLT, Hartley-normalised, >= 4 points)."""
    def norm(P):
        c = P.mean(0)
        s = np.sqrt(2) / np.mean(np.linalg.norm(P - c, axis=1))
        return np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])
    src, dst = np.asarray(src, float), np.asarray(dst, float)
    Ts, Td = norm(src), norm(dst)
    s = (Ts @ np.c_[src, np.ones(len(src))].T).T
    d = (Td @ np.c_[dst, np.ones(len(dst))].T).T
    A = []
    for (x, y, _), (u, v, _) in zip(s, d):
        A.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        A.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    H = np.linalg.svd(np.asarray(A))[2][-1].reshape(3, 3)
    H = np.linalg.inv(Td) @ H @ Ts
    return H / H[2, 2]


def project(H, P):
    P = np.atleast_2d(np.asarray(P, float))
    q = (H @ np.c_[P, np.ones(len(P))].T).T
    return q[:, :2] / q[:, 2:3]


def warp(n, H, box, scale=SCALE):
    """Card region box=(x0, y0, x1, y1) mm resampled at `scale` px/mm. Returns
    (img[iy, ix], xs, ys) with xs, ys ascending mm (img row 0 at y0)."""
    x0, y0, x1, y1 = box
    xs = np.arange(x0 + 0.5 / scale, x1, 1 / scale)
    ys = np.arange(y0 + 0.5 / scale, y1, 1 / scale)
    X, Y = np.meshgrid(xs, ys)
    uv = project(H, np.c_[X.ravel(), Y.ravel()])
    img = ndimage.map_coordinates(n, [uv[:, 1], uv[:, 0]], order=1, cval=1.0)
    return img.reshape(X.shape), xs, ys


def _grow(box, m):
    return (box[0] - m, box[1] - m, box[2] + m, box[3] + m)


# ------------------------------------------------------------------ profiles

def _crossings(prof, c, centre, half, plateau_half, out_from):
    """Left/right 50 % crossings of a darkness profile, scanning outward from the
    centre: level halfway between the feature's own plateau and the fabric round it."""
    inner = np.abs(c - centre) < plateau_half
    outer = np.abs(c - centre) > out_from
    plateau = float(np.median(prof[inner]))
    low = float(np.median(prof[outer])) if outer.any() else 0.0
    if plateau - low < 0.3:
        return None
    level = 0.5 * (plateau + low)
    ic = int(np.argmin(np.abs(c - centre)))
    edges = []
    for step in (-1, 1):
        i = ic
        while 0 < i < len(prof) - 1 and prof[i] >= level:
            i += step
        j = i - step                         # last index at/above the level
        if prof[i] >= level:
            return None                      # ran off the window
        t = (level - prof[i]) / (prof[j] - prof[i] + 1e-12)
        edges.append(c[i] + t * (c[j] - c[i]))
    return edges[1] - edges[0], 0.5 * (edges[0] + edges[1])


def _darkness(n, thread_level):
    return (1.0 - n) / max(1.0 - thread_level, 0.05)


# ------------------------------------------------------------------ measure

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def card_plan(card_pes=None):
    """StitchPlan of the built card file (mm, Y up, centred) and its path. Raises
    CalibrationError when it has not been built."""
    from . import pattern as P
    path = Path(card_pes or CARD_PES)
    if not path.exists():
        raise CalibrationError(f"no card stitch file at {path}: build the card first: "
                               "cad stitch build designs/calibration_card.py")
    return P.plan_of(P.read(str(path))), path


def render_plan(plan, px_per_mm=13.0, thread=0.45, res=40, erase=(), half=52.0, fabric=232):
    """A flat, square-on synthetic photo of a stitch plan: every stitch drawn as thread
    `thread` mm wide (round ends) in a grey from its colour on light fabric, rendered
    at `res` px/mm and downsampled to `px_per_mm`. `erase` boxes (mm) are painted
    over (tests). The card spans +-`half` mm round the image centre, Y up."""
    from PIL import Image, ImageDraw
    N = int(round(2 * half * res))
    im = Image.new("L", (N, N), fabric)
    dr = ImageDraw.Draw(im)
    r = thread * res / 2

    def grey(c):
        c = c.lstrip("#")
        R, G, B = (int(c[i:i + 2], 16) for i in (0, 2, 4))
        return int(0.299 * R + 0.587 * G + 0.114 * B) // 2 + 25

    shade = [grey(c) for c in plan.colors]

    def px(p):
        return ((p[0] + half) * res, (half - p[1]) * res)

    for b, run in plan.runs:
        pts = [px(p) for p in run]
        if len(pts) > 1:
            dr.line(pts, fill=shade[b], width=int(round(thread * res)))
        for x, y in pts:
            dr.ellipse([x - r, y - r, x + r, y + r], fill=shade[b])
    for x0, y0, x1, y1 in erase:
        dr.rectangle([px((x0, y1)), px((x1, y0))], fill=fabric)
    n = int(round(2 * half * px_per_mm))
    return im.resize((n, n), Image.LANCZOS)


_BASELINE = {}


def baseline(card, card_pes=None, px_per_mm=13.0, scale=SCALE):
    """The pipeline's measurements of a perfect zero-pull photo of the card file at
    about the photo's resolution (cached per file sha and resolution)."""
    from PIL import ImageFilter
    plan, path = card_plan(card_pes)
    res = float(np.clip(round(px_per_mm), 8, 25))
    key = (_sha256(path), res, getattr(card, "__file__", id(card)))
    if key not in _BASELINE:
        im = render_plan(plan, res).filter(ImageFilter.GaussianBlur(1.0))
        _BASELINE[key] = _measure_image(np.asarray(im, dtype=np.float64) / 255.0, card, scale)
    return _BASELINE[key]


def measure(photo_path, card_module=None, card_pes=None, scale=SCALE):
    """Measure a photo of the sewn calibration card, and the same features on a
    zero-pull synthetic photo of the card's stitch file `card_pes` (default
    output/embroidery/calibration_card/calibration_card.pes: the file that was sewn)
    as each feature's `baseline`. Returns the dict fit() turns into pull numbers.
    Raises CalibrationError when the card cannot be found or read, or not built."""
    card = load_card(card_module)
    _, pes = card_plan(card_pes)               # fail early when the card is not built
    m = _measure_image(load_grey(photo_path), card, scale)
    base = baseline(card, pes, m["photo_px_per_mm"], scale)
    for kind in ("fills", "satins"):
        ref = {(f["name"], f["axis"]): f["measured"] for f in base[kind]}
        for f in m[kind]:
            f["baseline"] = ref[(f["name"], f["axis"])]
    photo = Path(photo_path)
    m.update(photo=photo.name, photo_sha256=_sha256(photo), card_pes=str(pes),
             card_pes_sha256=_sha256(pes), baseline_thread_mm=base["thread_mm"])
    return m


def _measure_image(g, card, scale=SCALE):
    """measure() on a greyscale image (0..1) against the card's LAYOUT."""
    L = card.LAYOUT
    n = normalise(g)
    img_pts, side_px = find_fiducials(n)
    fids = [L[k] for k in ("fid_tl", "fid_bl", "fid_br", "fid_tr")]
    nominal = np.array([f["center"] for f in fids], float)

    H = homography(nominal, img_pts)
    thread_level = 0.2
    sizes = []
    for it in range(3):
        # thread level from the fiducial interiors, then refine their centres
        lv = [np.median(warp(n, H, _grow(f["bbox"], -f["size"] * 0.25), scale)[0]) for f in fids]
        thread_level = float(np.median(lv))
        found, sizes = [], []
        for f in fids:
            box = _grow(f["bbox"], 1.5)
            im, xs, ys = warp(n, H, box, scale)
            w = np.clip(_darkness(im, thread_level), 0, 1)
            w[w < 0.15] = 0
            tot = w.sum()
            if tot <= 0:
                raise CalibrationError("a fiducial square is blank in the rectified photo")
            X, Y = np.meshgrid(xs, ys)
            found.append([(w * X).sum() / tot, (w * Y).sum() / tot])
            sizes.append(float(np.sqrt(tot) / scale))
        H = homography(nominal, project(H, np.array(found)))
    # pull shrinks a square by at most ~0.7 mm and the thread adds ~0.45
    if any(abs(s - fids[0]["size"]) > 1.0 for s in sizes):
        raise CalibrationError(f"fiducial squares measure {', '.join(f'{s:.1f}' for s in sizes)} mm "
                               f"(card has {fids[0]['size']:g} mm): the photo is too distorted, "
                               "or this is not the calibration card")
    mpx = float(np.mean(np.linalg.norm(np.diff(np.r_[img_pts, img_pts[:1]], axis=0), axis=1))
                / np.mean(np.linalg.norm(np.diff(np.r_[nominal, nominal[:1]], axis=0), axis=1)))

    def dark(box):
        im, xs, ys = warp(n, H, box, scale)
        return _darkness(im, thread_level), xs, ys

    warnings = []
    if mpx < 8:
        warnings.append(f"photo resolution only {mpx:.1f} px/mm on the card; 10+ recommended")

    # thread gauges: integrated darkness across a running stitch = thread width
    gauges = {}
    for k, f in L.items():
        if f["kind"] != "gauge":
            continue
        cx, cy = f["center"]
        h = 0.3 * f["length"]
        box = (cx - h, cy - 1.2, cx + h, cy + 1.2) if f["axis"] == "x" else (cx - 1.2, cy - h, cx + 1.2, cy + h)
        d, xs, ys = dark(box)
        prof, c, c0 = (d.mean(1), ys, cy) if f["axis"] == "x" else (d.mean(0), xs, cx)
        low = np.median(prof[np.abs(c - c0) > 0.8])
        gauges[k] = float(np.sum((prof - low)[np.abs(c - c0) <= 0.8]) / scale)
    thread = float(np.median(list(gauges.values()))) if gauges else np.nan
    if not (0.2 <= thread <= 0.9):
        warnings.append(f"thread gauge read {thread:.2f} mm; using {THREAD_DEFAULT} mm")
        thread = THREAD_DEFAULT

    fills, satins = [], []
    for k, f in L.items():
        if f["kind"] == "fill":
            s = f["size"]
            cx, cy = f["center"]
            a = np.radians(f["angle"])
            for axis, c_along in (("x", abs(np.cos(a))), ("y", abs(np.sin(a)))):
                if axis == "x":      # extent in x over a band of rows in the middle
                    box = (cx - s / 2 - 2, cy - 0.25 * s, cx + s / 2 + 2, cy + 0.25 * s)
                    d, xs, ys = dark(box)
                    prof, c, c0 = d.mean(0), xs, cx
                else:
                    box = (cx - 0.25 * s, cy - s / 2 - 2, cx + 0.25 * s, cy + s / 2 + 2)
                    d, xs, ys = dark(box)
                    prof, c, c0 = d.mean(1), ys, cy
                r = _crossings(prof, c, c0, s / 2, 0.3 * s, s / 2 + 1.0)
                if r is None:
                    raise CalibrationError(f"cannot read the edges of {k} ({axis})")
                fills.append(dict(name=k, angle=f["angle"], axis=axis, along=round(c_along, 6),
                                  nominal=s, spacing=f.get("spacing", 0.4), measured=r[0],
                                  offset=r[1] - c0))
        elif f["kind"] == "satin":
            w = f["width"]
            cx, cy = f["center"]
            h = 0.3 * f["length"]
            m = w / 2 + 1.8
            if f["axis"] == "x":
                d, xs, ys = dark((cx - h, cy - m, cx + h, cy + m))
                prof, c, c0 = d.mean(1), ys, cy
            else:
                d, xs, ys = dark((cx - m, cy - h, cx + m, cy + h))
                prof, c, c0 = d.mean(0), xs, cx
            r = _crossings(prof, c, c0, w / 2, max(0.25 * w, 0.1), w / 2 + 1.0)
            if r is None:
                raise CalibrationError(f"cannot read the edges of {k}")
            satins.append(dict(name=k, width=w, axis=f["axis"], measured=r[0], offset=r[1] - c0))

    off = max(abs(x["offset"]) for x in fills + satins)
    if off > 0.5:
        warnings.append(f"a feature sits {off:.2f} mm off its nominal place: check the "
                        "rectified image (fabric stretched, or the photo bent)")
    return dict(
        card_version=getattr(card, "CARD_VERSION", None),
        photo_px_per_mm=round(mpx, 2),
        thread_mm=thread, gauges=gauges, thread_level=thread_level,
        fiducials_px=img_pts.tolist(), fiducial_mm=sizes, homography=H.tolist(),
        fills=fills, satins=satins, warnings=warnings,
    )


# ------------------------------------------------------------------ fit

def fit(m):
    """Pull numbers from measure()'s output: least squares for pull_fill over the
    along-row extents, one pull per satin width (mean of horizontal and vertical
    bars). Raises CalibrationError when the result is implausible."""
    T = m["thread_mm"]
    dT = T - m["baseline_thread_mm"]          # sewn thread vs the rendered one
    along = [f for f in m["fills"] if f["along"] > 0.3]
    across = [f for f in m["fills"] if f["along"] < 0.3]
    if not along or not m["satins"]:
        raise CalibrationError("no fill or satin measurements to fit")
    c = np.array([f["along"] for f in along])
    y = np.array([f["baseline"] + dT - f["measured"] for f in along])     # = 2 c p
    pull_fill = float((c @ y) / (2 * c @ c))
    resid = list(y - 2 * c * pull_fill)
    # across the rows: shrink per side (negative: the fabric pushes out that way)
    across_pull = [(f["baseline"] + dT - f["measured"]) / 2 for f in across]

    by_w = {}
    for s in m["satins"]:
        by_w.setdefault(s["width"], []).append((s["baseline"] + dT - s["measured"]) / 2)
    pull_satin = []
    for w in sorted(by_w):
        ps = by_w[w]
        p = float(np.mean(ps))
        pull_satin.append((w, round(p, 3)))
        resid += [2 * (p - q) for q in ps]                 # width residuals, mm
    resid = np.array(resid)
    out = dict(pull_fill=round(pull_fill, 3), pull_satin=pull_satin,
               residual_mm=round(float(np.sqrt(np.mean(resid ** 2))), 3),
               n=len(along) + len(m["satins"]),
               across_fill=round(float(np.mean(across_pull)), 3) if across_pull else None,
               thread_mm=round(T, 3))
    bad = [f"pull_fill {pull_fill:.2f}"] if not PULL_RANGE[0] <= pull_fill <= PULL_RANGE[1] else []
    bad += [f"satin {w:g} mm pull {p:.2f}" for w, p in pull_satin
            if not PULL_RANGE[0] <= p <= PULL_RANGE[1]]
    if bad:
        raise CalibrationError(f"implausible pull ({'; '.join(bad)}; expected "
                               f"{PULL_RANGE[0]}..{PULL_RANGE[1]} mm): wrong card, or a bad photo")
    if out["residual_mm"] > MAX_RESIDUAL:
        raise CalibrationError(f"measurements disagree by {out['residual_mm']:.2f} mm RMS "
                               f"(limit {MAX_RESIDUAL}): the card was stretched or wrinkled, "
                               "or the photo is not square-on; re-shoot it flat")
    return out


# ------------------------------------------------------------------ debug sheet

def save_rectified(photo_path, m, path, card_module=None, scale=10.0):
    """The card rectified to `scale` px/mm with every nominal feature box drawn in
    blue: a quick look that the fiducials were found and the features line up."""
    from PIL import Image, ImageDraw
    card = load_card(card_module)
    n = normalise(load_grey(photo_path))
    H = np.array(m["homography"])
    im, xs, ys = warp(n, H, (-50, -50, 50, 50), scale)
    rgb = Image.fromarray((np.clip(im[::-1], 0, 1) * 255).astype(np.uint8)).convert("RGB")
    dr = ImageDraw.Draw(rgb)
    for f in card.LAYOUT.values():
        x0, y0, x1, y1 = f["bbox"]
        dr.rectangle([(x0 + 50) * scale, (50 - y1) * scale, (x1 + 50) * scale, (50 - y0) * scale],
                     outline=(40, 110, 230))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    rgb.save(path)
    return path


# ------------------------------------------------------------------ CLI

def add_arguments(p):
    p.add_argument("photo", help="photo of the sewn designs/calibration_card.py (JPEG/PNG)")
    p.add_argument("--fabric", required=True, choices=F.names(), help="profile to calibrate")
    p.add_argument("--machine", required=True, help='e.g. "Brother PE800"')
    p.add_argument("--stabiliser", required=True, help="e.g. cut-away, tear-away")
    p.add_argument("--fabric-detail", default="", help='e.g. "cotton jersey 180 gsm"')
    p.add_argument("--card", help="calibration card module (default designs/calibration_card.py)")
    p.add_argument("--card-pes", help="the card stitch file that was sewn (default "
                   "output/embroidery/calibration_card/calibration_card.pes)")
    p.add_argument("--dry-run", action="store_true", help="measure and report, do not save")
    p.add_argument("--out", help=f"where the rectified check image goes (default {OUT.relative_to(ROOT)})")
    return p


def cmd_calibrate(args):
    photo = Path(args.photo)
    if not photo.exists():
        print(f"no such photo: {photo}", file=sys.stderr)
        return 1
    try:
        m = measure(photo, args.card, getattr(args, "card_pes", None))
        r = fit(m)
    except CalibrationError as e:
        print(f"calibration refused: {e}", file=sys.stderr)
        return 1
    old = F.profile(args.fabric)
    print(f"card v{m['card_version']}  photo {m['photo']}  {m['photo_px_per_mm']} px/mm  "
          f"thread {r['thread_mm']:.2f} mm")
    print(f"card file  {m['card_pes']}  sha256 {m['card_pes_sha256']}")
    for f in m["fills"]:
        print(f"  {f['name']:<10} {f['axis']}  {f['measured']:6.2f} mm (nominal {f['nominal']:g}, zero-pull {f['baseline']:.2f}, "
              f"{'along' if f['along'] > 0.3 else 'across'} rows)")
    for s in m["satins"]:
        print(f"  {s['name']:<10} {s['measured']:6.2f} mm (nominal {s['width']:g}, zero-pull {s['baseline']:.2f})")
    print(f"pull_fill  {r['pull_fill']:.3f} mm   (was {old['pull_fill']:.2f}); "
          f"across the rows {r['across_fill']} mm per side")
    print("pull_satin " + ", ".join(f"{w:g} mm: {p:.3f}" for w, p in r["pull_satin"]))
    print(f"residual   {r['residual_mm']:.3f} mm RMS over {r['n']} measurements")
    for w in m["warnings"]:
        print(f"WARNING {w}")
    out = Path(args.out) if args.out else OUT
    check = save_rectified(photo, m, out / f"{photo.stem}_rectified.png", args.card)
    print(f"check      {check}  (blue boxes should frame every feature)")
    if args.dry_run:
        print("dry run: profile not saved")
        return 0
    path = F.save_calibration(args.fabric, dict(
        pull_fill=r["pull_fill"], pull_satin=[list(wp) for wp in r["pull_satin"]],
        across_fill=r["across_fill"], thread_mm=r["thread_mm"],
        machine=args.machine, stabiliser=args.stabiliser, fabric_detail=args.fabric_detail,
        photo=m["photo"], photo_sha256=m["photo_sha256"], card_version=m["card_version"],
        card_pes=Path(m["card_pes"]).name, card_pes_sha256=m["card_pes_sha256"],
        residual_mm=r["residual_mm"], n=r["n"], date=date.today().isoformat(),
        measurements=dict(fills=[{k: (round(v, 3) if isinstance(v, float) else v) for k, v in f.items()}
                                 for f in m["fills"]],
                          satins=[{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}
                                  for s in m["satins"]]),
    ))
    print(f"saved      {path}")
    return 0
