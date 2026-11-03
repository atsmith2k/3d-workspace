"""Dragon's Hoard: a red dragon curled asleep on a mound of gold inside a mountain, the
patch cut to the mountain's peaks.

Spec:
  object:       an old dragon sleeping on a stolen treasure under the mountain (an
                original dragon, no film creature) for tees, hoodies, totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens, canvas and patches with tear-away
  threads:      charcoal (cave), pewter (rock seams), gold (hoard), brass (coin rims),
                yellow (glints), red (dragon), wine (wing, far legs, belly plates),
                black (line art: outlines, closed eye, mouth, wing fingers), silver (border): 9 colours
  must have:    a mountain-shaped patch 92 mm wide with three peaks and a 2.6 mm silver
                satin border; a dark cave inside with pewter rock seams; a gold hoard
                mound across the bottom with brass coin rims and four yellow glints; a red
                dragon 66 mm long curled on the hoard asleep: a thick coiled body, head
                resting on the gold with its eye closed (black line), two swept horns,
                a folded wine wing with three black finger lines, back spikes, a tail wrapped round
                the front ending in a spade, wine belly plates
  density:      the cave is knocked out under the hoard and dragon, the hoard under the
                dragon; fills tucked under the border; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString
from shapely.geometry import Point as Point_

from cadkit.stitch import *

from _kingdom import (C_, SIZES, fit, hoop_for, pieces, product, standard_checks, trim_path, tube,
                      widths_along)

DESCRIPTION = "Red dragon curled asleep on a gold hoard inside a mountain-shaped patch"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Dragon's Hoard Embroidery Design",
    "A red dragon curled asleep on a mound of gold coins deep inside the mountain",
    ["dragon", "sleeping dragon", "dragon hoard", "treasure", "gold coins", "mountain",
     "dragon embroidery", "dungeon", "dragon lair", "adventure"],
    "Tread softly: deep under the mountain an old red dragon lies curled asleep on a "
    "glittering hoard of gold, wing folded, tail wrapped round the treasure, on a patch "
    "cut to the mountain's three peaks.\n\n"
    "Great on hoodies, tees, tote bags, jackets and adventure patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 9, 24000)


BW = 2.6


def mountain():
    pts = [(-46, -40), (-46, -4), (-33, 13), (-24, 9), (-2, 42), (16, 24), (27, 31), (46, 6), (46, -40)]
    return poly(pts).buffer(-3.0, join_style="round").buffer(3.0, join_style="round")


def hoard():
    top = spline([(-47, -20), (-34, -17), (-20, -14), (-4, -15.5), (12, -13.5), (28, -16.5),
                  (40, -19), (47, -22)], samples=8)
    return poly([tuple(q) for q in top] + [(47, -50), (-47, -50)])


def dragon():
    """A dragon curled like a sleeping cat: body, neck and head resting on the gold at the
    front, the tail wrapped round under its chin, the wing folded over its back."""
    body = smooth([(-8.0, 0.0), (-2.0, 8.5), (10.0, 11.5), (22.0, 9.0), (30.5, 2.0),
                   (32.0, -8.0), (26.0, -15.5), (12.0, -17.0), (0.0, -16.0), (-7.0, -11.0)], samples=8)
    neck_p = spline([(-3.0, 3.0), (-12.0, 4.0), (-20.0, 0.5), (-24.0, -6.0)], samples=10)
    neck = tube(neck_p, widths_along(neck_p, 11.0, 9.0, 7.5, 6.6))
    head = smooth([(-28.5, -9.0), (-22.5, -8.0), (-16.5, -10.5), (-10.0, -13.0), (-7.6, -15.6),
                   (-9.4, -18.2), (-17.0, -19.0), (-25.0, -18.4), (-29.5, -14.5)], samples=8)
    horns = [tube(spline([(-25.5, -9.0), (-30.0, -5.4), (-35.5, -4.6)], samples=8), [3.0, 2.0, 1.2]),
             tube(spline([(-22.5, -8.6), (-25.0, -3.2), (-29.5, -0.2)], samples=8), [2.8, 1.9, 1.1])]
    tail_p = spline([(26.0, -7.0), (30.5, -12.0), (30.0, -18.5), (23.0, -23.0), (12.0, -24.0),
                     (0.0, -22.6), (-4.5, -21.6)], samples=10)
    tail_w = widths_along(tail_p, 3.5, 3.5, 3.4, 3.2, 2.8, 2.3, 1.8)   # under 7 mm at 5x7, round the bend too
    spade = poly([(-3.0, -21.0), (-6.5, -18.6), (-10.5, -22.0), (-6.4, -25.0)]).buffer(0.4).buffer(-0.4)
    paw = ellipse(-31.6, -19.0, 3.2, 1.8)
    wing = smooth([(-4.0, 6.0), (1.0, 13.5), (7.0, 19.0), (12.0, 19.5), (19.0, 16.0), (29.0, 9.0),
                   (25.0, 6.0), (21.0, 7.5), (17.5, 4.0), (12.5, 5.5), (8.5, 1.5), (2.5, 3.0)], samples=6)
    ribs = [spline([(7.5, 17.6), (17.0, 12.0), (25.5, 7.4)], samples=8),
            spline([(6.5, 16.8), (12.0, 10.5), (17.4, 5.2)], samples=8),
            spline([(5.5, 16.0), (7.5, 9.5), (8.8, 2.8)], samples=8)]
    arm = spline([(-2.0, 6.6), (2.5, 13.0), (8.0, 18.2), (14.0, 18.4), (28.0, 9.2)], samples=8)
    spikes = []
    for (x, y), ang in zip([(-10.5, 8.2), (-17.0, 6.0), (-22.0, 1.6)], (100, 125, 150)):
        a = math.radians(ang)
        tip = (x + 3.4 * math.cos(a), y + 3.4 * math.sin(a))
        tg = (math.cos(a - math.pi / 2) * 1.7, math.sin(a - math.pi / 2) * 1.7)
        spikes.append(poly([(x - tg[0], y - tg[1]), tip, (x + tg[0], y + tg[1])]))
    for x, y in [(29.0, 2.6), (31.4, -3.4)]:
        spikes.append(poly([(x - 1.8, y - 1.2), (x + 2.2, y + 2.4), (x + 1.4, y - 1.8)]))
    body_all = union(body, neck, *horns, paw)
    return dict(body=body_all, head=head, tail=(tail_p, tail_w), spade=spade, wing=wing, ribs=ribs,
                arm=arm, spikes=union(*spikes))


COINS = [(-38, -26, 3.4), (-30, -33, 3.2), (-24, -24, 3.0), (-11, -27, 3.4), (-2, -34, 3.0),
         (8, -26, 3.2), (14, -34, 3.0), (40, -28, 3.2), (34, -36, 3.0), (-20, -36, 3.0),
         (22, -21, 2.8), (-38, -36, 3.0)]
GLINTS = [(-28, -19), (2, -22), (44, -24), (-12, -38)]


DK, DO = 1.14, (2.0, -17.0)       # the dragon is drawn smaller, then scaled about its belly


def T(g):
    if isinstance(g, np.ndarray):
        return (g - DO) * DK + DO
    return scale(g, DK, DK, origin=DO)


def art():
    d = Design()
    mtn = mountain()
    inner = tuck(mtn, BW)
    gold = hoard() & mtn
    dr = dragon()
    body, head = T(dr["body"]), T(dr["head"])
    tail_p, tail_w = T(dr["tail"][0]), dr["tail"][1] * DK
    tail = tube(tail_p, tail_w)
    spade, wing, spikes = T(dr["spade"]), T(dr["wing"]), T(dr["spikes"])
    ribs = [T(r) for r in dr["ribs"]]
    arm = T(dr["arm"])
    beast = union(body, head, tail, spade, wing, spikes)

    # cave, rock seams
    d.fill(knockout(inner, gold, beast), C_["charcoal"], angle=60, name="cave")
    seams = [spline([(-42, -2), (-34, 4), (-26, 2), (-20, 9)], samples=8),
             spline([(-14, 22), (-6, 26), (2, 24), (8, 30)], samples=8),
             spline([(22, 14), (30, 10), (40, 4)], samples=8),
             spline([(-40, -12), (-33, -10), (-27, -13)], samples=8)]
    for sm in seams:
        for q in pieces(LineString(sm).intersection(inner.buffer(-1.5).difference(beast.buffer(1.0))), 3.0):
            d.run(q, C_["pewter"], bean=1, length=1.8, name="rock seam", trim_after=True)
    # hoard: gold mound, coin rims, glints
    coins = [circle(x, y, r) for x, y, r in COINS]
    glints = [star(4, 3.0, 0.9, x, y, rot=90) for x, y in GLINTS]
    gold_in = gold & inner
    d.fill(knockout(gold_in, beast, *glints), C_["gold"], angle=20, name="hoard")
    for c in coins:
        ring_ = LineString(np.asarray(c.exterior.coords)).intersection(gold_in.buffer(-1.2).difference(beast.buffer(1.0)))
        for q in pieces(ring_, 3.0):
            d.run(q, C_["brass"], bean=1, length=1.2, name="coin rim", trim_after=True)
    for g in glints:
        d.fill(g, C_["yellow"], angle=45, name="glint")
    # dragon: body, head, tail, spikes in red; wing in wine with red ribs
    rib_paths = [trim_path(r, 1.8, 0.4) for r in ribs]
    rib_w = [widths_along(r, 1.4, 1.1) for r in rib_paths]
    arm_p = trim_path(arm, 0.8, 1.0)
    arm_w = widths_along(arm_p, 1.8, 2.2, 1.8, 1.2)
    struts = tube(arm_p, arm_w)
    d.fill(knockout(spikes, body, head), C_["red"], angle=90, name="spikes")
    tail_cut = tube(trim_path(tail_p, 3.5, 0.0), tail_w[2:])
    d.fill(knockout(body, head, tail_cut, wing), C_["red"], angle=120, name="body")
    d.fill(head, C_["red"], angle=20, name="head")
    d.satin(tail_p, tail_w, C_["red"], taper=True, underlay="center", name="tail")
    d.fill(knockout(spade, tail), C_["red"], angle=60, name="tail spade")
    d.fill(wing, C_["wine"], angle=150, name="wing")
    # black line art: outlines front to back, closed eye, nostril, wing finger lines
    lines = []
    lines += [np.asarray(r) for r in outline_paths(head)]
    root = Point_(*tail_p[0]).buffer(5.0)          # the tail grows out of the body: no line round its root
    lines += pieces(LineString(np.asarray(outline_paths(tail)[0])).difference(union(head, root).buffer(0.3)), 2.0)
    lines += pieces(LineString(np.asarray(outline_paths(wing)[0])).difference(head.buffer(0.3)), 2.0)
    for ring_pts in outline_paths(union(body, spade, spikes)):
        lines += pieces(LineString(np.asarray(ring_pts)).difference(union(head, tail, wing).buffer(0.3)), 2.0)
    lines += [np.asarray(r) for r in rib_paths]
    for ln in lines:
        d.run(ln, C_["black"], bean=1, length=1.4, name="line", trim_after=True)
    eye = T(bezier((-21.0, -12.8), (-19.6, -14.0), (-17.6, -14.0), (-16.4, -12.6), 10))
    d.run(eye, C_["black"], bean=1, length=1.0, name="closed eye", trim_after=True)
    mouth = T(spline([(-9.2, -16.4), (-13.0, -16.6), (-17.5, -16.0)], samples=6))
    d.run(mouth, C_["black"], bean=1, length=1.2, name="mouth", trim_after=True)
    d.outline(mtn, C_["silver"], width=BW, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
