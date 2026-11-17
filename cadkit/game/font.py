"""Fonts we own, as TrueType files Cinder can load.

A `KIND = "font"` script returns `FontFace(glyphs)`: each glyph a shapely shape on a grid
where the cap height is 10 units and the baseline is y = 0, with its advance width. The build
writes `<name>.ttf` (fontTools; cap height 700 of 1000 units per em), reads it back through
FreeType (Pillow), and has Cinder's own font code parse it, bake its atlas and draw text in it
(cinder-probe). No third-party typeface is copied, so the font is ours to license.

`block_glyphs(stroke)` is the squared block alphabet of cadkit.stitch.lettering (A-Z), extended
here with digits and punctuation in the same construction: straight strokes of one weight, square
bowls, clipped corners.

What Cinder 0.1.1 does with a font: it bakes code points 32..255 at each pixel size used, draws
one glyph per code point with no kerning, wrapping or shaping, and draws '?' for anything else.
So a font should cover ASCII, and lowercase and accented letters should map to something.
"""
import json
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.affinity import scale as _scale, translate as _translate
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from .. import outputs
import importlib

L = importlib.import_module("cadkit.stitch.lettering")   # the package also exports a function of that name
from . import engine as E
from .checks import Check, _name_ok
from .render import BAD, BG, INK, MUTED, OK, _font

H, M = L.H, L.M
UNITS, CAP = 1000, 700                 # units per em; cap height in units (10 grid units)
K = CAP / H                            # font units per grid unit
ASCENT, DESCENT = 800, 200
_r, _d, _cut = L._r, L._d, L._cut


@dataclass
class FontFace:
    """Glyphs by character: (shape on the 10-unit cap grid, advance width in grid units)."""
    glyphs: dict
    family: str = "Block"
    tracking: float = 1.1              # space between letters, grid units
    space: float = 3.4                 # advance of the space character
    unicase: bool = True               # lowercase letters use the capitals
    fold_accents: bool = True          # accented Latin-1 letters use their base letter
    licence: str = "CC0-1.0"
    notes: str = ""

    def cmap(self):
        """code point -> glyph character, with the lowercase and accent fallbacks."""
        out = {ord(c): c for c in self.glyphs}
        for cp in range(32, 256):
            if cp in out:
                continue
            ch = chr(cp)
            base = unicodedata.normalize("NFD", ch)[0] if self.fold_accents else ch
            for cand in (base, base.upper() if self.unicase else base):
                if cand in self.glyphs:
                    out[cp] = cand
                    break
        return out


def _finish(g, w, below=0.0):
    """Trim strokes that ran past the glyph box, then clip every corner a little: the family look."""
    g = g.intersection(_r(0, -below, w, H))
    return g.buffer(-0.35, join_style="mitre").buffer(0.35, join_style="bevel")


def _mirror(g, w):
    return _scale(g, -1, 1, origin=(w / 2, 0))


