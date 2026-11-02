"""The embroidery design a script builds: an ordered list of stitch elements.

    d = Design()
    d.fill(heart(60), "#c8102e", angle=30)          # tatami fill, underlay on
    d.satin(spline(pts), 3.0, "white")               # satin column along a centreline
    d.run(outline, "black", bean=1)                  # running stitch; bean = triple
    d.outline(shape, "#222", width=1.6)              # satin border round every ring
    d.text("ANNA", 12, "navy")                       # filled lettering

Elements sew in the order they are added; a colour change happens whenever the colour
differs from the previous element. Put large background fills first, details on top,
outlines last. Every element also takes `name=` (its label in Inkscape),
`trim_after=True` and `**ink` (any other Ink/Stitch parameter, written verbatim as
inkstitch:<key>, e.g. `fill_method="contour_fill"`, `stroke_method="ripple_stitch"`).
"""
from dataclasses import dataclass, field

import numpy as np

from . import shapes as S
from .threads import resolve_color

# Hoop sewing fields in mm (width x height). The design must fit inside.
HOOPS = {
    "4x4": (100, 100), "5x7": (130, 180), "6x10": (160, 260), "8x8": (200, 200),
    "8x12": (200, 300), "2x6": (50, 150), "1.5x2": (40, 50),
}
DEFAULT_HOOP = "4x4"

# Defaults tuned for 40 wt polyester on a medium woven with tear-away/cut-away stabiliser.
FILL = dict(angle=45.0, spacing=0.40, stitch=3.0, underlay=True, underlay_spacing=2.0,
            underlay_inset=0.5, staggers=4, method="auto_fill", pull=0.0)
SATIN = dict(spacing=0.40, pull=0.20, underlay="auto")
RUN = dict(length=2.5, repeats=1, bean=0)


@dataclass
class Element:
    kind: str                     # "fill" | "satin" | "run"
    geom: object                  # shapely shape (fill), (left, right) rails (satin), (N,2) path (run)
    color: str                    # "#rrggbb"
    params: dict
    name: str = ""
    trim_after: bool = False
    ink: dict = field(default_factory=dict)

    @property
    def bounds(self):
        if self.kind == "fill":
            return self.geom.bounds
        pts = np.vstack(self.geom) if self.kind == "satin" else self.geom
        return (*pts.min(0), *pts.max(0))


class Design:
    def __init__(self, hoop=None):
        self.hoop = hoop
        self.elements = []

    def _add(self, kind, geom, color, params, name, trim_after, ink):
        el = Element(kind, geom, resolve_color(color), params,
                     name or f"{kind} {len(self.elements) + 1}", trim_after, ink)
        self.elements.append(el)
        return el

    def fill(self, shape, color, angle=None, spacing=None, stitch=None, underlay=None,
             method=None, name="", trim_after=False, **ink):
        """Tatami fill of a shapely shape (holes kept). `angle` of the rows in degrees,
        `spacing` row spacing mm (0.4 normal, 0.3 dense, 0.5+ light), `stitch` max
        stitch length mm, `underlay` True/False, `method` an Ink/Stitch fill method
        (auto_fill, contour_fill, guided_fill, meander_fill, circular_fill)."""
        shape = shape.buffer(0) if not shape.is_valid else shape
        if shape.is_empty:
            raise ValueError(f"fill '{name}' has an empty shape")
        p = dict(FILL)
        for k, v in dict(angle=angle, spacing=spacing, stitch=stitch, underlay=underlay,
                         method=method).items():
            if v is not None:
                p[k] = v
        return self._add("fill", shape, color, p, name, trim_after, ink)

    def satin(self, path, width, color, spacing=None, pull=None, underlay=None, name="",
              trim_after=False, **ink):
        """Satin column along a centreline path, `width` mm wide (a number, or one width
        per path point for a tapered column). 1-7 mm reads well; wider stitches snag,
        use a fill. `underlay` "auto" picks centre walk / contour / zigzag by width,
        or pass a list of them, or "none"."""
        path = np.asarray(path, float)
        w = np.broadcast_to(np.asarray(width, float), (len(path),)).copy()
        left, right = _rails(path, w)
        p = dict(SATIN, width=float(w.max()), width_min=float(w.min()))
        for k, v in dict(spacing=spacing, pull=pull, underlay=underlay).items():
            if v is not None:
                p[k] = v
        return self._add("satin", (left, right), color, p, name, trim_after, ink)

    def satin_rails(self, left, right, color, spacing=None, pull=None, underlay=None,
                    name="", trim_after=False, **ink):
        """Satin column between two rails with the same number of points; point i of
        one rail pairs with point i of the other."""
        left, right = np.asarray(left, float), np.asarray(right, float)
        if len(left) != len(right):
            raise ValueError("satin rails need the same number of points")
        w = np.linalg.norm(left - right, axis=1)
        p = dict(SATIN, width=float(w.max()), width_min=float(w.min()))
        for k, v in dict(spacing=spacing, pull=pull, underlay=underlay).items():
            if v is not None:
                p[k] = v
        return self._add("satin", (left, right), color, p, name, trim_after, ink)

    def run(self, path, color, length=None, repeats=None, bean=None, name="",
            trim_after=False, **ink):
        """Running stitch along a path. `bean=1` sews every stitch three times (bold
        line), `repeats=3` runs the path there-back-there."""
        p = dict(RUN)
        for k, v in dict(length=length, repeats=repeats, bean=bean).items():
            if v is not None:
                p[k] = v
        return self._add("run", np.asarray(path, float), color, p, name, trim_after, ink)

    def outline(self, shape, color, width=None, name="", corner=50.0, **kw):
        """Border every ring of a shape: a satin of `width` mm centred on the edge, or
        a bean-stitch run when width is None. Satin borders are split into separate
        columns at corners sharper than `corner` degrees (a column turning a sharp
        corner folds over itself: bunching and long stitches)."""
        out = []
        for i, ring_pts in enumerate(S.outline_paths(shape)):
            nm = f"{name or 'outline'} {i + 1}"
            if width:
                pieces = split_corners(ring_pts, corner, trim=0.45 * width)
                for j, piece in enumerate(pieces):
                    out.append(self.satin(_resample(piece, 1.0), width, color,
                                          name=nm + (f".{j + 1}" if len(pieces) > 1 else ""), **kw))
            else:
                kw.setdefault("bean", 1)
                out.append(self.run(ring_pts, color, name=nm, **kw))
        return out

    def text(self, string, size, color, x=0.0, y=0.0, font="Arial", bold=True, angle=None,
             spacing=0.35, name="", **kw):
        """Filled lettering, cap height `size` mm, centred on (x, y). Keep size >= 6 mm
        for fills; smaller lettering loses its counters."""
        shape = S.move(S.text_shape(string, size, font=font, bold=bold), x, y)
        return self.fill(shape, color, angle=angle if angle is not None else 90 - 15,
                         spacing=spacing, name=name or f"text {string}", **kw)

    # ---------- summaries ----------
    def bounds(self):
        b = np.array([el.bounds for el in self.elements])
        return (*b[:, :2].min(0), *b[:, 2:].max(0))

    def colors(self):
        """Thread colours in sewing order (one entry per colour block)."""
        seq = []
        for el in self.elements:
            if not seq or seq[-1] != el.color:
                seq.append(el.color)
        return seq


