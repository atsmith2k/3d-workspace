"""Natural Twenty: a shaded twenty-sided die showing its 20, with "NAT 20" below.

Spec:
  object:       tabletop RPG critical-hit die (a generic d20, no game branding) for
                tees, dice bags, tote bags, hoodies and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; dice bags and wovens with tear-away
  threads:      lavender, lilac, violet (die faces lit from the top left), gold (edges,
                numeral, lettering), purple (lettering shadow): 5 colours
  must have:    a 70 mm hexagon-outline die with ten visible faces in three shades;
                gold satin edges 1.4 mm on the faces, a 2.2 mm gold rim; a 13 mm "20"
                in the centre face; "NAT 20" in our block lettering, 12 mm caps, gold
                with a purple drop shadow under it; two four-point sparkles
  lettering:    `cadkit.stitch.lettering.block_text` (our own alphabet, no font licence)
  density:      faces knock out the numeral; edges sew on top; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Shaded d20 showing a natural twenty, with NAT 20 lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Natural Twenty d20 Embroidery Design",
    "A shaded purple twenty-sided die rolling a critical 20, with gold NAT 20 lettering",
    ["d20", "natural 20", "nat 20", "critical hit", "tabletop rpg", "dice", "dungeon master",
     "dice bag", "gamer embroidery"],
    "Every adventurer's favourite roll: a twenty-sided die in three shades of violet with gold "
    "edges, landing on a natural 20, and NAT 20 in bold gold block letters underneath.\n\n"
    "Great on dice bags, hoodies, tees, totes and game-night patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 14000)


R = 36.0          # hexagon (die silhouette) radius
RI = 0.56 * R     # inner (centre face) triangle radius
CY = 12.0         # die centre


def _pt(r, deg):
    a = math.radians(deg)
    return np.array([r * math.cos(a), CY + r * math.sin(a)])


def faces():
    """The ten visible faces as (polygon, shade) with the light from the top left."""
    H = {a: _pt(R, a) for a in (90, 30, 330, 270, 210, 150)}
    I = {a: _pt(RI, a) for a in (90, 210, 330)}
    tri = lambda *p: poly([tuple(v) for v in p])
    return [
        (tri(I[90], I[210], I[330]), "lilac"),
        (tri(I[90], I[210], H[150]), "lavender"),
        (tri(I[210], I[330], H[270]), "violet"),
        (tri(I[330], I[90], H[30]), "lilac"),
        (tri(I[90], H[150], H[90]), "lavender"),
        (tri(I[90], H[90], H[30]), "lilac"),
        (tri(I[210], H[210], H[150]), "lavender"),
        (tri(I[210], H[270], H[210]), "violet"),
        (tri(I[330], H[330], H[270]), "violet"),
        (tri(I[330], H[30], H[330]), "violet"),
    ], H, I


def _edges(H, I):
    """Every face edge inside the rim: the centre face's three, then the nine radial ones."""
    return [(I[90], I[210]), (I[210], I[330]), (I[330], I[90]),
            (I[90], H[90]), (I[90], H[150]), (I[90], H[30]),
            (I[210], H[150]), (I[210], H[210]), (I[210], H[270]),
            (I[330], H[270]), (I[330], H[330]), (I[330], H[30])]


def _sparkle(x, y, r):
    return star(4, r, r * 0.26, x, y, rot=90)


def art():
    d = Design()
    fs, H, I = faces()
    die = regular_polygon(6, R, 0, CY, rot=90)
    num = block_text("20", cap=12.5, stroke=2.4, tracking=1.2)
    x0, y0, x1, y1 = num.bounds
    num = move(num, -(x0 + x1) / 2, CY - 1.5 - (y0 + y1) / 2)
    word = block_text("NAT 20", cap=12, stroke=2.4, tracking=1.8)
    x0, y0, x1, y1 = word.bounds
    word = move(word, -(x0 + x1) / 2, -40 - y0)
    solid = union(*[poly(list(g.exterior.coords)) for g in polygons_of(word)])
    shadow = knockout(move(word, 1.0, -1.0), solid)      # never inside a counter
    sparkles = [_sparkle(-36, 38, 6.0), _sparkle(37, -16, 4.5)]

    # the faces stop under the gold edges and rim (0.4 mm overlap), so corners where
    # several edges meet the rim are not fill + satin + satin deep
    from shapely.geometry import LineString
    centre = poly([tuple(I[a]) for a in (90, 210, 330)])
    radial = []
    for a, b in _edges(H, I)[3:]:
        u = (b - a) / np.linalg.norm(b - a)
        radial.append((a + u * 1.6, b - u * 1.4))
    bands = union(*[LineString([tuple(a), tuple(b)]).buffer(0.7, cap_style="flat") for a, b in radial],
                  centre.exterior.buffer(0.7), die.exterior.buffer(1.1))
    for shade, angle in (("lavender", 60), ("lilac", 0), ("violet", 120)):
        for g, sh in fs:
            if sh == shade:
                d.fill(knockout(g, num, bands), C_[shade], angle=angle, name=f"{shade} face")
    d.fill(shadow, C_["purple"], angle=45, spacing=0.4, name="shadow")
    # the centre face's edges as one continuous ring; the radial edges stop short of
    # the ring and of the rim so five columns never pile into one vertex
    d.outline(centre, C_["gold"], width=1.4, name="centre edge")
    for a, b in radial:
        d.satin(line(tuple(a), tuple(b)), 1.4, C_["gold"], name="edge", underlay="center")
    d.outline(die, C_["gold"], width=2.2, name="rim")
    d.fill(num, C_["gold"], angle=0, spacing=0.35, name="numeral")
    d.fill(word, C_["gold"], angle=0, spacing=0.35, name="NAT 20")
    for g in sparkles:
        d.fill(g, C_["gold"], angle=45, name="sparkle")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
