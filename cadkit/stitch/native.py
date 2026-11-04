"""Built-in stitch engine: turns a Design into a pyembroidery EmbPattern without
Ink/Stitch. Tatami fill with underlay and edge-walk travel, satin columns with
centre-walk / contour / zigzag underlay, running and bean stitch, lock stitches and
trims. Ink/Stitch (`--engine inkstitch`, the default when it is installed) routes
fills more cleverly; this engine keeps the harness working anywhere and is the
reference the tests run on.

Everything here is mm with Y up; the pattern is written in 0.1 mm units, Y down.
"""
import numpy as np
import shapely
from pyembroidery import COLOR_CHANGE, END, JUMP, STITCH, TRIM, EmbPattern, EmbThread
from shapely import affinity
from shapely.geometry import LineString, Point
from shapely.ops import substring

from . import shapes as S
from .fabrics import stretch
from .svg import satin_underlay
from .threads import nearest_brother

LOCK = 0.4          # lock stitch length mm
TRIM_OVER = 3.0     # jumps longer than this get a trim
TRAVEL_STITCH = 2.5
SHORT_INSET = 0.3   # share of the column a satin short stitch stops short by


# ---------- running stitch ----------

def resample(path, length):
    """Points along a path no further apart than `length`; corners kept."""
    path = np.asarray(path, float)
    out = [path[0]]
    for a, b in zip(path[:-1], path[1:]):
        d = np.linalg.norm(b - a)
        if d < 1e-6:
            continue
        n = max(1, int(np.ceil(d / length - 1e-9)))
        out += [a + (b - a) * (i / n) for i in range(1, n + 1)]
    return np.asarray(out)


def even(path, length):
    """Points evenly spaced along a path, about `length` apart, first and last kept;
    vertices in between are not (a buffered outline has many 0.03 mm apart, and each
    would become a stitch)."""
    path = np.asarray(path, float)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    if L[-1] < 1e-6:
        return path[:1]
    n = max(1, int(np.ceil(L[-1] / length - 1e-9)))
    t = np.linspace(0, L[-1], n + 1)
    return np.c_[np.interp(t, L, path[:, 0]), np.interp(t, L, path[:, 1])]


def running(path, length=2.5, repeats=1, bean=0):
    pts = resample(path, length)
    out = [pts]
    for r in range(1, max(1, int(repeats))):
        out.append((pts[::-1] if r % 2 else pts)[1:])
    pts = np.vstack(out)
    if bean:
        b = [pts[0]]
        for a, c in zip(pts[:-1], pts[1:]):
            b += [c, a] * int(bean) + [c]
        pts = np.asarray(b)
    return pts


# ---------- fill ----------

def _row_segments(poly, spacing, angle):
    """Scan rows across the polygon rotated so rows run along X: list of
    (row_index, y, [(xa, xb), ...]) in rotated coordinates."""
    rp = affinity.rotate(poly, -angle, origin=(0, 0))
    x0, y0, x1, y1 = rp.bounds
    ys = np.arange(y0 + spacing / 2, y1, spacing)
    lines = [LineString([(x0 - 1, y), (x1 + 1, y)]) for y in ys]
    hits = shapely.intersection(rp, lines)
    rows = []
    for k, (y, h) in enumerate(zip(ys, hits)):
        segs = []
        for g in getattr(h, "geoms", [h]):
            if g.is_empty or g.geom_type != "LineString":
                continue
            xs = [c[0] for c in g.coords]
            if max(xs) - min(xs) > 0.25:
                segs.append((min(xs), max(xs)))
        rows.append((k, y, sorted(segs)))
    return rows


def _strips(rows):
    """Group row segments into strips that can be sewn back and forth without leaving
    the shape: a segment continues a strip when it is the only overlap both ways."""
    strips, prev = [], []           # prev: [(strip, xa, xb)]
    for k, y, segs in rows:
        cur = []
        for xa, xb in segs:
            over = [i for i, (_, pa, pb) in enumerate(prev) if pa < xb and xa < pb]
            target = None
            if len(over) == 1:
                _, pa, pb = prev[over[0]]
                back = [s for s in segs if s[0] < pb and pa < s[1]]
                if len(back) == 1:
                    target = prev[over[0]][0]
            if target is None:
                target = []
                strips.append(target)
            target.append((k, y, xa, xb))
            cur.append((target, xa, xb))
        prev = cur
    return strips


