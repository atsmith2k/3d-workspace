"""The Moon tarot card (XVIII): a large pale moon with a serene sleeping face and a ring of
gold rays, dripping drops of light between two distant towers, a wolf howling from a
rise, a winding path up from a rippled pool.

Spec:
  object:       tarot card "XVIII - THE MOON" (original scene; tarot imagery is centuries-
                old public domain, no published deck's artwork copied), part of the Arcana
                & Ink tarot series; tees, hoodies, totes, tarot bags, patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7); the card is
                66 x 100 nominal (about 59 x 90 at 4x4, 106 x 160 at 5x7)
  fabric:       knits with cut-away; wovens, canvas and tarot bags with tear-away
  threads:      bone (card face, path), navy (night sky, tower windows, plaques), peacock
                (land), blue (pool), white (moon, ripples), black (wolf), pewter (towers,
                moon face, wolf rim light), deep gold (rays, drops of light, stars, frame,
                lettering): 8 colours
  frame:        the series frame (`_tarot.py`): 2.4 mm gold outer border, 1.3 mm inner
                rule with notched corners and gold corner diamonds, 1.3 mm picture frame,
                "XVIII" in the top plaque between two diamonds, "THE MOON" in the bottom
                banner, block lettering 6.8 mm caps nominal (6.1 mm at 4x4), counters
                filled in the banner colour
  must have:    a 21 mm white moon sewn in a contour fill (rows follow the rim) with a
                sleeping face in pewter bean runs and 12 alternating tapered gold satin
                rays; four gold drops of light; two crenellated pewter towers 15 mm tall on the horizon
                with navy windows; a black wolf about 21 x 25 mm sitting in profile on a rise at the
                left, muzzle raised, pointed ears, chest ruff, bushy tail on the ground,
                a 1.3 mm pewter rim-light satin along its back;
                a bone path winding from the pool to the horizon, 6 mm wide at the pool
                narrowing to 1.6 mm; a blue pool with white ripple runs; four gold stars
  density:      every fill knocked out under everything above it; runs sew on the moon
                and pool only; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401
import _tarot as T

DESCRIPTION = "Tarot card XVIII, The Moon: a serene moon dripping light over two towers, a howling wolf and a winding path"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "The Moon Tarot Card Embroidery Design",
    "Tarot card XVIII, The Moon: a serene full moon dripping light over two towers, a howling "
    "wolf and a winding path, framed as a bone-and-gold tarot card",
    ["tarot", "tarot card", "the moon tarot", "the moon", "major arcana", "witchy", "occult",
     "celestial", "full moon", "howling wolf", "moon phase", "tarot embroidery"],
    "Card XVIII of the Arcana & Ink tarot series: a pale full moon with a calm, sleeping face "
    "and a ring of gold rays drips drops of light between two distant towers, while a wolf "
    "howls from a rise and a path winds up from a rippling pool. The scene sits in a bone "
    "card face with a gold double border, notched corners, a numeral plaque and the card "
    "name in bold block letters.\n\n"
    "Great on hoodies, tees, tote bags, tarot pouches and night-sky patches, and pairs with "
    "The Mage and The Tower from the same series.",
    mockups=("tshirt", "tote"),
)

ORDER = ["bone", "navy", "peacock", "blue", "white", "black", "pewter", "gold"]

MX, MY, MR = 0.0, 15.0, 10.5      # moon


def checks(p):
    return standard_checks(p, len(ORDER), 20000)


def sparkle(x, y, r):
    return star(4, r, r * 0.3, x, y, rot=90)


def drop(x, y, r):
    """Teardrop of light, point up, round bottom at (x, y)."""
    return union(circle(x, y, r, 40), poly([(x - r * 0.92, y + r * 0.4), (x, y + r * 2.6), (x + r * 0.92, y + r * 0.4)]))


def rays():
    """(path, widths) of 12 tapered satin rays round the moon, long and short in turn."""
    out = []
    for i in range(12):
        a = np.radians(90 + 15 + i * 30)
        r0, r1 = MR + 1.6, MR + (4.6 if i % 2 == 0 else 3.2)
        u = np.array([np.cos(a), np.sin(a)])
        pth = np.array([MX, MY]) + np.outer(np.linspace(r0, r1, 5), u)
        out.append((pth, np.linspace(2.0, 1.0, 5)))
    return out


def tower(x, base=-8.0, top=7.0, w=5.4):
    body = rect(w, top - base, x, (top + base) / 2)
    m = 1.6
    merlons = union(rect(m, 1.8, x - w / 2 + m / 2, top + 0.7), rect(m, 1.8, x + w / 2 - m / 2, top + 0.7))
    return union(body, merlons), rect(1.5, 2.6, x, top - 5.0)


WOLF = [(1.8, 0.0),
           (1.2, 0.9),
           (0.6, 2.0),
           (0.8, 7.0),
           (1.4, 9.5),
           (1.0, 11.0),
           (2.0, 11.8),
           (1.0, 12.6),
           (1.8, 13.6),
           (0.6, 14.2),
           (1.0, 15.6),
           (2.2, 17.8),
           (3.4, 20.4),
           (2.9, 20.8),
           (3.9, 22.6),
           (4.4, 23.8),
           (3.8, 24.4),
           (2.4, 23.0),
           (1.2, 22.6),
           (0.2, 23.4),
           (-0.2, 24.0),
           (-1.4, 26.4),
           (-2.0, 23.0),
           (-2.4, 21.4),
           (-2.8, 19.4),
           (-3.6, 17.6),
           (-4.6, 15.0),
           (-6.2, 11.8),
           (-8.4, 9.2),
           (-9.8, 7.0),
           (-10.6, 4.4),
           (-10.6, 2.6),
           (-13.0, 3.0),
           (-15.6, 2.8),
           (-17.6, 1.8),
           (-16.8, 0.6),
           (-14.0, 0.2),
           (-11.0, 0.0),
           (-6.0, 0.0),
           (-3.4, 0.0),
           (-3.0, 1.0),
           (-2.0, 2.0),
           (-1.0, 1.0),
           (-0.8, 0.0)]


def wolf(x, y, k=0.95):
    """(silhouette, rim path): a wolf sitting in profile facing right, muzzle raised,
    pointed ears, chest ruff, bushy tail on the ground; front paws at (x, y). The rim
    path runs 0.65 mm inside the back, for a rim-light satin."""
    g = poly(WOLF).buffer(0.25).buffer(-0.25)
    g = move(scale(g, k, k), x, y)
    ring = np.asarray(g.buffer(-0.65).exterior.coords)[:-1]
    on = (ring[:, 0] < x - 1.2 * k) & (ring[:, 1] > y + 4.5 * k) & (ring[:, 1] < y + 21.6 * k)
    i = int(np.argmin(on))                     # start the ring on a point off the back
    ring, on = np.roll(ring, -i, axis=0), np.roll(on, -i)
    rim = ring[on]
    if rim[0, 1] < rim[-1, 1]:
        rim = rim[::-1]                        # head end first
    return g, rim


def winding_path():
    c = spline([(1.0, -22.0), (-3.0, -18.0), (2.5, -14.0), (-1.5, -11.0), (0.0, -8.4)], 12)
    w = np.linspace(6.0, 1.6, len(c))
    t = np.gradient(c, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    n = np.c_[-t[:, 1], t[:, 0]] * (w / 2)[:, None]
    return poly(np.vstack([c + n, (c - n)[::-1]]))


def art():
    d = Design()
    F = T.frame("XVIII", "THE MOON")
    scene = F["scene"]

    moon = circle(MX, MY, MR, 160)
    land = poly([(-25, -6.6), (-16, -7.6), (-8, -8.6), (0, -8.2), (9, -7.2), (17, -8.0),
                 (25, -6.8), (25, -33), (-25, -33)])
    pool = smooth([(-26, -23.2), (-14, -22.4), (-4, -23.6), (8, -21.8), (18, -23.0), (26, -22.2),
                   (26, -34), (-26, -34)], 8)
    rise = smooth([(-26, -20.0), (-21, -19.2), (-15, -19.4), (-8, -20.6), (-4, -22.8), (-26, -24)], 8)
    towers = [tower(-19.2, top=6.0), tower(16.0, top=4.0)]
    drops = [drop(1.2, -1.2, 1.1), drop(4.8, -4.6, 1.0), drop(8.0, -0.8, 1.1), drop(10.8, -4.8, 1.0)]
    stars = [sparkle(-18.5, 26, 2.4), sparkle(19, 25, 2.0), sparkle(-20, 12, 1.8), sparkle(19.5, 13, 1.8)]

    face = [arc(MX - 3.6, MY + 3.2, 2.0, 200, 340), arc(MX + 3.6, MY + 3.2, 2.0, 200, 340),
            spline([(MX + 0.4, MY + 2.4), (MX - 0.6, MY - 0.6), (MX + 0.6, MY - 1.4)], 6),
            arc(MX, MY - 1.6, 2.6, 235, 305)]
    ripples = [spline([(-20, -25.5), (-14, -25.0), (-8, -25.6)], 6),
               spline([(6, -25.0), (12, -24.6), (19, -25.2)], 6),
               spline([(-13, -28.5), (-5, -28.0), (3, -28.6)], 6),
               spline([(9, -28.4), (15, -28.0), (20, -28.4)], 6)]

    L = [("fill", scene, "navy", dict(angle=30, name="sky"))]
    L += [("fill", g, "gold", dict(angle=45, name="star")) for g in stars]
    L += [("satin", r, "gold", dict(name="ray", taper=True)) for r in rays()]
    L += [("fill", moon, "white", dict(method="contour_fill", spacing=0.4, name="moon"))]
    L += [("run", p, "pewter", dict(bean=1, name="moon face")) for p in face]
    for body, win in towers:
        L += [("fill", body, "pewter", dict(angle=90, name="tower")),
              ("fill", win, "navy", dict(angle=90, name="tower window"))]
    L += [("fill", land, "peacock", dict(angle=-20, name="land")),
          ("fill", winding_path(), "bone", dict(angle=0, name="path")),
          ("fill", rise, "peacock", dict(angle=20, name="rise")),
          ("fill", pool, "blue", dict(angle=0, name="pool"))]
    L += [("run", p, "white", dict(name="ripple")) for p in ripples]
    wolf_g, rim = wolf(-5.4, -23.0, 0.95)
    L += [("fill", wolf_g, "black", dict(angle=75, name="wolf")),
          ("satin", (rim, 1.3), "pewter", dict(name="wolf rim light"))]
    L += [("fill", g, "gold", dict(angle=90, name="drop of light")) for g in drops]

    T.sew_face(d, F, C_["bone"])
    T.sew_scene(d, F, L, ORDER, C_, hooks={"navy": lambda d: T.sew_plaques(d, F, C_["navy"]),
                                           "gold": lambda d: T.sew_gold(d, F, C_["gold"])})
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
