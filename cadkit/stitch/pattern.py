"""Read any stitch pattern (from either engine, or a PES/DST/JEF file the user has)
into a StitchPlan the checks and the preview work on, and write the machine files.

A StitchPlan is mm with Y up, centred on the stitch extents:
  runs   [(block, (N, 2) points)]  continuous sewn stitches; a new run follows a jump
  jumps  [(block, a, b, trimmed)]  thread carried from one run to the next
  colors ['#rrggbb', ...]          one per colour block, in sewing order
"""
from dataclasses import dataclass, field

import numpy as np
import pyembroidery as pe

from .threads import CLOSE, delta_e94, nearest_brother

FORMATS = ("pes", "dst", "jef", "exp", "vp3", "xxx")

# Brother PEC palette codes 62-64 are machine functions on some models ("Applique
# Material" and friends make the machine stop), yet pyembroidery's PEC palette lists
# 62 as Orange and maps oranges and golds onto it (inkstitch/pystitch PR 140). The PES
# v6 header carries the exact RGB anyway; the PEC index is the machine's own lookup.
RESERVED_PEC = (0, 62, 63, 64)


def _pec_palette_without_function_codes(_get=__import__("pyembroidery.PecWriter", fromlist=["x"]).get_thread_set):
    threads = _get()
    for i in RESERVED_PEC:
        if i < len(threads):
            threads[i] = None
    return threads


for _m in ("pyembroidery.PecWriter", "pyembroidery.PesWriter"):
    __import__(_m, fromlist=["x"]).get_thread_set = _pec_palette_without_function_codes


@dataclass
class StitchPlan:
    runs: list
    jumps: list
    colors: list
    penetrations: int = 0
    trims: int = 0
    names: list = field(default_factory=list)

    @property
    def points(self):
        return np.vstack([r for _, r in self.runs]) if self.runs else np.zeros((0, 2))

    @property
    def bounds(self):
        p = self.points
        return (*p.min(0), *p.max(0))

    @property
    def size(self):
        x0, y0, x1, y1 = self.bounds
        return x1 - x0, y1 - y0

    def segments(self):
        """(block, a, b) arrays of every sewn stitch."""
        blk, a, b = [], [], []
        for block, r in self.runs:
            if len(r) > 1:
                a.append(r[:-1])
                b.append(r[1:])
                blk.append(np.full(len(r) - 1, block))
        if not a:
            return np.zeros(0, int), np.zeros((0, 2)), np.zeros((0, 2))
        return np.concatenate(blk), np.vstack(a), np.vstack(b)

    def stitch_lengths(self):
        _, a, b = self.segments()
        return np.linalg.norm(b - a, axis=1)

    def thread_length_m(self):
        """Top thread estimate: sewn length + 0.4 mm take-up per penetration + jumps."""
        sewn = self.stitch_lengths().sum()
        jumps = sum(np.linalg.norm(b - a) for _, a, b, _ in self.jumps)
        return (sewn + 0.4 * self.penetrations + jumps) / 1000

    def sew_minutes(self, spm=650):
        """Rough machine time: stitches at `spm` + 8 s per trim + 30 s per colour change."""
        return self.penetrations / spm + self.trims * 8 / 60 + (len(self.colors) - 1) * 0.5


