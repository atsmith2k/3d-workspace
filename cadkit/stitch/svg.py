"""Write a Design as an Ink/Stitch-ready SVG: one layer, one path per element in sewing
order, stitch parameters as inkstitch:* attributes. Opening it in Inkscape shows the
artwork; Extensions > Ink/Stitch > Params shows exactly what the harness asked for,
and Ink/Stitch's own Embroider / Save As produces the stitches.

The canvas is the hoop (W x H mm, viewBox in mm) with the design centred on it.
Design coordinates are Y up; SVG is Y down.
"""
from xml.sax.saxutils import escape

import numpy as np
from shapely.geometry import LineString, MultiLineString, Polygon
from shapely import shortest_line

from . import shapes as S
from .design import HOOPS, DEFAULT_HOOP
from .fabrics import stretch

NS = ('xmlns="http://www.w3.org/2000/svg" '
      'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
      'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" '
      'xmlns:inkstitch="http://inkstitch.org/namespace"')


def _b(v):
    return "True" if v else "False"


def satin_underlay(width, spec):
    """Underlay kinds for a satin of this width: 'auto' -> centre walk under 2 mm,
    contour from 2 mm, contour + zigzag from 4 mm."""
    if spec in (None, "none", False):
        return set()
    if spec == "auto":
        if width < 1.2:
            return set()
        if width < 2.0:
            return {"center"}
        return {"contour", "zigzag"} if width >= 4.0 else {"contour"}
    return set([spec] if isinstance(spec, str) else spec)


def ink_params(el, trim=None):
    """inkstitch:* attributes for an element (the harness defaults, then el.ink).
    `trim` overrides el.trim_after (the writer adds trims at gaps)."""
    p = el.params
    if el.kind == "fill":
        a = dict(fill_method=p["method"], angle=p["angle"], row_spacing_mm=p["spacing"],
                 max_stitch_length_mm=p["stitch"], staggers=p["staggers"],
                 fill_underlay=_b(p["underlay"]), underpath="True",
                 fill_underlay_angle=(p["angle"] + 90) % 180,
                 fill_underlay_row_spacing_mm=p["underlay_spacing"],
                 fill_underlay_inset_mm=p["underlay_inset"])
        # fill pull compensation is in the shape itself (sew_parts stretches it along
        # the rows): Ink/Stitch 3.0 ignores pull_compensation_mm on fills
    elif el.kind == "satin":
        u = satin_underlay(p["width"], p["underlay"])
        a = dict(satin_column="True", zigzag_spacing_mm=p["spacing"],
                 pull_compensation_mm=p["pull"], center_walk_underlay=_b("center" in u),
                 contour_underlay=_b("contour" in u), zigzag_underlay=_b("zigzag" in u))
    else:
        a = dict(stroke_method="running_stitch", running_stitch_length_mm=p["length"],
                 repeats=p["repeats"], bean_stitch_repeats=p["bean"])
    if el.trim_after if trim is None else trim:
        a["trim_after"] = "True"
    # lock stitches big enough to survive the document's 0.4 mm minimum stitch length
    # (Ink/Stitch's default half-stitch locks come out ~0.2 mm and get merged away)
    a.update(LOCKS)
    a.update(el.ink)
    return a


LOCKS = dict(lock_start="triangle", lock_end="triangle", lock_start_scale_mm=1.0, lock_end_scale_mm=1.0)
TRIM_GAP = 3.0      # mm; Ink/Stitch jumps without trimming, so the writer adds trims


def _geom_of(el, g):
    if el.kind == "fill":
        return g
    if el.kind == "satin":
        return MultiLineString([g[0], g[1]])
    return LineString(g)


