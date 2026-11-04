"""Rogue merit badge: a hooded cloak with glowing eyes behind two crossed daggers, a
night city of rooftops under a crescent moon, ROGUE on a ribbon banner, merrowed-look
satin border. Arcana & Ink adventurer badge series (frame in `_arcana_badge`).

Spec:
  object:       full round sew-on patch (or a direct design on a jacket, dice bag or tote)
  overall:      `size` mm diameter target; 90 mm stitched at 4x4, 120 mm at 5x7
  fabric:       twill patch blank with tear-away (patch); cut-away on knits
  threads:      charcoal (night sky, dagger grips), gray (far rooftops, ribbon folds),
                black (near rooftops, face shadow), purple (cloak), silver (ribbon,
                moon, blade shade), white (blade light, stars), gold (lit windows, eyes,
                guards, pommels), black (lettering, border): 7 threads, 8 blocks
  must have:    3.0 mm satin border (4x4) sewn last as one ring; spiral (circular) fill
                sky; crescent moon 15 mm; hooded cloak ~55 mm tall; two crossed daggers
                ~55 mm long; two rooftop ranges with lit windows; banner arc with ROGUE
                in block lettering, 8.5 mm caps (4x4), one fill per letter square to it
  lettering:    `cadkit.stitch.lettering.block_text`, set along the banner arc
  density:      every fill knocked out under what sews on top; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401  (SIZES: publish)
import _arcana_badge as F

DESCRIPTION = "Rogue merit badge patch: hooded cloak, crossed daggers, night rooftops, banner"
HOOP = "4x4"
DETAIL = (0, -27)
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Rogue Adventurer Patch Embroidery Design",
    "A round rogue merit badge: hooded cloak, crossed daggers and moonlit rooftops, ROGUE banner",
    ["rogue", "rpg class", "adventurer patch", "merit badge", "tabletop rpg", "thief",
     "dagger", "hooded cloak", "patch embroidery", "badge embroidery"],
    "Earn your stripes as the party's rogue: a hooded figure with glowing eyes behind two "
    "crossed daggers, moonlit city rooftops with lit windows, and ROGUE in bold block "
    "letters on a silver ribbon, all inside a thick satin border like a merrowed patch.\n\n"
    "Part of the adventurer merit-badge series. Great on patches, jackets, backpacks, "
    "dice bags and game-night hoodies.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 20000)


def _dagger(pommel, tip):
    """(blade light half, blade shade half, guard, grip, pommel) for one dagger."""
    p0, p1 = np.asarray(pommel, float), np.asarray(tip, float)
    u = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-u[1], u[0]])
    L = np.linalg.norm(p1 - p0)
    g = p0 + u * 12.5                       # guard centre
    P = lambda v: tuple(v)
    w = 3.1                                  # half blade width at the guard
    shoulder = g + u * (L - 12.5) * 0.62
    left = poly([P(g + u * 0.5), P(g + u * 0.5 + n * w), P(shoulder + n * w * 0.9), P(p1)])
    right = poly([P(g + u * 0.5), P(p1), P(shoulder - n * w * 0.9), P(g + u * 0.5 - n * w)])
    a = math.degrees(math.atan2(u[1], u[0]))
    guard = rotate(rounded_rect(3.0, 17.0, 1.2), a, origin=(0, 0))
    guard = move(guard, *g)
    grip = rotate(rect(10.5, 3.6), a)
    grip = move(grip, *(p0 + u * 6.0))
    pom = circle(*(p0 + u * 0.8), 2.6)
    return left, right, guard, grip, pom


def _buildings(spec, base=-30.0):
    """Union of buildings: (x0, x1, wall top, roof kind, roof height)."""
    out = []
    for x0, x1, top, kind, rh in spec:
        b = rect(x1 - x0, top - base, (x0 + x1) / 2, (top + base) / 2)
        if kind == "gable":
            b = b | poly([(x0 - 0.8, top - 0.1), ((x0 + x1) / 2, top + rh), (x1 + 0.8, top - 0.1)])
        elif kind == "spire":
            b = b | poly([(x0, top - 0.1), ((x0 + x1) / 2, top + rh), (x1, top - 0.1)])
        elif kind == "dome":
            b = b | ellipse((x0 + x1) / 2, top, (x1 - x0) / 2, rh)
        out.append(b)
    return union(*out)


def art():
    d = Design()
    hood = smooth([(0, 33), (6, 30), (11, 23), (13.5, 14), (14, 5), (17, -3), (23, -10),
                   (29, -18), (33, -28), (0, -30), (-33, -28), (-29, -18), (-23, -10),
                   (-17, -3), (-14, 5), (-13.5, 14), (-11, 23), (-6, 30)])
    face = smooth([(0, 22.5), (5.6, 19), (7.2, 12), (5.4, 5.5), (0, 3.2), (-5.4, 5.5),
                   (-7.2, 12), (-5.6, 19)])
    eyes = union(rotate(ellipse(2.9, 12.2, 1.9, 0.95), -12, origin=(2.9, 12.2)),
                 rotate(ellipse(-2.9, 12.2, 1.9, 0.95), 12, origin=(-2.9, 12.2)))
    A = _dagger((-21, -19), (27, 17))       # on top
    B = _dagger((21, -19), (-27, 17))
    dagA, dagB = union(*A), union(*B)
    blades = [knockout(s, dagA) for s in B[:2]] + list(A[:2])
    moon = circle(-22, 31, 7.6).difference(circle(-18.6, 33.4, 6.6))
    stars = [star(4, 3.6, 1.0, x, y) for x, y in ((20, 34), (31, 24), (-35, 15), (37, 7), (-8, 41))]
    far = F.clip(_buildings([
        (-50, -38, -6, "gable", 5), (-38, -31, 1, "spire", 11), (-31, -22, -9, "flat", 0),
        (-22, -15, -4, "gable", 4), (16, 24, -3, "dome", 4.5), (24, 32, 3, "gable", 6),
        (32, 40, -7, "flat", 0), (40, 50, -1, "spire", 8)]))
    near = F.clip(_buildings([
        (-50, -36, -16, "gable", 5), (-36, -27, -11, "gable", 4.5), (-27, -18, -18, "flat", 0),
        (18, 27, -14, "gable", 4), (27, 36, -19, "flat", 0), (36, 50, -12, "gable", 5)]))
    win = [rect(1.8, 2.6, x, y) for x, y in ((-31.5, -14.5), (-29, -14.5), (22.5, -17.5),
                                             (40, -15.5), (44, -15.5))]
    dag_all = dagA | dagB
    # the acute wedges where a blade leaves the cloak go to the cloak, not to slivers of sky
    closed = (hood | dag_all).buffer(1.5, quad_segs=8).buffer(-1.5, quad_segs=8)
    hood_c = F.clip(hood | (closed & hood.buffer(3.0)))
    windows = union(*win).difference(grow(hood_c | F.banner_all() | dagA | dagB, 0.6))

    banner = F.banner_all()
    txt = F.lettering("ROGUE")
    top_of_scene = [hood_c, dag_all, banner]

    # 1 charcoal: night sky as a spiral, and the dagger grips
    # the sky runs up into the blade tips (a fill cannot reach a needle point): it is
    # knocked out under the daggers opened by 0.9 mm, not under the bare points
    tips_open = dag_all.buffer(-0.9, quad_segs=8).buffer(0.9, quad_segs=8)
    F.backdrop(d, C_["charcoal"], [moon, *stars, far, near, hood_c, tips_open, banner])
    d.fill(knockout(B[3], B[2], B[4], dagA), C_["charcoal"], angle=0, name="grip")
    d.fill(knockout(A[3], A[2], A[4]), C_["charcoal"], angle=0, name="grip")
    # 2 gray: far rooftops, banner folds
    d.fill(knockout(far, near, *top_of_scene, windows), C_["gray"], angle=90, name="far roofs")
    d.fill(knockout(F.banner_folds(), F.banner_main(), dag_all), C_["gray"], angle=60,
           name="banner folds")
    # 3 black: near rooftops, the face shadow
    d.fill(knockout(near, *top_of_scene, windows), C_["black"], angle=90, name="near roofs")
    d.fill(knockout(face, eyes, dag_all), C_["black"], angle=75, name="face")
    # 4 purple: the cloak
    d.fill(knockout(hood_c, face, dag_all, banner), C_["purple"], angle=-55, name="cloak")
    # 5 silver: banner, moon, blade shade halves
    # rows at 0 deg like the shared sew_banner: at 2 deg one row end met the underlay's
    # turn points in the strip above the letters, 7 penetrations in one hole (stitchsim)
    d.fill(knockout(F.banner_main(), txt, dag_all, overlap=0.3), C_["silver"], angle=0, name="banner")
    d.fill(moon, C_["silver"], angle=30, name="moon")
    for i, s in enumerate((blades[1], blades[3])):
        d.fill(knockout(s, A[2], B[2] if i == 0 else A[2]), C_["silver"], angle=0, name="blade shade")
    # 6 white: blade light halves, stars
    for i, s in enumerate((blades[0], blades[2])):
        d.fill(knockout(s, A[2], B[2] if i == 0 else A[2]), C_["white"], angle=0, name="blade light")
    for s in stars:
        d.fill(s, C_["white"], angle=45, name="star")
    # 7 gold: windows, eyes, guards, pommels
    d.fill(windows, C_["gold"], angle=0, name="windows")
    d.fill(eyes, C_["gold"], angle=0, name="eyes")
    d.fill(knockout(B[2], dagA), C_["gold"], angle=0, name="guard")
    d.fill(knockout(B[4], dagA), C_["gold"], angle=0, name="pommel")
    d.fill(A[2], C_["gold"], angle=0, name="guard")
    d.fill(A[4], C_["gold"], angle=0, name="pommel")
    # 8 black: lettering, border
    F.sew_letters(d, "ROGUE", C_["black"])
    F.sew_border(d, C_["black"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