def plan_of(pattern, recenter=True):
    runs, jumps = [], []
    colors = []
    threads = list(pattern.threadlist)
    names = []

    def thread(i):
        if i < len(threads):
            t = threads[i]
            return "#%06x" % (t.color & 0xFFFFFF), (t.description or "")
        return "#808080", ""

    block, cur, last_pen, trimmed, pens, trims = 0, [], None, False, 0, 0
    c, n = thread(0)
    colors.append(c)
    names.append(n)

    def close():
        nonlocal cur
        if cur:
            runs.append((block, np.asarray(cur)))
        cur = []

    for x, y, cmd in pattern.stitches:
        cmd &= pe.COMMAND_MASK
        p = (x / 10.0, -y / 10.0)
        if cmd == pe.STITCH:
            if not cur and last_pen is not None:
                if np.hypot(p[0] - last_pen[0], p[1] - last_pen[1]) > 1e-6:
                    jumps.append((block, np.array(last_pen), np.array(p), trimmed))
            if not cur:
                trimmed = False
            cur.append(p)
            last_pen = p
            pens += 1
        elif cmd == pe.JUMP:
            close()
        elif cmd == pe.TRIM:
            close()
            if last_pen is not None and not trimmed:
                trims += 1
            trimmed = True
        elif cmd in (pe.COLOR_CHANGE, pe.COLOR_BREAK, pe.NEEDLE_SET):
            close()
            if pens == 0 and cmd != pe.COLOR_CHANGE:
                continue
            if cmd == pe.NEEDLE_SET and not runs:
                continue
            block += 1
            last_pen, trimmed = None, False
            c, n = thread(block)
            colors.append(c)
            names.append(n)
        elif cmd == pe.END:
            break
    close()
    # drop empty trailing colour blocks
    used = {b for b, _ in runs}
    keep = [i for i in range(len(colors)) if i in used]
    remap = {old: new for new, old in enumerate(keep)}
    runs = [(remap[b], r) for b, r in runs]
    jumps = [(remap[b], a, bb, t) for b, a, bb, t in jumps if b in remap]
    plan = StitchPlan(runs, jumps, [colors[i] for i in keep], pens, trims,
                      [names[i] for i in keep])
    if recenter and runs:
        x0, y0, x1, y1 = plan.bounds
        c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
        plan.runs = [(b, r - c) for b, r in plan.runs]
        plan.jumps = [(b, a - c, bb - c, t) for b, a, bb, t in plan.jumps]
    return plan


def read(path):
    pat = pe.read(str(path), READ_SETTINGS.get(str(path).rsplit(".", 1)[-1].lower()))
    if pat is None:
        raise ValueError(f"pyembroidery could not read {path}")
    return pat


def name_threads(pattern, colors=None):
    """Name every thread after the closest Brother palette colour, or by its hex when the
    palette has nothing close (a machine screen saying "Dark Gray" for navy misleads)."""
    for i, t in enumerate(pattern.threadlist):
        hexc = "#%06x" % (t.color & 0xFFFFFF)
        if colors and i < len(colors):
            t.set_color(*[int(colors[i][j:j + 2], 16) for j in (1, 3, 5)])
            hexc = colors[i]
        name, h = nearest_brother(hexc)
        close = delta_e94(hexc, h) <= CLOSE
        t.description = name if close else hexc
        t.brand = "Brother (nearest)" if close else ""
    return pattern


SHORT_JUMP = 3.0    # mm; untrimmed jumps up to this are sewn as stitches


def sew_short_jumps(pattern, max_mm=SHORT_JUMP):
    """Turn untrimmed jumps of up to `max_mm` into plain stitches, in place; returns how
    many. Engines jump between touching pieces (Ink/Stitch between elements), and the
    PES writer puts a trim on every jump, so each would cost the machine a trim (and
    leave a tail to tie in). Digitising software sews such short moves instead. Jumps
    that stay jumps are cut by the writers; tie_cuts locks both sides."""
    out, pending, last, n = [], [], None, 0
    st = pattern.stitches
    for idx, (x, y, cmd) in enumerate(st):
        c = cmd & pe.COMMAND_MASK
        if c == pe.JUMP and last is not None:
            pending.append((x, y, cmd))
            continue
        if c == pe.STITCH and pending:
            dist = ((x - last[0]) ** 2 + (y - last[1]) ** 2) ** 0.5 / 10.0
            if dist <= max_mm:
                # sew the move in stitches of at most 3 mm (the target itself follows)
                k = max(1, int(np.ceil(dist / 3.0)))
                for i in range(1, k):
                    out.append((last[0] + (x - last[0]) * i / k, last[1] + (y - last[1]) * i / k, pe.STITCH))
                n += 1
                pending = []
                last = (x, y)
                out.append((x, y, cmd))
                continue
            else:
                # a real move: the writer will trim it; tie_cuts locks both sides
                # once prepare has snapped the coordinates
                out += pending
            pending = []
        elif pending:
            out += pending
            pending = []
        if c in (pe.TRIM, pe.COLOR_CHANGE, pe.STOP, pe.END):
            last = None                     # a cut thread: the next jump must stay a jump
        elif c == pe.STITCH:
            last = (x, y)
        out.append((x, y, cmd))
    pattern.stitches = out + pending
    return n