def sew_parts(design):
    """[(element, geometry, trim_after)] in sewing order: a fill with separate islands
    becomes one path per island, and every part gets a trim when the next part is
    more than TRIM_GAP away or a different colour (Ink/Stitch leaves those as jump
    threads to snip by hand)."""
    parts = []
    for el in design.elements:
        if el.kind == "fill":
            # holes under 2 mm2 close up when sewn anyway, and Ink/Stitch's auto-fill can
            # fail on them: fill them in
            # pull compensation: rows sewn longer at both ends (fabrics.stretch), each
            # piece on its own: pieces a knockout split apart (a card face cut by the
            # rules sewn over it) must not grow back together through thin necks, which
            # Ink/Stitch's auto-fill gives up on
            pull = el.params.get("pull") or 0.0
            for piece in S.polygons_of(el.geom):
                for poly in S.polygons_of(stretch(piece, el.params["angle"], pull)):
                    parts.append((el, Polygon(poly.exterior, [r for r in poly.interiors if Polygon(r).area >= 2.0])))
        else:
            parts.append((el, el.geom))
    hide = getattr(design, "hide_jumps_mm", None)
    later = _later_cover(parts) if hide else None
    out = []
    for i, (el, g) in enumerate(parts):
        last_of_el = i + 1 == len(parts) or parts[i + 1][0] is not el
        if i + 1 == len(parts):
            trim = el.trim_after
        else:
            nel, ng = parts[i + 1]
            a, b = _geom_of(el, g), _geom_of(nel, ng)
            far = a.distance(b) > TRIM_GAP
            if far and hide and nel.color == el.color and not el.trim_after:
                # leave the move untrimmed when it might be buried under stitching sewn
                # later; pattern.sew_hidden_jumps routes it, or trims it after all
                far = shortest_line(a, b).length > hide or not later[i + 1].buffer(0.6).intersects(b)
            trim = far or nel.color != el.color or (last_of_el and el.trim_after)
        out.append((el, g, bool(trim)))
    return out


def _later_cover(parts):
    """later[i]: what parts i.. (sewn from part i on) cover, shrunk 0.4 mm."""
    foot = []
    for el, g in parts:
        if el.kind == "fill":
            foot.append(g)
        elif getattr(el, "area", None) is not None:
            foot.append(el.area)
        else:
            foot.append(_geom_of(el, g).buffer(0.3))
    later, acc = [None] * len(parts), Polygon()
    for i in range(len(parts) - 1, -1, -1):
        acc = acc.union(foot[i])
        later[i] = acc.buffer(-0.4)
    return later