def _strip_points(strip, stitch, staggers, angle):
    pts = []
    for j, (k, y, xa, xb) in enumerate(strip):
        off = (k % max(1, staggers)) / max(1, staggers) * stitch
        grid = np.arange(np.ceil((xa - off) / stitch), np.floor((xb - off) / stitch) + 1) * stitch + off
        grid = grid[(grid > xa + 0.3 * stitch) & (grid < xb - 0.3 * stitch)]
        xs = np.r_[xa, grid, xb]
        if j % 2:
            xs = xs[::-1]
        pts += [(x, y) for x in xs]
    a = np.radians(angle)
    c, s = np.cos(a), np.sin(a)
    p = resample(np.asarray(pts), stitch)      # splits long row-to-row connectors
    return np.c_[p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c]


def _travel(shape, a, b):
    """Stitches from a to b: straight when short, else along the nearest edge of the
    shape (shrunk a little, so it gets covered), else None (jump)."""
    d = np.linalg.norm(b - a)
    if d < 1.2:
        return np.array([b])
    inner = shape.buffer(-0.3)
    if LineString([a, b]).within(shape.buffer(0.05)):
        return resample(np.array([a, b]), TRAVEL_STITCH)[1:]
    best = None
    inner = inner.simplify(0.05)
    for poly in S.polygons_of(inner):
        for ring in [poly.exterior, *poly.interiors]:
            line = LineString(ring.coords)
            if line.distance(Point(a)) > 1.0 or line.distance(Point(b)) > 1.0:
                continue
            ta, tb, L = line.project(Point(a)), line.project(Point(b)), line.length
            fwd = (tb - ta) % L
            if fwd <= L / 2:
                seg = _ring_part(line, ta, ta + fwd)
            else:
                seg = _ring_part(line, tb, tb + (L - fwd))[::-1]
            if best is None or len(seg) < len(best):
                best = seg
    if best is None:
        return None
    return even(np.vstack([a, best, b]), TRAVEL_STITCH)[1:]


def _ring_part(line, t0, t1):
    L = line.length
    if t1 <= L:
        return np.asarray(substring(line, t0, t1).coords)
    return np.vstack([np.asarray(substring(line, t0, L).coords),
                      np.asarray(substring(line, 0, t1 - L).coords)])


def _fill_pass(shape, spacing, stitch, staggers, angle, start):
    """One fill pass (underlay or top): strips ordered nearest-first, joined by edge
    travel where possible. Returns a list of point runs (a new run = jump needed)."""
    runs, cur = [], None
    for poly in S.polygons_of(shape):
        strips = [_strip_points(s, stitch, staggers, angle)
                  for s in _strips(_row_segments(poly, spacing, angle))]
        strips = [s for s in strips if len(s) >= 2]
        pos = start if cur is None else cur[-1]
        while strips:
            if pos is None:
                i, rev = 0, False
            else:
                d = [(min(np.linalg.norm(s[0] - pos), np.linalg.norm(s[-1] - pos)), i)
                     for i, s in enumerate(strips)]
                i = min(d)[1]
                rev = np.linalg.norm(strips[i][-1] - pos) < np.linalg.norm(strips[i][0] - pos)
            s = strips.pop(i)
            s = s[::-1] if rev else s
            if cur is not None:
                t = _travel(poly, cur[-1], s[0])
                if t is not None:
                    cur = np.vstack([cur, t, s[1:]])
                    pos = cur[-1]
                    continue
                runs.append(cur)
            cur = s
            pos = cur[-1]
    if cur is not None:
        runs.append(cur)
    return runs


def fill(shape, p, start=None):
    runs = []
    if p["underlay"]:
        u = shape.buffer(-p["underlay_inset"])
        if not u.is_empty:
            runs += _fill_pass(u, p["underlay_spacing"], 3.0, 1, p["angle"] + 90, start)
    start = runs[-1][-1] if runs else start
    top = stretch(shape, p["angle"], p.get("pull") or 0.0)   # pull compensation along the rows
    return _join(runs + _fill_pass(top, p["spacing"], p["stitch"], p["staggers"], p["angle"], start),
                 shape)


def _join(runs, shape):
    """Merge consecutive runs whose gap is short or travels inside the shape."""
    out = []
    for r in runs:
        if out:
            t = _travel(shape, out[-1][-1], r[0])
            if t is not None:
                out[-1] = np.vstack([out[-1], t, r[1:]])
                continue
        out.append(r)
    return out


# ---------- satin ----------

def _param(rail_l, rail_r):
    mid = (rail_l + rail_r) / 2
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(mid, axis=0), axis=1))]
    return mid, s


def _at(rail, s, t):
    return np.c_[np.interp(t, s, rail[:, 0]), np.interp(t, s, rail[:, 1])]