def _covered_later(pattern, cell=2.0, counts=None):
    """(grid of the index of the last stitch that covers each `cell` (0.1 mm units) square,
    with a 1-cell margin so fill rows read as solid, eroded by one cell so only squares
    well inside later stitching count; origin). `counts(i)` picks the stitches that may
    cover (default all)."""
    from scipy.ndimage import maximum_filter, minimum_filter
    pts = np.array([(x, y) for x, y, _ in pattern.stitches], float)
    if len(pts) < 2:
        return None, None
    o = pts.min(axis=0) - 4 * cell
    shape = tuple((np.ceil((pts.max(axis=0) - o) / cell) + 8).astype(int))
    last = np.full(shape, -1, np.int64)
    prev = None
    for i, (x, y, cmd) in enumerate(pattern.stitches):
        if (cmd & pe.COMMAND_MASK) != pe.STITCH or (counts is not None and not counts(i)):
            prev = None
            continue
        if prev is not None:
            n = max(2, int(np.hypot(x - prev[0], y - prev[1]) / (cell / 2)) + 1)
            seg = (np.linspace(prev, (x, y), n) - o) / cell
            ij = seg.astype(int)
            last[ij[:, 0], ij[:, 1]] = i
        prev = (x, y)
    return minimum_filter(maximum_filter(last, size=3), size=3), (o, cell)


def _buried_route(grid, o, cell, a, b, j, reach):
    """Points from a to b (0.1 mm units) along which every square is covered by stitches
    after index j: the straight line when it is, else the shortest path through covered
    squares (no longer than 1.5 x reach), simplified. None when there is no such path."""
    from collections import deque
    from shapely.geometry import LineString

    def cells(p, q):
        k = max(2, int(np.hypot(q[0] - p[0], q[1] - p[1]) / (cell / 2)) + 1)
        return ((np.linspace(p, q, k) - o) / cell).astype(int)

    ok = grid > j
    ij = cells(a, b)
    if ok[ij[:, 0], ij[:, 1]].all():
        return [a, b]
    s, t = tuple(((np.array(a) - o) / cell).astype(int)), tuple(((np.array(b) - o) / cell).astype(int))
    pad = int(reach / cell / 2) + 2
    lo = np.maximum(np.minimum(s, t) - pad, 0)
    hi = np.minimum(np.maximum(s, t) + pad + 1, ok.shape)
    win = ok[lo[0]:hi[0], lo[1]:hi[1]].copy()
    s0, t0 = (s[0] - lo[0], s[1] - lo[1]), (t[0] - lo[0], t[1] - lo[1])
    for c in (s0, t0):                    # the ends sit on stitches: let the search start there
        win[max(c[0] - 1, 0):c[0] + 2, max(c[1] - 1, 0):c[1] + 2] = True
    prev = -np.ones(win.shape + (2,), np.int32)
    prev[s0] = s0
    q, limit = deque([s0]), 1.5 * reach / cell
    while q:
        c = q.popleft()
        if c == t0:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = c[0] + dx, c[1] + dy
            if 0 <= nx < win.shape[0] and 0 <= ny < win.shape[1] and win[nx, ny] and prev[nx, ny, 0] < 0:
                prev[nx, ny] = c
                q.append((nx, ny))
    else:
        return None
    path, c = [], t0
    while c != s0:
        path.append(c)
        c = tuple(prev[c])
    path.append(s0)
    if len(path) > limit:
        return None
    pts = [tuple((np.array(c) + lo + 0.5) * cell + o) for c in reversed(path)]
    line = LineString([a] + pts[1:-1] + [b]).simplify(cell)
    pts = list(line.coords)
    for p, r in zip(pts[:-1], pts[1:]):   # simplifying must not cut a corner over bare fabric
        ij = cells(p, r)
        if not ok[ij[:, 0], ij[:, 1]].all():
            return [a] + [tuple((np.array(c) + lo + 0.5) * cell + o) for c in reversed(path)][1:-1:3] + [b]
    return pts