def _ring_halves(geom, rungs):
    """Split a closed satin ring (paired rails, first pair == last) into two open
    columns at rung pairs roughly half the ring apart: [(d(pts), is_last), ...]."""
    left, right = geom
    n = len(left) - 1
    mid = (left + right) / 2
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(mid, axis=0), axis=1))]
    cand = sorted(set(rungs) | {0}) if rungs else [0, n // 2]
    a = cand[0]
    b = min(cand[1:] or [n // 2], key=lambda k: abs(s[k] - s[a] - s[-1] / 2))
    out = []
    for j, (u, v) in enumerate(((a, b), (b, a + n))):
        idx = np.arange(u, v + 1) % n
        l, r = left[idx], right[idx]
        inner = [k - u for k in (rungs or []) for k in (k, k + n) if u < k < v]

        def d(pts, l=l, r=r, inner=inner):
            out = ["M " + pts(_dedupe(l)), "M " + pts(_dedupe(r))]
            for k in inner:
                p, q = l[k], r[k]
                e = (q - p) / (np.linalg.norm(q - p) + 1e-9) * 0.3
                out.append("M " + pts([p - e, q + e]))
            return out
        out.append((d, j == 1))
    return out


def _dedupe(a):
    """Drop repeated consecutive points (a fan's pivot): Ink/Stitch rails want none."""
    a = np.asarray(a, float)
    keep = np.r_[True, np.linalg.norm(np.diff(a, axis=0), axis=1) > 1e-4]
    return a[keep]


def _fmt(v):
    return f"{v:.4g}" if isinstance(v, float) else str(v)


def to_svg(design, title="design"):
    hoop = design.hoop or DEFAULT_HOOP
    W, H = HOOPS[hoop] if isinstance(hoop, str) else hoop
    x0, y0, x1, y1 = design.bounds()
    W, H = max(W, x1 - x0 + 10), max(H, y1 - y0 + 10)

    def pts(a):
        a = np.asarray(a, float)
        return " ".join(f"{x + W / 2:.3f},{H / 2 - y:.3f}" for x, y in a)

    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg {NS} width="{W:g}mm" height="{H:g}mm" viewBox="0 0 {W:g} {H:g}">',
           f'<title>{escape(title)}</title>',
           f'<!-- generated by cadkit.stitch; hoop {hoop}; sewing order = document order -->',
           # document settings: stitches under 0.4 mm are merged (they break thread), jumps
           # under 3 mm are sewn through rather than trimmed
           '<metadata><inkstitch:min_stitch_len_mm>0.4</inkstitch:min_stitch_len_mm>'
           '<inkstitch:collapse_len_mm>3.0</inkstitch:collapse_len_mm></metadata>',
           '<g inkscape:groupmode="layer" inkscape:label="Embroidery" id="layer1">']
    parts = sew_parts(design)
    for i, (el, geom, trim) in enumerate(parts):
        # lock stitches only where the thread is cut: a tie-in after a trim or colour
        # change, a tie-off before one. A piece that runs on from (or into) its
        # neighbour needs neither (Ink/Stitch ties: 0 both, 1 before, 2 after, 3 neither)
        cut_before = i == 0 or parts[i - 1][2] or parts[i - 1][0].color != el.color
        cut_after = trim or i + 1 == len(parts) or parts[i + 1][0].color != el.color
        ties = {(True, True): 0, (True, False): 1, (False, True): 2, (False, False): 3}[(bool(cut_before), bool(cut_after))]
        if el.kind == "fill":
            d = []
            for ring in [geom.exterior, *geom.interiors]:
                d.append("M " + pts(np.asarray(ring.coords)[:-1]) + " Z")
            style = f"fill:{el.color};fill-rule:evenodd;stroke:none"
        elif el.kind == "satin" and el.params.get("closed"):
            # Ink/Stitch mis-sews closed rails, so a ring goes out as two open columns
            # meeting exactly at corners: the second starts where the first ends (no
            # trim, no gap), rungs keep the pairing round every corner.
            style = f"fill:none;stroke:{el.color};stroke-width:0.2"
            halves = _ring_halves(geom, el.params.get("rungs", []))
            attrs = " ".join(f'inkstitch:{k}="{_fmt(v)}"' for k, v in ink_params(el, False).items())
            for j, (dd, last) in enumerate(halves):
                a = attrs if not last else " ".join(
                    f'inkstitch:{k}="{_fmt(v)}"' for k, v in ink_params(el, trim).items())
                out.append(f'<path id="el{i + 1:03d}{"ab"[j]}" '
                           f'inkscape:label="{escape(f"{i + 1:02d}{"ab"[j]} {el.name}")}" '
                           f'style="{style}" {a} d="{" ".join(dd(pts))}"/>')
            continue
        elif el.kind == "satin":
            left, right = geom
            d = ["M " + pts(left), "M " + pts(right)]
            style = f"fill:none;stroke:{el.color};stroke-width:0.2"
        else:
            d = ["M " + pts(geom)]
            style = f"fill:none;stroke:{el.color};stroke-width:0.25;stroke-dasharray:0.5,0.25"
        attrs = " ".join(f'inkstitch:{k}="{_fmt(v)}"' for k, v in {**ink_params(el, trim), "ties": ties}.items())
        out.append(f'<path id="el{i + 1:03d}" inkscape:label="{escape(f"{i + 1:02d} {el.name}")}" '
                   f'style="{style}" {attrs} d="{" ".join(d)}"/>')
    out += ["</g>", "</svg>", ""]
    return "\n".join(out)
