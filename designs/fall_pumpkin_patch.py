"""Pumpkin Patch: three different pumpkins on a vine with leaves, tendrils and grass.

Spec:
  object:       harvest scene for tea towels, aprons, totes, porch pillows
  overall:      `size` mm wide (95 for 4x4, 160 for 5x7), about 0.75 as tall
  fabric:       medium wovens (linen, canvas, twill) with tear-away; knits with cut-away
  threads:      olive (vine, leaves), rust + pumpkin (big pumpkin ribs), mustard (middle
                pumpkin), cream + wheat (small heirloom pumpkin), caramel (rib lines,
                stems), moss (tendrils, leaf veins, grass): 8 colours
  must have:    three pumpkins of different size and colour overlapping in depth, each
                with 5 or 7 ribs in alternating tones and fill angles fanning with the
                curve; rib grooves as bean-stitch lines; curled satin stems; a vine behind
                with three lobed leaves and two tendril curls; grass blades along the base
  density:      everything knocked out where it is hidden (no stacked fills); max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M
from cadkit.stitch.shapes import path_length

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Three pumpkins on a leafy vine with curling tendrils and grass"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = dict(
    title="Pumpkin Patch Embroidery Design",
    summary="Three heirloom pumpkins on a curling vine, ribbed in two tones",
    tags=["fall embroidery", "pumpkin", "harvest", "thanksgiving", "pumpkin embroidery design"],
    collection=COLLECTION,
    mockups=['tote', 'tshirt'],
    description=(
        'Three heirloom pumpkins sit in a row on a leafy vine: a big rust and orange one, a golden one behind it and a small cream one in front. Each pumpkin is built from ribs in two alternating tones with the stitch direction fanning round the curve, and the grooves between the ribs are stitched in. A vine with lobed leaves and curling tendrils weaves behind their shoulders, and grass tufts finish the ground.\n\nA harvest piece for tea towels, aprons, porch pillows and totes.'
    ),
)


def checks(p):
    return standard_checks(p, 8, 20000)


def pumpkin_leaf(s=18.0):
    """Three rounded lobes, stem end at the origin, pointing up."""
    lobes = [rotate(M.leaf(s, s * 0.62), a, origin=(0, 0)) for a in (-52, 0, 52)]
    body = unary_union(lobes + [circle(0, s * 0.18, s * 0.22)])
    k = s * 0.06
    return body.buffer(k).buffer(-k * 1.4).buffer(k * 0.4)


def _along(ring, a, b):
    """The shorter way round a closed ring from near point a to near point b."""
    from shapely.geometry import Point
    from shapely.ops import substring
    L = ring.length
    ta, tb = ring.project(Point(a)), ring.project(Point(b))
    fwd = (tb - ta) % L
    if fwd <= L / 2:
        parts = [substring(ring, ta, min(L, ta + fwd))] + ([substring(ring, 0, ta + fwd - L)] if ta + fwd > L else [])
        pts = np.vstack([np.asarray(p.coords) for p in parts])
    else:
        back = L - fwd
        parts = [substring(ring, tb, min(L, tb + back))] + ([substring(ring, 0, tb + back - L)] if tb + back > L else [])
        pts = np.vstack([np.asarray(p.coords) for p in parts])[::-1]
    return np.vstack([[a], pts, [b]])


def place(g, x, y, ang):
    return move(rotate(g, ang, origin=(0, 0)), x, y)


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
    # ---- pumpkins: (centre, w, h, ribs, tones), back to front
    pumps = [
        ((-29, -11), 36, 27, 2, (C_["mustard"], C_["pumpkin"])),
        ((1, -8), 50, 37, 3, (C_["rust"], C_["pumpkin"])),
        ((31, -16), 27, 21, 2, (C_["cream"], C_["wheat"])),
    ]
    bodies = []
    for (cx, cy), w, h, n, _ in pumps:
        segs, stem, _ = M.pumpkin(w, h, n)
        bodies.append(move(unary_union([s for _, s in segs]), cx, cy))
    front_of = [unary_union(bodies[i + 1:]) if i + 1 < len(bodies) else None for i in range(len(bodies))]

    # ---- vine, leaves and tendrils behind
    # the vine weaves behind the pumpkins' shoulders; leaves tuck in behind them
    vine = spline([(-50, -6), (-41, 5), (-24, 9), (-10, 14), (10, 15), (25, 6), (40, 4), (50, 11)], samples=10)
    pumpkins_all = unary_union(bodies)
    leaves = [place(pumpkin_leaf(19), -44, 6, 38), place(pumpkin_leaf(17), -15, 14, 4),
              place(pumpkin_leaf(18), 21, 9, -42)]
    for i, lf in enumerate(leaves):
        d.fill(knockout(lf, pumpkins_all), C_["olive"], angle=60 + i * 40, name=f"leaf {i + 1}")
    vine_vis = knockout(LineString(vine).buffer(1.0), pumpkins_all, overlap=0.0)
    for part in polygons_of(vine_vis):
        line = np.asarray(LineString(vine).intersection(part.buffer(0.05)).coords) if             LineString(vine).intersection(part.buffer(0.05)).geom_type == "LineString" else None
        if line is not None and len(line) > 2 and path_length(line) > 3:
            d.satin(line, np.full(len(line), 1.7), C_["olive"], name="vine")

    # ---- pumpkin ribs: each segment minus the segments and pumpkins in front of it
    rib_lines = []
    ribs = {}       # colour -> [(shape, angle, name)]: ribs touch edge to edge, so each
                    # colour sews in one go whatever the depth order
    for k, ((cx, cy), w, h, n, tones) in enumerate(pumps):
        segs, stem, stem_path = M.pumpkin(w, h, n)
        placed = [(r, move(s, cx, cy)) for r, s in segs]
        for j, (rank, seg) in enumerate(placed):
            above = [s for r, s in placed[j + 1:]] + ([front_of[k]] if front_of[k] is not None else [])
            vis = knockout(seg, *above, overlap=0.0) if above else seg
            if vis.is_empty:
                continue
            side = np.sign(seg.centroid.x - cx)
            angle = 90 + side * (8 + 10 * rank)         # rows fan with the curve
            ribs.setdefault(tones[rank % 2], []).append((vis, angle, f"pumpkin {k + 1} rib"))
            if rank:                                     # the groove on its inner edge
                rib_lines.append((k, seg, above))
        bodies[k] = (bodies[k], stem, stem_path, (cx, cy), w, h)
    for col, items in ribs.items():
        for shape, angle, name in items:
            d.fill(shape, col, angle=angle, name=name)
    # each pumpkin's grooves chained into one serpentine run (down one, up the next)
    chains = {}
    for k, seg, above in rib_lines:
        edge = seg.exterior.difference(unary_union(above).buffer(0.2)) if above else seg.exterior
        for line in getattr(edge, "geoms", [edge]):
            pts = np.asarray(line.coords)
            if len(pts) > 3:
                chains.setdefault(k, []).append(pts)
    for k, lines in chains.items():
        lines.sort(key=lambda L: L[:, 0].mean())
        ring = LineString(np.asarray(bodies[k][0].buffer(-0.6).exterior.coords))
        path = []
        for i, L in enumerate(lines):
            down = L if L[0, 1] > L[-1, 1] else L[::-1]
            seg = down if i % 2 == 0 else down[::-1]
            if path:                    # hop to the next groove along the pumpkin's edge
                path.append(_along(ring, path[-1][-1], seg[0]))
            path.append(seg)
        d.run(np.vstack(path), C_["caramel"], length=1.8, name=f"pumpkin {k + 1} grooves")
    for body, stem, stem_path, (cx, cy), w, h in bodies:
        st = move(stem, cx, cy)
        hidden = [b[0] for b in bodies[bodies.index((body, stem, stem_path, (cx, cy), w, h)) + 1:]]
        st = knockout(st, *hidden) if hidden else st
        d.fill(st, C_["caramel"], angle=75, spacing=0.38, name="stem")

    # ---- leaf veins, tendrils and grass in front (one thread: moss)
    for lf, (x, y, ang, sz) in zip(leaves, [(-44, 6, 38, 19), (-15, 14, 4, 17), (21, 9, -42, 18)]):
        path = []
        for j, a in enumerate((52, 0, -52)):
            t = math.radians(a + ang)            # lobe direction: up, turned CCW by a + ang
            u = (-math.sin(t), math.cos(t))
            base = (x + u[0] * 1.5 + 0.5 * (j - 1), y + u[1] * 1.5)
            tip = (x + sz * 0.70 * u[0], y + sz * 0.70 * u[1])
            path += [base, tip]
        vis = LineString(path).difference(pumpkins_all.buffer(0.8))
        for part in getattr(vis, "geoms", [vis]):
            pts = np.asarray(part.coords)
            if len(pts) >= 2 and path_length(pts) > 2:
                d.run(pts, C_["moss"], length=1.5, name="leaf vein")
    for p0, p1, curl, cw in [((-28, 10), (-25, 19), 3.4, False), ((8, 15), (13, 24), 3.0, True),
                             ((43, 5), (48, 13), 2.6, False)]:
        t = M.tendril(p0, p1, curl, 1.5, cw)
        d.run(t, C_["moss"], bean=1, length=1.4, name="tendril")
    # grass: tufts along the ground, each one continuous bean-stitch path
    rng = np.random.default_rng(11)
    for tx in (-47, -36, -22, -9, 5, 18, 39, 47):
        d.run(grass_tuft(tx, -31, rng, blades=5, spread=1.3, hmin=4.0, hmax=9.5), C_["moss"], length=1.4, name="grass tuft")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