def sew_hidden_jumps(pattern, max_mm=15.0):
    """Sew untrimmed same-colour jumps of up to `max_mm` as travel when the whole move
    lies under stitching sewn later (a shadow piece to the next one under the letters
    that cover it): the travel is buried, and the machine saves a trim and two locks.
    Moves over fabric that stays bare keep their jump. In place; returns how many."""
    st = pattern.stitches
    if len(st) < 2:
        return 0
    # travel may hide under its own colour, or under a darker one: a dark thread under
    # a light fill shows through
    block, b = [], 0
    for _, _, cmd in st:
        if (cmd & pe.COMMAND_MASK) == pe.COLOR_CHANGE:
            b += 1
        block.append(b)
    lum = []
    for t in range(b + 1):
        c = pattern.threadlist[t].color if t < len(pattern.threadlist) else 0
        r, g, bl = (c >> 16) & 255, (c >> 8) & 255, c & 255
        lum.append(0.2126 * r + 0.7152 * g + 0.0722 * bl)
    grids = {}

    def grid_for(k):
        if k not in grids:
            hide_under = {t for t in range(len(lum)) if t == k or (t > k and lum[t] <= lum[k] + 8)}
            grids[k] = _covered_later(pattern, counts=lambda i: block[i] in hide_under)
        return grids[k]
    out, n, last, i = [], 0, None, 0
    while i < len(st):
        x, y, cmd = st[i]
        c = cmd & pe.COMMAND_MASK
        if c == pe.JUMP and last is not None:
            j = i
            while j < len(st) and (st[j][2] & pe.COMMAND_MASK) == pe.JUMP:
                j += 1
            if j < len(st) and (st[j][2] & pe.COMMAND_MASK) == pe.STITCH:
                tx, ty = st[j][0], st[j][1]
                d = np.hypot(tx - last[0], ty - last[1])
                route = None
                if 0 < d <= max_mm * 10:
                    grid, (o, cell) = grid_for(block[i])
                    route = _buried_route(grid, o, cell, last, (tx, ty), j, max_mm * 10)
                if route is not None:
                    for (ax, ay), (bx, by) in zip(route[:-1], route[1:]):
                        m = max(1, int(np.ceil(np.hypot(bx - ax, by - ay) / 30.0)))     # 3 mm travel stitches
                        out += [(ax + (bx - ax) * q / m, ay + (by - ay) * q / m, pe.STITCH) for q in range(1, m + 1)]
                    out.pop()                       # the target stitch follows
                    n += 1
                    i = j
                    continue
            out += st[i:j]
            i = j
            continue
        if c in (pe.TRIM, pe.COLOR_CHANGE, pe.STOP, pe.END):
            last = None
        elif c == pe.STITCH:
            last = (x, y)
        out.append((x, y, cmd))
        i += 1
    pattern.stitches = out
    return n


def _lock(at, out, toward=None, mm=0.4):
    """Lock stitches at `at` (0.1 mm units): two tiny stitches out and back along the
    last stitch's direction (or toward `toward`), so a cut thread cannot pull out."""
    x, y = at
    if toward is None:
        prev = next(((px, py) for px, py, c in reversed(out or []) if (c & pe.COMMAND_MASK) == pe.STITCH
                     and (px, py) != (x, y)), None)
        toward = prev if prev is not None else (x + 1, y)
    dx, dy = toward[0] - x, toward[1] - y
    L = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / L * mm * 10, dy / L * mm * 10
    return [(x + ux, y + uy, pe.STITCH), (x, y, pe.STITCH), (x + ux, y + uy, pe.STITCH), (x, y, pe.STITCH)]


