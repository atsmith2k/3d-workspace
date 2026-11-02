"""Toadstool Grove: four mushrooms on a mossy mound with a fern and grass.

Spec:
  object:       woodland motif for aprons, tea towels, kids' clothes, totes
  overall:      `size` mm wide (95 for 4x4, 160 for 5x7), about 0.8 as tall
  fabric:       medium wovens with tear-away; knits with cut-away
  threads:      olive (mound, fern), cream (stems), red (toadstool caps), rust (middle
                cap), caramel (porcini cap, fallen leaf), white (spots), wheat (gills,
                stem shading), bark (gill lines, fern rib), moss (grass): 9 colours
  must have:    four mushrooms of three kinds and four sizes overlapping in depth: a big
                red toadstool with white spots, gills and a stem ring; a rust one with
                cream-white spots; a brown porcini; a tiny red one; caps knocked out
                round their spots; a mossy mound, a fern frond with alternate leaflets,
                grass tufts, one fallen leaf
  density:      everything knocked out where hidden; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Red-capped toadstools and a porcini on a mossy mound with a fern"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = dict(
    title="Toadstool Grove Mushroom Embroidery Design",
    summary="Spotted toadstools and a porcini on a mossy mound with a fern",
    tags=["fall embroidery", "mushroom embroidery design", "toadstool", "woodland", "cottagecore"],
    collection=COLLECTION,
    mockups=['tote', 'tshirt'],
    description=(
        "A little grove on a mossy mound: a big red toadstool with white spots, gills fanning under the cap and a skirt on its stem, a rust-capped cousin, a brown porcini and one tiny red one, with a fern frond, grass tufts and a fallen leaf. Every cap is cut out round its spots, so nothing stacks.\n\nCottagecore charm for aprons, tea towels, kids' clothes and totes."
    ),
)


def checks(p):
    return standard_checks(p, 9, 22000)


def cap(cx, cy, w, h, rot=0.0):
    """A domed cap with a gently curved underside, (cap, underside band)."""
    t = np.linspace(0, math.pi, 60)
    top = np.c_[cx + w / 2 * np.cos(t), cy + h * np.sin(t) ** 0.8]
    under = np.c_[np.linspace(cx - w / 2, cx + w / 2, 20)[::-1] * 0 + np.linspace(cx - w / 2, cx + w / 2, 20),
                  cy - h * 0.12 * np.sin(np.linspace(0, math.pi, 20))][::-1]
    shape = Polygon(np.vstack([top, under[::-1][1:-1]])).buffer(0.6).buffer(-0.6)
    gills = ellipse(cx, cy - h * 0.08, w * 0.42, h * 0.16)
    return rotate(shape, rot, origin=(cx, cy)), rotate(gills, rot, origin=(cx, cy))


def stem(x, y0, y1, w0, w1, bend=0.0):
    t = np.linspace(0, 1, 20)
    xs = x + bend * np.sin(np.pi * t)
    w = w0 + (w1 - w0) * t
    left = np.c_[xs - w / 2, y0 + (y1 - y0) * t]
    right = np.c_[xs + w / 2, y0 + (y1 - y0) * t]
    return Polygon(np.vstack([left, right[::-1]])).buffer(0.8).buffer(-0.8)


def grass_tuft(x, base_y, rng, blades=4, spread=1.25, hmin=3.5, hmax=8.0):
    """One continuous single-thread path: each blade a slim V (up one side, down the
    other 0.5 mm over), so no needle hole is used twice."""
    path = []
    for j in range(blades):
        x0 = x + j * spread + rng.uniform(-0.25, 0.25)
        h = rng.uniform(hmin, hmax)
        lean = rng.uniform(-0.5, 0.5)
        up = bezier((x0, base_y), (x0, base_y + h * 0.5), (x0 + lean * h * 0.5, base_y + h * 0.85),
                    (x0 + lean * h, base_y + h), 8)
        down = up[::-1][1:] + (0.55, 0)
        path += list(up) + list(down)
    return np.array(path)


def art():
    d = Design()
    mush = []   # back to front: (cap colour, cap, gills, stem, spots)
    specs = [
        (C_["rust"], (19, 2, 27, 13, -12), (19, -24, -1, 7.0, 5.5, 1.5), [(13, 7, 1.6), (21, 10, 1.9), (26, 5, 1.4), (16, 12, 1.2)]),
        (C_["red"], (-6, 11, 42, 21, 4), (-6, -26, 9, 10.5, 7.5, -1.5), [(-18, 15, 2.6), (-8, 22, 3.0), (3, 18, 2.4), (-13, 25, 1.6), (8, 13, 1.8), (-21, 9, 1.5), (-2, 15, 1.5)]),
        (C_["caramel"], (-29, -7, 19, 10, 14), (-29, -26, -7, 7.5, 6.0, 0.8), []),
        (C_["red"], (33, -14, 10, 6, -8), (33, -26, -14, 3.6, 3.0, 0.4), [(32.5, -11.2, 1.25)]),
    ]
    for col, cp, st, spots in specs:
        c, g = cap(*cp)
        s = stem(*st)
        sp = unary_union([circle(x, y, r, res=24) for x, y, r in spots]).intersection(c.buffer(-0.8)) if spots else Polygon()
        mush.append(dict(col=col, cap=c, gills=g, stem=s, spots=sp))
    ring = stem(-6, 1.0, 4.0, 13.0, 12.0)           # the big toadstool's skirt
    mound = ellipse(0, -29, 47, 9.5)
    # fern frond rising behind the porcini
    rib = spline([(-49, -27), (-47, -14), (-42, -2), (-36, 8)], samples=10)
    leaflets = []
    for i in range(1, len(rib) - 2, 3):
        p, q = rib[i], rib[i + 1]
        a = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        L = 9.5 * (1 - i / len(rib)) + 3
        for side in (1, -1):
            g = rotate(M.leaf(L, L * 0.38, 0.15 * side), a - 90 + side * 58, origin=(0, 0))
            leaflets.append(move(g, p[0], p[1]))
    fern = unary_union(leaflets)
    leaf = move(rotate(M.leaf(13, 6, 0.3), -70, origin=(0, 0)), 30, -32)

    def front(i):
        return unary_union([unary_union([m["cap"], m["stem"]]) for m in mush[i + 1:]] + ([ring] if i < 1 else []))
    all_mush = unary_union([unary_union([m["cap"], m["stem"]]) for m in mush] + [ring])

    d.fill(knockout(mound, all_mush, leaf, overlap=0.0), C_["olive"], angle=5, name="moss mound")
    d.fill(knockout(fern, all_mush, mound, overlap=0.0), C_["olive"], angle=60, name="fern")
    for i, m in enumerate(mush):                     # stems, behind their own caps
        vis = knockout(m["stem"], m["cap"], front(i), overlap=0.0)
        if i == 1:
            vis = knockout(vis, ring, overlap=0.0)
        d.fill(vis, C_["cream"], angle=90, name="stem")
    d.fill(knockout(ring, mush[2]["cap"], mush[2]["stem"], overlap=0.0), C_["cream"], angle=0, name="skirt")
    for col in (C_["red"], C_["rust"], C_["caramel"]):
        for i, m in enumerate(mush):
            if m["col"] == col:
                d.fill(knockout(m["cap"], m["spots"], front(i), overlap=0.0), col, angle=20 + 25 * i, name="cap")
    d.fill(knockout(leaf, mound.difference(mound), overlap=0.0), C_["caramel"], angle=30, name="fallen leaf")
    for i, m in enumerate(mush):
        if not m["spots"].is_empty:
            d.fill(knockout(m["spots"], front(i), overlap=0.0), C_["white"], angle=0, underlay=False, spacing=0.36, name="spots")
    # wheat: gill bands and a shading line down each stem
    for i, m in enumerate(mush[:3]):
        g = knockout(m["gills"].intersection(m["cap"].buffer(-0.4)), front(i), overlap=0.0)
        if not g.is_empty and g.area > 4:
            d.fill(g, C_["wheat"], angle=90, underlay=False, name="gills")
    for i, m in enumerate(mush[:3]):
        x0, y0, x1, y1 = m["stem"].bounds
        shade = LineString([(x1 - 1.6, y0 + 3), (x1 - 1.4, y1 - 2)]).intersection(
            knockout(m["stem"], m["cap"], front(i), mound, overlap=0.0).buffer(-0.6))
        if shade.geom_type == "LineString" and shade.length > 2:
            d.run(np.asarray(shade.coords), C_["wheat"], length=1.5, name="stem shade", trim_after=True)
    # bark: gill lines, fern rib, leaf vein
    for i, m in enumerate(mush[:2]):
        cx, cy = m["gills"].centroid.x, m["gills"].centroid.y
        x0, y0, x1, y1 = m["gills"].bounds
        pts = []
        for k, x in enumerate(np.linspace(x0 + 1.5, x1 - 1.5, 17)):
            seg = [(x, y1 - 0.5), (cx + (x - cx) * 0.35, y0 + 0.6)]      # fanning in to the stem
            pts += seg if k % 2 == 0 else seg[::-1]
        clip = LineString(pts).intersection(knockout(m["gills"], front(i), overlap=0.0).buffer(-0.4))
        for part in getattr(clip, "geoms", [clip]):
            if part.geom_type == "LineString" and part.length > 1.5:
                d.run(np.asarray(part.coords), C_["bark"], length=1.0, name="gill lines")
    rib_vis = LineString(rib).difference(all_mush.buffer(0.5))
    for part in getattr(rib_vis, "geoms", [rib_vis]):
        if part.geom_type == "LineString" and part.length > 2:
            d.run(np.asarray(part.coords), C_["bark"], bean=1, length=1.4, name="fern rib")
    c = leaf.centroid
    d.run(np.array([[c.x - 4, c.y + 1.2], [c.x + 4, c.y - 1.2]]), C_["bark"], length=1.3, name="leaf vein")
    # moss: grass tufts along the mound
    rng = np.random.default_rng(3)
    for tx in (-42, -30, -17, 8, 22, 40):
        base_y = -29 + 9.5 * math.sqrt(max(0, 1 - (tx / 47) ** 2)) - 1.2
        clip = LineString(grass_tuft(tx, base_y, rng)).difference(all_mush.buffer(0.4))
        for part in getattr(clip, "geoms", [clip]):
            if part.geom_type == "LineString" and part.length > 2:
                d.run(np.asarray(part.coords), C_["moss"], length=1.3, name="grass", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
