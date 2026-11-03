"""Our own lettering, drawn for embroidery (no third-party font licences involved).

`block_text("TEXAS", cap=12)` sets a squared athletic block alphabet: heavy straight
strokes, square bowls with clipped corners, counters kept open enough for a satin
outline. Glyphs are drawn on a 10-unit cap height; `stroke` sets the weight.
"""
import numpy as np
from shapely.affinity import scale as _scale, translate as _translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

H = 10.0
M = H / 2


def _r(x0, y0, x1, y1):
    return box(x0, y0, x1, y1)


def _d(x0, y0, x1, y1, s):
    """A diagonal stroke, as heavy as a vertical one, run a little past its ends."""
    v = np.array([x1 - x0, y1 - y0], float)
    v /= np.linalg.norm(v)
    a, b = np.array([x0, y0]) - v * 3, np.array([x1, y1]) + v * 3
    return LineString([a, b]).buffer(s / 2 * 1.05, cap_style="flat")


def _cut(g, w, corner, c):
    """Clip a corner of the glyph box: 'bl', 'br', 'tr', 'tl'."""
    x = 0 if corner[1] == "l" else w
    y = 0 if corner[0] == "b" else H
    return g.difference(Polygon([(x + c, y), (x, y + c), (x - c, y), (x, y - c)]))