def _tie(end, nxt, mm=0.4):
    """Lock stitches for a run that ends at `end` and goes on (or comes in) from `nxt`
    (0.1 mm units), sewn 0.4-0.8 mm inside the run's first (or last) stitch: A, B, A, B
    with A and B on that stitch. The end hole gets no extra penetration, which matters
    where runs meet (a closed ring starts and ends in one hole; with a tie on both ends
    that hole took 8). Too short a stitch for that: the plain tie at the end itself."""
    dx, dy = nxt[0] - end[0], nxt[1] - end[1]
    L = (dx * dx + dy * dy) ** 0.5
    if L < 3.25 * mm * 10:
        return _lock(end, None, toward=nxt, mm=mm)
    a = (end[0] + dx / L * mm * 10, end[1] + dy / L * mm * 10, pe.STITCH)
    b = (end[0] + dx / L * mm * 20, end[1] + dy / L * mm * 20, pe.STITCH)
    return [a, b, a, b]


def _reverses(pts, end=False):
    """stitchsim's test for a tied run end (analysis.rs `locked`): within the first four
    stitches, one that turns back on the stitch before and is under 1.6 mm (the later
    of the two in sewing order). `pts` runs from the cut inward (0.1 mm units), so at a
    run's end (`end`) it is read backwards."""
    P = np.asarray(pts[:5], float)
    v = np.diff(P, axis=0)
    return any(np.hypot(*v[i if end else i + 1]) < 16 and float(v[i] @ v[i + 1]) < 0 for i in range(len(v) - 1))


def _groups(pts):
    """How many lock groups stitchsim counts at a run end (analysis.rs `lock_units`):
    a-b returns under 0.83 mm, closed triangles with sides under 1.23 mm, one stray
    stitch allowed between groups; two or more is a stacked lock. The limits sit
    between distances the 0.1 mm grid can produce, so float rounding in either reader
    cannot flip a verdict."""
    P = np.asarray(pts, float)
    d = lambda i, j: float(np.hypot(*(P[i] - P[j])))
    same = lambda i, j: d(i, j) <= 1.5
    g = i = gap = 0
    while i + 2 < len(P) and gap <= 1:
        if same(i + 2, i) and d(i, i + 1) < 8.3 and not same(i, i + 1):
            j = i + 2
            while j + 1 < len(P) and same(j + 1, j - 1):
                j += 1
            g += 2 if j - i - 1 > 5 else 1
            i, gap = j, 0
        elif (i + 3 < len(P) and same(i + 3, i)
              and all(d(i + t, i + t + 1) < 12.3 and not same(i + t, i + t + 1) for t in range(3))):
            g += 1
            i, gap = i + 3, 0
        else:
            i += 1
            gap += 1
    return g


