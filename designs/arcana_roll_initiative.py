"""Roll for Initiative: stacked block lettering on a ribbon banner, with two tumbling dice.

Spec:
  object:       tabletop-RPG humour lettering piece (generic phrase, no game branding) for
                tees, hoodies, dice bags, totes and game-night patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; dice bags, canvas and wovens with tear-away
  threads:      wine (banner tails), red (banner), teal (d20 shaded faces), white (d20 lit
                faces, d6, INITIATIVE), gold (motion streaks, sparkles, ROLL FOR offset
                shadow), navy (ROLL FOR, banner border and folds, dice rims, edges and
                pips): 6 colours
  must have:    "ROLL FOR" in our block lettering, 13 mm caps, navy with a gold offset
                shadow (kept out of the letter counters); a 100 mm red ribbon banner with
                notched wine tails and navy folds, a 1.6 mm navy satin border; "INITIATIVE"
                in white block lettering, 10 mm caps, on the banner; a tumbling d20
                (24 mm, teal and white facets, navy bean-run edges, 1.6 mm rim) and a d6
                (17 mm, white, five navy pips, 1.4 mm rim) above the words, each with three
                tapered gold motion streaks; three four-point gold sparkles
  lettering:    `cadkit.stitch.lettering.block_text` (our own alphabet, no font licence);
                at the 4x4 size the caps are 10.5 and 8 mm, fill rows 0.35 mm
  density:      fills knocked out under every satin band and under the letters; satin
                streaks clear of the dice rims; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "ROLL FOR INITIATIVE block lettering on a ribbon banner with a d20 and a d6"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Roll for Initiative Embroidery Design",
    "ROLL FOR INITIATIVE in bold block letters on a red ribbon banner, with a tumbling d20 and d6",
    ["roll for initiative", "d20", "d6", "dice", "tabletop rpg", "game master", "game night",
     "dice bag", "gamer embroidery", "rpg lettering"],
    "The four words that start every fight: ROLL FOR in bold navy block letters with a gold "
    "offset shadow, and INITIATIVE in white across a red ribbon banner. A teal d20 and a white "
    "d6 tumble in above, trailing gold motion streaks.\n\n"
    "Great on tees, hoodies, dice bags, totes and game-night patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 16000)


def _centred(t, cx, y_base):
    x0, y0, x1, y1 = t.bounds
    return move(t, cx - (x0 + x1) / 2, y_base - y0)


def _solid(t):
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(t)])


def _sparkle(x, y, r):
    return star(4, r, r * 0.27, x, y, rot=90)


# --- banner -----------------------------------------------------------------------
BY0, BY1, BX = -26.0, -9.0, 46.0     # banner body
TD = 6.0                              # tails drop this far below the body


def banner():
    body = rect(2 * BX, BY1 - BY0, 0, (BY0 + BY1) / 2)
    tails, folds = [], []
    for s in (-1, 1):
        x_in, x_out = s * (BX - 7), s * (BX + 11)
        t = poly([(x_in, BY1 - 4), (x_out, BY1 - 4), (s * (BX + 6), (BY0 + BY1) / 2 - TD / 2 - 2),
                  (x_out, BY0 - TD), (x_in, BY0 - TD)])
        tails.append(t.difference(body))
    folds = [poly([(s * BX, BY0), (s * (BX - 7), BY0 - TD), (s * BX, BY0 - TD)]) for s in (-1, 1)]
    return body, tails, folds


# --- dice -------------------------------------------------------------------------
D20 = (-17.0, 27.0, 12.0, -14.0)      # centre x, y, radius, tilt deg
D6 = (24.0, 25.5, 16.5, 17.0)         # centre x, y, side, tilt deg


def d20():
    cx, cy, r, tilt = D20
    ri = 0.55 * r

    def pt(rr, deg):
        a = math.radians(deg + tilt)
        return np.array([cx + rr * math.cos(a), cy + rr * math.sin(a)])

    H = {a: pt(r, a) for a in (90, 30, 330, 270, 210, 150)}
    I = {a: pt(ri, a) for a in (90, 210, 330)}
    tri = lambda *p: poly([tuple(v) for v in p])
    lit = [tri(I[90], I[210], H[150]), tri(I[90], H[150], H[90]), tri(I[210], H[210], H[150]),
           tri(I[90], I[210], I[330])]
    shade = [tri(I[210], I[330], H[270]), tri(I[330], I[90], H[30]), tri(I[90], H[90], H[30]),
             tri(I[210], H[270], H[210]), tri(I[330], H[330], H[270]), tri(I[330], H[30], H[330])]
    edges = [(I[90], I[210]), (I[210], I[330]), (I[330], I[90]),
             (I[90], H[90]), (I[90], H[150]), (I[90], H[30]),
             (I[210], H[150]), (I[210], H[210]), (I[210], H[270]),
             (I[330], H[270]), (I[330], H[330]), (I[330], H[30])]
    hexa = poly([tuple(H[a]) for a in (90, 150, 210, 270, 330, 30)])
    return hexa, lit, shade, edges


def d6():
    cx, cy, s, tilt = D6
    body = rotate(rounded_rect(s, s, 2.6, cx, cy), tilt, origin=(cx, cy))
    q = s * 0.29
    pips = [circle(cx + dx, cy + dy, 1.75) for dx, dy in ((-q, -q), (q, q), (0, 0), (-q, q), (q, -q))]
    pips = [rotate(g, tilt, origin=(cx, cy)) for g in pips]
    return body, pips


def _streaks(cx, cy, r, deg, lens):
    """Three tapered motion streaks trailing away from a die, along direction `deg`."""
    u = np.array([math.cos(math.radians(deg)), math.sin(math.radians(deg))])
    n = np.array([-u[1], u[0]])
    out = []
    for k, L in zip((-1, 0, 1), lens):
        a = np.array([cx, cy]) + u * (r + 3.2) + n * k * r * 0.55
        b = a + u * L
        pts = [tuple(a + (b - a) * t) for t in np.linspace(0, 1, 6)]
        out.append((pts, [1.9, 1.8, 1.6, 1.3, 1.0, 0.6]))
    return out


def art():
    d = Design()
    body, tails, folds = banner()
    silhouette = union(body, *tails, *folds)
    rim_banner = silhouette.exterior.buffer(0.8)
    seams = [LineString([(s * BX, BY0 + 0.4), (s * BX, BY1 - 4 - 1.5)]) for s in (-1, 1)]

    roll = _centred(block_text("ROLL FOR", cap=13, stroke=2.6, tracking=1.5), 0, -3.0)
    shadow = knockout(move(roll, 1.3, -1.3), _solid(roll))
    init = _centred(block_text("INITIATIVE", cap=10, stroke=2.5, tracking=1.5), 0, (BY0 + BY1) / 2 - 5)

    hexa, lit, shade, edges = d20()
    die6, pips = d6()
    rim20 = hexa.exterior.buffer(0.8)
    rim6 = die6.exterior.buffer(0.7)
    cx, cy, r, tilt = D20
    ri = 0.55 * r
    runs = []
    for a, b in edges:
        u = (b - a) / np.linalg.norm(b - a)
        runs.append([tuple(a + u * 0.9), tuple(b - u * 0.5)])
    streaks = (_streaks(cx, cy, r, 196, (9, 14, 10)) +
               _streaks(D6[0], D6[1], D6[2] * 0.62, 200, (6, 11, 8)))
    sparkles = [_sparkle(-40, 34, 5.0), _sparkle(43, 41, 4.2), _sparkle(4, 40, 3.6)]

    # banner: tails, then the body (letters knocked out, border band kept clear)
    seam_bands = [g.buffer(0.75, cap_style="flat") for g in seams]
    for t in tails:
        d.fill(knockout(t, rim_banner, *folds, *seam_bands), C_["wine"], angle=-30, name="banner tail")
    d.fill(knockout(body, init, rim_banner, *seam_bands), C_["red"], angle=20, name="banner")
    # d20 faces, the d6 and the white lettering
    for g in shade:
        d.fill(knockout(g, rim20), C_["teal"], angle=110, name="d20 shade")
    for g in lit:
        d.fill(knockout(g, rim20), C_["white"], angle=40, name="d20 lit")
    d.fill(knockout(die6, rim6, *pips), C_["white"], angle=-30, name="d6")
    d.fill(init, C_["white"], angle=0, spacing=0.35, name="INITIATIVE")
    # gold: streaks, sparkles, the offset shadow
    for pts, w in streaks:
        d.satin(pts, w, C_["gold"], name="streak", taper=True)
    for g in sparkles:
        d.fill(g, C_["gold"], angle=45, name="sparkle")
    d.fill(shadow, C_["gold"], angle=45, spacing=0.4, name="shadow")
    # navy: folds, seams, border, dice detail, ROLL FOR last
    for g in folds:
        d.fill(knockout(g, rim_banner), C_["navy"], angle=60, name="fold")
    for s in seams:
        d.satin(list(s.coords), 1.5, C_["navy"], name="seam")
    d.outline(silhouette, C_["navy"], width=1.6, name="banner border")
    for pts in runs:
        d.run(pts, C_["navy"], bean=1, name="d20 edge")
    d.outline(hexa, C_["navy"], width=1.6, name="d20 rim")
    for g in pips:
        d.fill(g, C_["navy"], angle=0, name="pip")
    d.outline(die6, C_["navy"], width=1.4, name="d6 rim")
    d.fill(roll, C_["navy"], angle=0, spacing=0.35, name="ROLL FOR")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
