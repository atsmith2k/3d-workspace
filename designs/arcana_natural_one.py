"""Natural One: a cracked, chipped d20 showing a 1, smoking, over red NAT 1 / CRITICAL FAIL.

Spec:
  object:       tabletop-RPG humour piece, the evil twin of Natural Twenty (a generic d20,
                no game branding) for tees, hoodies, dice bags, totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; dice bags and wovens with tear-away
  threads:      charcoal (shadow faces), pewter (lit faces), gray (smoke puff), red
                (centre face, cracks, NAT 1), bone (the 1, face edges), black (rim, crumbs,
                lettering shadow, CRITICAL FAIL): 6 colours
  must have:    a 60 mm d20 tilted 16 deg with a chunk chipped off its upper-left corner
                and two crumbs flying off; faces in charcoal and pewter, a red centre face
                with a 13 mm bone "1"; bone bean-run face edges; two jagged tapered red
                satin cracks (from the chip, and from the lower right) to the centre
                face; a 2.2 mm black rim; a gray
                smoke puff rising from the upper right; "NAT 1" in our block lettering,
                15 mm caps, red with a black drop shadow, split by a hairline crack and
                chipped corners (distressed); "CRITICAL FAIL" 7 mm caps in black below
  lettering:    `cadkit.stitch.lettering.block_text` (our own alphabet, no font licence);
                at the 4x4 size caps are ~14 and 6.6 mm, fill rows 0.35 mm
  density:      faces knocked out under the numeral, the crack and the rim; edge runs stop
                short of every vertex; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Cracked, smoking d20 rolling a natural 1, with NAT 1 / CRITICAL FAIL lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Natural One Critical Fail d20 Embroidery Design",
    "A cracked, chipped, smoking charcoal d20 showing a 1, with red NAT 1 and CRITICAL FAIL lettering",
    ["nat 1", "natural 1", "critical fail", "d20", "dice", "tabletop rpg", "game master",
     "game night", "dice bag", "gamer humor", "funny embroidery"],
    "Every adventurer's worst roll: a charcoal twenty-sided die, chipped, cracked down the middle "
    "and still smoking, landing on a red-faced 1. NAT 1 sits underneath in battered red block "
    "letters, with CRITICAL FAIL spelled out below.\n\n"
    "Great on tees, hoodies, dice bags, totes and game-night patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 16000)


R, CX, CY, TILT = 30.0, 0.0, 20.0, -16.0
RI = 0.56 * R


def _pt(r, deg):
    a = math.radians(deg + TILT)
    return np.array([CX + r * math.cos(a), CY + r * math.sin(a)])


def die():
    H = {a: _pt(R, a) for a in (90, 30, 330, 270, 210, 150)}
    I = {a: _pt(RI, a) for a in (90, 210, 330)}
    tri = lambda *p: poly([tuple(v) for v in p])
    centre = tri(I[90], I[210], I[330])
    lit = [tri(I[90], I[210], H[150]), tri(I[90], H[150], H[90]), tri(I[90], H[90], H[30])]
    dark = [tri(I[210], I[330], H[270]), tri(I[330], I[90], H[30]), tri(I[210], H[210], H[150]),
            tri(I[210], H[270], H[210]), tri(I[330], H[330], H[270]), tri(I[330], H[30], H[330])]
    edges = [(I[90], H[90]), (I[90], H[150]), (I[90], H[30]),
             (I[210], H[150]), (I[210], H[210]), (I[210], H[270]),
             (I[330], H[270]), (I[330], H[330]), (I[330], H[30])]
    hexa = poly([tuple(H[a]) for a in (90, 150, 210, 270, 330, 30)])
    # a chunk bitten out of the upper-left corner
    c = H[150]
    chip = poly([tuple(c + v) for v in ((-6, 6), (-6, -9.5), (2.5, -8.2), (1.0, -3.6), (5.6, -2.2),
                                         (4.0, 2.0), (8.8, 4.0), (6, 9))])
    return hexa.difference(chip), centre, lit, dark, edges, H, I, chip


def crack_path(H, I):
    """Jagged crack from the chip towards the centre face."""
    a = H[150] + np.array([5.2, -4.6])
    b = I[90] * 0.45 + I[210] * 0.55
    pts = [a]
    for t, off in ((0.25, 2.2), (0.5, -1.8), (0.75, 1.6)):
        p = a + (b - a) * t
        n = np.array([-(b - a)[1], (b - a)[0]]) / np.linalg.norm(b - a)
        pts.append(p + n * off)
    pts.append(b)
    # a second crack from the lower-right rim towards the centre face's lower corner
    a2 = H[330] * 0.62 + H[270] * 0.38
    b2 = I[330] * 0.8 + I[210] * 0.2
    n2 = np.array([-(b2 - a2)[1], (b2 - a2)[0]]) / np.linalg.norm(b2 - a2)
    pts2 = [a2, a2 + (b2 - a2) * 0.35 + n2 * 1.6, a2 + (b2 - a2) * 0.7 - n2 * 1.2, b2]
    return pts, pts2


def _clip_path(pts, keep):
    """The part of a path inside `keep` (the crack stops clear of the rim)."""
    g = LineString(pts).intersection(keep)
    g = max(getattr(g, "geoms", [g]), key=lambda x: x.length)
    return [tuple(c) for c in g.coords]


def smoke():
    blobs = [circle(26, 50, 5.4), circle(32, 53, 4.4), circle(21, 55, 4.0), circle(28, 58.5, 4.6),
             circle(35, 59, 3.4), circle(23.5, 47.0, 3.4)]
    return union(*blobs).buffer(0.6).buffer(-0.6)


def _centred(t, cx, y_base):
    x0, y0, x1, y1 = t.bounds
    return move(t, cx - (x0 + x1) / 2, y_base - y0)


def _solid(t):
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(t)])


def lettering():
    word = _centred(block_text("NAT 1", cap=15, stroke=2.8, tracking=1.6), 0, -27)
    x0, y0, x1, y1 = word.bounds
    solid = _solid(word)
    # distress: one hairline crack across the word and a few chipped corners
    crack = LineString([(x0 - 3, -18.5), (x0 + 12, -20.8), (x0 + 22, -17.6), (x0 + 33, -21.2),
                        (x0 + 44, -18.0), (x1 + 3, -20.4)]).buffer(0.55)
    bites = [poly([(x0 - 1, y1 + 1), (x0 + 3.2, y1 + 1), (x0 - 1, y1 - 3.2)]),
             poly([(x1 + 1, y0 - 1), (x1 - 3.6, y0 - 1), (x1 + 1, y0 + 3.6)]),
             poly([(x0 + 26, y1 + 1), (x0 + 29.5, y1 + 1), (x0 + 27.4, y1 - 2.4)])]
    face = word.difference(union(crack, *bites))
    face = union(*[g for g in polygons_of(face) if g.area > 2.0])
    shadow = move(word, 1.4, -1.4).difference(solid.buffer(0.0)).difference(crack)
    shadow = knockout(shadow, solid)
    sub = _centred(block_text("CRITICAL FAIL", cap=7, stroke=2.6, tracking=1.5), 0, -39.5)
    return face, shadow, sub


def art():
    d = Design()
    hexa, centre, lit, dark, edges, H, I, chip = die()
    num = block_text("1", cap=13, stroke=2.8)
    nx0, ny0, nx1, ny1 = num.bounds
    c = (I[90] + I[210] + I[330]) / 3
    num = rotate(move(num, c[0] - (nx0 + nx1) / 2, c[1] - 1.0 - (ny0 + ny1) / 2), TILT, origin=tuple(c))
    keep = hexa.buffer(-2.7)
    cracks = [_clip_path(c, keep) for c in crack_path(H, I)]
    crack_band = union(*[LineString(c).buffer(1.0) for c in cracks])
    rim = hexa.exterior.buffer(1.1)
    puff = smoke()
    crumbs = [rotate(rect(3.0, 2.4, H[150][0] - 9.5, H[150][1] + 3.5), 25, origin=(H[150][0] - 9.5, H[150][1] + 3.5)),
              rotate(rect(2.2, 2.0, H[150][0] - 7.0, H[150][1] + 10.0), -15,
                     origin=(H[150][0] - 7.0, H[150][1] + 10.0))]
    face, shadow, sub = lettering()

    clip = lambda g: g.intersection(hexa)
    for g in dark:
        d.fill(knockout(clip(g), rim, crack_band), C_["charcoal"], angle=120, name="dark face")
    for g in lit:
        d.fill(knockout(clip(g), rim, crack_band), C_["pewter"], angle=50, name="lit face")
    d.fill(knockout(puff, rim), C_["gray"], angle=80, spacing=0.45, name="smoke")
    d.fill(knockout(clip(centre), num, rim, crack_band), C_["red"], angle=0, name="centre face")
    for c, w in zip(cracks, (2.2, 1.8)):
        n = len(c)
        d.satin(c, list(np.linspace(w, 0.7, n)), C_["red"], name="crack", taper=True)
    d.fill(face, C_["red"], angle=0, spacing=0.35, name="NAT 1")
    d.fill(num, C_["bone"], angle=-16, spacing=0.35, name="numeral")
    # face edges: bean runs that stop short of every vertex (no needle pile-ups), the
    # centre face's own edge as one ring
    for a, b in edges:
        u = (b - a) / np.linalg.norm(b - a)
        seg = LineString([tuple(a + u * 0.9), tuple(b - u * 0.6)]).intersection(hexa.buffer(-0.4))
        for part in getattr(seg, "geoms", [seg]):
            if part.length > 2.0 and part.geom_type == "LineString":
                d.run(list(part.coords), C_["bone"], bean=1, name="edge")
    ring = list(centre.exterior.coords)
    d.run(ring, C_["bone"], bean=1, name="centre edge")
    d.outline(hexa, C_["black"], width=2.2, name="rim")
    for g in crumbs:
        d.fill(g, C_["black"], angle=30, name="crumb")
    d.fill(shadow, C_["black"], angle=45, spacing=0.4, name="shadow")
    d.fill(sub, C_["black"], angle=0, spacing=0.35, name="CRITICAL FAIL")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
