"""Hearth & Kettle: a stone fireplace with a log fire, a copper kettle hanging from an
iron crane over the flames, and a teapot and two mugs on the oak mantel.

Spec:
  object:       a cozy cottage hearth (generic cozy fantasy, no named place) for tea
                towels, aprons, cushions, tees and framed hoops
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (towels, aprons, canvas) with tear-away; knits with cut-away
  threads:      gray, silver (stones), charcoal (firebox, mortar lines), light brown
                (mantel, logs), clay brown (copper kettle), red, orange, harvest gold
                (fire, kettle glint), black (crane, bail, mantel edge), emerald (teapot),
                amber red (mugs), beige (steam): 12 colours
  must have:    an 84 x 66 mm stone surround on a 96 mm hearth slab, a round-topped
                firebox 50 mm wide with a ring of nine arch stones; two crossed logs and
                three-tone flames; an 18 mm copper kettle with a 1.2 mm black
                outline on a bail, hung clear above a low fire, from a black crane
                with steam curling from its spout; a 100 x 7 mm oak mantel with an
                emerald teapot and two amber mugs on it
  density:      stones and firebox knocked out under fire, kettle, crane; mortar lines
                are single runs; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _hollow import C_, SIZES, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Stone hearth with a log fire, a hanging copper kettle and a teapot on the mantel"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Cozy Hearth and Kettle Embroidery Design",
    "A stone cottage fireplace with a crackling log fire, a copper kettle on an iron crane and a teapot on the mantel",
    ["hearth", "fireplace", "kettle", "teapot", "tea time", "cottage kitchen", "cozy kitchen",
     "tea towel embroidery", "apron embroidery", "cottagecore kitchen"],
    "Tea by the fire: a round-topped stone hearth with a crackling log fire, a copper "
    "kettle swinging on its iron crane with steam curling from the spout, and a green teapot "
    "and two mugs waiting on the oak mantel.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tea towels, aprons, "
    "cushions, tees and framed hoops.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 12, 22000)


SURROUND = rect(84, 66, 0, -6.5)              # x -42..42, y -39.5..26.5
SLAB = rect(96, 6, 0, -42.5)                  # y -45.5..-39.5
OPEN_Y = -6.5                                 # where the firebox arch springs (a course joint)
OPENING = union(rect(50, 33, 0, -23.0), ellipse(0, OPEN_Y, 25, 17))
ARCH = ellipse(0, OPEN_Y, 32, 23.3).difference(OPENING) & rect(80, 30, 0, OPEN_Y + 15)
MANTEL = rect(100, 7, 0, 30)                  # y 26.5..33.5


def _wedges(band, cx, cy, n):
    """The arch band cut into n stones by rays from (cx, cy)."""
    out = []
    for i in range(n):
        a0, a1 = np.pi * i / n, np.pi * (i + 1) / n
        sector = poly([(cx, cy)] + [(cx + 60 * np.cos(a), cy + 60 * np.sin(a))
                                    for a in np.linspace(a0, a1, 8)])
        out.append(band & sector)
    return out


def _wall_stones():
    """Staggered courses of stones over the surround (outside the arch and firebox)."""
    wall = SURROUND.difference(ARCH).difference(OPENING)
    stones, joints = [], []
    h = 66 / 8
    for r in range(8):
        y0 = -39.5 + r * h
        off = 0 if r % 2 else 7.0
        for i in range(0, 8):
            x0 = -42 - off + i * 14.0
            g = rect(14, h, x0 + 7, y0 + h / 2) & wall
            if not g.is_empty and g.area > 4:
                stones.append(((r + i) % 2, g))
            joints.append([(x0, y0), (x0, y0 + h)])
        if r:
            joints.append([(-42, y0), (42, y0)])
    return wall, stones, joints


def flames():
    outer = smooth([(-17, -33), (-19, -24), (-15, -14), (-16, -6), (-11, -12), (-9, -20), (-3, -21),
                    (3, -21), (9, -20), (11, -11), (16, -4), (16, -14), (19, -24), (17, -33)], samples=8)
    mid = smooth([(-12, -33), (-13, -26), (-10, -18), (-6, -22), (0, -21.5), (6, -22),
                  (10, -18), (13, -26), (12, -33)], samples=8)
    core = smooth([(-7, -33), (-7.5, -28), (-4, -24), (0, -25.5), (4, -24), (7.5, -28), (7, -33)],
                  samples=8)
    low = lambda g: scale(g, 1.0, 0.72, origin=(0, -33))          # the fire burns low under the kettle
    return low(outer), low(mid), low(core)


def kettle():
    body = union(ellipse(0, -11, 11, 8.5), rect(18, 4, 0, -17.6))
    lid = ellipse(0, -3.0, 6.5, 2.6)
    knob = circle(0, -0.2, 2.3)          # wide enough for the 1.2 mm outline to wrap without piling up
    sp = np.asarray(spline([(8, -10), (13, -7), (16.5, -2.5)], samples=8))
    spout = strip(sp, np.linspace(4.2, 2.4, len(sp)))
    glint = smooth([(-8, -7.5), (-6, -5.5), (-3.5, -5.5), (-6.5, -9.5), (-8.5, -11)], samples=6)
    k, o = 0.82, (0, -3.0)
    place = lambda g: move(scale(g, k, k, origin=o), 0, 2.0)     # smaller and higher, clear of the fire
    tip = (sp[-1] - np.array(o)) * k + np.array(o) + [0, 2.0]
    return place(union(body, lid, knob, spout)), place(glint), tip


def art():
    d = Design()
    wall, stones, joints = _wall_stones()
    arch_stones = _wedges(ARCH, 0, OPEN_Y, 9)
    outer, mid, core = flames()
    logs = [strip(np.array([(-19, -38), (17, -31)]), 5.6), strip(np.array([(19, -38), (-15, -31)]), 5.6)]
    kbody, glint, tip = kettle()
    bail = arc(0, -4.3, 9.4, 10, 170)
    crane = union(rect(2.6, 46, -21.6, -16.5), rect(25.0, 2.6, -10.4, 7.0),
                  LineString([(-21, -4), (-11, 6.5)]).buffer(1.1, cap_style="flat"))
    # the hook joins the arm to the top of the bail only: reaching down onto the knob it
    # stacked crane fill, bail satin and kettle outline in one spot (3.6 layers)
    hook = rect(1.6, 1.4, 0, 5.4)
    iron = union(crane, hook)
    steam = [spline([(tip[0] + 0.5, tip[1] + 2.2), (tip[0] + 3.5, tip[1] + 5.5), (tip[0] + 1.0, tip[1] + 9.0),
                     (tip[0] + 3.0, tip[1] + 12.5)], samples=8),
             spline([(tip[0] + 3.4, tip[1] + 1.4), (tip[0] + 6.5, tip[1] + 3.6), (tip[0] + 5.6, tip[1] + 7.0)],
                    samples=8)]
    fire_all = union(outer, *logs)
    kband = grow(kbody, 0.6)                                       # the kettle and its black outline
    bail_band = LineString(bail).buffer(0.8)

    # teapot and mugs on the mantel
    pot = union(ellipse(-30, 40.5, 9.5, 7.0), ellipse(-30, 47.6, 5.0, 1.8), circle(-30, 50.0, 1.6),
                strip(np.asarray(spline([(-37.5, 39), (-42.5, 43), (-44.5, 47)], samples=6)),
                      np.linspace(3.6, 2.2, 6)),
                ring(-20.0, 41.0, 4.2, 2.4))
    pot = pot.difference(rect(30, 10, -30, 28.5))
    mugs = [union(rect(7.5, 9.5, x, 38.25), ring(x + 4.6, 38.5, 3.2, 1.7)) for x in (18, 31)]

    # 1-2 stones in two shades
    for tone, color in ((0, "gray"), (1, "silver")):
        for i, g in enumerate(arch_stones):
            if i % 2 == tone:
                d.fill(knockout(g, iron), C_[color], angle=90 + 20 * i, name="arch stone")
        for t, g in stones:
            if t == tone:
                d.fill(g, C_[color], angle=0 if tone else 90, name="stone")
    d.fill(SLAB, C_["silver"], angle=0, name="hearth slab")
    # 3 charcoal: firebox back, then mortar lines over the stones
    d.fill(knockout(OPENING, fire_all, kband, iron, bail_band), C_["charcoal"], angle=45, name="firebox")
    for j in joints:
        g = LineString(j).intersection(shrink(wall, 0.6))
        for s in getattr(g, "geoms", [g]):
            if s.geom_type == "LineString" and s.length > 1.5:
                d.run(list(s.coords), C_["charcoal"], name="mortar")
    for i in range(1, 9):
        a = np.pi * i / 9
        p0 = (25.8 * np.cos(a), OPEN_Y + 17.8 * np.sin(a))
        p1 = (31.2 * np.cos(a), OPEN_Y + 22.5 * np.sin(a))
        g = LineString([p0, p1]).difference(grow(iron, 0.8))
        if g.length > 1.5:
            d.run(list(g.coords), C_["charcoal"], name="arch joint")
    # 4 light brown: logs, mantel
    for i, g in enumerate(logs):
        d.fill(knockout(g, kband, *logs[i + 1:]), C_["wood"], angle=[100, 80][i], name="log")
    d.fill(MANTEL, C_["wood"], angle=0, name="mantel")
    # 5 copper kettle
    d.fill(knockout(kbody, glint, iron), C_["rust"], angle=70, name="kettle")
    # 6-8 fire
    d.fill(knockout(outer, mid, kband, *logs), C_["red"], angle=90, name="flame outer")
    d.fill(knockout(mid, core, kband, *logs), C_["flame"], angle=90, name="flame")
    d.fill(knockout(core, kband, *logs), C_["yellow"], angle=90, name="flame core")
    d.fill(glint, C_["yellow"], angle=30, name="kettle glint")
    # 9 black: crane, hook, bail, the mantel's lower edge
    d.fill(iron, C_["black"], angle=0, name="crane")
    d.satin(bail, 1.2, C_["black"], name="bail")
    d.outline(kbody, C_["black"], width=1.2, name="kettle outline")
    d.run([(-48.6, 27.6), (48.6, 27.6)], C_["black"], bean=1, name="mantel edge")
    # 10 teapot, 11 mugs, 12 steam
    d.fill(pot, C_["green"], angle=60, name="teapot")
    for g in mugs:
        d.fill(g, C_["wine"], angle=90, name="mug")
    for st in steam:
        d.run(st, C_["bone"], bean=1, name="steam")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
