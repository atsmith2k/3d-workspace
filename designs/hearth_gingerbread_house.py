"""Gingerbread House: an iced gingerbread house with gumdrops and a peppermint.

Spec:
  object:       gingerbread house for kids' wear, aprons, tea towels, sweatshirts
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens (aprons, towels) with tear-away
  threads:      ginger (walls), cocoa (chocolate roof), gold (windows), pink (door),
                red (gumdrops, peppermint), green (gumdrops), white (scalloped icing
                eaves, wall edge, window frames, peppermint stripes): 7 colours
  must have:    a 44 mm wide house with a gable; a 7.2 mm thick chocolate roof with
                alternating red and green gumdrops; a 1.6 mm white satin icing scallop
                under the eaves and a 1.4 mm icing edge round the walls; two gold windows
                with icing frames; an arched pink door; a 8.4 mm peppermint in the gable
  density:      details and the eave icing knock out the walls and roof; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Iced gingerbread house with a chocolate roof, gumdrops and a peppermint"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Gingerbread House Embroidery Design",
    "An iced gingerbread house with gumdrops, a chocolate roof and a peppermint",
    ["gingerbread house", "gingerbread", "christmas baking", "christmas candy", "kids christmas",
     "christmas apron"],
    "A sweet gingerbread house with a chocolate roof dotted with gumdrops, scalloped white "
    "icing, glowing windows, a pink candy door and a peppermint in the gable.\n\nGreat on kids' "
    "wear, aprons, tea towels and sweatshirts.",
    mockups=("tshirt", "tote"),
)

HALF = 22.0


def checks(p):
    return standard_checks(p, 7, 13000)


def _roof_line(t):
    """Point on the roof's centre line, t in 0..1 from the left eave to the right."""
    a, b, c = np.array([-29.0, -2.0]), np.array([0.0, 22.0]), np.array([29.0, -2.0])
    return a + (b - a) * (2 * t) if t <= 0.5 else b + (c - b) * (2 * t - 1)


def art():
    d = Design()
    walls = union(rect(2 * HALF, 28, 0, -14), poly([(-HALF, -0.1), (0, 18), (HALF, -0.1)]))
    roof = LineString([_roof_line(0), _roof_line(0.5), _roof_line(1)]).buffer(3.6, cap_style="flat",
                                                                              join_style="mitre")
    # icing scallop just under the roof's lower edge
    pts = []
    for t in np.linspace(0.02, 0.98, 120):
        p = _roof_line(t)
        n = np.array([0, -1.0])
        drip = 1.4 * abs(np.sin(np.pi * t * 12))
        pts.append(p + n * (4.6 + drip))
    icing = np.array(pts)
    icing_geom = LineString(icing).buffer(0.8)
    edge_ring = np.array(rounded_rect(2 * HALF, 30, 3, 0, -13).exterior.coords)
    edge = edge_ring[edge_ring[:, 1] < -2.5]
    edge = edge[np.argsort(np.arctan2(edge[:, 1] + 13, edge[:, 0]))]
    windows = [rounded_rect(8, 8, 1.4, -11, -9), rounded_rect(8, 8, 1.4, 11, -9)]
    door = union(rect(10, 9, 0, -23.5), circle(0, -19, 5))
    pep = circle(0, 6.0, 4.2)
    stripes = union(*[rotate(rect(1.6, 9, 0, 6.0), 45 * k, origin=(0, 6.0)) for k in range(4)]).intersection(pep)
    stripes = stripes.difference(circle(0, 6.0, 1.0))
    drops = []
    for k, t in enumerate(np.r_[np.linspace(0.08, 0.40, 4), np.linspace(0.60, 0.92, 4)]):
        x, y = _roof_line(t)
        drops.append((circle(x, y, 2.3), "red" if k % 2 == 0 else "green"))
    d.fill(knockout(walls, roof, icing_geom, *[grow(w, 0.6) for w in windows], door, pep), C_["ginger"], angle=80, name="walls")
    d.fill(knockout(roof, *[g for g, _ in drops]), C_["cocoa"], angle=0, name="chocolate roof")
    for g in windows:
        d.fill(tuck(g, 1.2), C_["gold"], angle=45, name="window")
    d.fill(door, C_["pink"], angle=90, name="door")
    d.fill(knockout(pep, stripes), C_["red"], angle=None, name="peppermint")
    for g, c in drops:
        if c == "red":
            d.fill(g, C_["red"], angle=45, underlay=False, name="gumdrop")
    for g, c in drops:
        if c == "green":
            d.fill(g, C_["green"], angle=45, underlay=False, name="gumdrop")
    d.satin(icing, 1.6, C_["white"], name="icing", trim_after=True)
    d.satin(edge, 1.4, C_["white"], name="wall icing", trim_after=True)
    for g in windows:
        d.outline(g, C_["white"], width=1.2, name="window icing")
    d.fill(stripes, C_["white"], angle=None, underlay=False, name="peppermint stripes")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
