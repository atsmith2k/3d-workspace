"""Runeblade: a longsword point-down with a line of Elder Futhark runes in its fuller,
a curled gold crossguard, a laced leather grip, a gemmed pommel and an ivy vine
winding round the blade.

Spec:
  object:       fantasy / viking-age rune sword (original art) for tees, hoodies, jackets,
                totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, where the 100 mm field
                keeps it to 90 mm tall; 160 for 5x7), vertical
  fabric:       knits with cut-away; patches and wovens with tear-away
  threads:      silver (lit bevel), gray (shaded bevel), wood (grip),
                charcoal (fuller, grip lacing), gold (runes, crossguard, pommel), green (pommel
                gem, vine, leaves), leaf (leaf veins): 7 colours, one block each
  must have:    a slim 9.2 mm blade (about 70% of the length) split into light and dark
                bevel halves that curve into a smooth 1.2 mm point; a 4.2 mm
                charcoal fuller carrying five Elder Futhark runes in gold satin,
                T A L U T (tiwaz, ansuz-laguz-uruz = "alu", the charm word on
                migration-period bracteates, between two tiwaz, the war rune), 6 mm
                tall with 1.3 mm strokes; a 34 mm gold crossguard with recurved,
                tapered curls; a brown grip with a dark zigzag lacing; a gold ring
                pommel with a green gem; an ivy vine that crosses in front of the blade,
                passes behind it lower down, with four smooth three-lobed leaves veined in light green
  lettering:    runes drawn here as satin strokes (historical alphabet, public domain)
  density:      bevels knocked out under the fuller, the vine and the leaves; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Longsword point-down with Elder Futhark runes, curled crossguard and ivy"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Runeblade Sword Embroidery Design",
    "A silver longsword with glowing gold runes, a curled crossguard, a gemmed pommel and ivy",
    ["sword", "runes", "viking runes", "elder futhark", "longsword", "rune sword", "ivy",
     "medieval", "norse", "high fantasy", "warrior"],
    "A blade worthy of a saga: a silver longsword pointing down, its fuller carved with a "
    "line of genuine Elder Futhark runes in gold, a curled gold crossguard, a laced leather "
    "grip and an emerald pommel, with a sprig of ivy winding round the steel.\n\n"
    "Great on tees, hoodies, jackets, totes and sew-on patches for faire days and game nights.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 16000)


GUARD_Y = 14.0
TIP_Y = -53.0
RUNE_W = 1.3
RKX, RKY = 0.9, 1.25   # rune glyph scale: 6 mm tall, tall and narrow like carved runes
VINE_W = 1.5


def blade_halves():
    """Lit (left) and shaded (right) bevels as clean polygons: straight edges that taper
    from 9.2 mm under the guard, then curve smoothly into a 1.2 mm wide point."""
    top = GUARD_Y - 1.0
    curve = bezier((3.5, -36.0), (3.3, -44.0), (1.6, -49.5), (0.6, TIP_Y), 16)
    right = [(0.0, top), (4.6, top)] + [tuple(q) for q in curve] + [(0.0, TIP_Y)]
    left = [(-x, y) for x, y in right]
    return poly(left[::-1]), poly(right)


# Elder Futhark glyphs as satin stroke centrelines in a 4.8 mm tall box (x centred,
# y from 0 to 4.8); branches start at the stem's edge so no two columns end in one spot
RUNES = {
    "t": [[(0, 0), (0, 3.3)], [(-1.45, 3.05), (0, 4.75), (1.45, 3.05)]],
    "a": [[(-0.85, 0), (-0.85, 4.8)], [(-0.3, 4.45), (1.4, 3.3)], [(-0.3, 2.55), (1.4, 1.4)]],
    "l": [[(-0.6, 0), (-0.6, 4.8)], [(-0.05, 4.45), (1.4, 3.3)]],
    "u": [[(-1.25, 0), (-1.25, 4.8)], [(-0.7, 4.55), (1.25, 3.4), (1.25, 0)]],
}


def rune_paths(word="talut", top=8.6, step=7.3):
    out = []
    for i, ch in enumerate(word):
        y0 = top - 4.8 * RKY - i * step
        for stroke in RUNES[ch]:
            out.append(np.array([(x * RKX, y0 + y * RKY) for x, y in stroke], float))
    return out


def guard_path():
    dy = GUARD_Y - 18.0
    half = [(16.4, 13.0), (17.0, 15.6), (15.6, 17.8), (12.0, 18.4), (6.0, 18.2), (0.0, 18.0)]
    pts = [(14.2, 12.4)] + half + [(-x, y) for x, y in half[::-1][1:]] + [(-14.2, 12.4)]
    path = spline([(x, y + dy) for x, y in pts], samples=8)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    t = s / s[-1]
    # 1.5 mm at the curl tips, 3.2 mm across the middle
    w = 1.5 + 1.7 * np.clip(np.minimum(t, 1 - t) / 0.28, 0, 1) ** 0.8
    return path, w


LEAF = [(0, 0.06), (-0.22, -0.06), (-0.48, 0.02), (-0.66, 0.38), (-0.40, 0.45),
        (-0.27, 0.60), (-0.14, 0.86), (0, 1.02), (0.14, 0.86), (0.27, 0.60), (0.40, 0.45),
        (0.66, 0.38), (0.48, 0.02), (0.22, -0.06)]


def _place(pts, size, x, y, deg):
    a = np.radians(deg)
    c, s_ = np.cos(a), np.sin(a)
    p = np.asarray(pts, float) * size
    return np.c_[p[:, 0] * c - p[:, 1] * s_ + x, p[:, 0] * s_ + p[:, 1] * c + y]


def ivy_leaf(size, x, y, deg):
    """Smooth three-lobed ivy leaf, stem end at (x, y), pointing `deg` from +y, and its
    veins (main vein with the two side veins from the base) as run paths."""
    g = poly([tuple(q) for q in spline(_place(LEAF, size, x, y, deg), samples=10, closed=True)])
    veins = [_place([(-0.36, 0.38), (0, 0.2), (0, 0.78)], size, x, y, deg),
             _place([(0.36, 0.38), (0.05, 0.23)], size, x, y, deg)]
    return g, veins


VINE = [(-12.0, -21.0), (-8.6, -25.4), (-4.0, -29.6), (0.0, -32.0), (4.2, -34.2),
        (7.6, -37.0), (8.2, -40.4), (5.0, -42.6), (0.0, -44.0), (-4.6, -45.4),
        (-7.4, -48.0), (-8.6, -51.6)]
BEHIND_Y = -41.0     # the vine passes behind the blade below this


def vine_pieces(bl):
    """The vine centreline: in front of the blade at the upper crossing, behind it at the
    lower one (cut out under the blade, ends tucked 0.3 mm onto it)."""
    path = spline(VINE, samples=12)
    lower = LineString(path[path[:, 1] < BEHIND_Y])
    upper = LineString(path[path[:, 1] >= BEHIND_Y])
    behind = lower.difference(bl.buffer(-0.3))
    pieces = list(behind.geoms) if behind.geom_type != "LineString" else [behind]
    joined = LineString(list(upper.coords) + list(pieces[0].coords)[1:])
    return [np.array(p.coords) for p in [joined] + pieces[1:] if p.length > 2.0]


def art(size=95.0):
    d = Design()
    left, right = blade_halves()
    bl = union(left, right)
    fuller = rounded_rect(4.2, 38.5, 1.0, 0, 9.6 - 38.5 / 2)
    runes = rune_paths()
    vines = vine_pieces(bl)
    leafs = [ivy_leaf(11.5, -12.0, -21.0, 62), ivy_leaf(10.5, 8.2, -40.4, -112),
             ivy_leaf(9.0, 4.2, -34.2, -28), ivy_leaf(10.0, -8.6, -51.6, 150)]
    leaves = [g for g, _ in leafs]
    vine_band = union(*[LineString(v).buffer(VINE_W / 2, cap_style="flat") for v in vines])
    over = union(vine_band, *leaves)

    # rows across the blade: their ends trace the long edges and the point cleanly
    # knockout drops slivers under 1 mm, which would eat the narrow point: the point
    # (below the vine) is kept whole
    point = rect(30, 20, 0, -45.6 - 10)
    lit = union(knockout(left.difference(point), fuller, over), left & point.buffer(0.4))
    shade = union(knockout(right.difference(point), fuller, over), right & point.buffer(0.4))
    d.fill(lit, C_["silver"], angle=-10, name="lit bevel")
    d.fill(shade, C_["gray"], angle=10, name="shaded bevel")

    grip = rounded_rect(5.0, 18.6, 1.2, 0, 24.9)
    d.fill(grip, C_["wood"], angle=30, name="grip")

    rune_bands = union(*[LineString(r).buffer(RUNE_W / 2, cap_style="flat", join_style="mitre")
                         for r in runes])
    # fuller knocked out under the runes; slivers between strokes are kept down to
    # ~1.15 mm as sewn (narrower ones drop: the rune satins cover them)
    sliver = 1.15 / (size / 100.0)
    groove = knockout(fuller, rune_bands, overlap=0.15, min_width=max(0.7, min(1.25, sliver)))
    # one fill per rune, cut in the gaps between runes (0.2 mm overlap): as one piece the
    # travel kept running through the narrow strip beside the ansuz branches (7 needle
    # visits to one hole at 5x7)
    cuts = [8.6 - 4.8 * RKY - i * 7.3 - (7.3 - 4.8 * RKY) / 2 for i in range(4)]
    edges = [20.0] + cuts + [-40.0]
    for hi, lo in zip(edges, edges[1:]):
        part = groove & rect(10, hi - lo + 0.4, 0, (hi + lo) / 2)
        d.fill(part, C_["charcoal"], angle=90, name="fuller")
    zig = [((-1.8 if i % 2 == 0 else 1.8), 17.0 + i * 1.7) for i in range(10)]
    d.run(line(*zig), C_["charcoal"], bean=1, name="grip lacing")

    for r in runes:
        d.satin(r, RUNE_W, C_["gold"], name="rune", underlay="center")
    gp, gw = guard_path()
    d.satin(gp, gw, C_["gold"], name="crossguard", taper=True, underlay="center")
    d.outline(circle(0, 38.6, 3.6), C_["gold"], width=2.2, name="pommel")

    d.fill(circle(0, 38.6, 2.8), C_["green"], angle=45, name="pommel gem")
    for v in vines:
        d.satin(v, VINE_W, C_["green"], name="vine", underlay="center")
    for i, g in enumerate(leaves):
        d.fill(g, C_["green"], angle=(30, 120, 160, 70)[i], name="ivy leaf")
    for _, veins in leafs:
        for v in veins:
            d.run(v, C_["leaf"], bean=1, name="leaf vein")
    return d


def design(p):
    return fit(art(p.size), p.size, hoop_for(p.size))
