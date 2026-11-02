"""Harvest Moon Owl: a barn owl on an oak branch in front of a big harvest moon.

Spec:
  object:       night scene for pillows, sweatshirts, framed hoops, tote bags
  overall:      `size` mm wide (95 for 4x4, 160 for 5x7), about 0.75 as tall
  fabric:       medium wovens and sweatshirt fleece; cut-away under the moon fill on knits
  threads:      cream (moon), olive + rust (oak leaves), caramel (owl back, head, wings,
                acorn nuts), wheat (moon craters, feather scallops), white (breast, face
                disc), bark (branch, face rim, beak, chevrons, acorn caps, leaf veins),
                charcoal (eyes, talons): 8 colours
  must have:    a moon disc behind everything, filled light (0.5 mm rows) to keep it soft,
                with faint craters;
                a tapered branch with two twigs, three oak leaves and two acorns; the owl
                with a heart-shaped white face and dark rim, two eyes with highlights left
                open in the eye fill, a beak, a cream breast with chevron marks, two wings
                with three rows of feather scallops, talons gripping the branch
  density:      everything knocked out where hidden; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Barn owl on an oak branch against a harvest moon"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = dict(
    title="Harvest Moon Owl Embroidery Design",
    summary="A barn owl on an oak branch against a big harvest moon",
    tags=["fall embroidery", "owl embroidery design", "harvest moon", "woodland", "halloween embroidery"],
    collection=COLLECTION,
    mockups=['tshirt', 'tote'],
    description=(
        'A barn owl perches on an oak branch in front of a pale harvest moon. Its heart-shaped white face is ringed in brown, the dark eyes keep their highlights, the white breast carries chevron markings and the golden wings are layered with rows of feather scallops. Oak leaves and acorns hang from the branch, and faint craters mark the moon, which is filled with an open stitch so it stays soft.\n\nFor pillows, sweatshirts, framed hoops and Halloween-to-Thanksgiving decor.'
    ),
)


def checks(p):
    return standard_checks(p, 8, 26000)


def band(center, widths):
    c = np.asarray(center, float)
    dlt = np.gradient(c, axis=0)
    n = np.c_[-dlt[:, 1], dlt[:, 0]]
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    w = np.asarray(widths)[:, None] / 2
    return Polygon(np.vstack([c + n * w, (c - n * w)[::-1]])).buffer(0).buffer(0.6).buffer(-0.6)


def wing(sign):
    """A wing hanging down one side of the body, as a curved leaf shape."""
    g = M.leaf(30, 11, bend=0.18 * sign)
    g = rotate(g, 180 + 10 * sign, origin=(0, 0))      # pointing down
    return move(g, -2 + 12.5 * sign, 11)


def art():
    d = Design()
    moon = circle(0, 9, 36, res=180)
    # branch and twigs
    br_c = spline([(-52, -24), (-25, -21), (0, -21.5), (25, -18.5), (50, -12)], samples=12)
    branch = band(br_c, np.linspace(6.5, 3.6, len(br_c)))
    twig1 = band(spline([(28, -18), (35, -10), (40, -4)], samples=8), np.linspace(2.6, 1.6, 17))
    twig2 = band(spline([(-38, -22.5), (-45, -30), (-49, -33)], samples=8), np.linspace(2.6, 1.6, 17))
    wood = unary_union([branch, twig1, twig2])
    leaves = [(C_["olive"], move(rotate(M.oak_leaf(20, 4), -40, origin=(0, 0)), 40, -4), -40),
              (C_["rust"], move(rotate(M.oak_leaf(18, 4), -95, origin=(0, 0)), 46, -12), -95),
              (C_["olive"], move(rotate(M.oak_leaf(17, 4), 140, origin=(0, 0)), -48, -33), 140)]
    acorns = []
    for x, rot in ((20, -8), (31.5, 10)):              # apart, so no pocket of fabric is trapped
        nut, cap, stem = M.acorn(11)
        f = lambda g, x=x, rot=rot: move(rotate(g, 180 + rot, origin=(0, 0)), x, -25)
        acorns.append((f(nut), f(cap), f(stem)))
    # owl
    body = ellipse(-2, -3, 15, 19)
    head = circle(-2, 19, 13.5)
    owl = unary_union([body, head])
    face = move(heart(24), -2, 18.5)                # a barn owl's heart: point at the chin
    face = face.intersection(head.buffer(-0.8))
    # eyes kept 1.5 mm inside the face edge: a thinner rim of face would be dropped
    eyes = [circle(x, 19.3, 3.1) for x in (-6.8, 2.8)]
    glints = [circle(x + 0.9, 20.2, 1.05) for x in (-6.8, 2.8)]
    beak = Polygon([(-2, 16.2), (-0.7, 13.5), (-2, 11.2), (-3.3, 13.5)])
    breast = ellipse(-2, -6, 10, 13.5).intersection(body.buffer(-0.5))
    wings = [wing(-1), wing(1)]
    talons = [band(np.array([[x + dx, -19.5], [x + dx * 1.6, -22.5]]), [1.4, 1.2]) for x in (-8, 4) for dx in (-1.6, 0, 1.6)]
    front = unary_union([owl, *wings])

    acorn_all = unary_union([unary_union([n, c]) for n, c, _ in acorns])
    leaf_all = unary_union([l for _, l, _ in leaves])
    d.fill(knockout(moon, front, wood, leaf_all, acorn_all), C_["cream"], angle=0, spacing=0.50, name="moon")
    for tone in (C_["olive"], C_["rust"]):
        for tn, lf, a in leaves:
            if tn == tone:
                d.fill(knockout(lf, wood, overlap=0.0), tone, angle=a + 120, name="oak leaf")
    # owl back first, then wings over it, then the face and breast
    d.fill(knockout(owl, face, breast, *wings, overlap=0.0), C_["caramel"], angle=80, name="owl back")
    for k, w in enumerate(wings):
        d.fill(w, C_["caramel"], angle=100 if k else 80, name="wing")
    for nut, cap, stem in acorns:
        d.fill(knockout(nut, cap, overlap=0.0), C_["caramel"], angle=70, name="acorn")
    hidden = unary_union([front, wood, leaf_all, acorn_all]).buffer(1.0)
    for cx, cy, r in ((-22, 30, 4.5), (20, 30, 3.2), (24, 14, 2.4), (-26, 4, 3.0), (14, 35, 2.0)):
        crater = LineString(arc(cx, cy, r, 150, 330, 6)).difference(hidden)   # faint crater rims
        for part in getattr(crater, "geoms", [crater]):
            if part.geom_type == "LineString" and part.length > 3:
                d.run(np.asarray(part.coords), C_["wheat"], length=1.6, name="crater", trim_after=True)
    for k, w in enumerate(wings):                         # three rows of feather scallops
        sign = 1 if k else -1
        for row, y in enumerate((4, -4, -12)):
            xs = np.linspace(-2 + sign * 8.5, -2 + sign * 16.5, 5)
            pts = []
            for x in xs:
                pts += [(x - 1.0, y), (x, y - 1.6), (x + 1.0, y)]
            clip = LineString(pts).intersection(w.buffer(-1.0))
            for part in getattr(clip, "geoms", [clip]):
                if part.geom_type == "LineString" and part.length > 2:
                    d.run(np.asarray(part.coords), C_["wheat"], length=1.0, name="feather scallops", trim_after=True)
    d.fill(knockout(breast, *wings, overlap=0.0), C_["white"], angle=90, name="breast")
    d.fill(knockout(face, beak, *[e.difference(g) for e, g in zip(eyes, glints)], overlap=0.0),
           C_["white"], angle=30, name="face")
    d.fill(knockout(wood, owl, *wings, leaf_all, acorn_all, overlap=0.0), C_["bark"], angle=10, name="branch")
    d.run(np.asarray(face.exterior.coords), C_["bark"], bean=1, length=1.3, name="face rim")
    d.fill(beak, C_["bark"], angle=90, underlay=False, name="beak")
    for row, (y, xs) in enumerate(((0, (-6, 2)), (-6, (-8, -2, 4)), (-12, (-5, 1)))):
        for x in xs:                                     # chevrons on the breast
            d.run(np.array([[x - 1.3, y + 1.0], [x, y], [x + 1.3, y + 1.0]]), C_["bark"], length=1.0,
                  name="chevron", trim_after=True)
    for nut, cap, stem in acorns:
        d.fill(cap, C_["bark"], angle=10, spacing=0.38, name="acorn cap")
        d.run(stem, C_["bark"], bean=1, length=1.0, name="acorn stem")
    for tn, lf, a in leaves:
        t = math.radians(a + 90)
        c = lf.centroid
        vein = LineString([(c.x - 9 * math.cos(t), c.y - 9 * math.sin(t)), (c.x + 9 * math.cos(t), c.y + 9 * math.sin(t))])
        clip = vein.intersection(knockout(lf, wood, overlap=0.0).buffer(-1.0))
        if clip.geom_type == "LineString" and clip.length > 2:
            d.run(np.asarray(clip.coords), C_["bark"], length=1.3, name="leaf vein")
    for e, g in zip(eyes, glints):
        d.fill(knockout(e, g, overlap=0.0), C_["charcoal"], angle=45, name="eye")
    for t in talons:
        d.fill(t, C_["charcoal"], angle=90, underlay=False, name="talon")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
