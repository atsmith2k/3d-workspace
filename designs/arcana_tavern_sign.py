"""Tavern Sign: a hanging plank sign on chains from a wrought-iron bracket, with a foaming
tankard and TAVERN in gold block letters.

Spec:
  object:       fantasy-inn sign (generic, no named inn) for tees, totes, aprons, bar
                towels, hoodies and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; aprons, towels (add a topper) and wovens with tear-away
  threads:      light brown (planks), dark brown (grain runs, plank seam, TAVERN inset
                panel, board rim), pewter (tankard), brass (tankard hoops), white (foam),
                gold (pin-line, TAVERN), black (bracket and chains): 7 colours
  must have:    a 92 x 50 mm board of planks (a dark brown 1.5 mm satin seam that
                stop clear of the art and 1.5 mm short of the rim, single-run grain lines
                2 mm inside the rim), a 2.2 mm dark brown rim; two chains (eye ring, an
                oval link, a side-on link) up to a black wrought-iron bracket with a wall
                plate, a brace and a scroll; a 25 mm pewter tankard with two brass hoops,
                a handle and white foam spilling over with a drip; "TAVERN" in our block
                lettering, 10 mm caps, gold on an 84 x 16 mm dark brown painted inset
                with a gold bean-run pin-line 1.3 mm inside its edge
  lettering:    `cadkit.stitch.lettering.block_text` (our own alphabet, no font licence);
                ~9.4 mm caps at the 4x4 size, fill rows 0.35 mm
  density:      planks knocked out under seam, rim, tankard and inset; inset knocked
                out under the letters; max 3.5
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Hanging plank tavern sign with a foaming tankard and gold TAVERN lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Tavern Sign Embroidery Design",
    "A hanging wooden tavern sign on iron chains with a foaming tankard and gold TAVERN lettering",
    ["tavern", "tavern sign", "fantasy inn", "tankard", "ale", "beer", "renaissance faire",
     "tabletop rpg", "game night", "bar towel", "apron embroidery"],
    "Every adventure starts at the inn: a weathered three-plank sign swinging on iron chains from "
    "a wrought-iron bracket, painted with a pewter tankard of foaming ale and TAVERN in gold block "
    "letters on a dark painted inset.\n\n"
    "Great on aprons, bar towels, tees, totes and game-night hoodies.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 18000)


BX, BY0, BY1 = 46.0, -31.0, 20.0     # board half-width, bottom, top
SEAMS = (5.0,)                       # plank seam above the inset
PANEL_Y = -20.4                      # dark inset centre (84 x 16, y -28.4..-12.4)
BAR_Y = 41.0                         # bracket bar centre
CHAIN_X = 30.0


def _centred(t, cx, y_base):
    x0, y0, x1, y1 = t.bounds
    return move(t, cx - (x0 + x1) / 2, y_base - y0)


def _solid(t):
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(t)])


def tankard():
    body = rounded_rect(17, 16, 1.6, -2.5, 0.5)                   # x -11..6, y -7.5..8.5
    handle = ring(6.5, 1.0, 5.4, 2.6).difference(rect(10, 20, 1.5, 0))
    pewter = union(body, handle)
    hoops = [rect(17.4, 2.2, -2.5, -4.6), rect(17.4, 2.2, -2.5, 4.4)]
    foam = union(circle(-9.5, 9.6, 3.2), circle(-5.0, 11.4, 3.6), circle(0.4, 11.0, 3.4),
                 circle(5.0, 9.4, 2.9), rect(17.6, 3.0, -2.5, 8.6),
                 rounded_rect(3.2, 6.0, 1.6, -9.6, 5.2))          # drip down the left
    k, o = 1.15, (-2.5, 1.0)
    sc = lambda g: scale(g, k, k, origin=o)
    return sc(pewter), [sc(h) for h in hoops], sc(foam)


def chain(x):
    eye = ring(x, BY1 + 3.6, 2.5, 1.2)
    oval = ellipse(x, BY1 + 9.0, 2.3, 4.2).difference(ellipse(x, BY1 + 9.0, 1.0, 2.8))
    side = rect(1.6, 7.6, x, BY1 + 15.6)
    return union(eye, oval, side)


def bracket():
    bar = rounded_rect(92, 3.0, 1.2, -3.0, BAR_Y)                  # x -49..43
    plate = rounded_rect(4.0, 22, 1.2, -50.5, BAR_Y - 4)
    brace = LineString([(-49, BAR_Y - 12), (-26, BAR_Y - 1)]).buffer(1.2, cap_style="flat")
    scroll = ring(-37.5, BAR_Y - 6.8, 3.3, 1.8)
    finial = regular_polygon(4, 3.0, 44.5, BAR_Y, rot=0)
    return union(bar, plate, brace, scroll, finial)


def art():
    d = Design()
    board = rounded_rect(2 * BX, BY1 - BY0, 3.0, 0, (BY0 + BY1) / 2)
    rim = board.exterior.buffer(1.1)
    pewter, hoops, foam = tankard()
    mug = union(pewter, foam)
    # TAVERN on a dark painted inset with a gold pin-line (gold reads strongly on it)
    panel = rounded_rect(84, 16, 2.0, 0, PANEL_Y)
    pin = list(panel.buffer(-1.3, join_style="round").exterior.coords)
    word = _centred(block_text("TAVERN", cap=10, stroke=2.7, tracking=2.4), 0, PANEL_Y - 5)
    art_zone = union(mug, panel).buffer(1.6)
    inner = board.buffer(-2.6)                                    # seams/grain stop 1.5 short of the rim

    seams = []
    for y in SEAMS:
        g = LineString([(-BX, y), (BX, y)]).intersection(inner).difference(art_zone)
        seams += [list(s.coords) for s in getattr(g, "geoms", [g]) if s.length > 3]
    seam_bands = [LineString(s).buffer(0.75, cap_style="flat") for s in seams]

    # grain: gentle waves along each plank, clear of seams and art
    grain = []
    planks = [(PANEL_Y + 8, SEAMS[0]), (SEAMS[0], BY1)]
    keep = board.buffer(-3.1).difference(art_zone.buffer(0.6))
    for i, (y0, y1) in enumerate(planks):
        h = y1 - y0
        for j, f in enumerate((0.3, 0.7) if h > 12 else (0.5,)):
            yc = y0 + h * f
            xs = np.linspace(-BX, BX, 60)
            ys = yc + 0.9 * np.sin(xs / 7.0 + i * 1.7 + j * 2.3)
            g = LineString(list(zip(xs, ys))).difference(union(*seam_bands).buffer(1.0)).intersection(keep)
            grain += [list(s.coords) for s in getattr(g, "geoms", [g])
                      if s.geom_type == "LineString" and s.length > 4]

    d.fill(knockout(board, rim, mug, panel, *seam_bands), C_["wood"], angle=0, name="planks")
    for g in grain:
        d.run(g, C_["bark"], name="grain")
    for s in seams:
        d.satin(s, 1.5, C_["bark"], name="seam")
    d.fill(knockout(panel, word), C_["bark"], angle=-30, name="inset panel")
    d.outline(board, C_["bark"], width=2.2, name="board rim")
    d.fill(knockout(pewter, foam, *hoops), C_["pewter"], angle=90, name="tankard")
    for h in hoops:
        d.fill(h.difference(foam), C_["brass"], angle=90, name="hoop")
    d.fill(foam, C_["white"], angle=30, name="foam")
    d.run(pin, C_["gold"], bean=1, name="pin-line")
    d.fill(word, C_["gold"], angle=0, spacing=0.35, name="TAVERN")
    d.fill(bracket(), C_["black"], angle=0, name="bracket")
    for x in (-CHAIN_X, CHAIN_X):
        d.fill(chain(x), C_["black"], angle=90, name="chain")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
