"""Holly Wreath: a ring of holly leaves in two greens with red berries and a red bow.

Spec:
  object:       classic Christmas wreath for front-door banners, tea towels, stockings,
                sweatshirts and framed hoops (the middle is open for a name or monogram)
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7), round
  fabric:       knits with cut-away; wovens and towels with tear-away (+ topper on towels)
  threads:      pine (dark leaves), leaf (light leaves and the dark leaves' veins), red
                (berries and bow), berry (bow shading folds): 4 colours
  must have:    20 spiky holly leaves round a 34 mm radius ring, alternating dark and
                light and tilting in and out; clusters of three berries (2.4 mm radius)
                between every other pair; a 40 mm bow at the bottom with tails
  density:      light leaves knock out the dark ones, berries and bow knock out the
                leaves; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Holly-leaf wreath with red berry clusters and a red bow"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Holly Wreath Embroidery Design",
    "A holly wreath with red berries and a bow, open in the middle for a name",
    ["holly wreath", "christmas wreath", "monogram frame", "holly berries", "christmas towel"],
    "A traditional holly wreath: sixteen spiky leaves in two greens, clusters of red berries and a "
    "red ribbon bow. The middle is left open so you can add a name, initial or year.\n\nGreat on "
    "tea towels, stockings, door banners and sweatshirts.",
    mockups=("tote", "tshirt"),
)


def checks(p):
    return standard_checks(p, 4, 12000)


def _place(g, x, y, deg):
    return move(rotate(g, deg, origin=(0, 0)), x, y)


def art():
    d = Design()
    RING, N, L = 34.0, 20, 22.0
    leaves, veins = [], []
    for i in range(N):
        t = 90 + 360 * (i + 0.5) / N                         # around the ring
        tilt = 22 if i % 2 else -22                          # in and out of the ring
        a = math.radians(t)
        x, y = RING * math.cos(a), RING * math.sin(a)
        deg = t + 90 + tilt                                  # along the ring, counter-clockwise
        leaf = M.holly_leaf(L, L * 0.46, spikes=3)
        leaf = move(leaf, -L / 2, 0)
        vein = M.holly_vein(L) - np.array([L / 2, 0])
        leaves.append(_place(leaf, x, y, deg))
        r = math.radians(deg)
        rot = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
        veins.append(vein @ rot.T + np.array([x, y]))
    bow_y = -RING - 2
    dark = [leaves[i] for i in range(N) if i % 2 == 0]
    light = [leaves[i] for i in range(N) if i % 2 == 1]
    berries = []
    for i in range(0, N, 2):
        a = math.radians(90 + 360 * i / N)
        cx, cy = (RING + 1) * math.cos(a), (RING + 1) * math.sin(a)
        for k in range(3):
            b = math.radians(90 + 120 * k + 360 * i / N)
            berries.append(circle(cx + 2.6 * math.cos(b), cy + 2.6 * math.sin(b), 2.4))
    lo, ro, knot, lt, rt = M.bow(40)
    bow = [move(g, 0, bow_y) for g in (lo, ro, knot, lt, rt)]
    bow_all = union(*bow)
    berries = [b for b in berries if b.distance(bow_all) > 1.0]
    top_of_dark = union(*light, *berries, bow_all)
    for g in dark:
        d.fill(knockout(g, top_of_dark), C_["pine"], angle=None, name="dark leaf")
    on_light = union(*berries, bow_all)
    for g in light:
        d.fill(knockout(g, on_light), C_["leaf"], name="light leaf")
    for i in range(0, N, 2):
        v = veins[i]
        if LineString(v).distance(bow_all) > 1.5:
            d.run(v, C_["leaf"], bean=1, name="vein", trim_after=True)
    for b in berries:
        d.fill(b, C_["red"], angle=45, underlay=False, name="berry")
    lo, ro, knot, lt, rt = bow
    d.fill(knockout(lt, lo, ro, knot), C_["red"], angle=75, name="tail")
    d.fill(knockout(rt, lo, ro, knot), C_["red"], angle=105, name="tail")
    d.fill(knockout(lo, knot), C_["red"], angle=150, name="loop")
    d.fill(knockout(ro, knot), C_["red"], angle=30, name="loop")
    for side in (-1, 1):                                    # the loops' inner folds
        fold = spline(np.array([(side * 4.0, bow_y + 1.5), (side * 9.0, bow_y + 4.5), (side * 14.0, bow_y + 4.0)]), 8)
        d.run(fold, C_["berry"], bean=1, name="fold", trim_after=True)
    d.fill(knot, C_["berry"], angle=90, name="knot")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
