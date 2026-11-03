"""Ranger merit badge: a longbow in front of a fletched quiver, a hawk soaring over
snow-capped mountains and a pine forest, RANGER on a ribbon banner, merrowed-look satin
border. Arcana & Ink adventurer badge series (frame in `_arcana_badge`).

Spec:
  object:       full round sew-on patch (or a direct design on a jacket, dice bag or tote)
  overall:      `size` mm diameter target; 90 mm stitched at 4x4, 120 mm at 5x7
  fabric:       twill patch blank with tear-away (patch); cut-away on knits
  threads:      sky blue (sky), blue (mountains), emerald (pine forest, ribbon folds),
                light brown (quiver, bow stave, arrow shafts), dark brown (quiver bands,
                quiver mouth, bow grip, hawk), white (snow caps, fletching, bow string), leaf green
                (ribbon), deep green (lettering, border): 8 threads, 8 blocks
  must have:    3.0 mm satin border (4x4) sewn last as one ring; spiral (circular) fill
                sky; a quiver ~35 mm long with two fletched arrows; a longbow ~60 mm
                tip to tip with a string; a soaring hawk ~22 mm; mountains with snow
                caps; a pine treeline; banner arc with RANGER in block lettering,
                8.5 mm caps (4x4)
  lettering:    `cadkit.stitch.lettering.block_text`, set along the banner arc
  density:      every fill knocked out under what sews on top; the string is a single
                run over the fills; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401  (SIZES: publish)
import _arcana_badge as F

DESCRIPTION = "Ranger merit badge patch: longbow, fletched quiver, hawk, mountains, pines, banner"
HOOP = "4x4"
DETAIL = (0, -27)
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Ranger Adventurer Patch Embroidery Design",
    "A round ranger merit badge: longbow, fletched quiver and a hawk over mountains and pines, RANGER banner",
    ["ranger", "rpg class", "adventurer patch", "merit badge", "tabletop rpg", "archer",
     "longbow", "quiver", "hawk", "patch embroidery", "badge embroidery"],
    "For the party's tracker and sharpshooter: a longbow in front of a fletched quiver, a "
    "hawk soaring over snow-capped mountains and a pine forest, and RANGER in bold block "
    "letters on a green ribbon, inside a thick satin border like a merrowed patch.\n\n"
    "Part of the adventurer merit-badge series. Great on patches, jackets, backpacks, "
    "dice bags and camp or game-night hoodies.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 20000)


def _strip(path, widths):
    """A filled strip along a path, `widths` (one per point) wide."""
    path = np.asarray(path, float)
    w = np.asarray(widths, float)
    tan = np.gradient(path, axis=0)
    nrm = np.c_[-tan[:, 1], tan[:, 0]] / np.linalg.norm(tan, axis=1)[:, None]
    l, r = path + nrm * w[:, None] / 2, path - nrm * w[:, None] / 2
    return poly(list(map(tuple, l)) + list(map(tuple, r[::-1])))


def quiver():
    """(body, bands, shafts, fletching): drawn opening up, then tipped so the arrows lean
    left and set behind the bow."""
    body = rounded_rect(12.5, 36, 3.6, 0, 0)
    bands = union(rect(13.2, 3.4, 0, 15.6), rect(13.2, 3.0, 0, -14.6))
    shafts = union(*[rect(1.4, h, x, 17 + h / 2) for x, h in ((-3.4, 9.5), (0.0, 12.5), (3.4, 10.0))])

    def vane(x, y):
        """Fletching: a feather with a V notch at the nock end."""
        return poly([(x - 1.6, y), (x, y + 1.6), (x + 1.6, y), (x + 1.6, y + 6.4),
                     (x, y + 5.0), (x - 1.6, y + 6.4)])
    fletch = union(vane(-3.4, 22.2), vane(0.0, 25.2), vane(3.4, 22.7))
    # the dark mouth of the quiver between the arrows (no slivers of sky trapped there)
    mouth = rect(6.8, 9.0, 0, 21.0).difference(shafts).difference(fletch)
    place = lambda g: move(rotate(g, 22, origin=(0, 0)), 6.0, 3.0)
    return place(body), place(bands), place(shafts), place(fletch), place(mouth)


def bow():
    """The stave (a strip along an arc, thick at the grip, slim at the tips), the grip
    wrap and the string's end points."""
    a, b = np.array([-25.0, -13.0]), np.array([23.0, 35.0])
    chord = b - a
    n = np.array([chord[1], -chord[0]]) / np.linalg.norm(chord)    # bulge to lower right
    sag = 10.0
    t = np.linspace(0, 1, 49)
    pts = a + np.outer(t, chord) + np.outer(4 * t * (1 - t) * sag, n)
    w = 2.0 + 2.4 * np.sin(np.pi * t)
    stave = _strip(pts, w)
    g = pts[24]
    u = chord / np.linalg.norm(chord)
    grip = poly([tuple(g + u * 4.0 + n * 3.0), tuple(g + u * 4.0 - n * 3.0),
                 tuple(g - u * 4.0 - n * 3.0), tuple(g - u * 4.0 + n * 3.0)]) & grow(stave, 0.3)
    string = np.array([pts[1], pts[-2]])
    return stave, grip, string


