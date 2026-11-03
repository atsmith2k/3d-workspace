"""Hedgehog in a Waistcoat: a storybook hedgehog standing in a green waistcoat with gold
buttons and a watch chain, holding a teacup, on a grass tuft.

Spec:
  object:       a dapper woodland hedgehog (cozy fantasy / storybook, original character)
                for tees, totes, baby clothes, cushions and framed hoops
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      leaf green (grass), dark brown (spines), light brown (spine strokes,
                feet), khaki (face, ear, arms), white (shirt front), emerald
                (waistcoat), deep gold (buttons, watch chain), amber red (teacup),
                black (eye, nose): 9 colours
  must have:    a 60 x 72 mm spiny coat with a zigzag edge on the back and top and
                light-brown spine strokes; a pointed khaki face with a black nose and
                eye; a 31 x 44 mm waistcoat with a V front over a white shirt, three
                2.6 mm gold buttons and a bean-run watch chain; arms holding a 9 mm
                teacup; two feet on a tuft of tapered satin grass blades
  density:      coat knocked out under face, waistcoat, arms; strokes are bean runs
                2 mm inside the coat; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hollow import C_, SIZES, backfill, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Storybook hedgehog in a green waistcoat holding a teacup"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Hedgehog in a Waistcoat Embroidery Design",
    "A storybook hedgehog in a green waistcoat with gold buttons and a watch chain, holding a teacup",
    ["hedgehog", "woodland animal", "storybook animal", "waistcoat", "teacup", "tea time",
     "cute hedgehog", "baby embroidery", "nursery", "woodland nursery", "animal embroidery"],
    "A very respectable hedgehog, dressed for afternoon tea in a green waistcoat with gold buttons "
    "and a watch chain, standing on a tuft of grass with a teacup held carefully in both paws.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tees, totes, baby clothes, "
    "cushions and framed hoops.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 9, 18000)


def coat():
    """The spiny coat: an egg with spikes over the back (angles 55..290 deg)."""
    cx, cy, rx, ry = -6.0, 2.0, 27.0, 34.0
    pts = []
    n = 72
    for i in range(n):
        a = np.radians(i * 360 / n)
        deg = i * 360 / n
        spiky = 50 <= deg <= 295
        k = 1.0 + (0.11 if (spiky and i % 2 == 0) else 0.0)
        pts.append((cx + rx * k * np.cos(a), cy + ry * k * np.sin(a)))
    return poly(pts), (cx, cy, rx, ry)


def art():
    d = Design()
    body, (cx, cy, rx, ry) = coat()
    face = smooth([(0, 33), (9, 31), (17, 25), (25, 19), (32, 14.5), (32.5, 11.5), (25, 9.5), (17, 7.5),
                   (10, 8), (4, 14)], samples=8)
    ear = ellipse(5.5, 30.5, 3.4, 3.8)
    vest = ellipse(9, -11, 15.5, 22)
    shirt = poly([(2.5, 11), (15.5, 11), (9, -5)]) & vest
    vest_only = vest.difference(shirt)
    buttons = [circle(9.0, y, 1.3) for y in (-9.5, -15.5, -21.5)]
    chain = spline([(9.6, -15.5), (14, -18.5), (19.5, -16.0)], samples=8)
    arm1 = strip(np.asarray(spline([(-1, 0), (8, -5), (19.5, -7.2)], samples=6)), [4.6, 4.2, 3.8])
    arm2 = strip(np.asarray(spline([(17.5, 4.5), (22, 1.8), (24.0, -2.6)], samples=6)), [3.8, 3.5, 3.2])
    cup = union(poly([(17.5, -3.5), (27, -3.5), (25.8, -10.5), (18.7, -10.5)]), ellipse(22.2, -11.0, 4.4, 1.0))
    handle_path = arc(26.4, -6.8, 2.2, -95, 95)              # a satin loop off the cup's side
    cup_handle = LineString(handle_path).buffer(0.7)
    cupg = union(cup, cup_handle)
    feet = [ellipse(-1, -36.0, 6.5, 2.8), ellipse(15, -35.5, 6.5, 2.8)]
    nose = circle(32.0, 13.0, 1.9)
    eye = ellipse(20.5, 20.0, 1.3, 1.7)
    front = union(face, ear, vest, arm1, arm2, cupg, *feet)

    strokes = []
    rng = np.random.default_rng(7)
    inside = shrink(body, 2.0).difference(grow(front, 1.6))
    for r in (0.45, 0.62, 0.79):
        for a in np.arange(40, 320, 15 + 6 * r) + rng.uniform(-3, 3, 1)[0]:
            t = np.radians(a)
            p0 = (cx + rx * r * np.cos(t), cy + ry * r * np.sin(t))
            p1 = (cx + rx * (r + 0.13) * np.cos(t + 0.06), cy + ry * (r + 0.13) * np.sin(t + 0.06))
            g = LineString([p0, p1]).intersection(inside)
            if g.geom_type == "LineString" and g.length > 2.5:
                strokes.append(list(g.coords))

    blades = []
    for x0 in np.linspace(-16, 30, 12):
        h = 5 + 3 * abs(np.sin(x0))
        lean = 0.3 if x0 % 2 else -0.3
        blades.append(M.blade((x0, -39.5), h, lean=lean, width=1.8))

    # 1 grass behind the feet
    for path, w in blades:
        d.satin(path, w, C_["leaf"], name="grass blade", taper=True)
    # 2 dark brown coat, 3 light brown strokes and feet
    d.fill(knockout(body, front), C_["bark"], angle=60, name="spines")
    for s in strokes:
        d.run(s, C_["wood"], bean=1, name="spine stroke")
    for g in feet:
        d.fill(g, C_["wood"], angle=0, name="foot")
    # 4 khaki face, ear, arms
    d.fill(knockout(face, nose, eye, ear), C_["khaki"], angle=-20, name="face")
    d.fill(ear, C_["khaki"], angle=60, name="ear")
    d.fill(knockout(arm1, cupg, arm2), C_["khaki"], angle=-15, name="arm")
    d.fill(knockout(arm2, cupg), C_["khaki"], angle=70, name="arm")
    # 5 shirt, 6 waistcoat
    d.fill(knockout(shirt, face), C_["white"], angle=90, name="shirt")
    d.fill(knockout(vest_only, *buttons, arm1, arm2, cupg), C_["green"], angle=80, name="waistcoat")
    # 7 gold buttons and chain, 8 teacup, 9 eye and nose
    for b in buttons:
        d.fill(knockout(b, arm1), C_["gold"], angle=0, name="button")
    g = LineString(chain).difference(grow(union(*buttons, arm1, cupg), 0.6))
    for q in getattr(g, "geoms", [g]):
        if q.length > 1.5:
            d.run(list(q.coords), C_["gold"], bean=1, name="watch chain")
    d.fill(knockout(cup, arm2), C_["wine"], angle=0, name="teacup")
    d.satin(handle_path, 1.4, C_["wine"], name="cup handle")
    d.fill(nose, C_["black"], angle=0, name="nose")
    d.fill(eye, C_["black"], angle=90, name="eye")
    backfill(d, C_["bark"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
