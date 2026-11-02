"""Cozy Cabin: an arch-framed autumn scene, a log cabin among pines and fall trees.

Spec:
  object:       scene badge for pillows, framed hoops, jacket backs (5x7), totes
  overall:      `size` mm tall (95 for 4x4, 160 for 5x7), about 0.78 as wide, arch-shaped
  fabric:       medium wovens with tear-away; the sky is a light 0.5 mm fill, so knits
                take a medium cut-away
  threads:      cream (sky), mustard (sun, mustard tree, lit window), moss (far hills),
                olive (near hill, pines), rust (maple tree, drifting leaves), caramel
                (cabin logs), cranberry (roof), wheat (path, smoke), bark (trunks,
                chimney, door, log lines, window panes, arch border): 9 colours
  must have:    an arch frame with a 2.4 mm satin border, every element kept inside it;
                a light sky fill; a low sun behind two layers of hills; a log cabin with
                a roof, chimney, door, lit window with panes and log lines; chimney
                smoke; three pines of three sizes; two round autumn trees; a winding
                path that widens toward the viewer; three drifting leaves
  density:      every layer knocked out under the ones in front; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Log cabin among pines and autumn trees in an arch-framed dusk scene"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = dict(
    title="Cozy Autumn Cabin Scene Embroidery Design",
    summary="A log cabin among pines and fall trees at dusk, in an arch frame",
    tags=["fall embroidery", "cabin embroidery design", "autumn scene", "landscape", "cozy cabin"],
    collection=COLLECTION,
    mockups=['tote', 'tshirt'],
    description=(
        'An arch-framed autumn scene: a log cabin with a cranberry roof, a glowing window and chimney smoke, set among pines and two round fall trees in rust and gold, with a winding path to the door, a low sun behind rolling hills and leaves drifting across a soft dusk sky.\n\nThe showpiece of the collection, for pillows, framed hoops, jacket backs and totes.'
    ),
)


def checks(p):
    return standard_checks(p, 9, 30000)


def arch_shape(w=70.0, bottom=-45.0, shoulder=10.0):
    r = w / 2
    t = np.linspace(0, math.pi, 90)
    top = np.c_[r * np.cos(t), shoulder + r * np.sin(t)]
    return Polygon(np.vstack([[(r, bottom)], top, [(-r, bottom)]]))


def pine(x, y, h, tiers=3):
    """(foliage, trunk) for a pine whose trunk base is at (x, y)."""
    parts = []
    for k in range(tiers):
        f = k / tiers
        w = h * (0.55 - 0.13 * k)
        y0 = y + h * 0.12 + h * 0.26 * k
        parts.append(Polygon([(x - w / 2, y0), (x + w / 2, y0), (x, y0 + h * 0.42)]))
    trunk = rect(h * 0.09, h * 0.18, x, y + h * 0.07)
    return unary_union(parts).buffer(0.3).buffer(-0.3), trunk


def round_tree(x, y, h, r):
    crown = unary_union([circle(x, y + h, r), circle(x - r * 0.55, y + h - r * 0.35, r * 0.7),
                         circle(x + r * 0.55, y + h - r * 0.3, r * 0.72)])
    trunk = Polygon([(x - 0.9, y), (x + 0.9, y), (x + 0.6, y + h - r * 0.5), (x - 0.6, y + h - r * 0.5)])
    return crown, trunk


def art():
    d = Design()
    arch = arch_shape()
    inner = arch.buffer(-1.0)
    clip = lambda g: g.intersection(inner)
    sun = clip(circle(15, 2, 9.5))
    far = clip(Polygon(np.vstack([[(-40, -30)], np.c_[np.linspace(-40, 40, 40), 2 + 3.5 * np.sin(np.linspace(0, 5.5, 40))], [(40, -30)]])))
    near = clip(Polygon(np.vstack([[(-40, -50)], np.c_[np.linspace(-40, 40, 40), -12 + 6 * np.cos(np.linspace(0.3, 3.4, 40))], [(40, -50)]])))
    # path from the door widening toward the bottom edge
    pc = spline([(-9, -24), (-6, -30), (4, -35), (2, -41), (-4, -47)], samples=10)
    tw = np.linspace(3.0, 13.0, len(pc))
    dl = np.gradient(pc, axis=0)
    nrm = np.c_[-dl[:, 1], dl[:, 0]] / np.linalg.norm(dl, axis=1, keepdims=True)
    path = clip(Polygon(np.vstack([pc + nrm * tw[:, None] / 2, (pc - nrm * tw[:, None] / 2)[::-1]])).buffer(0))
    # cabin
    body = rect(24, 14, -7, -17)
    roof = Polygon([(-21.5, -10.5), (7.5, -10.5), (-7, 1.5)]).buffer(0.4).buffer(-0.4)
    chimney = rect(3.6, 9, 1.5, -3)
    door = rect(5, 8.5, -12, -19.75)
    window = rect(6, 5.5, -1.5, -16)
    cabin = unary_union([body, roof, chimney])
    pines = [pine(-24, -14, 27), pine(26, -15, 21), pine(32, -6, 12, 3)]
    trees = [round_tree(13, -13, 13, 5.8), round_tree(-17, -6, 9, 4.2)]     # the far tree tucks behind the pine
    leaves = [move(rotate(M.leaf(5.5, 2.7, 0.3), a, origin=(0, 0)), x, y) for x, y, a in ((-18, 30, 40), (-6, 37, -30), (22, 26, 110))]

    fg = unary_union([cabin, path] + [p for pr in pines for p in pr] + [t for tr in trees for t in tr])
    d.fill(knockout(inner, sun, far, near, fg, *leaves, chimney, overlap=0.0), C_["cream"], angle=0, spacing=0.50, name="sky")
    # mustard: sun, far tree crown, lit window
    d.fill(knockout(sun, far, near, fg, overlap=0.0), C_["mustard"], angle=0, name="sun")
    far_crown, far_trunk = trees[1]
    d.fill(knockout(clip(far_crown), pines[0][0], cabin, overlap=0.0), C_["mustard"], angle=40, name="mustard tree")
    d.fill(window, C_["mustard"], angle=90, underlay=False, name="window glow")
    d.fill(knockout(far, near, fg, overlap=0.0), C_["moss"], angle=10, name="far hills")
    d.fill(knockout(near, cabin, path, *[p for pr in pines for p in pr], *trees[0], overlap=0.0), C_["olive"], angle=-8, name="near hill")
    for fol, trunk in pines:
        d.fill(knockout(clip(fol), cabin, overlap=0.0), C_["olive"], angle=90, name="pine")
    crown, trunk = trees[0]
    d.fill(knockout(clip(crown), pines[1][0], overlap=0.0), C_["rust"], angle=-40, name="maple tree")
    for k, lf in enumerate(leaves):
        d.fill(lf, C_["rust"] if k != 1 else C_["rust"], angle=30 + 50 * k, underlay=False, name="drifting leaf")
    d.fill(knockout(body, door, window, roof, overlap=0.0), C_["caramel"], angle=0, name="cabin logs")
    d.fill(roof, C_["cranberry"], angle=-20, name="roof")
    d.fill(knockout(path, cabin, overlap=0.0), C_["wheat"], angle=90, name="path")
    smoke = bezier((1.5, 2.5), (-3, 9), (6, 14), (1, 22), 20)
    d.run(smoke, C_["wheat"], bean=1, length=1.5, name="smoke")
    # bark: trunks, chimney, door, log lines, panes, border
    for fol, trunk in pines:
        d.fill(knockout(clip(trunk), cabin, overlap=0.0), C_["bark"], angle=90, underlay=False, name="trunk")
    for crown, trunk in trees:
        t = knockout(trunk, crown, cabin, overlap=0.0)
        if not t.is_empty:
            d.fill(t, C_["bark"], angle=90, underlay=False, name="trunk")
    d.fill(knockout(chimney, roof, overlap=0.0), C_["bark"], angle=90, name="chimney")
    d.fill(door, C_["bark"], angle=90, name="door")
    bx0, by0, bx1, by1 = body.bounds
    logs_area = knockout(body, door, window.buffer(0.8), roof, overlap=0.0).buffer(-0.3)
    for y in np.arange(by0 + 2.4, by1 - 0.8, 2.4):          # one run per log seam
        lines = LineString([(bx0 + 0.6, y), (bx1 - 0.6, y)]).intersection(logs_area)
        for part in getattr(lines, "geoms", [lines]):
            if part.geom_type == "LineString" and part.length > 2:
                d.run(np.asarray(part.coords), C_["bark"], length=1.6, name="log seam", trim_after=True)
    wx0, wy0, wx1, wy1 = window.bounds
    d.run(np.array([[wx0, (wy0 + wy1) / 2], [wx1, (wy0 + wy1) / 2], [(wx0 + wx1) / 2, (wy0 + wy1) / 2],
                    [(wx0 + wx1) / 2, wy1], [(wx0 + wx1) / 2, wy0]]), C_["bark"], length=1.2, name="window panes")
    d.outline(arch, C_["bark"], width=2.4, name="arch border")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
