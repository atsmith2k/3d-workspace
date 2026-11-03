"""Forbidden Grimoire: a thick closed spellbook with a gold moon-and-eye sigil and brass
fittings, and a lit candle beside it.

Spec:
  object:       witchy / dark-fantasy spellbook motif (original sigil, no branding) for
                tote bags, tees, hoodies, book sleeves and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; canvas and wovens with tear-away
  threads:      purple (cover boards), bone (page block, candle), khaki (page lines,
                candle shading), black (spine, strap, wick, candle edge), brass (spine
                bands, corner caps, clasp, panel frame, candle dish), flame (flame), gold
                (sigil, flame core, sparkles): 7 colours
  must have:    a 52 x 62 mm cover face with a 7 mm black spine on the left and four brass
                spine bands; the book's thickness shown down and to the right as a cream
                page block between the front and back boards, with page-line runs; brass
                caps on the two outer corners; a black strap and brass clasp across the fore
                edge; a brass frame run on the cover; a 30 mm gold sigil (a ring of runes,
                an eye in the middle, a crescent moon crowning the ring); a 10 mm candle on
                a brass dish with drips, a black wick and a two-tone flame; two sparkles
  density:      fills knocked out under every satin and outline band; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString, Polygon

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Closed spellbook with a gold moon-and-eye sigil and a lit candle"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Forbidden Grimoire Embroidery Design",
    "A thick purple spellbook with brass corners, a gold arcane sigil and a lit candle",
    ["spellbook", "grimoire", "witchy", "dark fantasy", "gothic", "book of spells", "witch",
     "candle", "arcane", "bookish embroidery", "halloween embroidery"],
    "A thick, well-worn spellbook bound in deep purple leather, with a black spine, brass "
    "corner caps, a strapped clasp and cream page edges. A gold sigil glows on the cover: a "
    "watchful eye inside a ring of runes, crowned by a crescent moon. A candle burns beside it.\n\n"
    "Great on tote bags, book sleeves, hoodies, tees and witchy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 18000)


V = np.array([7.0, -6.0])              # the book's thickness, seen down and to the right
X0, X1, Y0, Y1 = -38.0, 14.0, -28.0, 34.0
SPINE = 7.0


def _sweep(g, f):
    return union(g, move(g, *(V * f))).convex_hull


def _band(path, w):
    return LineString(path).buffer(w / 2, cap_style="flat")


def sparkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


def sigil(cx, cy):
    """(satin paths with widths, fill shapes, run paths) of the cover sigil."""
    sat, fills, runs = [], [], []
    sat.append((circle_path(cx, cy, 15.0, 120), 1.8))
    runs.append(circle_path(cx, cy, 11.2, 100))
    # runes between the rings: diamonds and short bars alternating
    for k in range(12):
        a = np.radians(90 + 15 + k * 30)
        r = 13.1
        x, y = cx + r * np.cos(a), cy + r * np.sin(a)
        if k % 2:
            fills.append(rotate(poly([(x, y + 1.3), (x + 1.0, y), (x, y - 1.3), (x - 1.0, y)]),
                                np.degrees(a) - 90, origin=(x, y)))
        else:
            t = np.array([np.cos(a), np.sin(a)])
            sat.append((np.array([(x, y) - t * 1.0, (x, y) + t * 1.0]), 1.2))
    # the eye: an almond ring with a solid iris and a slit pupil left open
    t = np.linspace(-1, 1, 41)
    upper = np.c_[cx + 8.5 * t, cy + 4.6 * (1 - t ** 2)]
    lower = np.c_[cx + 8.5 * t, cy - 4.6 * (1 - t ** 2)]
    eye = poly(np.vstack([upper, lower[::-1]]))
    fills.append(("eye", eye))
    fills.append(("iris", circle(cx, cy, 3.4) - ellipse(cx, cy, 0.7, 2.4)))
    # a crescent crowning the ring, horns up
    moon = circle(cx, cy + 21.0, 5.2) - circle(cx, cy + 23.4, 4.4)
    fills.append(moon)
    return sat, fills, runs, eye


def art():
    d = Design()
    face = Polygon([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)])
    front = _sweep(face, 0.18) - face                         # front board edge
    pages = _sweep(face, 0.80) - _sweep(face, 0.18)
    back = _sweep(face, 1.0) - _sweep(face, 0.80)
    boards = union(face, front, back)
    book = union(boards, pages)
    spine = rounded_rect(SPINE + 3, Y1 - Y0 + 2, 1.5, X0 + SPINE / 2 - 1.5, (Y0 + Y1) / 2) & \
        Polygon([(X0 - 2, Y0 - 2), (X0 + SPINE, Y0 - 2), (X0 + SPINE, Y1 + 2), (X0 - 2, Y1 + 2)])
    spine = (spine | Polygon([(X0, Y0), (X0 + SPINE, Y0), (X0 + SPINE + V[0] * 0.18, Y0 + V[1] * 0.18),
                              (X0 + V[0] * 0.18, Y0 + V[1] * 0.18)])).buffer(0)
    bands = [np.array([(X0 + 0.8, y), (X0 + SPINE - 0.8, y)]) for y in (27, 13, -5, -19)]
    caps = [(boards & Polygon([(-1, 40), (30, 40), (30, 9)])) - spine,
            (boards & Polygon([(30, -46), (30, -15), (-1, -46)])) - spine]
    caps = [c.buffer(-0.3).buffer(0.3) for c in caps]
    strap = (Polygon([(8, -0.5), (X1 + V[0] + 0.3, -0.5 + V[1]), (X1 + V[0] + 0.3, 7.5 + V[1]), (8, 7.5)])
             & book.buffer(0.3))
    clasp = rounded_rect(6.0, 10, 1.5, 9.5, 3.5)
    sat, sfills, sruns, eye = sigil(-12.5, 1.5)
    frame = rounded_rect(X1 - X0 - SPINE - 7, Y1 - Y0 - 7, 2, (X0 + SPINE + X1) / 2, (Y0 + Y1) / 2).exterior
    cover_top = union(spine, *caps, strap, clasp)

    # candle
    cx = 33.0
    candle = poly([(cx - 5, -33), (cx + 5, -33), (cx + 5, 0.5), (cx + 3.6, 2.2), (cx + 2.2, 1.0),
                   (cx + 1.0, 2.6), (cx - 1.2, 2.4), (cx - 2.6, 0.8), (cx - 3.8, 2.0), (cx - 5, 1.0)])
    drips = union(rounded_rect(2.2, 9, 1.1, cx - 2.6, -2.5), rounded_rect(2.0, 6, 1.0, cx + 2.2, -1.5))
    shade = (candle & Polygon([(cx + 2.2, -40), (cx + 6, -40), (cx + 6, 4), (cx + 2.2, 4)])) - drips
    shade = shade.buffer(-0.2).buffer(0.2)
    dish = union(ellipse(cx, -34.5, 9.5, 2.8), rounded_rect(12, 3, 1.0, cx, -32.8))
    flame = smooth([(cx, 21), (cx + 2.4, 14), (cx + 3.4, 9.5), (cx + 2.2, 6.4), (cx, 5.6),
                    (cx - 2.2, 6.4), (cx - 3.4, 9.5), (cx - 2.4, 14)], 8).buffer(0)
    core = smooth([(cx, 14.5), (cx + 1.5, 10), (cx + 1.4, 7.6), (cx, 7.0), (cx - 1.4, 7.6),
                   (cx - 1.5, 10)], 8).buffer(0)
    sparkles = [sparkle(30, 32, 5.0), sparkle(-36, -38, 3.6)]

    # satin bands of everything sewn over the cover: fills stop under them
    sig_bands = union(*[_band(pth, w) for pth, w in sat])
    eye_ring = eye.exterior.buffer(0.7)
    over_cover = union(cover_top, sig_bands, *[(f[1] if isinstance(f, tuple) else f) for f in sfills if not (isinstance(f, tuple) and f[0] == "eye")],
                       eye_ring)

    # purple
    d.fill(knockout(face, over_cover), C_["purple"], angle=70, name="cover")
    d.fill(knockout(union(front, back), cover_top), C_["purple"], angle=-40, name="boards")
    # bone
    d.fill(knockout(pages, cover_top), C_["bone"], angle=-40, spacing=0.42, name="pages")
    d.fill(knockout(candle, shade, dish, overlap=0.4), C_["bone"], angle=90, name="candle")
    # khaki page lines: parallel to the fore edge and the tail edge
    hidden = union(cover_top).buffer(1.2)
    for f in (0.32, 0.49, 0.66):
        o = V * f
        for seg in (LineString([(X1 + o[0], Y1 + o[1] - 2.5), (X1 + o[0], Y0 + o[1] + 1.5)]),
                    LineString([(X0 + SPINE + o[0] + 1.5, Y0 + o[1]), (X1 + o[0] - 1.5, Y0 + o[1])])):
            vis = seg.difference(hidden)
            for g in getattr(vis, "geoms", [vis]):
                if g.geom_type == "LineString" and g.length > 3:
                    d.run(np.asarray(g.coords), C_["khaki"], length=2.0, name="page line", trim_after=True)
    d.fill(knockout(shade, dish), C_["khaki"], angle=90, name="candle shade")
    # black
    d.fill(knockout(spine, *[_band(b, 1.6) for b in bands]), C_["black"], angle=90, name="spine")
    d.fill(knockout(strap, clasp), C_["black"], angle=0, name="strap")
    d.satin(np.array([(cx, 2.0), (cx, 6.2)]), 1.1, C_["black"], name="wick")
    d.run(np.asarray(candle.exterior.coords), C_["black"], bean=1, length=1.6, name="candle edge")
    # brass
    for b in bands:
        d.satin(b, 1.6, C_["brass"], name="spine band")
    for c in caps:
        d.fill(c, C_["brass"], angle=45, name="corner cap")
    d.fill(clasp, C_["brass"], angle=90, name="clasp")
    vis = LineString(frame.coords).difference(union(*caps, strap, clasp, sig_bands).buffer(1.6))
    for g in getattr(vis, "geoms", [vis]):
        if g.geom_type == "LineString" and g.length > 3:
            d.run(np.asarray(g.coords), C_["brass"], bean=1, length=1.8, name="frame", trim_after=True)
    d.fill(dish, C_["brass"], angle=0, name="dish")
    # flame
    d.fill(knockout(flame, core), C_["flame"], angle=90, name="flame")
    # gold
    d.fill(core, C_["gold"], angle=90, underlay=False, name="flame core")
    for pth, w in sat:
        d.satin(pth, w, C_["gold"], name="sigil ring" if len(pth) > 2 else "rune")
    for pth in sruns:
        d.run(pth, C_["gold"], bean=1, length=1.5, name="inner ring")
    for f in sfills:
        if isinstance(f, tuple):
            nm, g = f
            if nm == "eye":
                d.outline(g, C_["gold"], width=1.4, name="eye")
            else:
                d.fill(g, C_["gold"], angle=45, name=nm)
        else:
            d.fill(f, C_["gold"], angle=30, name="sigil")
    for s in sparkles:
        d.fill(s, C_["gold"], angle=45, name="sparkle")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
