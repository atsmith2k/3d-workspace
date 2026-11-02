"""Sweater Weather Mug: a latte in a knit-sleeved mug, steam, cinnamon and leaves, script.

Spec:
  object:       cosy motif for sweatshirts, mug rugs, tea towels, totes
  overall:      `size` mm tall (95 for 4x4, 160 for 5x7), about 0.95 as wide
  fabric:       sweatshirt fleece and knits with cut-away and a topper; wovens with tear-away
  threads:      cream (mug, handle), caramel (coffee, cinnamon sticks), cranberry (knit
                sleeve), rust (maple leaf), mustard (leaf), wheat (rim, latte heart, knit
                chevrons, steam), bark (outlines, cinnamon curls, leaf veins, lettering):
                7 colours
  must have:    a mug body and handle with a dark outline; a knit sleeve with three rows
                of chevrons and ribbed edges; a coffee surface inside the rim with a latte
                heart; three steam curls; two cinnamon sticks and two leaves at the base;
                `words` (default "sweater weather") in script, about 0.75 of the width
  density:      sleeve, coffee and leaves knocked out where they overlap; max 3.5 layers
"""
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Knit-sleeved latte mug with steam, cinnamon and leaves, 'sweater weather'"
HOOP = "4x4"
PARAMS = dict(size=95.0, words="sweater weather", script="Segoe Script", script_file="segoescb.ttf")
PRODUCT = dict(
    title="Sweater Weather Latte Mug Embroidery Design",
    summary="A latte in a knit-sleeved mug with steam, cinnamon and 'sweater weather'",
    tags=["fall embroidery", "sweater weather", "coffee embroidery design", "cozy", "pumpkin spice"],
    collection=COLLECTION,
    mockups=['tshirt', 'tote'],
    description=(
        "A latte in a cream mug wrapped in a cranberry knit sleeve, with stitched chevron rows and ribbed edges, a heart in the foam and steam curling up. Cinnamon sticks and two leaves rest at the base, and 'sweater weather' is set in script below.\n\nCosy art for sweatshirts, mug rugs, tea towels and totes."
    ),
)


def checks(p):
    return standard_checks(p, 7, 24000)


