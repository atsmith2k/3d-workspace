"""Sleeping Fox: a fox curled nose to tail on a bed of fallen leaves.

Spec:
  object:       character motif for baby blankets, sweatshirts, pillows, totes
  overall:      `size` mm wide (95 for 4x4, 160 for 5x7), about 0.7 as tall
  fabric:       knits and fleece with cut-away (and a water-soluble topper on fleece);
                wovens with tear-away
  threads:      mustard, olive, caramel (leaf bed and drifting leaves), rust (body,
                head, ears), pumpkin (tail, fur flicks), cream (tail tip, face mask,
                chest), bark (inner ears, closed eye, nose, definition lines, leaf
                veins): 7 colours
  must have:    body, a tail wrapping in front of it with a cream tip, the head resting
                on the tail with two ears, a cream face mask, closed eye and nose; fur
                fills following the curl; light fur flicks; 7 leaves under the fox and
                3 drifting above
  density:      every part knocked out under the parts in front; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Fox curled asleep on a bed of fallen leaves"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = dict(
    title="Sleeping Fox Embroidery Design",
    summary="A fox curled nose to tail, asleep on fallen leaves",
    tags=["fall embroidery", "fox embroidery design", "woodland animal", "baby embroidery", "autumn fox"],
    collection=COLLECTION,
    mockups=['tshirt', 'tote'],
    description=(
        'A red fox curled nose to tail, fast asleep on a bed of fallen leaves. The body, head and ears are stitched in rust with the fill following the curl; the bushy tail is a lighter orange ending in a cream tip, with a cream face mask and chest, dark inner ears and nose, a sleepy closed eye and soft fur flicks along the back. A few leaves drift down above.\n\nA woodland piece for baby blankets, sweatshirts, pillows and totes.'
    ),
)


def checks(p):
    return standard_checks(p, 7, 22000)


def band(center, widths):
    """Polygon round a centreline with a width per point (rounded ends)."""
    c = np.asarray(center, float)
    d = np.gradient(c, axis=0)
    n = np.c_[-d[:, 1], d[:, 0]]
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    w = np.asarray(widths)[:, None] / 2
    ring = np.vstack([c + n * w, (c - n * w)[::-1]])
    return Polygon(ring).buffer(0).buffer(0.8).buffer(-0.8)


def art():
    d = Design()
    # body: a low mound (the tail hides its lower edge)
    body = ellipse(6, 0, 30, 19).intersection(rect(80, 30, 6, 11)).union(ellipse(6, -2, 29, 8))
    # tail: sweeps along the front from the haunch to under the chin, cream tip
    tail_c = spline([(33, 4), (31, -8), (14, -14.5), (-12, -14.5), (-31, -11.5), (-45, -6.5)], samples=14)
    t = np.linspace(0, 1, len(tail_c))
    tail_w = 3 + 14 * np.sin(np.pi * np.clip(t * 1.1, 0, 1)) ** 0.6     # emerges thin from the haunch
    tail_w[-6:] = np.maximum(tail_w[-6:] * np.linspace(1, 0.5, 6), 3)
    tail = band(tail_c, tail_w)
    tail_tip = tail.intersection(Polygon([(-60, -40), (-30, -40), (-34, 30), (-60, 30)]))
    # head resting on the tail at the left, snout pointing down-left
    head = unary_union([ellipse(-22, 6, 12.5, 10),
                        Polygon([(-28, 10.5), (-45, 0.5), (-43.5, -3.0), (-26, -2)]).buffer(1.8).buffer(-0.9)])
    ears = [Polygon([(-20, 10.5), (-9.5, 9.0), (-12.5, 26)]), Polygon([(-30, 11.0), (-18.5, 12.0), (-27.5, 26)])]
    ears = [e.buffer(0.9).buffer(-0.9) for e in ears]
    inner_ears = [scale(e, 0.45, 0.5, origin=(e.centroid.x, e.centroid.y + 1.2)).intersection(e.buffer(-0.9)) for e in ears]
    head_all = unary_union([head] + ears)
    mask = head.intersection(Polygon([(-50, -8), (-16, -8), (-17, -0.5), (-27, 1.2), (-38, -0.2), (-50, -1.5)]))
    chest = ellipse(-12, -3, 6, 5)
    paw = Polygon()

    # ---- leaf bed (behind the fox) and drifting leaves
    rng = np.random.default_rng(5)
    fox = unary_union([body, tail, head_all, chest])
    tones = [C_["mustard"], C_["olive"], C_["caramel"]]
    bed = []
    for i, (x, y, a, L) in enumerate([(-44, -12, 150, 17), (-33, -24, 115, 18), (-15, -28, 95, 18), (3, -28, 80, 18),
                                      (21, -26, 62, 18), (36, -21, 40, 17), (46, -9, 20, 15)]):
        lf = move(rotate(M.leaf(L, L * 0.46, rng.uniform(-0.3, 0.3)), a - 90, origin=(0, 0)), x, y)
        bed.append((tones[i % 3], knockout(lf, fox, overlap=0.0), a))
    drift = [(31, 28, 30, None, M.maple_leaf(13)), (45, 17, -20, 11, None), (-46, 22, 15, 11, None)]
    floating = []
    for i, (x, y, a, L, shape) in enumerate(drift):
        g = shape if shape is not None else M.leaf(L, L * 0.48, 0.25)
        floating.append((tones[(i + 1) % 3], move(rotate(g, a, origin=(0, 0)), x, y), a))
    for tone in tones:
        for tn, lf, a in bed + floating:
            if tn == tone and not lf.is_empty:
                d.fill(lf, tone, angle=a + 30, name="leaf")

    # ---- fox, back to front
    d.fill(knockout(body, tail, head_all, chest), C_["rust"], angle=20, name="body")
    d.fill(knockout(head, mask, *inner_ears), C_["rust"], angle=-35, name="head")
    for k, (e, ie) in enumerate(zip(ears, inner_ears)):
        behind = [ears[0]] if k == 1 else []          # the far ear tucks behind the near one
        d.fill(knockout(e, ie, head, *behind, overlap=0.0), C_["rust"], angle=80, name="ear")
    d.fill(knockout(tail, tail_tip, head_all, overlap=0.0), C_["pumpkin"], angle=-12, name="tail")
    for k in range(8):                                   # fur flicks along the back
        a = math.radians(30 + k * 15)
        x, y = 6 + 25 * math.cos(a), 1 + 14.5 * math.sin(a)
        f = np.array([[x, y], [x + 2.2 * math.cos(a + 2.2), y + 2.2 * math.sin(a + 2.2)],
                      [x + 3.8 * math.cos(a + 2.5), y + 3.8 * math.sin(a + 2.5)]])
        clip = LineString(f).intersection(knockout(body, tail, head_all).buffer(-0.8))
        if clip.geom_type == "LineString" and clip.length > 1.5:
            d.run(np.asarray(clip.coords), C_["pumpkin"], bean=1, length=1.2, name="fur flick", trim_after=True)
    d.fill(knockout(tail_tip, head_all, overlap=0.0), C_["cream"], angle=-30, name="tail tip")
    d.fill(mask, C_["cream"], angle=-20, name="face mask")
    d.fill(knockout(chest, head_all, tail, overlap=0.0), C_["cream"], angle=60, name="chest")
    # bark: inner ears, paw, nose, eye, definition lines, leaf veins
    for ie in inner_ears:
        d.fill(ie, C_["bark"], angle=80, underlay=False, name="inner ear")
    d.fill(circle(-44.0, -1.5, 1.8), C_["bark"], angle=0, underlay=False, name="nose")
    eye = bezier((-33.0, 5.5), (-31.0, 3.6), (-28.0, 3.6), (-26.0, 5.6), 12)
    d.run(eye, C_["bark"], bean=1, length=1.0, name="closed eye")
    # the tail's upper edge and the head outline, so the parts read apart
    tail_edge = LineString(np.asarray(tail.exterior.coords)).intersection(body.buffer(0.4)).difference(head_all.buffer(0.6))
    for part in getattr(tail_edge, "geoms", [tail_edge]):
        if part.geom_type == "LineString" and part.length > 3:
            d.run(np.asarray(part.coords), C_["bark"], length=1.6, name="tail line")
    head_line = LineString(np.asarray(head_all.exterior.coords)).difference(LineString(np.asarray(head_all.exterior.coords)).intersection(tail.buffer(-0.5)))
    for part in getattr(head_line, "geoms", [head_line]):
        if part.geom_type == "LineString" and part.length > 3:
            d.run(np.asarray(part.coords), C_["bark"], length=1.6, name="head line")
    for tn, lf, a in bed + floating:
        if lf.is_empty:
            continue
        c = lf.representative_point()
        t = math.radians(a)
        vein = LineString([(c.x - 7 * math.cos(t), c.y - 7 * math.sin(t)), (c.x + 7 * math.cos(t), c.y + 7 * math.sin(t))])
        clip = vein.intersection(lf.buffer(-1.0))
        if clip.geom_type == "LineString" and clip.length > 2:
            d.run(np.asarray(clip.coords), C_["bark"], length=1.4, name="leaf vein")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