def hawk(x, y, k=1.0):
    half = [(0, 3.6), (1.3, 2.4), (4.5, 3.2), (8.5, 3.9), (12.0, 2.6), (9.6, 1.4), (10.4, 0.4),
            (7.8, 0.2), (8.4, -0.8), (5.4, -0.5), (2.0, -1.2), (3.0, -5.6), (0, -6.4)]
    pts = half + [(-px, py) for px, py in reversed(half[1:-1])]
    return move(scale(rotate(poly(pts), -8), k), x, y)


def _tree(x, base, h, w):
    tiers = [poly([(x - w / 2 * s, base + h * lo), (x, base + h * hi), (x + w / 2 * s, base + h * lo)])
             for s, lo, hi in ((1.0, 0.0, 0.55), (0.8, 0.28, 0.8), (0.58, 0.55, 1.0))]
    return union(*tiers)


def art():
    d = Design()
    peaks = [(-37, 15), (-18, 21), (6, 16), (28, 23)]
    mountains = F.clip(poly([(-55, -6), (-37, 15), (-30, 4), (-18, 21), (-6, 6), (6, 16),
                             (16, 4), (28, 23), (37, 9), (44, 10), (55, 0), (55, -40), (-55, -40)]))
    caps = []
    for x, y in peaks:
        jag = poly([(x - 9, y - 6), (x - 3.2, y - 3.8), (x, y - 6.8), (x + 3.2, y - 4.0),
                    (x + 9, y - 6.2), (x + 9, y + 1), (x - 9, y + 1)])
        caps.append(mountains & jag)
    caps = union(*caps)
    trees = [_tree(x, -14, h, w) for x, h, w in (
        (-46, 15, 8), (-40, 19, 9), (-33, 14, 8), (-26, 18, 9), (-19, 13, 7.5), (-12, 16, 8.5),
        (-5, 12, 7.5), (2, 15, 8), (10, 13, 7.5), (17, 17, 8.5), (24, 13, 7.5), (31, 18, 9),
        (38, 14, 8), (45, 17, 8.5))]
    forest = F.clip(union(*trees, rect(120, 40, 0, -33.5)))

    q_body, q_bands, q_shafts, q_fletch, q_mouth = quiver()
    stave, grip, string = bow()
    bird = hawk(-19, 31, 0.92)
    banner = F.banner_all()
    txt = F.lettering("RANGER")
    bow_all = stave | grip
    quiv_all = union(q_body, q_bands, q_shafts, q_fletch, q_mouth)
    front = [quiv_all, bow_all, banner]

    # 1 sky blue: the sky
    F.backdrop(d, C_["sky"], [mountains, forest, bird, *front], angle=30)
    # 2 blue: mountains
    d.fill(knockout(mountains, caps, forest, *front), C_["blue"], angle=-35, name="mountains")
    # 3 emerald: the pine forest, ribbon folds
    d.fill(knockout(forest, *front), C_["green"], angle=90, name="pines")
    d.fill(knockout(F.banner_folds(), F.banner_main(), bow_all, quiv_all), C_["green"], angle=60,
           name="banner folds")
    # 4 light brown: quiver body, arrow shafts, bow stave
    d.fill(knockout(q_body, q_bands, bow_all, min_width=1.5), C_["wood"], angle=22 + 90, name="quiver")
    d.fill(knockout(q_shafts, q_fletch, q_body, q_bands, bow_all), C_["wood"], angle=22 + 90,
           name="arrow shafts")
    d.fill(knockout(stave, grip, banner), C_["wood"], angle=-40, name="bow stave")
    # 5 dark brown: quiver bands, bow grip, hawk
    d.fill(knockout(q_bands, bow_all), C_["bark"], angle=22, name="quiver bands")
    d.fill(knockout(q_mouth, bow_all), C_["bark"], angle=22, name="quiver mouth")
    d.fill(grip, C_["bark"], angle=50, name="bow grip")
    d.fill(bird, C_["bark"], angle=80, name="hawk")
    # 6 white: snow caps, fletching, bow string
    d.fill(knockout(caps, forest, *front), C_["white"], angle=35, name="snow caps")
    d.fill(knockout(q_fletch, bow_all), C_["white"], angle=22 + 90, name="fletching")
    d.run(string, C_["white"], bean=1, name="bow string")
    # 7 leaf green: the ribbon
    d.fill(knockout(F.banner_main(), txt, bow_all, quiv_all, overlap=0.3), C_["leaf"], angle=2,
           name="banner")
    # 8 deep green: lettering, border
    F.sew_letters(d, "RANGER", C_["pine"])
    F.sew_border(d, C_["pine"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