def art(p):
    d = Design()
    mx, my, mw, mh = -4.0, 6.0, 40.0, 38.0
    body = rounded_rect(mw, mh, 5.0, mx, my).union(rect(mw, 10, mx, my + mh / 2 - 5))
    rim = ellipse(mx, my + mh / 2, mw / 2, 4.2)
    mug = body.union(rim)
    coffee = ellipse(mx, my + mh / 2 + 0.2, mw / 2 - 2.4, 2.9)
    handle = ellipse(mx + mw / 2 + 2, my + 2, 10.5, 11.5).difference(ellipse(mx + mw / 2 + 2, my + 2, 5.8, 7.0))
    handle = handle.difference(body.buffer(-0.5))
    sleeve = body.intersection(rect(mw + 4, 17, mx, my - 1.0))
    heart_ = move(rotate(heart(7.5), 0, origin=(0, 0)), mx, my + mh / 2 + 0.6)
    heart_ = scale(heart_, 1.0, 0.42, origin=(mx, my + mh / 2 + 0.6))      # foreshortened on the surface
    # cinnamon sticks and leaves at the base
    sticks = [rotate(rounded_rect(30, 4.2, 2.0, 0, 0), a, origin=(0, 0)) for a in (8, -4)]
    sticks = [move(s, x, y) for s, (x, y) in zip(sticks, ((-14, -15.5), (-10, -19.5)))]
    maple = move(rotate(M.maple_leaf(17), -28, origin=(0, 0)), 18.5, -16)
    leaf2 = move(rotate(M.leaf(15, 7, 0.3), -118, origin=(0, 0)), 30, -10)
    fam = p.script
    fp = Path("C:/Windows/Fonts") / p.script_file
    words = text_shape(p.words, 20.0, font=fam, bold=True, font_path=str(fp) if fp.exists() else None)
    x0, y0, x1, y1 = words.bounds
    # a 0.2 mm stroke added all round so the script's thin joins sew
    words = move(centered(scale(words, 74.0 / (x1 - x0))).buffer(0.2), 0, -31)

    base = unary_union(sticks + [maple, leaf2])
    d.fill(knockout(body, sleeve, rim, base, overlap=0.0), C_["cream"], angle=90, name="mug")
    d.fill(knockout(handle, base, overlap=0.0), C_["cream"], angle=0, name="handle")
    d.fill(knockout(coffee, heart_, overlap=0.0), C_["caramel"], angle=0, name="coffee")
    for k, s in enumerate(sticks):
        above = unary_union(sticks[k + 1:] + [maple, leaf2])
        d.fill(knockout(s, above, overlap=0.0), C_["caramel"], angle=8 if k == 0 else -4, name="cinnamon")
    d.fill(knockout(sleeve, base, overlap=0.0), C_["cranberry"], angle=90, name="knit sleeve")
    d.fill(maple, C_["rust"], angle=60, name="maple leaf")
    d.fill(knockout(leaf2, maple, overlap=0.0), C_["mustard"], angle=-30, name="leaf")
    # wheat: rim ring, latte heart, chevron rows and rib lines on the sleeve, steam
    d.fill(knockout(rim, coffee, overlap=0.0), C_["wheat"], angle=0, underlay=False, name="rim")
    d.fill(heart_, C_["wheat"], angle=90, underlay=False, name="latte heart")
    sb = sleeve.bounds
    rows = []
    for r, y in enumerate((sb[1] + 4.0, sb[1] + 8.5, sb[1] + 13.0)):
        xs = np.arange(sb[0] + 1.0, sb[2] - 0.5, 3.2)
        pts = []
        for x in xs:
            pts += [(x, y + 1.1), (x + 1.6, y - 1.1)]
        pts.append((xs[-1] + 3.2, y + 1.1))
        rows.append(np.array(pts) if r % 2 == 0 else np.array(pts)[::-1])
    knit = LineString(np.vstack(rows)).intersection(knockout(sleeve, base, overlap=0.0).buffer(-0.8))
    for part in getattr(knit, "geoms", [knit]):
        if part.geom_type == "LineString" and part.length > 2:
            d.run(np.asarray(part.coords), C_["wheat"], bean=1, length=1.0, name="knit chevrons")
    for y in (sb[1] + 1.2, sb[3] - 1.2):
        rib = LineString([(sb[0], y), (sb[2], y)]).intersection(knockout(sleeve, base, overlap=0.0).buffer(-0.5))
        for part in getattr(rib, "geoms", [rib]):
            if part.geom_type == "LineString" and part.length > 2:
                d.run(np.asarray(part.coords), C_["wheat"], length=1.6, name="rib line", trim_after=True)
    for k, x in enumerate((-13, -3, 7)):
        y0 = my + mh / 2 + 6
        steam = bezier((x, y0), (x - 4, y0 + 6), (x + 5, y0 + 10), (x + (1 if k != 1 else -1), y0 + 17 + 2 * (k == 1)), 18)
        d.run(steam, C_["wheat"], bean=1, length=1.5, name="steam", trim_after=True)
    # bark: outlines, cinnamon curls, leaf veins, lettering
    outline_mug = LineString(np.asarray(mug.union(handle).buffer(0.2).exterior.coords)).difference(base.buffer(0.6))
    for part in getattr(outline_mug, "geoms", [outline_mug]):
        if part.geom_type == "LineString" and part.length > 3:
            d.run(np.asarray(part.coords), C_["bark"], bean=1, length=1.8, name="mug outline")
    for (x, y), a in (((-14, -15.5), 8), ((-10, -19.5), -4)):
        u = np.array([math.cos(math.radians(a)), math.sin(math.radians(a))])
        for end in (-1, 1):                              # a rolled curl at each visible end
            c = np.array([x, y]) + u * end * 13.2
            if knockout(circle(c[0], c[1], 1.6), maple, leaf2, overlap=0.0).area < 6:
                continue
            curl = M.spiral(0.35, 1.5, 1.1, start=0, n=24) + c
            d.run(curl, C_["bark"], length=0.9, name="cinnamon curl", trim_after=True)
    for g, a in ((maple, -28 + 90), (leaf2, -118 + 90)):
        c = g.centroid
        t = math.radians(a)
        vein = LineString([(c.x - 8 * math.cos(t), c.y - 8 * math.sin(t)), (c.x + 8 * math.cos(t), c.y + 8 * math.sin(t))])
        clip = vein.intersection(g.buffer(-0.9))
        if clip.geom_type == "LineString" and clip.length > 2:
            d.run(np.asarray(clip.coords), C_["bark"], length=1.3, name="leaf vein", trim_after=True)
    d.fill(words, C_["bark"], angle=70, spacing=0.36, name="lettering")
    return d


def design(p):
    return fit(art(p), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
