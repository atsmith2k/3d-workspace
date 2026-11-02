"""Acceptance checks for embroidery designs, run on the final stitch plan (whichever
engine made it) and on the design's shapes:

    def checks(p):
        return [size(w=p.width, tol=2), hoop(), stitches(max=15000), colors(3),
                max_density(3.5), long_stitches(7.0), min_feature(1.0), trims(max=10)]

Each check sees a context with `plan` (StitchPlan), `design`, `params`, `hoop`
(name, (w, h)) and `density` (thread layers grid). Same Check/custom as cadkit.checks.
"""
import numpy as np

from ..checks import Check, _range, check_results, custom, format_check, run_checks
from . import shapes as S
from .design import HOOPS

__all__ = ["size", "hoop", "stitches", "colors", "max_density", "long_stitches",
           "short_stitches", "min_feature", "trims", "jump_threads", "coverage", "custom",
           "check_results", "format_check", "run_checks", "density_grid", "thin_features",
           "coverage_gaps"]

THREAD_W = 0.3      # mm, 40 wt polyester lying flat
CELL = 1.0          # density grid cell, mm


def density_grid(plan, cell=CELL, thread_w=THREAD_W):
    """Thread layers per cell (sewn thread area / cell area), box-smoothed over 3x3
    cells: a normal fill reads ~0.8-1.0, satin ~1.5-1.8, >3.5 is bulletproof.
    Returns (grid[y, x], (x0, y0), cell)."""
    _, a, b = plan.segments()
    if not len(a):
        return np.zeros((1, 1)), (0.0, 0.0), cell
    L = np.linalg.norm(b - a, axis=1)
    n = np.maximum(1, np.ceil(L / 0.1).astype(int))
    idx = np.repeat(np.arange(len(a)), n)
    t = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n) + 0.5) / np.repeat(n, n)
    pts = a[idx] + (b - a)[idx] * t[:, None]
    w = (L / n)[idx] * thread_w
    x0, y0 = pts.min(0) - 2 * cell
    x1, y1 = pts.max(0) + 2 * cell
    nx, ny = int((x1 - x0) / cell) + 1, int((y1 - y0) / cell) + 1
    ix = ((pts[:, 0] - x0) / cell).astype(int)
    iy = ((pts[:, 1] - y0) / cell).astype(int)
    g = np.zeros((ny, nx))
    np.add.at(g, (iy, ix), w)
    g /= cell * cell
    p = np.pad(g, 1)
    sm = sum(p[1 + dy:1 + dy + ny, 1 + dx:1 + dx + nx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9
    return sm, (x0, y0), cell


def thin_features(design, mm=1.0):
    """[(element name, area mm2, (x, y))]: the largest piece of each fill narrower than
    `mm` (pointed tips only lose a sliver each), and satins
    narrower than `mm`: they sew as a mess of tiny stitches or vanish."""
    out = []
    for el in design.elements:
        if el.kind == "fill":
            kept = el.geom.buffer(-mm / 2).buffer(mm / 2 + 0.01)
            pieces = S.polygons_of(el.geom.difference(kept))
            if pieces:
                big = max(pieces, key=lambda g: g.area)    # sharp tips lose a little each;
                if big.area > 0.5:                         # a sliver is one long piece
                    c = big.representative_point()
                    out.append((el.name, big.area, (c.x, c.y)))
        elif el.kind == "satin" and (el.params["width_body"] < mm if el.params.get("taper")
                                     else el.params["width_min"] < mm):
            left, right = el.geom
            i = int(np.argmin(np.linalg.norm(left - right, axis=1)))
            out.append((el.name, 0.0, tuple((left[i] + right[i]) / 2)))
    return out


def size(w=None, h=None, tol=1.0):
    """Stitched size: a number (+-tol mm) or a (lo, hi) range."""
    def fn(c):
        sw, sh = c.plan.size
        bad, got = [], []
        for k, spec, v in (("w", w, sw), ("h", h, sh)):
            if spec is None:
                continue
            lo, hi = _range(spec, tol)
            got.append(f"{k}={v:.1f}")
            if not lo <= v <= hi:
                bad.append(f"{k}={v:.1f} not in {lo:.1f}..{hi:.1f}")
        return not bad, ", ".join(bad) if bad else " ".join(got)
    return Check("size", fn)


def hoop(name=None, margin=0.0):
    """Fits the hoop's sewing field (the design's HOOP unless named)."""
    def fn(c):
        hn = name or c.hoop[0]
        W, H = HOOPS[hn] if isinstance(hn, str) else hn
        sw, sh = c.plan.size
        ok = sw + 2 * margin <= W and sh + 2 * margin <= H
        return ok, f"{sw:.1f} x {sh:.1f} mm in {hn} ({W} x {H})"
    return Check("hoop", fn)


def stitches(max=None, min=None):
    def fn(c):
        n = c.plan.penetrations
        ok = (max is None or n <= max) and (min is None or n >= min)
        return ok, f"{n} stitches" + (f" (max {max})" if max else "")
    return Check("stitches", fn)


def colors(n):
    """Number of colour blocks: exact, or a (lo, hi) range."""
    def fn(c):
        k = len(c.plan.colors)
        lo, hi = (n, n) if not isinstance(n, (tuple, list)) else n
        return lo <= k <= hi, f"{k} colour blocks"
    return Check("colors", fn)


def max_density(layers=3.5):
    def fn(c):
        g = c.density[0]
        return g.max() <= layers, f"max {g.max():.2f} thread layers (limit {layers})"
    return Check("max_density", fn)


def long_stitches(max_mm=7.0, allow=0):
    """Sewn stitches longer than max_mm snag; allow a few."""
    def fn(c):
        n = int((c.plan.stitch_lengths() > max_mm).sum())
        return n <= allow, f"{n} stitches over {max_mm} mm"
    return Check("long_stitches", fn)


def short_stitches(min_mm=0.3, max_share=0.03):
    """Very short stitches pile up and break thread."""
    def fn(c):
        L = c.plan.stitch_lengths()
        share = float((L < min_mm).mean()) if len(L) else 0.0
        return share <= max_share, f"{share:.1%} under {min_mm} mm"
    return Check("short_stitches", fn)


def min_feature(mm=1.0, max_mm2=3.0):
    """No fill area narrower than `mm`, no satin narrower than `mm`."""
    def fn(c):
        bad = [t for t in thin_features(c.design, mm) if t[1] > max_mm2 or t[1] == 0.0]
        if not bad:
            return True, f"nothing under {mm} mm"
        return False, "; ".join(f"{n} at ({x:.0f},{y:.0f})" + (f" {a:.1f} mm2" if a else " satin")
                                for n, a, (x, y) in bad[:4])
    return Check("min_feature", fn)


def trims(max=None):
    def fn(c):
        return max is None or c.plan.trims <= max, f"{c.plan.trims} trims"
    return Check("trims", fn)


def jump_threads(over_mm=3.0, max=0):
    """Untrimmed jump threads longer than over_mm (they need snipping by hand unless
    the machine trims jumps itself)."""
    def fn(c):
        n = sum(1 for _, a, b, t in c.plan.jumps if not t and np.linalg.norm(b - a) > over_mm)
        return n <= max, f"{n} untrimmed jumps over {over_mm} mm"
    return Check("jump_threads", fn)


SPREAD = 0.45       # mm a sewn row covers once the thread flattens (40 wt, tension on)
PX = 10             # coverage raster, pixels per mm
CLOSE_GAP = 1.2     # mm; gaps between elements narrower than twice this count as bare


def _area_of(el):
    """The fabric area an element is meant to cover (fills and satins; runs cover none)."""
    from shapely.geometry import Polygon
    if getattr(el, "area", None) is not None:
        return el.area
    if el.kind == "fill":
        return el.geom
    if el.kind == "satin":
        left, right = el.geom
        ring = np.vstack([left, right[::-1]])
        return Polygon(ring).buffer(0)
    return None


def _thread(draw, pts, width):
    """Draw stitches `width` px wide measured across the thread. PIL measures a line's
    width along its major axis, so a diagonal stitch drawn plainly comes out up to 30 %
    thin and diagonal fill rows would leave fake gaps between them."""
    pts = np.asarray(pts, float)
    for a, b in zip(pts[:-1], pts[1:]):
        d = b - a
        L = float(np.hypot(*d))
        k = L / max(abs(d[0]), abs(d[1]), 1e-9) if L > 0 else 1.0
        draw.line([tuple(a), tuple(b)], fill=255, width=max(1, int(np.ceil(width * k))))


def coverage_gaps(plan, design, inset=0.35, spread=SPREAD):
    """[(element name, gap mm2, (x, y))]: the largest patch of each fill or satin that no
    stitch of its colour covers (a sewn row covers `spread` mm; the outer `inset` mm is
    ignored, pull and the border take that). Bare fabric inside a shape is a break in
    a border, a hole between fill sections or rows pulled apart."""
    from PIL import Image, ImageDraw
    from scipy import ndimage
    from shapely import contains_xy
    bx0, by0, bx1, by1 = design.bounds()
    px0, py0, px1, py1 = plan.bounds
    off = np.array([(px0 + px1 - bx0 - bx1) / 2, (py0 + py1 - by0 - by1) / 2])
    W, H = int((bx1 - bx0 + 4) * PX), int((by1 - by0 + 4) * PX)
    ox, oy = bx0 - 2, by0 - 2

    def pix(p):
        p = np.asarray(p) - off
        return list(zip((p[:, 0] - ox) * PX, (H - (p[:, 1] - oy) * PX)))

    sewn, by_block = {}, {}
    for block, run in plan.runs:
        c = plan.colors[block]
        if c not in sewn:
            sewn[c] = Image.new("L", (W, H), 0)
        if block not in by_block:
            by_block[block] = Image.new("L", (W, H), 0)
        if len(run) > 1:
            _thread(ImageDraw.Draw(sewn[c]), pix(run), spread * PX)
            _thread(ImageDraw.Draw(by_block[block]), pix(run), spread * PX)
    # stitches sewn after an element hide it as well as its own thread does: per colour
    # block, everything sewn in the blocks after it (when the design's blocks line up
    # with the file's)
    blocks, cur = [], None
    for el in design.elements:
        if el.color != cur:
            blocks.append(el.color)
            cur = el.color
    block_of, b, cur = {}, -1, None
    for el in design.elements:
        if el.color != cur:
            b += 1
            cur = el.color
        block_of[el.name] = b
    later = {}
    if blocks == list(plan.colors):
        acc = np.zeros((H, W), bool)
        for blk in range(len(blocks) - 1, -1, -1):
            later[blk] = acc.copy()
            if blk in by_block:
                acc |= np.asarray(by_block[blk]) > 0
    xs = ox + (np.arange(W) + 0.5) / PX
    ys = oy + (H - np.arange(H) - 0.5) / PX
    gx, gy = np.meshgrid(xs, ys)
    from shapely.ops import unary_union
    allsewn = np.zeros((H, W), bool)
    for im in sewn.values():
        allsewn |= np.asarray(im) > 0
    areas = [(el.name, el.color, _area_of(el)) for el in design.elements]
    areas = [a for a in areas if a[2] is not None]
    # the whole design too, any thread: catches gaps *between* elements (a fill pulled
    # back from its border too far, shapes that should touch)
    # (enclosed slots that closing by CLOSE_GAP fills: that narrow a slot between shapes
    # is a mistake, and a counter that narrow fills in when sewn anyway; notches in the
    # outer silhouette are left alone)
    whole = []
    if areas:
        from shapely.geometry import Polygon
        u = unary_union([a for *_, a in areas])
        holes = unary_union([Polygon(r) for g in S.polygons_of(u) for r in g.interiors])
        slots = u.buffer(CLOSE_GAP).buffer(-CLOSE_GAP).difference(u).intersection(holes)
        if not slots.is_empty:
            whole = [("design (between elements)", None, slots.buffer(inset))]
    out = []
    for name, color, area in areas + whole:
        if color is not None and color not in sewn:
            continue
        area = area.buffer(-inset)
        if area.is_empty:
            continue
        a0, b0, a1, b1 = area.bounds
        cols = slice(max(0, int((a0 - ox) * PX)), min(W, int((a1 - ox) * PX) + 2))
        rows = slice(max(0, int(H - (b1 - oy) * PX) - 1), min(H, int(H - (b0 - oy) * PX) + 1))
        want = contains_xy(area, gx[rows, cols], gy[rows, cols])
        if color is None:
            cover = allsewn
        else:
            cover = np.asarray(sewn[color]) > 0
            if block_of.get(name) in later:
                cover = cover | later[block_of[name]]
        bare = want & ~cover[rows, cols]
        lab, n = ndimage.label(bare)
        if not n:
            continue
        # hairlines between rows (files snap to 0.1 mm, so rows can sit 0.5 mm apart)
        # close up when the thread spreads: only patches 0.3 mm thick somewhere count
        thick = ndimage.maximum(ndimage.distance_transform_edt(bare), lab, range(1, n + 1))
        bare = np.isin(lab, 1 + np.nonzero(np.asarray(thick) >= 1.5)[0])
        lab, n = ndimage.label(bare)
        if not n:
            continue
        sizes = ndimage.sum(bare, lab, range(1, n + 1))
        k = int(np.argmax(sizes))
        yy, xx = np.nonzero(lab == k + 1)
        out.append((name, float(sizes[k]) / PX ** 2,
                    (float(gx[rows, cols][yy[0], xx[0]]), float(gy[rows, cols][yy[0], xx[0]]))))
    return out


def coverage(max_mm2=1.0):
    """Every fill and satin is covered by its own thread: no bare patch over `max_mm2`
    (a gap in a border, a hole between fill sections)."""
    def fn(c):
        bad = [g for g in coverage_gaps(c.plan, c.design) if g[1] > max_mm2]
        if not bad:
            return True, f"no bare patch over {max_mm2} mm2"
        bad.sort(key=lambda g: -g[1])
        return False, "; ".join(f"{n} {a:.1f} mm2 at ({x:.0f},{y:.0f})" for n, a, (x, y) in bad[:4])
    return Check("coverage", fn)
