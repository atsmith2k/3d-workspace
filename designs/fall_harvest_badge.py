"""Harvest Badge: a sunflower and wheat sheaf in a round badge with a ribbon banner.

Spec:
  object:       patch-style badge for jackets, totes, caps (5x7), framed hoops
  overall:      `size` mm wide (95 for 4x4, 160 for 5x7); the banner runs past the ring
  fabric:       twill, canvas and denim with tear-away; as a patch on felt or twill
  threads:      wheat (inner ring, wheat stalks), olive (leaves), mustard (back petals),
                pumpkin (front petals), bark (seed disc, border), caramel (seed hatch),
                rust (banner), cream (lettering): 8 colours
  must have:    a 2.4 mm satin border ring and a bean-stitch inner ring; a sunflower with
                two staggered layers of 16 petals, a seed disc with a crosshatch, two
                leaves; four wheat stalks fanning behind, each ear's grains outlined as
                loops in one bean-stitch run with an awn; a curved ribbon banner with
                notched tails, breaking out past the border, carrying `word` (default
                "HARVEST") in spaced capitals at least 7 mm tall
  density:      petals, disc, wheat and banner knocked out where hidden; max 3.5 layers;
                fabric pockets between petals up to 6 mm2 are intended (coverage
                between_mm2=6), every element itself fully covered
"""
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Sunflower and wheat badge with a 'HARVEST' ribbon banner"
HOOP = "4x4"
PARAMS = dict(size=95.0, word="HARVEST", serif="Cambria", serif_file="cambriab.ttf")
PRODUCT = dict(
    title="Harvest Sunflower Badge Embroidery Design",
    summary="Sunflower and wheat in a round badge with a HARVEST ribbon",
    tags=["fall embroidery", "sunflower embroidery design", "harvest", "wheat", "patch design"],
    collection=COLLECTION,
    mockups=['cap', 'tote'],
    description=(
        'A sunflower and a sheaf of wheat inside a round badge, with a rust ribbon banner reading HARVEST that breaks out past the border. The sunflower has two staggered rings of petals round a crosshatched seed disc, and the wheat ears are worked as outlined grains, like hand embroidery.\n\nPatch-style art for jackets, caps, totes and framed hoops.'
    ),
)


def checks(p):
    # petal gaps are part of the flower: allow the small fabric pockets between petals
    return standard_checks(p, 8, 26000, between_mm2=6.0)


def spaced(word, cap, family, path, track):
    glyphs, x = [], 0.0
    for ch in word:
        g = text_shape(ch, cap, font=family, bold=True, font_path=path)
        gx0, _, gx1, _ = g.bounds
        glyphs.append(move(g, x - gx0, 0))
        x += (gx1 - gx0) + track
    return centered(unary_union(glyphs))


def ribbon(y=-25.0, half=50.0, h=11.0, sag=3.0, tail=8.0):
    """(band, [tails]): a smile-curved band and two notched tails tucked behind it."""
    xs = np.linspace(-half + tail, half - tail, 40)
    yc = y + sag * (xs / (half - tail)) ** 2
    top = np.c_[xs, yc + h / 2]
    bot = np.c_[xs, yc - h / 2]
    band = Polygon(np.vstack([top, bot[::-1]]))
    tails = []
    for sgn in (-1, 1):
        x0 = sgn * (half - tail - 2)
        yy = y + sag + -2.5
        tails.append(Polygon([(x0, yy + h / 2), (sgn * half, yy + h / 2), (sgn * (half - 3.5), yy),
                              (sgn * half, yy - h / 2), (x0, yy - h / 2)]))
    return band, tails


