"""Tankard & Pie: a cozy table still life: a wooden stave tankard of foaming ale, a
steaming lattice-top cherry pie in a clay dish and a wedge of cheese, on a gingham
tablecloth.

Spec:
  object:       an inn-table supper (cozy fantasy / cottagecore) for tea towels, aprons,
                tote bags, cushions and tees
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (towels, aprons, canvas) with tear-away; knits with cut-away
  threads:      white, amber red, red (gingham, foam), light brown (tankard staves),
                dark brown (stave lines, handle), brass (hoops), clay brown (pie dish),
                khaki (lattice crust), harvest gold (cheese), deep gold (crimped rim,
                cheese holes), beige (steam): 11 colours
  must have:    a 96 x 20 mm three-tone gingham tablecloth band with a scalloped hem;
                a 22 x 32 mm stave tankard with two brass hoops, a handle and spilling
                foam; a 46 mm pie dish with a lattice-top pie (five strips each way over
                red filling) inside a crimped rim; two steam curls; a cheese wedge with
                three holes
  density:      gingham cells overlap 0.3 mm at their corners (no bare pinholes); every
                fill knocked out under what sews on top; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hollow import C_, SIZES, backfill, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Foaming tankard, lattice cherry pie and cheese on a gingham tablecloth"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Tankard and Cherry Pie Embroidery Design",
    "A foaming wooden tankard, a steaming lattice cherry pie and a wedge of cheese on a red gingham tablecloth",
    ["cherry pie", "pie", "tankard", "ale", "cheese", "gingham", "tea towel embroidery",
     "kitchen embroidery", "apron embroidery", "baking", "cozy kitchen", "tavern supper"],
    "Supper at the inn: a wooden stave tankard of foaming ale, a lattice-top cherry pie still "
    "steaming in its clay dish and a wedge of cheese, set out on a red gingham tablecloth.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tea towels, aprons, totes, "
    "cushions and tees.",
    mockups=("tshirt", "tote"),
)

CELL = 6.0
TOP = -22.0          # table edge


def checks(p):
    return standard_checks(p, 11, 22000)


def cloth():
    hem = smooth([(-48, TOP)] + [(x, -42.5 + 1.6 * np.cos((x + 48) / 12 * 2 * np.pi)) for x in np.linspace(-48, 48, 33)]
                 + [(48, TOP)], samples=3)
    hem = hem.buffer(0)
    cells = {0: [], 1: [], 2: []}
    for i in range(16):
        for j in range(4):
            g = rect(CELL + 0.6, CELL + 0.6, -48 + CELL * (i + 0.5), TOP - CELL * (j + 0.5)) & hem
            if g.area > 0.5:
                cells[(i % 2) + (j % 2)].append(g)
    return hem, [union(*cells[k]) for k in (0, 1, 2)]


def tankard():
    body = rect(22, 32, -29, TOP + 14)                   # x -40..-18, y -24..8
    body = union(body, ellipse(-29, TOP - 2, 11, 1.6))
    handle = ring(-39.6, TOP + 15, 7.6, 4.4).difference(rect(10, 30, -34.6, TOP + 15))
    hoops = [rect(22.8, 2.6, -29, y) for y in (TOP + 3.5, TOP + 24.0)]
    foam = union(circle(-37.5, TOP + 30.5, 3.6), circle(-32.0, TOP + 33.4, 4.2), circle(-25.6, TOP + 33.0, 4.0),
                 circle(-20.2, TOP + 30.6, 3.4), rect(23.0, 3.4, -29, TOP + 29.0),
                 rounded_rect(3.4, 7.0, 1.7, -21.2, TOP + 26.0))
    staves = [[(x, TOP - 2.6), (x, TOP + 28.5)] for x in (-35.0, -29.0, -23.0)]
    return body, handle, hoops, foam, staves


def pie():
    cx = 14.0
    dish = poly([(cx - 24, TOP + 3), (cx - 21, TOP - 5.5), (cx + 21, TOP - 5.5), (cx + 24, TOP + 3)])
    dish = union(dish, ellipse(cx, TOP - 5.5, 21, 1.8))
    top = ellipse(cx, TOP + 3.0, 24, 7.2)
    crimp = top.difference(ellipse(cx, TOP + 3.0, 20.4, 5.2))
    crimp = union(crimp, *[circle(cx + 22.2 * np.cos(a), TOP + 3.0 + 6.2 * np.sin(a), 1.5)
                           for a in np.linspace(0, 2 * np.pi, 24, endpoint=False)]) & top.buffer(0.9)
    filling = ellipse(cx, TOP + 3.0, 21.2, 5.8)
    strips = []
    for k in np.linspace(-14, 14, 5):
        strips.append(strip(np.array([(cx + k - 5, TOP - 4), (cx + k + 5, TOP + 10)]), 2.6))
        strips.append(strip(np.array([(cx + k + 5, TOP - 4), (cx + k - 5, TOP + 10)]), 2.6))
    lattice = union(*strips) & filling
    steam = [spline([(cx - 6, TOP + 11), (cx - 3.5, TOP + 15), (cx - 6.5, TOP + 19), (cx - 4, TOP + 23)], samples=8),
             spline([(cx + 5, TOP + 11), (cx + 7.5, TOP + 15), (cx + 4.5, TOP + 19.5), (cx + 7, TOP + 24)], samples=8)]
    return dish, crimp, filling, lattice, steam


def art():
    d = Design()
    hem, (white, wine, red) = cloth()
    body, handle, hoops, foam, staves = tankard()
    dish, crimp, filling, lattice, steam = pie()
    cheese = poly([(-16, TOP - 12), (-2, TOP - 12), (-2, TOP - 4), (-16, TOP - 9.5)])
    holes = [circle(-6.5, TOP - 8.6, 1.3), circle(-11, TOP - 10.0, 1.0), circle(-4.2, TOP - 6.0, 0.9)]
    holes = [g for g in holes if cheese.buffer(-0.4).contains(g)]
    mug = union(body, handle, foam)
    pie_all = union(dish, crimp, filling)
    on_cloth = union(mug, pie_all, cheese)

    # 1-3 gingham: white, the half-tone stripes, the full red squares
    d.fill(knockout(white, wine, red, on_cloth), C_["white"], angle=0, name="gingham white")
    d.fill(foam, C_["white"], angle=30, name="foam")
    d.fill(knockout(wine, red, on_cloth), C_["wine"], angle=0, name="gingham stripe")
    d.fill(knockout(red, on_cloth), C_["red"], angle=0, name="gingham red")
    d.fill(knockout(filling, lattice, crimp), C_["red"], angle=60, name="cherry filling")
    # tankard
    d.fill(knockout(body, foam, *hoops), C_["wood"], angle=90, name="tankard")
    for st in staves:
        g = LineString(st).intersection(shrink(body, 0.8)).difference(grow(union(foam, *hoops), 0.9))
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "LineString" and q.length > 1.5:
                d.run(list(q.coords), C_["bark"], bean=1, name="stave line")
    d.fill(knockout(handle, body), C_["bark"], angle=0, name="handle")
    for h in hoops:
        d.fill(knockout(h, foam), C_["brass"], angle=90, name="hoop")
    # pie
    d.fill(knockout(dish, crimp, filling), C_["rust"], angle=0, name="pie dish")
    d.fill(knockout(lattice, crimp), C_["khaki"], angle=0, name="lattice")
    d.fill(knockout(cheese, *holes), C_["yellow"], angle=20, name="cheese")
    d.fill(crimp, C_["gold"], angle=90, name="crimped rim")
    for g in holes:
        d.fill(g, C_["gold"], angle=0, name="cheese hole")
    for s in steam:
        d.run(s, C_["bone"], bean=1, name="steam")
    backfill(d, C_["wine"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
