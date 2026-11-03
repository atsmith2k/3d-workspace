"""Foraging Basket: a woven willow basket heaped with toadstools, a fat brown bolete
and golden chanterelles, with a fallen mushroom and leaves beside it.

Spec:
  object:       a mushroom-foraging basket (cozy fantasy / cottagecore) for tees, totes,
                tea towels, aprons and framed hoops
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      emerald (grass), leaf green, moss (leaves), light brown, khaki (basket weave, handle),
                dark brown (rim, weave shadow line), beige (mushroom stems), red
                (toadstool caps), white (spots), clay brown (bolete cap), deep gold
                (chanterelles): 11 colours
  must have:    a 64 mm basket woven in a checker of 8 x 5.5 mm cells in two shades,
                a 70 x 6 mm dark rim and a 4.5 mm handle arching over; a 30 mm red
                toadstool with white spots, a 22 mm bolete, two chanterelles, three leaves
                tucked in; a grass bank with a fallen toadstool and two leaves on it
  density:      everything knocked out under what sews on top; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hollow import C_, SIZES, backfill, close_gaps, small_holes, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Woven foraging basket heaped with toadstools, a bolete and chanterelles"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Mushroom Foraging Basket Embroidery Design",
    "A woven willow basket heaped with red toadstools, a brown bolete and golden chanterelles",
    ["mushroom", "mushrooms", "toadstool", "foraging", "forager", "mushroom basket",
     "cottagecore mushroom", "goblincore", "woodland", "fairy mushroom"],
    "A good morning's foraging: a woven willow basket heaped with a spotted red toadstool, a "
    "fat brown bolete and golden chanterelles, one more mushroom tumbled out on the grass "
    "beside a couple of fallen leaves.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tees, totes, tea towels, "
    "aprons and framed hoops.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 11, 18000)


RIM_Y = -2.0


def basket():
    body = smooth([(-32, RIM_Y), (-30.5, -18), (-26, -31), (-17, -36.5), (0, -38), (17, -36.5),
                   (26, -31), (30.5, -18), (32, RIM_Y)], samples=8)
    body = union(body, rect(64, 3, 0, RIM_Y - 1.0))
    rim = rounded_rect(70, 6, 2.6, 0, RIM_Y)
    t = np.linspace(np.pi, 0, 40)
    handle = strip(np.c_[24 * np.cos(t), RIM_Y + 38 * np.sin(t)], 4.5)
    cells = []
    h = 5.5
    for r in range(7):
        y0 = RIM_Y - 3 - (r + 1) * h
        for i in range(-5, 5):
            x0 = i * 8.0 + (4.0 if r % 2 else 0.0)
            g = rect(8, h, x0 + 4, y0 + h / 2) & body
            if g.area > 3:
                cells.append(((r + i) % 2, g, r))
        # top part band under the rim (y RIM_Y-3..RIM_Y) is covered by the rim
    return body, rim, handle, cells


def toadstool(cx, base, w, h, stem_w, stem_h, tilt=0.0):
    cap = smooth([(cx - w / 2, base + stem_h), (cx - w * 0.46, base + stem_h + h * 0.55),
                  (cx - w * 0.25, base + stem_h + h * 0.92), (cx, base + stem_h + h),
                  (cx + w * 0.25, base + stem_h + h * 0.92), (cx + w * 0.46, base + stem_h + h * 0.55),
                  (cx + w / 2, base + stem_h)], samples=8)
    cap = union(cap, rect(w, 1.6, cx, base + stem_h + 0.4))
    stem = smooth([(cx - stem_w / 2, base), (cx - stem_w * 0.42, base + stem_h * 0.6),
                   (cx - stem_w * 0.38, base + stem_h + 1), (cx + stem_w * 0.38, base + stem_h + 1),
                   (cx + stem_w * 0.42, base + stem_h * 0.6), (cx + stem_w / 2, base)], samples=6)
    o = (cx, base)
    return rotate(cap, tilt, origin=o), rotate(stem, tilt, origin=o)


def chanterelle(cx, base, h, tilt):
    g = poly([(cx - 1.4, base), (cx - 1.8, base + h * 0.5), (cx - h * 0.45, base + h * 0.92),
              (cx - h * 0.2, base + h), (cx + h * 0.2, base + h * 0.96), (cx + h * 0.45, base + h * 0.9),
              (cx + 1.8, base + h * 0.5), (cx + 1.4, base)])
    return rotate(g.buffer(0.8).buffer(-0.8), tilt, origin=(cx, base))


def art():
    d = Design()
    body, rim, handle, cells = basket()
    red_cap, red_stem = toadstool(-7, RIM_Y - 1, 30, 15, 7.0, 13, tilt=-6)
    bol_cap, bol_stem = toadstool(15, RIM_Y - 1, 22, 11, 10.5, 8, tilt=12)
    ch = [chanterelle(-24, RIM_Y - 1, 16, 18), chanterelle(27, RIM_Y - 1, 13, -22)]
    spots = [circle(x, y, r) for x, y, r in ((-15.5, 18.0, 2.2), (-6.0, 24.5, 2.4), (2.5, 19.5, 2.0),
                                             (-10.0, 13.5, 1.6), (6.5, 14.0, 1.5), (-19.5, 12.5, 1.4))]
    spots = [g for g in spots if red_cap.buffer(-0.4).contains(g)]
    f_cap, f_stem = toadstool(38, -37, 14, 7.0, 4.0, 6.0, tilt=-72)
    f_spots = [circle(*c, 1.2) for c in ((41.0, -29.8), (44.8, -33.6))]
    grass = smooth([(-46, -38), (-40, -41.5), (-20, -43.5), (0, -44), (20, -43.5), (40, -42), (50, -38.5),
                    (44, -35.5), (30, -35), (0, -35.5), (-30, -35), (-43, -35.5)], samples=8)
    sprigs = [(move(rotate(M.leaf(19, 7.5, bend=0.1), 150), -27, 6), 150)]
    mouth = ellipse(0, RIM_Y + 3.0, 30, 7.0)                     # the dark inside of the basket
    f_spots = [g for g in f_spots if f_cap.buffer(-0.3).contains(g)]
    leaves = [(move(rotate(M.leaf(20, 8, bend=0.15), 200), -30, -36), 200, M.leaf_vein(20, bend=0.15), (-30, -36)),
              (move(rotate(M.leaf(16, 7, bend=-0.2), 160), -31, -35), 160, M.leaf_vein(16, bend=-0.2), (-31, -35))]
    shrooms = union(red_cap, red_stem, bol_cap, bol_stem, *ch)
    fallen = union(f_cap, f_stem)
    front = union(rim, body)
    handle = close_gaps(handle, shrooms, front, r=2.0)
    shrooms = union(red_cap, red_stem, bol_cap, bol_stem, *ch)
    mouth = union(mouth, small_holes(mouth, shrooms, front, handle, *[l for l, _ in sprigs]))

    # grass under the basket, the fallen mushroom and the leaves
    d.fill(knockout(grass, body, fallen, *[l[0] for l in leaves]), C_["green"], angle=0, name="grass")
    # mushrooms in the basket (stems first, caps over them)
    d.fill(knockout(red_stem, red_cap, front), C_["bone"], angle=90, name="toadstool stem")
    d.fill(knockout(bol_stem, bol_cap, red_cap, red_stem, front), C_["bone"], angle=80, name="bolete stem")
    d.fill(knockout(f_stem, f_cap), C_["bone"], angle=20, name="fallen stem")
    d.fill(knockout(red_cap, *spots, front), C_["red"], angle=70, name="toadstool cap")
    d.fill(knockout(f_cap, *f_spots), C_["red"], angle=20, name="fallen cap")
    d.fill(knockout(bol_cap, red_cap, red_stem, front), C_["rust"], angle=110, name="bolete cap")
    for g in ch:
        d.fill(knockout(g, red_cap, red_stem, bol_cap, bol_stem, front), C_["gold"], angle=90, name="chanterelle")
    for g in spots + f_spots:
        d.fill(g, C_["white"], angle=45, name="spot")
    # leaves tucked into the basket behind the mushrooms, and at the foot
    for g, deg in sprigs:
        d.fill(knockout(g, shrooms, front), C_["leaf"], angle=deg + 70, name="tucked leaf")
    for i, (g, deg, v, at) in enumerate(leaves):
        d.fill(knockout(g, body, *[l[0] for l in leaves[:i]]), C_["leaf"], angle=deg + 60, name="leaf")
    for i, (g, deg, v, at) in enumerate(leaves):
        vis = knockout(g, body, *[l[0] for l in leaves[:i]])
        path = move(rotate(np.asarray(v), deg), *at)
        cut = LineString(path).intersection(shrink(vis, 1.5))
        for s in getattr(cut, "geoms", [cut]):
            if s.geom_type == "LineString" and s.length > 3:
                d.run(list(s.coords), C_["moss"], bean=1, name="leaf vein")
    # basket weave: two shades in a checker, rows alternating direction
    d.fill(knockout(handle, shrooms, front, *[g for g, _ in sprigs]), C_["khaki"], angle=0, name="handle")
    for tone, color in ((0, "khaki"), (1, "wood")):
        for t, g, r in cells:
            if t == tone:
                d.fill(knockout(g, rim), C_[color], angle=0 if tone else 90, name="weave")
    d.fill(knockout(mouth, shrooms, front, handle, *[g for g, _ in sprigs]), C_["bark"], angle=0,
           name="basket mouth")
    d.fill(rim, C_["bark"], angle=0, name="rim")
    d.outline(body.difference(rim), C_["bark"], name="basket edge")
    backfill(d, C_["bark"], max_area=60)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
