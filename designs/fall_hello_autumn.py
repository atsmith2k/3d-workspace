"""Hello Autumn: script and spaced-capital lettering under an arching leaf garland.

Spec:
  object:       word art for sweatshirts, tea towels, door banners, pillows
  overall:      `size` mm wide (95 for 4x4, 160 for 5x7), about 0.8 as tall
  fabric:       sweatshirt fleece and knits with cut-away (topper on fleece); wovens with
                tear-away
  threads:      bark (garland branch, leaf veins), mustard, olive, pumpkin, caramel
                (garland leaves), cranberry (berries), rust ("hello"), charcoal
                ("AUTUMN"): 8 colours
  must have:    `word1` (default "hello") in script, about 0.66 of the size wide; `word2`
                (default "AUTUMN") in spaced serif capitals at least 8 mm tall; an arching
                branch over the words with 11 alternating leaves of three kinds in four
                tones, a vein in every leaf, three berry clusters; a small leaf flourish
                each side of word2; two leaves drifting below
  density:      lettering and leaves do not overlap; max 3.5 layers
"""
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "'Hello Autumn' lettering under an arching garland of leaves and berries"
HOOP = "4x4"
PARAMS = dict(size=95.0, word1="hello", word2="AUTUMN",
              script="Segoe Script", script_file="segoescb.ttf", serif="Cambria", serif_file="cambriab.ttf")
PRODUCT = dict(
    title="Hello Autumn Lettering Embroidery Design",
    summary="Script and capital lettering under an arching leaf and berry garland",
    tags=["fall embroidery", "hello autumn", "fall lettering", "sweatshirt embroidery", "leaf garland"],
    collection=COLLECTION,
    mockups=['tshirt', 'tote'],
    description=(
        "'hello' in a flowing script with 'AUTUMN' set beneath in spaced capitals, under an arching branch hung with maple, oak and willow leaves in four fall tones and clusters of cranberries. Small leaves flank the capitals and two more drift below.\n\nMade for sweatshirts, tea towels, door banners and pillows."
    ),
)


def checks(p):
    return standard_checks(p, 8, 22000)


def font(p, name, file):
    fp = Path("C:/Windows/Fonts") / file if file else None
    return name, (str(fp) if fp and fp.exists() else None)


def spaced(word, cap, family, path, track):
    """Capitals set one by one with extra tracking (mm), centred."""
    glyphs, x = [], 0.0
    for ch in word:
        g = text_shape(ch, cap, font=family, bold=True, font_path=path)
        gx0, _, gx1, _ = g.bounds
        glyphs.append(move(g, x - gx0, 0))
        x += (gx1 - gx0) + track
    return centered(unary_union(glyphs))


def art(p):
    d = Design()
    fam, fp = font(p, p.script, p.script_file)
    hello = text_shape(p.word1, 20.0, font=fam, bold=True, font_path=fp)
    x0, y0, x1, y1 = hello.bounds
    hello = move(centered(scale(hello, 64.0 / (x1 - x0))), 0, 2)
    fam2, fp2 = font(p, p.serif, p.serif_file)
    # a 0.3 mm stroke added all round: serif hairlines would sew under 1 mm otherwise
    autumn = move(spaced(p.word2, 9.0, fam2, fp2, 2.4).buffer(0.3, join_style="mitre"), 0, -19.5)
    ax0, ay0, ax1, ay1 = autumn.bounds

    arch = spline([(-47, 4), (-30, 21), (0, 29), (30, 21), (47, 4)], samples=12)
    leaves = []
    kinds = ["maple", "leaf", "oak", "leaf"]
    tones = [C_["mustard"], C_["olive"], C_["pumpkin"], C_["caramel"]]
    n = 11
    for i in range(n):
        f = 0.06 + 0.88 * i / (n - 1)
        k = int(f * (len(arch) - 1))
        p0, p1 = arch[k], arch[min(k + 1, len(arch) - 1)]
        tang = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
        side = 1 if i % 2 == 0 else -1
        kind = kinds[i % 4]
        L = 11.5 if kind != "maple" else 10.0
        if kind == "maple":
            g = rotate(M.maple_leaf(L), tang + 90 * side - 90 + 90, origin=(0, 0))
            g = move(g, p0[0] + side * 4.0 * -math.sin(math.radians(tang)), p0[1] + side * 4.0 * math.cos(math.radians(tang)))
            vein_dir = tang + 90 * side
        else:
            g = M.leaf(L, L * 0.45, 0.2 * side) if kind == "leaf" else M.oak_leaf(L * 1.1, 3)
            ang = tang + side * 55 - 90
            g = move(rotate(g, ang, origin=(0, 0)), p0[0], p0[1])
            vein_dir = ang + 90
        leaves.append((tones[i % 4], g, vein_dir))
    drift = [(C_["caramel"], move(rotate(M.leaf(9, 4.2, 0.3), 200, origin=(0, 0)), -40, -24), 290),
             (C_["mustard"], move(rotate(M.maple_leaf(9), -25, origin=(0, 0)), 42, -24), 65)]
    flourishes = []
    for sign in (-1, 1):
        x = (ax0 - 4.5) if sign < 0 else (ax1 + 4.5)
        flourishes.append((C_["olive"], move(rotate(M.leaf(7.5, 3.4, 0.2 * sign), -90 * sign + 20 * sign, origin=(0, 0)), x, -19 + 0.5), 0))
    words = unary_union([hello, autumn])
    all_leaves = leaves + drift + flourishes

    for tone in tones:
        for tn, g, a in all_leaves:
            if tn == tone:
                d.fill(knockout(g, words.buffer(1.2), overlap=0.0), tone, angle=a + 40, name="leaf")
    d.run(arch, C_["bark"], bean=1, length=1.8, name="garland branch")
    for tn, g, a in all_leaves:                              # one vein down each leaf
        c = g.centroid
        t = math.radians(a)
        vein = LineString([(c.x - 6 * math.cos(t), c.y - 6 * math.sin(t)), (c.x + 6 * math.cos(t), c.y + 6 * math.sin(t))])
        clip = vein.intersection(g.buffer(-0.9))
        if clip.geom_type == "LineString" and clip.length > 2:
            d.run(np.asarray(clip.coords), C_["bark"], length=1.2, name="leaf vein", trim_after=True)
    for f in (0.28, 0.5, 0.72):
        k = int(f * (len(arch) - 1))
        cx, cy = arch[k]
        pts = [(cx + 1.8 * math.cos(math.radians(a)), cy + 1.8 * math.sin(math.radians(a)) + 2.2) for a in (90, 210, 330)]
        d.fill(knockout(M.dots(pts, 1.35), words.buffer(1.0), overlap=0.0), C_["cranberry"], angle=0, underlay=False,
               spacing=0.35, name="berries")
    d.fill(hello, C_["rust"], angle=75, spacing=0.36, name=p.word1)
    d.fill(autumn, C_["charcoal"], angle=90, spacing=0.36, name=p.word2)
    return d


def design(p):
    return fit(art(p), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
