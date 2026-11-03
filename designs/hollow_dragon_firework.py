"""Dragon Firework: a round night-sky patch over a party field: a firework dragon of
orange fire with a golden belly and a trail of sparks loops over a striped party
pavilion and a string of lanterns, with bursts and stars in the sky.

Spec:
  object:       a birthday-party firework shaped like a dragon (cozy fantasy, original
                art) on a round sew-on patch, for patches, jackets, totes, tees and hoodies
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       twill patch blank with tear-away (patch); cut-away on knits
  threads:      navy (sky), emerald (field), red (pavilion stripes), white (pavilion, stars),
                dark brown (poles, lantern string), orange (dragon), harvest gold
                (dragon belly, bursts), deep gold (sparks, lanterns, border): 8 colours
  must have:    a 92 mm round patch with a 3.2 mm deep-gold satin border sewn last as
                one ring; a navy sky; a 70 mm dragon (S-curved body with a spiked ridge, 
                a big scalloped bat wing with gold finger bones, a horned head breathing sparks) with a gold belly stripe and a curling trail of nine sparks
                off its tail; two 14-16 mm bursts of radiating rays; four small stars; a
                rolling field with an 18 mm red and white striped pavilion with a pennant
                and a string of seven lanterns between two poles
  density:      sky and field knocked out under everything; rays and string are bean
                runs on the sky; max 3.5
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *

from _hollow import C_, SIZES, backfill, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Round night-sky patch: a firework dragon over a party field with a pavilion and lanterns"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Dragon Firework Patch Embroidery Design",
    "A round night-sky patch: a firework shaped like a dragon loops over a party pavilion and lanterns",
    ["dragon firework", "firework", "fireworks", "dragon", "birthday party", "party", "night sky",
     "patch embroidery", "badge embroidery", "celebration", "summer festival"],
    "The finest birthday party the hill has ever seen: a firework shaped like a dragon bursts over the "
    "party field and loops across the night sky in orange fire with a golden belly, trailing "
    "sparks over a striped pavilion, a string of lanterns and two starbursts, all inside a round "
    "patch with a gold satin border.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great as a sew-on patch, and on "
    "jackets, hoodies, totes and tees.",
    mockups=("tshirt", "tote"),
)

R = 46.0
BORDER = 3.2


def checks(p):
    return standard_checks(p, 8, 20000)


def tube(path, widths):
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / 0.25)))
    pts = np.c_[np.interp(t, s, path[:, 0]), np.interp(t, s, path[:, 1])]
    w = np.interp(np.linspace(0, 1, len(pts)), np.linspace(0, 1, len(widths)), widths)
    return union(*[Point(*q).buffer(r / 2, quad_segs=10) for q, r in zip(pts, w)]).simplify(0.05)


def dragon():
    """(body + head + horns + spikes, belly, [near wing, far wing], eye, spark trail path,
    mouth sparks centres)."""
    spine = np.asarray(spline([(-34, 0), (-25, 10), (-13, 12), (-3, 5), (7, 6), (15, 13), (20, 19)], samples=12))
    w = np.interp(np.linspace(0, 1, len(spine)), np.linspace(0, 1, 7), [1.4, 3.2, 5.6, 7.2, 7.2, 6.2, 5.0])
    body = tube(spine, w)
    tan = np.gradient(spine, axis=0)
    tan /= np.linalg.norm(tan, axis=1)[:, None]
    left = np.c_[-tan[:, 1], tan[:, 0]]                                     # the back
    # belly: a stripe along the lower side of the thick middle
    i0, i1 = len(spine) // 5, len(spine) - len(spine) // 6
    mid = spine[i0:i1] - left[i0:i1] * (w[i0:i1, None] * 0.22)
    belly = strip(mid, np.interp(np.linspace(0, 1, len(mid)), [0, 0.5, 1], [1.4, 2.6, 1.8]))
    # spine ridge: little spikes along the back every ~5 mm
    spikes = []
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(spine, axis=0), axis=1))]
    for t in np.arange(8, s[-1] - 6, 5.0):
        k = int(np.searchsorted(s, t))
        p, n, u = spine[k], left[k], tan[k]
        base = p + n * (w[k] / 2 - 0.4)
        spikes.append(poly([tuple(base - u * 1.4), tuple(base + n * 2.6 + u * 0.4), tuple(base + u * 1.4)]))
    # head facing right: skull, snout, jaw, swept-back horns
    hp = [(-2, 2.6), (3, 4.2), (8, 3.4), (12.5, 2.4), (14.6, 0.8), (14.2, -0.8), (9.5, -1.0), (7.0, -2.6),
          (2.0, -3.6), (-2.2, -2.4)]
    head = smooth(hp, samples=6)
    horns = union(poly([(0.0, 3.0), (-6.5, 8.6), (2.6, 3.8)]), poly([(3.2, 3.6), (-2.0, 9.8), (5.4, 3.6)]))
    eye_l = circle(6.2, 1.4, 0.95)
    place = lambda g: move(rotate(g, -8, origin=(0, 0)), 19.0, 19.5)
    head, horns, eye = place(head), place(horns), place(eye_l)
    snout = place(Point(14.4, 0.0).buffer(0.01)).centroid
    # bat wings: leading edge up to the tip, scalloped trailing edge
    def wing(root, elbow, tip, fingers, back):
        pts = [root, elbow, tip]
        prev = tip
        for f in fingers + [back]:
            mx, my = (prev[0] + f[0]) / 2, (prev[1] + f[1]) / 2
            # the membrane sags between finger tips, toward the wing root
            pts += [(mx + (elbow[0] - mx) * 0.38, my + (elbow[1] - my) * 0.38), f]
            prev = f
        return poly(pts).buffer(0.5).buffer(-0.5)
    near = wing((7, 8), (3, 23), (-3, 35), [(-11, 31), (-17, 24)], (-11, 12))
    sparks_path = np.asarray(spline([tuple(spine[0]), (-39, -7), (-36, -15), (-28, -16), (-25, -10)], samples=10))
    mouth = [(snout.x + 3.0, snout.y - 0.6, 1.8), (snout.x + 6.4, snout.y - 1.8, 1.4), (snout.x + 4.6, snout.y + 2.2, 1.2)]
    bones = [[(3.2, 22), (-11, 31)], [(3.6, 21), (-17, 24)], [(4.6, 17), (-11, 12)]]
    return union(body, head, horns, *spikes), belly, [near], eye, sparks_path, mouth, bones


def burst(cx, cy, r, n=12, start=0.0):
    rays = []
    for i in range(n):
        a = np.radians(start + 360 * i / n)
        r1 = r * (1.0 if i % 2 == 0 else 0.7)
        rays.append([(cx + 1.4 * np.cos(a), cy + 1.4 * np.sin(a)), (cx + r1 * np.cos(a), cy + r1 * np.sin(a))])
    return rays


def art():
    d = Design()
    disc = circle(0, 0, R - BORDER / 2, res=256)
    inner = tuck(disc, BORDER)
    field = smooth([(-50, -24), (-30, -18), (-10, -22), (12, -16), (32, -21), (50, -16), (50, -50), (-50, -50)], samples=8) & inner
    # pavilion: striped body, roof, pennant pole
    px, py = -18.0, -20.0
    tent_body = rect(18, 9, px, py - 4.5 + 0.0)
    roof = poly([(px - 11, py), (px, py + 9), (px + 11, py)])
    tent = union(tent_body, roof)
    stripes = [rect(3.0, 30, px + x, py) & tent for x in (-7.5, -1.5, 4.5)]
    door = union(rect(4.4, 5.0, px, py - 6.5), circle(px, py - 4.0, 2.2)) & tent_body
    pole_t = rect(1.2, 4.6, px, py + 11.0)
    pennant = poly([(px + 0.6, py + 13.2), (px + 6.0, py + 11.8), (px + 0.6, py + 10.4)])
    # lantern string between two poles
    poles = [rect(1.4, 16, 6, -12.5), rect(1.4, 14, 36, -14.5)]
    sx = np.linspace(6.7, 35.3, 30)
    sy = -5.0 + (-7.6 + 5.0) * (1 - ((sx - 21) / 14.3) ** 2) + 0.0 * sx
    string = np.c_[sx, sy]
    lan_x = np.linspace(10, 32, 7)
    lan_y = np.interp(lan_x, sx, sy) - 1.8
    lanterns = [ellipse(x, y, 1.3, 1.6) for x, y in zip(lan_x, lan_y)]

    dg, belly, wings, eye, sparks_path, mouth, bones = dragon()
    sparks = []
    seg = np.linalg.norm(np.diff(sparks_path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    for i, t in enumerate(np.linspace(3.0, s[-1], 9)):
        x, y = np.interp(t, s, sparks_path[:, 0]), np.interp(t, s, sparks_path[:, 1])
        rr = 2.6 - 1.2 * i / 8
        sparks.append(star(4, rr, rr * 0.45, x, y, rot=90 + 20 * i))
    sparks += [star(4, r, r * 0.45, x, y, rot=10) for x, y, r in mouth]
    bursts = burst(-31, 20, 6.5, start=10) + burst(30, -2, 7.0, start=0)
    stars = [star(4, 2.0, 0.8, x, y) for x, y in ((-36, 14), (-6, 38), (36, 16), (30, 34))]
    stars = [g for g in stars if not g.intersects(union(dg, *wings).buffer(2.5))]

    everything = union(field, tent, pole_t, pennant, *poles, *lanterns, dg, *wings, *sparks, *stars)
    ray_bands = union(*[LineString(r).buffer(0.6) for r in bursts])
    string_band = LineString(string).buffer(0.6)
    # 1 sky, 2 field
    d.fill(knockout(inner, everything), C_["navy"], angle=30, name="sky")
    d.fill(knockout(field, tent, *poles), C_["green"], angle=-10, name="field")
    # 3 red: roof and stripes, pennant; 4 white: body between the stripes, stars
    d.fill(knockout(roof, pole_t), C_["red"], angle=45, name="roof")
    for g in stripes:
        d.fill(knockout(g.difference(roof), door), C_["red"], angle=90, name="stripe")
    d.fill(pennant, C_["red"], angle=0, name="pennant")
    d.fill(knockout(tent_body, door, *stripes), C_["white"], angle=90, name="pavilion")
    for g in stars:
        d.fill(g, C_["white"], angle=0, name="star")
    # 5 dark brown: door, poles, string
    d.fill(door, C_["bark"], angle=90, name="door")
    for g in poles + [pole_t]:
        d.fill(g, C_["bark"], angle=90, name="pole")
    g = LineString(string).difference(union(*lanterns).buffer(0.6))
    for q in getattr(g, "geoms", [g]):
        if q.length > 1.2:
            d.run(list(q.coords), C_["bark"], name="lantern string")
    # 6 orange dragon, 7 harvest gold belly and bursts
    d.fill(knockout(dg, belly, eye, *wings), C_["flame"], angle=60, name="dragon")
    d.fill(knockout(wings[0], dg), C_["flame"], angle=110, name="near wing")
    d.fill(belly, C_["yellow"], angle=0, name="belly")
    for r in bursts:
        d.run(r, C_["yellow"], bean=1, name="burst ray")
    for b in bones:
        g = LineString(b).intersection(shrink(wings[0], 1.4)).difference(grow(dg, 1.0))
        for q in getattr(g, "geoms", [g]):
            if q.geom_type == "LineString" and q.length > 2:
                d.run(list(q.coords), C_["yellow"], bean=1, name="wing bone")
    # 8 deep gold: sparks, lanterns, eye, border
    for g in sparks:
        d.fill(g, C_["gold"], angle=0, name="spark")
    for g in lanterns:
        d.fill(g, C_["gold"], angle=90, name="lantern")
    d.fill(eye, C_["gold"], angle=0, name="eye")
    d.outline(disc, C_["gold"], width=BORDER, name="border")
    backfill(d, C_["navy"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