def _tie_for(pts, end=False, used=None):
    """The lock to sew after a run's first point (`pts` from the cut inward), or None
    when stitchsim already reads the run as tied. Three tie forms: inside the first
    stitch, on the run's second point, on the end hole itself. Of those that read as
    tied and do not stack onto a lock-like turn already there (a satin's narrow end),
    the one whose holes the rest of the design uses least (`used`: penetrations per
    0.2 mm cell) wins, so two runs ending in one hole don't both tie there."""
    if _reverses(pts, end):
        return None
    snap = lambda q: [(round(x), round(y), c) for x, y, c in q]
    options = [snap(_tie(pts[0], pts[1])), snap(_lock(pts[0], None, toward=pts[1]))]
    if len(pts) > 2:
        # tie on the second point: out to it, back 0.4 mm toward the cut and over again
        options.insert(1, snap([(*pts[1], pe.STITCH)] + _lock(pts[1], None, toward=pts[0])[:3]))
    best = None
    for t in options:
        holes = [(x, y) for x, y, _ in t]
        cand = [pts[0]] + holes + list(pts[1:])
        w = min(16, max(2, (len(cand) - 1) // 2))
        if not (_reverses(cand, end) and _groups(cand[:w + 1]) <= 1):
            continue
        add = {}
        for x, y in holes:
            k = (round(x / 2), round(y / 2))
            add[k] = add.get(k, 0) + 1
        load = max((used or {}).get(k, 0) + n for k, n in add.items())   # the busiest hole after it
        if best is None or load < best[0]:
            best = (load, t)
    return best[1] if best else options[0]


def tie_cuts(pattern):
    """Make sure every run of stitches between cuts (trims, colour changes, stops, the
    jumps the writers will cut, the design's start and end) starts and ends with a lock
    stitchsim recognises, in place; returns how many locks were added. Engines tie most
    cuts themselves, but Ink/Stitch's triangle lock sometimes starts a stitch too late
    or closes a little off, which ties nothing. A run that already has one is left
    alone (a second tie on top is a stacked lock). Runs after `prepare`, on the snapped
    coordinates the files carry: a triangle lock that closes 0.14 mm off before
    rounding can close 0.16 mm off after it."""
    st = pattern.stitches
    cut = lambda c: c in (pe.TRIM, pe.COLOR_CHANGE, pe.STOP, pe.END, pe.JUMP)
    runs, cur = [], []
    for i, (x, y, cmd) in enumerate(st):
        if (cmd & pe.COMMAND_MASK) == pe.STITCH:
            cur.append(i)
        elif cut(cmd & pe.COMMAND_MASK) and cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    used = {}
    for x, y, c in st:
        if (c & pe.COMMAND_MASK) == pe.STITCH:
            k = (round(x / 2), round(y / 2))
            used[k] = used.get(k, 0) + 1
    tie_in, tie_off = {}, {}
    for r in runs:
        pts = [tuple(st[i][:2]) for i in r]
        # drop repeats of one point (a landing stitch on the jump target)
        pts = [q for j, q in enumerate(pts) if j == 0 or q != pts[j - 1]]
        if len(pts) < 2:
            continue
        t = _tie_for(pts, used=used)
        if t:
            tie_in[r[0]] = t
        t = _tie_for(pts[::-1], end=True, used=used)
        if t:
            tie_off[r[-1]] = t[::-1]
    out = []
    for i, s in enumerate(st):
        out += tie_off.get(i, [])
        out.append(s)
        out += tie_in.get(i, [])
    pattern.stitches = out
    return len(tie_in) + len(tie_off)


def prepare(pattern, label=None):
    """Spell out what every writer needs, in place; returns (trims added, duplicate
    stitches dropped). The PES/PEC writers cut every jump on their own, but DST, EXP,
    JEF, XXX, U01 keep a bare jump as a jump (the thread is dragged across, or left for
    the operator to snip) and VP3, which has no jump, sews it as one long stitch. So a
    jump that leaves sewn thread behind gets an explicit TRIM first. A stitch onto the
    point it is already at is a second penetration in one hole: dropped (machines have
    frozen on DST files full of them). `label` becomes the file name shown on the
    machine: letters and digits only (other characters have corrupted PEC headers).
    The design is centred on the origin, and coordinates snapped to whole 0.1 mm units: the VP3 writer truncates
    float deltas, so fractional points drift the design up to 0.3 mm by the end."""
    out, trims, dups = [], 0, 0
    attached, prev, last = False, None, None
    # centre the design on the origin (machines place and bounds-check a design from it;
    # an SE600 resets on a design far from it)
    sewn = [(x, y) for x, y, c in pattern.stitches if (c & pe.COMMAND_MASK) == pe.STITCH]
    cx, cy = ((min(p[0] for p in sewn) + max(p[0] for p in sewn)) / 2,
              (min(p[1] for p in sewn) + max(p[1] for p in sewn)) / 2) if sewn else (0, 0)
    for x, y, cmd in pattern.stitches:
        x, y = int(round(x - cx)), int(round(y - cy))
        c = cmd & pe.COMMAND_MASK
        if c == pe.STITCH:
            if prev == pe.STITCH and last is not None and (x, y) == last:
                dups += 1
                continue
            attached, last = True, (x, y)
        elif c == pe.JUMP:
            if attached:
                out.append((last[0], last[1], pe.TRIM))
                trims += 1
                attached = False
        elif c in (pe.TRIM, pe.COLOR_CHANGE, pe.END):
            attached = False
        out.append((x, y, cmd))
        prev = c
    pattern.stitches = out
    if label:
        clean = "".join(ch for ch in label if ch.isascii() and ch.isalnum())
        if clean:
            pattern.extras["name"] = clean[:16]
    return trims, dups


LONG_MAX = 12.1     # mm; the longest stitch a DST (ternary) machine moves in one step


def _zero_stitches(pat):
    """Consecutive stitch commands onto the same point."""
    n, prev = 0, None
    for x, y, cmd in pat.stitches:
        c = cmd & pe.COMMAND_MASK
        if c == pe.STITCH and prev is not None and prev[2] == pe.STITCH and (x, y) == prev[:2]:
            n += 1
        prev = (x, y, c)
    return n


def verify_files(written, ref):
    """Read every written file back and compare it with `ref` (the plan of the pattern
    that was written): {fmt: [problem, ...]}, empty lists when the file sews what the
    design says. Catches what a writer loses or adds: colours, size, sewn path, long
    stitches (a jump written as a stitch), untrimmed jumps and doubled penetrations."""
    out = {}
    ref_len = float(ref.stitch_lengths().sum())
    for fmt, path in written.items():
        probs = []
        try:
            pat = read(path)
            plan = plan_of(pat)
        except Exception as e:                      # noqa: BLE001 (any decode failure)
            out[fmt] = [f"cannot be read back: {e}"]
            continue
        if len(plan.colors) != len(ref.colors):
            probs.append(f"{len(plan.colors)} colour blocks, design has {len(ref.colors)}")
        if max(abs(a - b) for a, b in zip(plan.size, ref.size)) > 0.3:
            probs.append(f"size {plan.size[0]:.1f} x {plan.size[1]:.1f} mm, design is "
                         f"{ref.size[0]:.1f} x {ref.size[1]:.1f}")
        L = plan.stitch_lengths()
        if len(L) and L.max() > max(LONG_MAX, float(ref.stitch_lengths().max(initial=0)) + 0.3):
            probs.append(f"{int((L > LONG_MAX).sum())} stitches over {LONG_MAX} mm, up to "
                         f"{L.max():.1f} mm (a move written as a stitch?)")
        sewn = float(L.sum())
        if ref_len and abs(sewn - ref_len) / ref_len > 0.005:
            probs.append(f"sewn thread {sewn / 1000:.2f} m, design {ref_len / 1000:.2f} m")
        unt = [float(np.linalg.norm(b - a)) for _, a, b, t in plan.jumps if not t]
        unt = [d for d in unt if d > SHORT_JUMP]
        if unt:
            probs.append(f"{len(unt)} untrimmed jumps, up to {max(unt):.1f} mm")
        z = _zero_stitches(pat)
        if z:
            probs.append(f"{z} doubled penetrations (zero-length stitches)")
        if abs(plan.penetrations - ref.penetrations) > len(ref.jumps) + len(ref.colors):
            probs.append(f"{plan.penetrations} stitches, design has {ref.penetrations}")
        out[fmt] = probs
    return out


# PES v6 carries exact RGB. JEF gets explicit trim commands (80 02 00 00 x3): without
# them a Janome reader guesses trims from jump length per axis, so a 3 mm diagonal
# jump goes uncut.
WRITE_SETTINGS = {"pes": {"version": "6t"}, "jef": {"trims": True}}
READ_SETTINGS = {"jef": {"trims": True}}


def write_all(pattern, out_stem, formats=FORMATS, label=None):
    """Write the pattern in every format; returns {fmt: path}. PES is version 6 so the
    exact RGB of every thread travels with the file. Short untrimmed jumps are sewn
    first (sew_short_jumps), so the writers don't turn each into a trim; then the
    pattern is `prepare`d so every format cuts the jumps that stay."""
    sew_short_jumps(pattern)
    prepare(pattern, label or out_stem.name)
    tie_cuts(pattern)
    written = {}
    for fmt in formats:
        path = out_stem.with_suffix("." + fmt)
        settings = WRITE_SETTINGS.get(fmt, {})
        pe.write(pattern, str(path), settings)
        written[fmt] = path
    return written