def satin(left, right, p):
    mid, s = _param(left, right)
    L = s[-1]
    across = right - left
    w = np.linalg.norm(across, axis=1, keepdims=True) + 1e-9
    u = across / w
    passes = []
    kinds = satin_underlay(p["width"], p["underlay"])
    if "center" in kinds:
        c = resample(mid, 2.0)
        passes.append(np.vstack([c, c[::-1][1:]]))
    if "contour" in kinds:
        inset = np.minimum(w * 0.2, 0.6)
        passes.append(np.vstack([resample(left + u * inset, 2.0),
                                 resample((right - u * inset)[::-1], 2.0)]))
    if "zigzag" in kinds:
        t = np.arange(0, L, 3.0 / 2)
        inset = np.minimum(w * 0.25, 1.0)
        zl = _at(left + u * inset, s, t)
        zr = _at(right - u * inset, s, t)
        passes.append(np.array([zl[i] if i % 2 == 0 else zr[i] for i in range(len(t))]))
    end_at_start = "zigzag" in kinds
    pull = p["pull"]
    sp = p["spacing"]
    t = np.arange(0, L + 1e-9, sp / 2)
    if len(t) < 2:
        t = np.array([0, L])
    pl = _at(left - u * pull, s, t)
    pr = _at(right + u * pull, s, t)
    # short stitches: where one rail is compressed (the inside of a curve or a fan
    # corner) every other stitch stops short of it, so the ends don't pile into one hole
    for a, b in ((pl, pr), (pr, pl)):
        gap = np.r_[np.inf, np.linalg.norm(np.diff(a[::2], axis=0), axis=1)]
        tight = np.repeat(gap < 0.25 * sp * 2, 2)[:len(t)]
        short = tight & (np.arange(len(t)) % 4 < 2)
        a[short] += (b[short] - a[short]) * SHORT_INSET
    zz = np.array([pl[i] if i % 2 == 0 else pr[i] for i in range(len(t))])
    passes.append(zz[::-1] if end_at_start else zz)
    return [np.vstack(passes)]


# ---------- assembly ----------

def stitch_runs(el, start=None):
    if el.kind == "fill":
        return fill(el.geom, el.params, start)
    if el.kind == "satin":
        return satin(*el.geom, el.params)
    p = el.params
    return [running(el.geom, p["length"], p["repeats"], p["bean"])]


def _lock(p, q):
    """Tiny back-and-forth stitches at p, heading toward q."""
    v = q - p
    n = np.linalg.norm(v)
    if n < 1e-6:
        return [p]
    v = v / n * min(LOCK, n)
    return [p, p + v, p, p + v, p]


def build_pattern(design):
    """Design -> EmbPattern (0.1 mm units, Y down), with locks, trims and colour changes."""
    pat = EmbPattern()
    pos, color, prev_trim, run = None, None, False, None

    def put(cmd, xy):
        pat.add_stitch_absolute(cmd, float(xy[0] * 10), float(-xy[1] * 10))

    def tie_off(run):
        for q in _lock(run[-1], run[-2] if len(run) > 1 else run[-1])[1:]:
            put(STITCH, q)

    els = design.elements
    for ei, el in enumerate(els):
        runs = stitch_runs(el, pos)
        for ri, run in enumerate(runs):
            run = np.asarray(run)
            if color != el.color:
                if color is not None:
                    put(TRIM, pos)
                    pat.add_command(COLOR_CHANGE)
                name, _ = nearest_brother(el.color)
                pat.add_thread(EmbThread(el.color, description=f"{el.color} ~{name}"))
                color = el.color
                new_start = True
            else:
                gap = np.linalg.norm(run[0] - pos)
                new_start = gap > TRIM_OVER or (ri == 0 and prev_trim) or ri > 0
                if new_start:
                    put(TRIM, pos)
                elif gap > 0:
                    for q in resample(np.array([pos, run[0]]), TRAVEL_STITCH)[1:]:
                        put(STITCH, q)
            if new_start:
                put(JUMP, run[0])
                for q in _lock(run[0], run[1] if len(run) > 1 else run[0]):
                    put(STITCH, q)
            for q in run[1:] if new_start else run:
                put(STITCH, q)
            tie_needed = (ri < len(runs) - 1) or el.trim_after
            if tie_needed:
                tie_off(run)
            pos = run[-1]
        prev_trim = el.trim_after
        # tie off before a colour change too
        if ei + 1 < len(els) and els[ei + 1].color != el.color and not el.trim_after:
            tie_off(run)
    if pos is not None:
        if not (els[-1].trim_after):
            tie_off(run)
        put(TRIM, pos)
    pat.add_command(END)
    return pat