def split_corners(ring, corner=50.0, trim=0.0):
    """Split a closed ring into open paths at points where it turns by more than
    `corner` degrees, each piece shortened by `trim` mm at a sharp end so neighbouring
    satin columns meet instead of piling up. No sharp corner -> [ring] unchanged."""
    pts = np.asarray(ring, float)
    if np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    n = len(pts)
    d_in = pts - np.roll(pts, 1, axis=0)
    d_out = np.roll(pts, -1, axis=0) - pts
    ang = np.degrees(np.abs(np.arctan2(d_in[:, 0] * d_out[:, 1] - d_in[:, 1] * d_out[:, 0], np.einsum("ij,ij->i", d_in, d_out))))
    sharp = [i for i in range(n) if ang[i] > corner]
    if not sharp:
        return [np.vstack([pts, pts[:1]])]
    out = []
    for a, b in zip(sharp, sharp[1:] + [sharp[0] + n]):
        idx = np.arange(a, b + 1) % n
        piece = pts[idx]
        if trim:
            piece = _trim_ends(piece, trim)
        if piece is not None and len(piece) >= 2:
            out.append(piece)
    return out


def _trim_ends(path, mm):
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    if L[-1] <= 2 * mm + 0.5:
        return path
    keep = np.r_[mm, L[(L > mm) & (L < L[-1] - mm)], L[-1] - mm]
    return np.c_[np.interp(keep, L, path[:, 0]), np.interp(keep, L, path[:, 1])]


def _resample(path, step):
    """Path with points no further apart than `step` (closed rings stay closed)."""
    seg = np.diff(path, axis=0)
    out = [path[0]]
    for a, d in zip(path[:-1], seg):
        n = max(1, int(np.ceil(np.linalg.norm(d) / step)))
        out += [a + d * (i / n) for i in range(1, n + 1)]
    return np.asarray(out)


def _rails(path, width):
    """Left/right rails of a centreline at half the width each side, using averaged
    normals at the joints so corners don't cross."""
    d = np.diff(path, axis=0)
    seg_n = np.c_[-d[:, 1], d[:, 0]]
    seg_n /= np.linalg.norm(seg_n, axis=1, keepdims=True) + 1e-12
    closed = np.allclose(path[0], path[-1])
    n = np.zeros_like(path)
    n[:-1] += seg_n
    n[1:] += seg_n
    if closed:
        n[0] = n[-1] = seg_n[0] + seg_n[-1]
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    # keep the column width across a bend: scale by 1/cos(half angle), capped
    cosh = np.ones(len(path))
    cosh[1:-1] = np.clip(np.einsum("ij,ij->i", n[1:-1], seg_n[1:]), 0.5, 1.0)
    half = (width / 2 / cosh)[:, None]
    return path + n * half, path - n * half