def art(p):
    d = Design()
    R = 44.0
    border = circle(0, 0, R, res=180)
    cx, cy = -5.0, 9.0
    disc = circle(cx, cy, 10.0)
    front = [move(g, cx, cy) for g in M.petal_ring(16, 8.8, 13.0, 5.6, jitter=4, start=0, seed=2)]
    # the back layer is wide enough to fill behind the front petals (no fabric between them)
    back = [move(g, cx, cy) for g in M.petal_ring(16, 9.0, 15.5, 10.5, jitter=2, start=11.25, seed=7)]
    leaves = [move(rotate(M.leaf(19, 10, 0.2), 128, origin=(0, 0)), -18, -9),     # clear of the petals
              move(rotate(M.leaf(17, 9, -0.2), -48, origin=(0, 0)), 11, -8)]
    stalks = []
    for k, a in enumerate((48, 60, 72, 84)):
        stem, grains = M.wheat(46 - k * 2, 7, 5.5, lean=0.08)
        g = lambda s, a=a: move(rotate(s, a - 90, origin=(0, 0)), 14, -22)
        stalks.append((np.asarray(g(stem)), [g(x) for x in grains]))
    band, tails = ribbon()
    fam = p.serif
    fp = Path("C:/Windows/Fonts") / p.serif_file
    word = move(spaced(p.word, 7.6, fam, str(fp) if fp.exists() else None, 1.6).buffer(0.25, join_style="mitre"), 0, -24.0)

    inside = border.buffer(-2.0)
    flower = unary_union([disc] + front + back)
    banner_all = unary_union([band] + tails)

    d.run(circle_path(0, 0, R - 4.0, res=180), C_["wheat"], bean=1, length=2.0, name="inner ring")
    for stem, grains in stalks:
        vis = LineString(stem).difference(unary_union([flower, banner_all, *leaves]).buffer(0.6))
        for part in getattr(vis, "geoms", [vis]):
            if part.geom_type == "LineString" and part.length > 3:
                d.run(np.asarray(part.coords), C_["wheat"], bean=1, length=1.6, name="wheat stalk", trim_after=True)
    # each ear: its grains as outlined loops (detached-chain style), one run per ear,
    # each loop starting where the last one ended so the thread never doubles back
    for stem, grains in stalks:
        path = []
        for g in grains:
            ring = np.asarray(g.exterior.coords)[:-1]
            start = int(np.argmin(np.linalg.norm(ring - (path[-1] if path else stem[0]), axis=1)))
            ring = np.roll(ring, -start, axis=0)
            path += list(ring) + [ring[0] + (ring[1] - ring[0]) * 0.3]
        path += [stem[-1], stem[-1] + (stem[-1] - stem[-6]) * 0.9]   # awn off the top
        d.run(np.array(path), C_["wheat"], length=1.0, name="wheat ear", trim_after=True)
    for i, lf in enumerate(leaves):
        d.fill(knockout(lf, flower, banner_all, overlap=0.0), C_["olive"], angle=40 + 80 * i, name="sunflower leaf")
    d.fill(knockout(unary_union(back), disc, *front, banner_all), C_["mustard"], angle=0, name="back petals")
    for k, pt in enumerate(front):
        ang = 90 + 360 * k / 16
        d.fill(knockout(pt, disc, banner_all, overlap=0.0), C_["pumpkin"], angle=ang, name="petal")
    d.fill(knockout(disc, banner_all, overlap=0.0), C_["bark"], angle=45, name="seed disc")
    d.outline(border, C_["bark"], width=2.4, name="border")
    for a in (45, -45):                                     # seed crosshatch, one run per direction
        t = math.radians(a)
        u, n = np.array([math.cos(t), math.sin(t)]), np.array([-math.sin(t), math.cos(t)])
        pts = []
        for k, off in enumerate(np.arange(-9, 9.01, 1.8)):
            seg = [np.array([cx, cy]) + n * off - u * 10, np.array([cx, cy]) + n * off + u * 10]
            pts += seg if k % 2 == 0 else seg[::-1]
        clip = LineString(pts).intersection(knockout(disc, banner_all, overlap=0.0).buffer(-0.9))
        for part in getattr(clip, "geoms", [clip]):
            if part.geom_type == "LineString" and part.length > 1.5:
                d.run(np.asarray(part.coords), C_["caramel"], length=1.1, name="seed hatch")
    for t in tails:
        d.fill(knockout(t, band, overlap=0.0), C_["rust"], angle=-30, name="ribbon tail")
    d.fill(knockout(band, word, overlap=0.0), C_["rust"], angle=0, name="ribbon")
    d.fill(word, C_["cream"], angle=90, spacing=0.36, name="lettering")
    return d


def design(p):
    return fit(art(p), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
