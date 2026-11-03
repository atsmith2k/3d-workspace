"""Celtic Knot Triskele: a three-lobed interlace knot woven through a circle band.

Spec:
  object:       Celtic interlace knot (a three-lobed triquetra drawn as one endless band)
                woven over-under through a ring, for tees, totes, hoodies, bags and patches
  overall:      `size` mm on the long side (round: 90 mm in the 4x4 hoop, 120 mm in the 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      gold (the knot), emerald green (the ring), dark brown (the edge lines): 3
  must have:    the knot as satin bands 4.0 mm wide (nominal) and the ring as a 4.0 mm
                satin band; at every one of the 9 crossings the under band breaks, stopping
                0.6 mm clear of the over band's edge each side, so the weave reads; every
                band piece outlined by a single dark run 0.25 mm outside its edge, the
                broken ends capped by the same run
  technique:    satin only (no fills): a satin-column showcase; band pieces are plain open
                columns, never stacked; the over band sews straight across the gap
  gaps:         the breaks at the crossings are bare fabric on purpose (that is how the
                weave reads), so `coverage` allows enclosed pockets between elements up
                to 7 mm2 at 95 mm (the break, 1 mm by a band width); every band itself
                must be fully covered
  density:      no stacking anywhere; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Celtic interlace triquetra knot woven over and under through a ring"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Celtic Knot Triskele Embroidery Design",
    "A gold three-lobed Celtic knot woven over and under through an emerald ring, in satin bands",
    ["celtic knot", "triquetra", "triskele", "interlace", "knotwork", "celtic embroidery",
     "satin stitch", "irish", "pagan", "high fantasy", "endless knot"],
    "An endless three-lobed Celtic knot in gleaming gold satin, woven over and under through "
    "an emerald ring the way the old manuscript knots were drawn: every band breaks cleanly "
    "where it passes beneath another, and a fine dark edge line crisps up each strand.\n\n"
    "Great on tees, hoodies, tote bags, book bags, cushions and Celtic-themed patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 3, 16000, between_mm2=7.0 * (p.size / 95.0) ** 2)


U = 15.0            # mm per unit of the trefoil curve (lobe tips at 3 units)
RC = 2.2 * U        # ring radius
W = 4.0             # band width (knot and ring)
GAP = 0.6           # bare fabric between an under band's end and the over band's edge
EDGE = 0.25         # edge run sits this far outside the band


def _knot():
    t = np.linspace(0, 2 * np.pi, 1500, endpoint=False)
    # trefoil projection, turned so one lobe points straight up
    x, y = -(np.sin(t) + 2 * np.sin(2 * t)), -(np.cos(t) - 2 * np.cos(2 * t))
    return np.c_[x, y] * U


def _ring():
    t = np.linspace(0, 2 * np.pi, 1200, endpoint=False) + math.radians(90)
    return np.c_[np.cos(t), np.sin(t)] * RC


def _arclen(P):
    Q = np.vstack([P, P[:1]])
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]


def _crossings(strands):
    """[(strand a, s along a, strand b, s along b, point, angle)] for every crossing."""
    K, I, A, B, LA, LB = [], [], [], [], [], []
    for k, P in enumerate(strands):
        L = _arclen(P)
        Q = np.vstack([P, P[:1]])
        n = len(P)
        K += [k] * n
        I += list(range(n))
        A.append(Q[:-1]); B.append(Q[1:]); LA.append(L[:-1]); LB.append(L[1:])
    K, I = np.array(K), np.array(I)
    A, B, LA, LB = np.vstack(A), np.vstack(B), np.concatenate(LA), np.concatenate(LB)
    D = B - A
    out = []
    for n in range(len(A)):
        m = np.arange(n + 1, len(A))
        den = D[n, 0] * D[m, 1] - D[n, 1] * D[m, 0]
        w = A[m] - A[n]
        with np.errstate(divide="ignore", invalid="ignore"):
            u = (w[:, 0] * D[m, 1] - w[:, 1] * D[m, 0]) / den
            v = (w[:, 0] * D[n, 1] - w[:, 1] * D[n, 0]) / den
        ok = (np.abs(den) > 1e-12) & (u >= 0) & (u < 1) & (v >= 0) & (v < 1)
        same = K[m] == K[n]
        near = np.abs(I[m] - I[n])
        near = np.minimum(near, np.array([len(strands[k]) for k in K[m]]) - near)
        ok &= ~(same & (near <= 2))
        for j in np.nonzero(ok)[0]:
            mm = m[j]
            ang = abs(math.atan2(den[j], float(D[n] @ D[mm])))
            out.append((int(K[n]), LA[n] + u[j] * (LB[n] - LA[n]), int(K[mm]),
                        LA[mm] + v[j] * (LB[mm] - LA[mm]), A[n] + u[j] * D[n], ang))
    return out


def _weave(strands):
    """For each strand, the area its under-passes must stay out of: the over band's
    neighbourhood (band plus GAP) at every crossing where this strand goes under.
    Over/under alternates along every strand."""
    xs = _crossings(strands)
    events = {k: [] for k in range(len(strands))}
    for n, (ka, sa, kb, sb, p, ang) in enumerate(xs):
        events[ka].append((sa, n, 0))
        events[kb].append((sb, n, 1))
    under = {}                                    # crossing n -> which side (0 a, 1 b) is under
    for k in range(len(strands)):
        ev = sorted(events[k])
        start = None
        for idx, (s, n, side) in enumerate(ev):
            if n in under:
                start = (idx, under[n] == side)
                break
        i0, is_under = start if start else (0, False)
        for idx in range(len(ev)):
            s, n, side = ev[(i0 + idx) % len(ev)]
            u = is_under if idx % 2 == 0 else not is_under
            if n in under:
                assert (under[n] == side) == u, "the diagram does not alternate"
            else:
                under[n] = side if u else 1 - side
    masks = {k: [] for k in range(len(strands))}
    for n, (ka, sa, kb, sb, p, ang) in enumerate(xs):
        k, (ko, so) = (ka, (kb, sb)) if under[n] == 0 else (kb, (ka, sa))
        P = strands[ko]
        L = _arclen(P)
        Q = np.vstack([P, P[:1]])
        s = np.linspace(so - 14, so + 14, 60) % L[-1]
        loc = np.c_[np.interp(s, L, Q[:, 0]), np.interp(s, L, Q[:, 1])]
        su = sa if under[n] == 0 else sb
        masks[k].append((su, LineString(loc).buffer(W / 2 + GAP, cap_style="flat")))
    return masks


def _runs(out):
    """Maximal runs of True in a circular bool array: [(start, length)]."""
    n = len(out)
    if out.all():
        return [(0, n)]
    first = int(np.argmin(out))                   # a False: start scanning after it
    runs, i = [], 0
    while i < n:
        j = (first + i) % n
        if out[j]:
            k = 0
            while k < n and out[(j + k) % n]:
                k += 1
            runs.append((j, k))
            i += k
        else:
            i += 1
    return runs


def _resample_n(pts, n):
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    s = np.linspace(0, L[-1], n)
    return np.c_[np.interp(s, L, pts[:, 0]), np.interp(s, L, pts[:, 1])]


def _pieces(P, masks):
    """Rails (left, right) of every piece of the closed band P outside `mask`. Each rail
    is cut where it meets the mask, so a broken end runs parallel to the over band."""
    from shapely import contains_xy
    n = len(P)
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    nrm = np.c_[-t[:, 1], t[:, 0]]
    Lr, Rr = P + nrm * W / 2, P - nrm * W / 2
    S = _arclen(P)[:-1]
    total = _arclen(P)[-1]

    def inside(A):
        hit = np.zeros(n, bool)
        for su, m in masks:                       # a crossing only cuts its own stretch
            near = np.abs((S - su + total / 2) % total - total / 2) < 12
            hit |= near & contains_xy(m, A[:, 0], A[:, 1])
        return hit
    oc, ol, orr = ~inside(P), ~inside(Lr), ~inside(Rr)
    out = []
    for a, k in _runs(oc):
        mid = (a + k // 2) % n
        rng = []
        for ok in (ol, orr):
            for b, m in _runs(ok):
                if (mid - b) % n < m:
                    rng.append((b, m))
                    break
        # pair rails by centreline index; past the end of the rail that is cut sooner,
        # its partner walks along the slanted cut edge, so the stitches fill the wedge
        # and the end runs parallel to the over band (kept 1.1 mm wide at the tip)
        rel = [((b - mid + n // 2) % n - n // 2, m) for b, m in rng]
        lo = min(r[0] for r in rel)
        hi = max(r[0] + r[1] - 1 for r in rel)
        idx = np.arange(lo, hi + 1)
        A = [Lr, Rr]
        rails = [A[j][(mid + np.clip(idx, r0, r0 + m - 1)) % n].copy() for j, (r0, m) in enumerate(rel)]
        for end in (0, 1):                       # 0: start of the piece, 1: its end
            e = [r0 if end == 0 else r0 + m - 1 for r0, m in rel]
            short = int(np.argmax(e)) if end == 0 else int(np.argmin(e))
            longj = 1 - short
            if e[short] == e[longj]:
                continue
            p0 = A[short][(mid + e[short]) % n]
            p1 = A[longj][(mid + e[longj]) % n]
            cut = np.linalg.norm(p1 - p0)
            fmax = max(0.0, 1 - 1.1 / cut) if cut > 0 else 0.0
            span = range(e[longj], e[short]) if end == 0 else range(e[short] + 1, e[longj] + 1)
            for i in span:
                f = (i - e[short]) / (e[longj] - e[short])
                rails[short][i - lo] = p0 + (p1 - p0) * f * fmax
        keep = np.r_[np.arange(0, len(idx), 2), len(idx) - 1]
        keep = np.unique(keep)
        rails = [r[keep] for r in rails]
        out.append(tuple(rails))
    return out


def art():
    d = Design()
    knot, ring_ = _knot(), _ring()
    masks = _weave([knot, ring_])
    pieces = [("gold", "knot", pc) for pc in _pieces(knot, masks[0])]
    pieces += [("green", "ring", pc) for pc in _pieces(ring_, masks[1])]
    # bands first (knot pieces in order along the knot, then the ring), edge runs last
    for col, nm, (l, r) in pieces:
        d.satin_rails(l, r, C_[col], name=f"{nm} band", underlay="center")
    for col, nm, (l, r) in pieces:
        band = Polygon(np.vstack([l, r[::-1]])).buffer(EDGE, join_style="round").simplify(0.05)
        rim = np.asarray(band.exterior.coords)
        d.run(rim, C_["bark"], length=1.8, name=f"{nm} edge", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
