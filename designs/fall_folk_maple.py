"""Folk Maple: a sugar-maple leaf turning from olive to rust, inside a scalloped ring.

Spec:
  object:       standalone motif for totes, tea towels, sweatshirts, framed hoops
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7), round
  fabric:       medium wovens with tear-away; knits and sweatshirts with cut-away
  threads:      olive, moss, mustard, pumpkin, rust (the five leaf lobes, green to rust as
                it turns), wheat (veins, scallop ring), bark (stem, outline), cranberry
                (berries): 8 colours, every one an exact Brother thread
  must have:    each lobe its own colour with its fill running along that lobe's vein;
                light tapered satin veins to every lobe tip; a curved stem; a 1.25 mm satin
                outline that is one continuous ring; a scalloped bean-stitch ring with
                12 berry dots
  density:      lobes meet edge to edge (no stacked fills); max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Sugar-maple leaf in five turning tones inside a scalloped berry ring"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = dict(
    title="Folk Maple Leaf Embroidery Design",
    summary="A maple leaf mid-turn, olive to rust, in a scalloped berry ring",
    tags=["fall embroidery", "maple leaf", "autumn", "folk art", "leaf embroidery design"],
    collection=COLLECTION,
    mockups=['tote', 'tshirt'],
    description=(
        "A sugar-maple leaf caught mid-turn: its five lobes shade from olive and moss through gold to pumpkin and rust, and each lobe's stitches run along its own vein so the leaf catches the light the way a real one does. Light satin veins with fine side veins, a dark outline and a curved stem sit inside a scalloped ring dotted with cranberry berries.\n\nMade for tote bags, tea towels, sweatshirts and framed hoops."
    ),
)


def checks(p):
    return standard_checks(p, 8, 16000)


def art():
    d = Design()
    h = 56.0
    leaf_cy = 4.0
    sectors = M.maple_sectors(h)                    # sorted by lobe angle, left to right
    tones = [C_["rust"], C_["pumpkin"], C_["mustard"], C_["moss"], C_["olive"]]
    leaf = M.maple_leaf(h)
    # sew from the green side round to rust, so the colours change in order
    for (a, sec), tone in sorted(zip(sectors, tones), key=lambda st: -st[0][0]):
        body = tuck(sec.buffer(0.35).intersection(leaf), 1.25)
        d.fill(move(body, 0, leaf_cy), tone, angle=90 - a, spacing=0.40, name=f"lobe {a:.0f}")
    # veins start a little out from the centre so five columns don't pile into one hole;
    # each first gets fine side veins as one out-and-back bean run that the satin covers
    for v in M.maple_veins(h):
        v = v * [1, 1]
        v[-1] *= 0.82                      # end clear of the outline at the lobe tip
        tip = v[-1]
        L = math.hypot(*tip)
        u = tip / L
        n = np.array([-u[1], u[0]])
        v = np.vstack([u * 2.6, v[1:]])
        path = [u * 2.6]
        for f in (0.35, 0.55, 0.75):
            for j, side in enumerate((1, -1)):
                base = u * L * (f + 0.03 * j)
                twig = base + (u * 0.75 + n * side * 0.66) * L * 0.30 * (1.1 - f)
                path += [base, twig, base + u * 1.2]      # zigzag on: no hole is sewn twice
        path.append(tip)
        # kept 2 mm inside the leaf so side veins never pile onto the outline at a tip
        from shapely.geometry import LineString
        inside = LineString(path).intersection(leaf.buffer(-2.0))
        for part in getattr(inside, "geoms", [inside]):
            if part.geom_type == "LineString" and part.length > 1.5:
                d.run(move(np.asarray(part.coords), 0, leaf_cy), C_["wheat"], length=1.5, name="side veins")
        d.satin(move(v, 0, leaf_cy), M.taper(v, 1.45, 1.15), C_["wheat"], name="vein", underlay="center")
    ring = M.scallop(46.0, 24, 1.8)
    d.run(ring, C_["wheat"], bean=1, length=2.2, name="scallop ring")
    # the stem starts at the outline, not under it (two satins crossing pile up)
    from shapely.geometry import LineString
    stem = LineString(M.maple_stem(h, bend=0.18)).difference(leaf.buffer(0.3))
    stem = max(getattr(stem, "geoms", [stem]), key=lambda g: g.length)
    stem = np.asarray(stem.segmentize(1.0).coords)
    d.satin(move(stem, 0, leaf_cy), M.taper(stem, 1.8, 1.3), C_["bark"], name="stem")
    d.outline(move(leaf, 0, leaf_cy), C_["bark"], width=1.25, name="leaf outline")
    berries = [p for i, p in enumerate(M.ring_points(44.6, 24, start=7.5)) if i % 2 == 0]
    d.fill(M.dots(berries, 1.25), C_["cranberry"], angle=0, underlay=False, spacing=0.35, name="berries")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
