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
    pat = pe.read(str(path))
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
    that stay jumps get lock stitches on both sides, since the writer will cut them."""
    out, pending, last, n = [], [], None, 0
    for x, y, cmd in pattern.stitches:
        c = cmd & pe.COMMAND_MASK
        if c == pe.JUMP and last is not None:
            pending.append((x, y, cmd))
            continue
        if c == pe.STITCH and pending:
            dist = ((x - last[0]) ** 2 + (y - last[1]) ** 2) ** 0.5 / 10.0
            if dist <= max_mm:
                # sew the move in stitches of at most 3 mm
                k = max(1, int(np.ceil(dist / 3.0)))
                for i in range(1, k + 1):
                    out.append((last[0] + (x - last[0]) * i / k, last[1] + (y - last[1]) * i / k, pe.STITCH))
                n += 1
                pending = []
                last = (x, y)
                out.append((x, y, cmd))
                continue
            else:
                # a real move: the writer will trim it, so lock the thread both sides
                out += ([] if _locked(out) else _lock(last, out)) + pending
                out += _lock((x, y), None, toward=last)          # back along the jump
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


def _locked(out, mm=1.2):
    """True when the thread already ends in a lock: the last stitches go back and forth
    over the same tiny stitch (a, b, a, b), not just a fill row turning round."""
    pts = [(x, y) for x, y, c in out[-8:] if (c & pe.COMMAND_MASK) == pe.STITCH][-4:]
    if len(pts) < 4:
        return False
    close = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 1
    a, b, c, d = pts
    short = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 < mm * 10
    return short and close(a, c) and close(b, d)


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


def write_all(pattern, out_stem, formats=FORMATS):
    """Write the pattern in every format; returns {fmt: path}. PES is version 6 so the
    exact RGB of every thread travels with the file. Short untrimmed jumps are sewn
    first (sew_short_jumps), so the writers don't turn each into a trim."""
    sew_short_jumps(pattern)
    written = {}
    for fmt in formats:
        path = out_stem.with_suffix("." + fmt)
        settings = {"version": "6t"} if fmt == "pes" else {}
        pe.write(pattern, str(path), settings)
        written[fmt] = path
    return written