def block_glyphs(stroke=2.0):
    """A-Z from the lettering we own, plus digits and punctuation drawn to match."""
    s = stroke
    out = {}
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ.'-":
        g, w = L._glyph(ch, s)
        if g is not None and not g.is_empty:
            out[ch] = (g, w)
    w = 6.6

    def add(ch, parts, width=w, cuts=(), below=0.0, raw=False):
        g = unary_union(parts)
        for corner, c in cuts:
            g = _cut(g, width, corner, c)
        out[ch] = (g if raw else _finish(g, width, below), width)

    ring = _r(0, 0, w, H).difference(_r(s, s, w - s, H - s))
    add("0", [ring, _r(w / 2 - s * 0.36, M - 1.3, w / 2 + s * 0.36, M + 1.3)],
        cuts=[(c, 1.8) for c in ("tl", "tr", "bl", "br")])
    w1 = s + 2.6
    add("1", [_r(w1 - s, 0, w1, H), _r(0, H - 1.2 - s, w1 - s, H - 1.2), _r(0, 0, w1 + 1.6, s)], width=w1 + 1.6,
        cuts=[("tr", 0.0)])
    add("2", [_r(0, H - s, w, H), _r(w - s, M - s / 2, w, H), _r(0, M - s / 2, w, M + s / 2), _r(0, 0, s, M + s / 2),
              _r(0, 0, w, s), _r(0, H - s - 1.2, s, H)], cuts=[("tl", 1.6), ("tr", 1.6)])
    add("3", [_r(0, H - s, w, H), _r(1.6, M - s / 2, w, M + s / 2), _r(0, 0, w, s), _r(w - s, 0, w, H),
              _r(0, H - s - 1.2, s, H), _r(0, 0, s, s + 1.2)], cuts=[("tr", 1.6), ("br", 1.6)])
    add("4", [_r(0, 3.2, s, H), _r(0, 3.2, w, 3.2 + s), _r(w - s - 0.9, 0, w - 0.9, H)])
    add("5", [_r(0, H - s, w, H), _r(0, M - s / 2, s, H), _r(0, M - s / 2, w, M + s / 2), _r(w - s, 0, w, M + s / 2),
              _r(0, 0, w, s), _r(0, 0, s, s + 1.2)], cuts=[("br", 1.6), ("bl", 1.6)])
    add("6", [_r(0, 0, s, H), _r(0, H - s, w, H), _r(0, M - s / 2, w, M + s / 2), _r(0, 0, w, s),
              _r(w - s, 0, w, M + s / 2), _r(w - s, H - s - 1.2, w, H)], cuts=[("tl", 1.8), ("bl", 1.6), ("br", 1.6)])
    add("7", [_r(0, H - s, w, H), _d(w - s * 0.55, H - s * 0.4, 2.3, 0, s), _r(0, H - s - 1.2, s, H)])
    add("8", [ring, _r(0, M - s / 2, w, M + s / 2)], cuts=[(c, 1.5) for c in ("tl", "tr", "bl", "br")])
    add("9", [_r(w - s, 0, w, H), _r(0, H - s, w, H), _r(0, M - s / 2, w, M + s / 2), _r(0, 0, w, s),
              _r(0, M - s / 2, s, H), _r(0, 0, s, s + 1.2)], cuts=[("tr", 1.8), ("tl", 1.6), ("bl", 1.6)])
    dot = _r(0, 0, s, s)
    tail = Polygon([(0, 0), (s, 0), (s, -0.4), (s * 0.35, -1.9), (-0.2, -1.9), (s * 0.35, 0)])
    add(",", [dot, tail], width=s, below=2.0)
    add(":", [dot, _translate(dot, 0, 4.6)], width=s)
    add(";", [dot, tail, _translate(dot, 0, 4.6)], width=s, below=2.0)
    add("!", [dot, _r(0, 3.2, s, H)], width=s)
    wq = 6.0
    add("?", [_r(0, H - s, wq, H), _r(wq - s, 4.8, wq, H), _r(wq / 2 - s / 2, 4.8, wq, 4.8 + s),
              _r(wq / 2 - s / 2, 3.1, wq / 2 + s / 2, 4.8 + s), _r(wq / 2 - s / 2, 0, wq / 2 + s / 2, s),
              _r(0, H - s - 1.4, s, H)], width=wq, cuts=[("tl", 1.5), ("tr", 1.5)])
    wp = 6.0
    add("+", [_r(0, M - s / 2, wp, M + s / 2), _r(wp / 2 - s / 2, M - 3, wp / 2 + s / 2, M + 3)], width=wp)
    add("=", [_r(0, 2.9, wp, 2.9 + s * 0.85), _r(0, 5.6, wp, 5.6 + s * 0.85)], width=wp)
    ws = 5.6
    slash = _d(0.6, 0, ws - 0.6, H, s)
    add("/", [slash], width=ws)
    out["\\"] = (_mirror(out["/"][0], ws), ws)
    wb = 3.8
    add("(", [_r(0, 0, s, H), _r(0, H - s, wb, H), _r(0, 0, wb, s)], width=wb, cuts=[("tl", 1.9), ("bl", 1.9)])
    out[")"] = (_mirror(out["("][0], wb), wb)
    add("[", [_r(0, 0, s, H), _r(0, H - s, wb, H), _r(0, 0, wb, s)], width=wb)
    out["]"] = (_mirror(out["["][0], wb), wb)
    wc = 8.2
    add("%", [_r(0, H - 3.1, 3.1, H), _r(wc - 3.1, 0, wc, 3.1), _d(1.3, 0, wc - 1.3, H, s * 0.8)], width=wc)
    wh, t = 7.8, s * 0.75
    add("#", [_r(1.6, 0, 1.6 + t, H), _r(wh - 1.6 - t, 0, wh - 1.6, H), _r(0, 2.8, wh, 2.8 + t), _r(0, 6.0, wh, 6.0 + t)],
        width=wh)
    wa = 5.4
    add("*", [_r(wa / 2 - t / 2, 5.0, wa / 2 + t / 2, 9.8), _d(0.5, 6.2, wa - 0.5, 8.6, t), _d(0.5, 8.6, wa - 0.5, 6.2, t)],
        width=wa, raw=True)
    out["*"] = (out["*"][0].intersection(_r(0, 4.6, wa, H)), wa)
    wl = 5.8
    add("<", [_d(wl - 0.3, H - 1.6, 0.9, M, s * 0.9), _d(0.9, M, wl - 0.3, 1.6, s * 0.9)], width=wl)
    out[">"] = (_mirror(out["<"][0], wl), wl)
    add("_", [_r(0, -1.7, 6.0, -1.7 + s * 0.8)], width=6.0, below=2.0)
    add('"', [_r(0, H - 3.4, s * 0.8, H), _r(s * 0.8 + 1.0, H - 3.4, s * 1.6 + 1.0, H)], width=s * 1.6 + 1.0)
    return out