def _glyph(ch, s):
    """(shape, advance width) for one character on the 10-unit grid."""
    w = 7.0
    g = None
    if ch == "A":
        w = 7.6
        g = unary_union([_r(0, 0, s, H), _r(w - s, 0, w, H), _r(0, H - s, w, H), _r(0, 2.9, w, 2.9 + s * 0.85)])
        g = _cut(_cut(g, w, "tl", 2.2), w, "tr", 2.2)
    elif ch == "B":
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w - 0.5, H), _r(0, 0, w, s),
                         _r(0, M - s / 2 + 0.2, w - 0.3, M + s / 2 + 0.2),
                         _r(w - 0.5 - s, M, w - 0.5, H), _r(w - s, 0, w, M + 0.5)])
        g = _cut(_cut(g, w - 0.5, "tr", 1.4), w, "br", 1.4)
    elif ch == "C":
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(0, 0, w, s),
                         _r(w - s, H - s - 1.3, w, H), _r(w - s, 0, w, s + 1.3)])
        g = _cut(_cut(g, w, "tl", 1.8), w, "bl", 1.8)
    elif ch == "D":
        g = _r(0, 0, w, H).difference(_r(s, s, w - s, H - s))
        g = _cut(_cut(g, w, "tr", 2.4), w, "br", 2.4)
    elif ch == "E":
        w = 6.2
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(0, 0, w, s), _r(0, M - s / 2, w - 0.9, M + s / 2)])
    elif ch == "F":
        w = 6.2
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(0, M - s / 2 - 0.3, w - 0.9, M + s / 2 - 0.3)])
    elif ch == "G":
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(0, 0, w, s), _r(w - s, H - s - 1.3, w, H),
                         _r(w - s, 0, w, M + s / 2 - 0.2), _r(w * 0.48, M - s / 2 - 0.2, w, M + s / 2 - 0.2)])
        g = _cut(_cut(g, w, "tl", 1.8), w, "bl", 1.8)
    elif ch == "H":
        g = unary_union([_r(0, 0, s, H), _r(w - s, 0, w, H), _r(0, M - s / 2, w, M + s / 2)])
    elif ch == "I":
        w = s
        g = _r(0, 0, s, H)
    elif ch == "J":
        w = 6.4
        g = unary_union([_r(w - s, 0, w, H), _r(0, 0, w, s), _r(0, 0, s, 3.6)])
        g = _cut(_cut(g, w, "bl", 1.4), w, "br", 1.6)
    elif ch == "K":
        w = 7.4
        g = unary_union([_r(0, 0, s, H), _d(s - 0.4, M - 0.6, w - 0.6, H, s), _d(s + 1.2, M + 0.6, w - 0.4, 0, s)])
    elif ch == "L":
        w = 6.0
        g = unary_union([_r(0, 0, s, H), _r(0, 0, w, s)])
    elif ch == "M":
        w = 9.4
        g = unary_union([_r(0, 0, s, H), _r(w - s, 0, w, H), unary_union([_d(0.6, H, w / 2, M - 1.5, s), _d(w - 0.6, H, w / 2, M - 1.5, s)]).intersection(_r(0, M - 3.0, w, H))])
    elif ch == "N":
        w = 7.6
        g = unary_union([_r(0, 0, s, H), _r(w - s, 0, w, H), _d(0.8, H, w - 0.8, 0, s)])
    elif ch == "O":
        g = _r(0, 0, w, H).difference(_r(s, s, w - s, H - s))
        for c in ("bl", "br", "tr", "tl"):
            g = _cut(g, w, c, 2.2)
    elif ch == "P":
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(w - s, M - 0.6, w, H), _r(0, M - 0.6, w, M - 0.6 + s)])
        g = _cut(g, w, "tr", 1.8)
    elif ch == "Q":
        o = _r(0, 0, w, H).difference(_r(s, s, w - s, H - s))
        for c in ("bl", "br", "tr", "tl"):
            o = _cut(o, w, c, 2.2)
        g = o.union(_d(w * 0.52, 3.0, w + 0.2, -1.0, s * 0.9).intersection(_r(w * 0.4, -1.2, w + 0.4, 3.4)))
    elif ch == "R":
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(w - s, M - 0.6, w, H), _r(0, M - 0.6, w, M - 0.6 + s),
                         _d(w * 0.42, M - 0.2, w - 0.4, 0, s)])
        g = _cut(g, w, "tr", 1.8)
    elif ch == "S":
        g = unary_union([_r(0, H - s, w, H), _r(0, M - s / 2, s, H), _r(0, M - s / 2, w, M + s / 2),
                         _r(w - s, 0, w, M + s / 2), _r(0, 0, w, s)])      # no spurs: they close the counters
        g = _cut(_cut(g, w, "tl", 1.6), w, "br", 1.6)
    elif ch == "T":
        g = unary_union([_r(0, H - s, w, H), _r(w / 2 - s / 2, 0, w / 2 + s / 2, H)])
    elif ch == "U":
        g = unary_union([_r(0, 0, s, H), _r(w - s, 0, w, H), _r(0, 0, w, s)])
        g = _cut(_cut(g, w, "bl", 2.0), w, "br", 2.0)
    elif ch == "V":
        w = 7.8
        g = unary_union([_d(0.9, H, w / 2, 0.4, s), _d(w - 0.9, H, w / 2, 0.4, s)])
    elif ch == "W":
        w = 10.6
        g = unary_union([_d(0.9, H, w * 0.27, 0.4, s), _d(w * 0.27, 0.4, w / 2, H - 2.6, s),
                         _d(w / 2, H - 2.6, w * 0.73, 0.4, s), _d(w * 0.73, 0.4, w - 0.9, H, s)])
    elif ch == "X":
        w = 7.6
        g = unary_union([_d(0.8, H, w - 0.8, 0, s), _d(w - 0.8, H, 0.8, 0, s)])
    elif ch == "Y":
        w = 7.6
        arms = unary_union([_d(0.8, H, w / 2, M - 0.4, s), _d(w - 0.8, H, w / 2, M - 0.4, s)])
        g = unary_union([arms.intersection(_r(0, M - 1.2, w, H)), _r(w / 2 - s / 2, 0, w / 2 + s / 2, M + 0.4)])
    elif ch == "Z":
        w = 6.8
        g = unary_union([_r(0, H - s, w, H), _r(0, 0, w, s), _d(w - 0.6, H - s + 0.2, 0.6, s - 0.2, s)])
    elif ch == "0":
        g = _r(0, 0, w, H).difference(_r(s, s, w - s, H - s))
        for c in ("bl", "br", "tr", "tl"):
            g = _cut(g, w, c, 2.2)
    elif ch == "1":
        w = 5.4
        x = w / 2 - s / 2 + 0.4
        g = unary_union([_r(x, 0, x + s, H), _r(0.3, H - s, x + s, H), _r(0, 0, w, s)])
    elif ch == "2":
        g = unary_union([_r(0, H - s, w, H), _r(w - s, M - s / 2, w, H), _r(0, M - s / 2, w, M + s / 2),
                         _r(0, 0, s, M + s / 2), _r(0, 0, w, s)])
        g = _cut(g, w, "tr", 1.6)
    elif ch == "3":
        g = unary_union([_r(0, H - s, w, H), _r(1.4, M - s / 2, w, M + s / 2), _r(0, 0, w, s), _r(w - s, 0, w, H)])
        g = _cut(_cut(g, w, "tr", 1.6), w, "br", 1.6)
    elif ch == "4":
        g = unary_union([_r(0, M - 0.8, s, H), _r(0, M - 0.8, w, M - 0.8 + s), _r(w - s - 0.4, 0, w - 0.4, H)])
    elif ch == "5":
        g = unary_union([_r(0, H - s, w, H), _r(0, M - s / 2, s, H), _r(0, M - s / 2, w, M + s / 2),
                         _r(w - s, 0, w, M + s / 2), _r(0, 0, w, s)])
        g = _cut(g, w, "br", 1.6)
    elif ch == "6":
        g = unary_union([_r(0, 0, s, H), _r(0, H - s, w, H), _r(0, M - s / 2, w, M + s / 2),
                         _r(w - s, 0, w, M + s / 2), _r(0, 0, w, s)])
        g = _cut(_cut(_cut(g, w, "tl", 1.8), w, "bl", 1.6), w, "br", 1.6)
    elif ch == "7":
        g = unary_union([_r(0, H - s, w, H), _d(w - 0.6, H - s + 0.2, 2.2, 0, s)])
    elif ch == "8":
        g = _r(0, 0, w, H).difference(_r(s, s, w - s, M - s / 2)).difference(_r(s, M + s / 2, w - s, H - s))
        for c in ("bl", "br", "tr", "tl"):
            g = _cut(g, w, c, 1.6)
    elif ch == "9":
        g = unary_union([_r(0, H - s, w, H), _r(0, M - s / 2, s, H), _r(0, M - s / 2, w, M + s / 2),
                         _r(w - s, 0, w, H), _r(0, 0, w, s)])
        g = _cut(_cut(_cut(g, w, "tl", 1.6), w, "tr", 1.8), w, "br", 1.6)
    elif ch == ".":
        w = s
        g = _r(0, 0, s, s)
    elif ch == "'":
        w = s
        g = _r(0, H - 3.2, s, H)
    elif ch == "-":
        w = 4.0
        g = _r(0, M - s / 2, w, M + s / 2)
    elif ch == " ":
        return None, 3.6
    else:
        raise ValueError(f"block_text has no glyph for {ch!r}")
    g = g.intersection(_r(0, -1.2 if ch == "Q" else 0, w + (0.4 if ch == "Q" else 0), H))   # trim run-past diagonals
    g = g.buffer(-0.35, join_style="mitre").buffer(0.35, join_style="bevel")   # small clip on every corner
    return g, w


def block_text(string, cap=10.0, stroke=2.3, tracking=1.0):
    """`string` in the block alphabet, cap height `cap` mm, baseline y=0, starting at x=0.
    `tracking` is the gap between letters in grid units (1 unit = cap/10)."""
    parts, x = [], 0.0
    for ch in string.upper():
        g, w = _glyph(ch, stroke)
        if g is not None:
            parts.append(_translate(g, x, 0))
        x += w + tracking
    k = cap / H
    return _scale(unary_union(parts), k, k, origin=(0, 0))
