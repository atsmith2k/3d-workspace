"""Beacon Fires: a chain of signal fires lit on the peaks of three mountain ridges under a
twilight sky, in a round gold-bordered scene.

Spec:
  object:       hilltop beacons calling a kingdom to war, lit one after another along
                the ridges (an original landscape) for tees, hoodies, totes and patches
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      navy, purple, wine, rust (twilight sky bands, top to horizon), white
                (stars), gray, pewter, black (back, middle, front ridges; cairns
                pewter, black, pewter), flame,
                yellow (fires), gold (border): 10 colours
  must have:    a 92 mm round scene, 2.6 mm gold satin border; four sky bands sewn as
                horizontal rows; three jagged ridges, lighter as they recede; five
                beacons on peaks, each a stone cairn under a three-tongued fire, the
                front one 14 mm tall, the back ones 6 mm, yellow hearts in the larger
                three; six four-point stars in the top band
  density:      sky and ridges are knocked out under everything above them, fills are
                tucked under the border; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *

from _kingdom import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Chain of beacon fires lit along three mountain ridges under a twilight sky"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Beacon Fires Embroidery Design",
    "Signal fires blazing on the peaks of three mountain ridges under a purple twilight sky",
    ["beacons", "beacon fires", "signal fire", "mountains", "mountain range", "call for aid",
     "landscape embroidery", "night sky", "kingdom", "epic"],
    "The beacons are lit: a chain of signal fires blazes from peak to peak across three "
    "dark mountain ridges, under a twilight sky fading from navy to ember, all in a round "
    "scene bordered in gold.\n\n"
    "Great on hoodies, tees, tote bags, jackets and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 10, 20000)


R = 46.0
BW = 2.6

BACK = [(-52, 3), (-40, 9), (-31, 4), (-21, 15), (-12, 7), (-4, 11), (6, 4), (16, 19),
        (25, 10), (35, 14), (52, 5)]
MID = [(-52, -12), (-41, -5), (-31, -11), (-17, 3), (-7, -7), (3, -3), (12, -11), (29, 2),
       (40, -7), (52, -4)]
FRONT = [(-52, -31), (-36, -25), (-22, -31), (-4, -11), (9, -25), (22, -30), (37, -23),
         (52, -30)]
# (peak x, peak y, fire height, ridge)
BEACONS = [(-21, 15, 6.0, 0), (16, 19, 6.5, 0), (-17, 3, 9.0, 1), (29, 2, 9.0, 1), (-4, -11, 15.0, 2)]


DROP = 5.0      # every ridge sits this much lower than drawn: more twilight sky


def ridge(pts):
    """The ridge silhouette down to the bottom of the scene."""
    g = poly([(x, y - DROP) for x, y in pts] + [(52, -60), (-52, -60)])
    # peaks and valleys eased (r 1 mm): fill rows piling into a sharp V make a needle pile-up
    return g.buffer(1.0, join_style="round").buffer(-2.0, join_style="round").buffer(1.0, join_style="round")


def flame(x, y, h):
    """Three-tongued fire standing on (x, y), h tall."""
    w = h * 0.62
    pts = [(x - w / 2, y), (x - w * 0.48, y + h * 0.35), (x - w * 0.30, y + h * 0.62),
           (x - w * 0.22, y + h * 0.45), (x - w * 0.08, y + h * 0.80), (x + w * 0.02, y + h * 1.0),
           (x + w * 0.12, y + h * 0.66), (x + w * 0.28, y + h * 0.80), (x + w * 0.42, y + h * 0.42),
           (x + w / 2, y)]
    # notches between the tongues closed to 0.9 mm radius: the ridge fill behind a fire
    # otherwise turns in them and piles the needle up
    return smooth(pts, samples=8).buffer(0.9).buffer(-0.9)


def heart(x, y, h):
    return smooth([(x - h * 0.16, y), (x - h * 0.14, y + h * 0.3), (x, y + h * 0.55),
                   (x + h * 0.14, y + h * 0.3), (x + h * 0.16, y)], samples=8)


def cairn(x, y, h):
    """A squat stone beacon tower on the peak (the same colour as the next ridge darker)."""
    w = max(2.6, h * 0.42)
    t = max(1.6, h * 0.16)
    return poly([(x - w / 2, y - 3.0), (x - w * 0.42, y + t), (x + w * 0.42, y + t), (x + w / 2, y - 3.0)])


def art():
    d = Design()
    disc = circle(0, 0, R, res=256)
    inner = tuck(disc, BW)
    ridges = [ridge(BACK), ridge(MID), ridge(FRONT)]
    fires, hearts, cairns = [], [], []
    for x, y, h, k in BEACONS:
        y -= DROP
        top = y + max(1.6, h * 0.16)
        cairns.append((cairn(x, y, h), k))
        fires.append(flame(x, top - 0.3, h))
        if h >= 9:
            hearts.append(heart(x, top + 0.4, h * 0.75))
    cairn_all = union(*[c for c, _ in cairns])
    top_all = union(*fires, cairn_all)
    stars = [star(4, 2.6, 0.8, x, y, rot=90) for x, y in
             ((-24, 33), (-8, 38), (9, 30), (27, 34), (-36, 24), (36, 23))]
    stars = [s for s in stars if inner.buffer(-1.5).contains(s)]

    land = union(*ridges)
    sky = inner - land.buffer(-0.4)
    bands = [("navy", 20, 99), ("purple", 8, 20), ("wine", -1, 8), ("rust", -99, -1)]
    for col, y0, y1 in bands:
        g = sky & rect(200, y1 - y0, 0, (y0 + y1) / 2)
        g = knockout(g, top_all, *stars)
        # neighbouring bands overlap 0.4 mm so no fabric shows between them
        if y0 > -99:
            g = g | (sky & rect(200, 0.4, 0, y0)) - top_all
        if not g.is_empty:
            d.fill(g, C_[col], angle=0, spacing=0.42, name=f"{col} sky")
    for s in stars:
        d.fill(s, C_["white"], angle=45, name="star")
    # ridges back to front: each knocked out under the nearer ones and the beacons on it
    cols = ["gray", "pewter", "black"]
    angs = [70, 115, 40]
    for i, rg in enumerate(ridges):
        nearer = union(*ridges[i + 1:]) if i < 2 else None
        g = rg & inner
        g = knockout(g, *(x for x in (nearer, top_all) if x is not None))
        d.fill(g, C_[cols[i]], angle=angs[i], name=f"{cols[i]} ridge")
        # cairns sew in the next darker ridge colour (front ones pewter), ordered so
        # each colour stays one block: gray ridge, pewter cairns + ridge, black cairns
        if i == 0:
            later = [c for c, k in cairns if k == 0]
        elif i == 1:
            later = [c for c, k in cairns if k == 2]
        else:
            later = []
        for c in later:
            d.fill(c, C_["pewter"], angle=0, name="cairn")
        if i == 1:
            for c, k in cairns:
                if k == 1:
                    d.fill(c, C_["black"], angle=0, name="cairn")
    for f in fires:
        d.fill(knockout(f, *hearts), C_["flame"], angle=90, name="fire")
    for h in hearts:
        d.fill(h, C_["yellow"], angle=90, name="fire heart")
    d.outline(disc, C_["gold"], width=BW, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