# ---------------------------------------------------------------- TrueType

def _rings(shape):
    polys = list(shape.geoms) if isinstance(shape, MultiPolygon) else [shape]
    for poly in polys:
        if poly.is_empty or poly.area < 0.01:
            continue
        p = orient(poly, sign=-1.0)                       # TrueType: outer contours run clockwise
        yield list(p.exterior.coords)[:-1]
        for hole in p.interiors:
            yield list(hole.coords)[:-1]


def glyph_name(ch):
    return "space" if ch == " " else f"uni{ord(ch):04X}"


def write_ttf(face, path, name):
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    order, glyphs, metrics = [".notdef", "space"], {}, {}
    pen = TTGlyphPen(None)                                 # .notdef: a hollow box, so a missing glyph shows
    for ring in ([(60, 0), (60, CAP), (480, CAP), (480, 0)], [(130, 70), (410, 70), (410, CAP - 70), (130, CAP - 70)]):
        pen.moveTo(ring[0])
        for pt in ring[1:]:
            pen.lineTo(pt)
        pen.closePath()
    glyphs[".notdef"], metrics[".notdef"] = pen.glyph(), (540, 60)
    glyphs["space"], metrics["space"] = TTGlyphPen(None).glyph(), (int(round(face.space * K)), 0)
    lsb = face.tracking / 2
    for ch, (shape, width) in sorted(face.glyphs.items()):
        if ch == " ":
            continue
        pen = TTGlyphPen(None)
        xmin = None
        for ring in _rings(shape):
            pts = [(int(round((x + lsb) * K)), int(round(y * K))) for x, y in ring]
            xmin = min([p[0] for p in pts] + ([xmin] if xmin is not None else []))
            pen.moveTo(pts[0])
            for pt in pts[1:]:
                pen.lineTo(pt)
            pen.closePath()
        gname = glyph_name(ch)
        order.append(gname)
        glyphs[gname] = pen.glyph()
        metrics[gname] = (int(round((width + face.tracking) * K)), xmin or 0)
    cmap = {cp: glyph_name(ch) for cp, ch in face.cmap().items()}
    cmap[32] = "space"
    fb = FontBuilder(UNITS, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=-DESCENT)
    fb.setupNameTable(dict(familyName=face.family, styleName="Regular", uniqueFontIdentifier=f"cadkit:{name}",
                           fullName=face.family, psName=name.replace("_", "-"), version="Version 1.000",
                           copyright=f"Drawn by code in the cadkit workspace. {face.licence}.",
                           licenseDescription=face.licence))
    fb.setupOS2(sTypoAscender=ASCENT, sTypoDescender=-DESCENT, sTypoLineGap=0, usWinAscent=ASCENT,
                usWinDescent=DESCENT, sCapHeight=CAP, sxHeight=CAP)
    fb.setupPost()
    fb.save(str(path))
    return len(order)


