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
           "short_stitches", "min_feature", "trims", "jump_threads", "custom",
           "check_results", "format_check", "run_checks", "density_grid", "thin_features"]

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
        elif el.kind == "satin" and el.params["width_min"] < mm:
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