def advance_units(face, text):
    """Width of a line of text in font units, as an engine with no kerning lays it out."""
    cmap = face.cmap()
    total = 0
    for ch in text:
        if ch == " ":
            total += int(round(face.space * K))
        elif ord(ch) in cmap:
            total += int(round((face.glyphs[cmap[ord(ch)]][1] + face.tracking) * K))
        else:
            total += 540
    return total


# ---------------------------------------------------------------- checks

def covers(chars):
    """Every one of these characters has a glyph of its own (not a fallback)."""
    def fn(ctx):
        missing = [c for c in chars if c != " " and c not in ctx.face.glyphs]
        return not missing, f"missing: {''.join(missing)}" if missing else f"{len(chars)} characters drawn"
    return Check("covers", fn)


def distinct(a, b, min_share=0.08):
    """Two glyphs that are easy to confuse differ over at least this share of their box."""
    def fn(ctx):
        size = 48
        f = ImageFont.truetype(str(ctx.ttf), size)

        def bitmap(ch):
            im = Image.new("L", (size * 2, size * 2), 0)
            ImageDraw.Draw(im).text((size // 2, size // 4), ch, font=f, fill=255)
            return np.asarray(im, float) / 255
        d = float(np.abs(bitmap(a) - bitmap(b)).sum() / max(bitmap(a).sum(), bitmap(b).sum()))
        return d >= min_share, f"'{a}' and '{b}' differ over {d:.0%} of their ink (wanted {min_share:.0%})"
    return Check(f"distinct {a}{b}", fn)


def stroke_at(px, at_least=1.5):
    """The thinnest stroke is at least this many pixels wide when the font is set at `px` pixels."""
    def fn(ctx):
        thin = min(_thinnest(shape) for ch, (shape, _) in ctx.face.glyphs.items() if ch.isalnum())
        got = thin * K / (ASCENT + DESCENT) * px
        return got >= at_least, f"thinnest letter or digit stroke is {got:.1f} px at {px} px (wanted {at_least})"
    return Check(f"stroke at {px} px", fn)


def _thinnest(shape):
    """Width of the narrowest part of a shape: twice the largest inset that leaves nothing out."""
    lo, hi = 0.0, 3.0
    for _ in range(14):
        mid = (lo + hi) / 2
        opened = shape.buffer(-mid, join_style="mitre").buffer(mid, join_style="mitre")
        if shape.difference(opened).area > 0.02 * shape.area:
            hi = mid
        else:
            lo = mid
    return 2 * lo


def custom(name, fn):
    """fn(ctx) -> (ok, detail); ctx.face, ctx.ttf, ctx.probe (the engine's report or None), ctx.params."""
    return Check(name, fn)


def _shapes(ctx):
    bad = []
    for ch, (shape, width) in ctx.face.glyphs.items():
        if shape.is_empty or not shape.is_valid:
            bad.append(f"'{ch}' is empty or self-intersecting")
            continue
        x0, y0, x1, y1 = shape.bounds
        if x0 < -0.5 or x1 > width + 0.5:
            bad.append(f"'{ch}' reaches outside its advance ({x0:.1f}..{x1:.1f} of {width:.1f})")
        if y1 * K > ASCENT or y0 * K < -DESCENT:
            bad.append(f"'{ch}' leaves the line ({y0:.1f}..{y1:.1f})")
        if width <= 0:
            bad.append(f"'{ch}' has no advance")
    return not bad, "; ".join(bad[:6]) or f"{len(ctx.face.glyphs)} glyphs: valid outlines inside their advance and the line"


def _freetype(ctx):
    """A second reader: FreeType, through Pillow, loads the file and agrees on the advances."""
    f = ImageFont.truetype(str(ctx.ttf), UNITS)
    bad = []
    for text in ("HELLO 0123", "AV!?"):
        got, want = f.getlength(text), advance_units(ctx.face, text)
        if abs(got - want) > 2:
            bad.append(f"'{text}' is {got:.0f} units wide in FreeType, {want} built")
    for ch in ctx.face.glyphs:
        box = f.getbbox(ch)
        if box is None or box[2] - box[0] <= 0:
            bad.append(f"'{ch}' renders empty")
    if f.getname()[0] != ctx.face.family:
        bad.append(f"family name reads back as {f.getname()[0]}")
    return not bad, "; ".join(bad[:5]) or "FreeType loads it, every glyph renders, advances match"


def _fallbacks(ctx):
    cmap = ctx.face.cmap()
    ascii_missing = [chr(c) for c in range(33, 127) if c not in cmap]
    latin_missing = sum(1 for c in range(160, 256) if c not in cmap)
    ok = all(chr(c) in "".join(map(chr, cmap)) for c in range(ord("a"), ord("z") + 1))
    return ok, (f"{len(cmap)} of 223 code points in 33..255 have a glyph; ASCII without one: "
                f"{''.join(ascii_missing) or 'none'}; Latin-1 without one: {latin_missing}"
                + ("" if ok else "; lowercase letters have no glyph"))


def _engine(ctx):
    p = ctx.probe
    if p is None:
        return False, "not run: no cinder-probe"
    f = p["font"]
    want = advance_units(ctx.face, "HELLO 0123") * 24 / (ASCENT + DESCENT)
    bad = []
    if f["glyphs"] != 224:
        bad.append(f"the engine baked {f['glyphs']} glyphs, not 224")
    if abs(f["sample_width"] - want) > 4:
        bad.append(f"'HELLO 0123' at 24 px is {f['sample_width']:.0f} px in the engine, {want:.0f} expected")
    if abs(f["line_height"] - 24) > 1:
        bad.append(f"line height {f['line_height']} at 24 px")
    if p["gpu_errors"]:
        bad.append(f"{p['gpu_errors']} GPU errors")
    return not bad, "; ".join(bad) or (f"Cinder parsed it, baked 224 glyphs into a {f['atlas_width']} x {f['atlas_height']} "
                                       f"atlas at 24 px, and measures 'HELLO 0123' at {f['sample_width']:.0f} px "
                                       f"(expected {want:.0f})")


def ink_match(frame_png, node, ttf, text):
    """How well the engine's pixels in a label's rectangle match the font's own glyphs: the
    overlap (intersection over union) of bright pixels with FreeType's rendering of the same text
    at the same size, at the best alignment within a few pixels. Near 1 for the right glyphs;
    low when the engine drew something else (the wrong atlas under the right layout looks like text
    and measures correctly, which is why this looks at pixels)."""
    x, y, w, h = int(node["x"]), int(node["y"]), int(node["w"]), int(node["h"])
    with Image.open(frame_png) as im:
        g = np.asarray(im.convert("L"), float)
    crop = g[y:y + h, x:x + w]
    floor = np.percentile(crop, 20)
    got = crop > floor + 0.5 * (crop.max() - floor)
    pad = 16
    ref = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(ref).text((pad, pad), text, font=ImageFont.truetype(str(ttf), h), fill=255)
    ref = np.asarray(ref) > 128
    # The engine puts each character on whole pixels, FreeType does not, so a long line drifts by a
    # few pixels end to end: align in segments of about two characters and average.
    seg = max(int(h * 1.2), 12)
    scores = []
    for x0 in range(0, w - seg // 2, seg):
        piece = got[:, x0:x0 + seg]
        if piece.sum() < 0.03 * piece.size:
            continue                                        # a space
        best = 0.0
        for dy in range(0, 2 * pad + 1):
            for dx in range(-8, 9):
                xs = pad + x0 + dx
                r = ref[dy:dy + h, xs:xs + piece.shape[1]]
                if r.shape != piece.shape or xs < 0:
                    continue
                union = (r | piece).sum()
                if union:
                    best = max(best, float((r & piece).sum() / union))
        scores.append(best)
    return float(np.mean(scores)) if scores else 0.0


def _engine_draws(ctx):
    if ctx.probe is None or ctx.shot is None:
        return False, "not run: no cinder-probe frame"
    scores = []
    for node in ctx.probe["nodes"]:
        if node["kind"] == "label" and node["text"]:
            scores.append((int(node["h"]), ink_match(ctx.shot, node, ctx.ttf, node["text"])))
    ok = bool(scores) and min(s for _, s in scores) >= 0.7
    return ok, ("the engine's pixels match the font's glyphs: " + ", ".join(f"{s:.0%} overlap at {h} px" for h, s in scores)
                + ("" if ok else " (under 70 %: the engine is not drawing this font's shapes)"))


def static_checks():
    return [Check("name", _name_ok), Check("outlines", _shapes), Check("freetype", _freetype),
            Check("fallbacks", _fallbacks)]


# ---------------------------------------------------------------- build

SPECIMEN = ["THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG", "0123456789  +-=/%#*<>()[]  .,:;!?'\"_",
            "Score 12,450   Level 3/9   HP 80%   Press [E]", "GEMS 0/3 * KEY: none * 12:07"]


def render_font(path, face, ttf, engine_shot, title, lines, results, ready):
    W = 1600
    rows = [(64, SPECIMEN[0][:26]), (40, SPECIMEN[1]), (26, SPECIMEN[2]), (18, SPECIMEN[3]), (13, SPECIMEN[0])]
    spec_h = sum(int(px * 1.45) for px, _ in rows) + 30
    shot_h = 360 if engine_shot else 0
    sheet = Image.new("RGB", (W, 60 + spec_h + shot_h + 30 + 18 * (len(lines) + len(results) + 1)), BG)
    d = ImageDraw.Draw(sheet)
    d.text((16, 14), title, fill=INK, font=_font(26))
    d.text((W - 190, 16), "ready YES" if ready else "ready NO", fill=OK if ready else BAD, font=_font(24))
    y = 66
    d.rectangle([0, 60, W, 60 + spec_h], fill=(32, 30, 28))
    for px, text in rows:
        d.text((20, y), text, font=ImageFont.truetype(str(ttf), px), fill=(238, 232, 220))
        d.text((W - 70, y + 2), f"{px} px", fill=MUTED, font=_font(12))
        y += int(px * 1.45)
    d.text((20, 60 + spec_h - 18), "specimen, rendered by FreeType", fill=MUTED, font=_font(12))
    if engine_shot:
        with Image.open(engine_shot) as im:
            crop = im.convert("RGB").crop((240, 270, 1040, 450)).resize((1600, 360), Image.LANCZOS)
        sheet.paste(crop, (0, 60 + spec_h))
        d.text((10, 60 + spec_h + 6), "as Cinder draws it: 48, 24 and 18 px (2x)", fill=(255, 255, 255), font=_font(13))
    ty = 60 + spec_h + shot_h + 12
    for line in lines:
        d.text((12, ty), line, fill=INK, font=_font(13))
        ty += 18
    ty += 4
    for r in results:
        d.text((12, ty), ("PASS  " if r["ok"] else "FAIL  ") + r["name"] + ": " + r["detail"][:175],
               fill=OK if r["ok"] else BAD, font=_font(13))
        ty += 18
    sheet.save(path)


def mojo_snippet(name, rel="fonts"):
    return "\n".join([
        f"# {name}: draw the game's interface in this font (cinder.ui has one font per renderer).",
        "# In Game.start, BEFORE anything is drawn: the renderer uploads a glyph atlas the first time a",
        "# size is drawn and never again, so a font swapped in later is laid out right and drawn wrong.",
        "# Cinder 0.1.1 has no public setting for the UI font; _ensure_ui_renderer is the engine's own",
        "# lazy constructor, called early here.",
        "from cinder.ui import Font, FontCache",
        "app._ensure_ui_renderer()",
        f'var font = Font.from_file(app.lib.ptr(), String("{rel}/{name}.ttf"))',
        "app.ui_renderer.value().fonts = FontCache(font^)"])


def build_font(path, mod, params, out_root, use_engine=True, quiet=False):
    t0 = time.time()
    path = Path(path)
    name = path.stem
    p = SimpleNamespace(**params)
    face = mod.build(p)
    if not isinstance(face, FontFace):
        raise SystemExit('a KIND = "font" script must return cadkit.game.font.FontFace from build(p)')
    out = Path(out_root) / name
    out.mkdir(parents=True, exist_ok=True)
    ttf = out / f"{name}.ttf"
    count = write_ttf(face, ttf, name)
    cmap = face.cmap()
    info = dict(schema="cadkit-font/1", family=face.family, file=ttf.name, units_per_em=UNITS, cap_height=CAP,
                ascent=ASCENT, descent=DESCENT, glyphs=sorted(face.glyphs), code_points=len(cmap) + 1,
                unicase=face.unicase, folds_accents=face.fold_accents, kerning=False, licence=face.licence)
    (out / f"{name}.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    probe, problem, shot = None, None, out / f"{name}_in_engine.png"
    if use_engine:
        probe, problem = E.probe_font(ttf, shot)
    ctx = SimpleNamespace(face=face, ttf=ttf, params=params, name=name, probe=probe,
                          shot=shot if probe and shot.exists() else None)
    spec = mod.checks(p) if callable(getattr(mod, "checks", None)) else []
    checks = static_checks() + ([Check("engine", _engine), Check("engine draws it", _engine_draws)]
                                if use_engine and probe else []) + list(spec)
    results = [c.run(ctx) for c in checks]
    blockers = [f"check {r['name']}: {r['detail']}" for r in results if not r["ok"]]
    steps = dict(static=dict(ok=not blockers, checks=results))
    if probe is None:
        blockers.append("not verified in Cinder: " + ("skipped (--no-engine)" if not use_engine else problem))
    else:
        steps["engine"] = dict(ok=True, font=probe["font"], gpu_errors=probe["gpu_errors"],
                               method="cinder-probe: Font.from_file, bake at 24 px, sample text drawn at 48, 24 and 18 px")
    ready = not blockers
    drawn = "".join(sorted(c for c in face.glyphs if c != " "))
    lines = [f"{name}  (font)  {getattr(mod, 'DESCRIPTION', '')}",
             f"family   {face.family}; {count} glyphs in the file; {len(cmap) + 1} code points mapped",
             f"drawn    {drawn}",
             f"metrics  {UNITS} units per em, cap height {CAP}, ascent {ASCENT}, descent {DESCENT}; no kerning "
             "(Cinder applies none)",
             f"file     {ttf.name} {ttf.stat().st_size / 1024:.1f} kB"]
    if probe:
        f = probe["font"]
        lines.append(f"engine   Cinder baked {f['glyphs']} glyphs at 24 px into {f['atlas_width']} x {f['atlas_height']} "
                     f"and drew the sample with {probe['gpu_errors']} GPU errors")
    for r in results:
        lines.append(f"check    {'PASS' if r['ok'] else 'FAIL'}  {r['name']}: {r['detail']}")
    lines += ["BLOCKER  " + b for b in blockers]
    lines.append(f"ready    {'YES' if ready else 'NO'}")
    preview = out / f"{name}_preview.png"
    render_font(preview, face, ttf, shot if probe and shot.exists() else None,
                f"{name}: {getattr(mod, 'DESCRIPTION', '')}",
                [l for l in lines if not l.startswith(("check", "BLOCKER", "ready"))], results, ready)
    build = dict(schema="cadkit-game-build/1", name=name, kind="font", description=getattr(mod, "DESCRIPTION", ""),
                 params=params, ready=ready, blockers=blockers,
                 stats=dict(family=face.family, glyphs=sorted(face.glyphs), code_points=len(cmap) + 1,
                            units_per_em=UNITS, cap_height=CAP, ttf_bytes=ttf.stat().st_size,
                            unicase=face.unicase, licence=face.licence),
                 use_snippet=mojo_snippet(name), notes=face.notes,
                 files=dict(ttf=ttf.name, json=f"{name}.json", preview=preview.name, sha256=outputs.sha256(ttf)),
                 product=dict(getattr(mod, "PRODUCT", {}) or {}), source_sha256=outputs.sha256(path),
                 engine=E.probe_info(), steps=steps, report=lines, built_at=outputs.now_iso(),
                 seconds=round(time.time() - t0, 1), git=outputs.git_info())
    outputs.save_json(out / "build.json", build)
    outputs.save_json(out / "readiness.json", dict(ready=ready, blockers=blockers, steps=steps))
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    build["out"] = str(out)
    if not quiet:
        print("\n".join(lines))
        print(f"preview  {preview}")
    return build
