"""Crystal Snowflake: a six-armed dendrite snowflake in three cool blues.

Spec:
  object:       minimalist winter motif (not overtly Christmas) for sweatshirts, beanies,
                tea towels, mugs rugs and framed hoops
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7), hexagonal
  fabric:       knits and sweatshirts with cut-away; wovens with tear-away
  threads:      navy (centre hexagon), ice (side branches and tip crystals), sky (six
                main arms, sewn last over the branch roots): 3 colours, exact Brother threads
  must have:    six tapered satin arms from a filled hexagonal centre; two pairs of side
                branches per arm at 55 deg, each pair one V sewn before the arms so the arm
                covers its roots and the hop between them; a small diamond crystal at
                every arm tip
  density:      satins only meet the centre fill's edge; max 3.5 layers
"""
import math

import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Six-armed dendrite snowflake in navy, sky and ice blue"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Crystal Snowflake Embroidery Design",
    "A crisp six-armed snowflake in three cool blues",
    ["snowflake embroidery", "minimalist winter", "scandi", "frozen", "winter sweatshirt"],
    "A crisp six-armed snowflake: tapered satin arms in sky blue grow from a navy hexagon, each with "
    "two pairs of ice-blue side branches and a small crystal at the tip. Minimal and wintry rather "
    "than Christmassy, so it works from December to March.\n\nGreat on sweatshirts, beanies, tea "
    "towels and framed hoops.",
    mockups=("tshirt", "cap"),
)


def checks(p):
    return standard_checks(p, 3, 9000)


def art():
    d = Design()
    R = 44.0
    hexagon = regular_polygon(6, R * 0.16, rot=90)
    d.fill(hexagon, C_["navy"], angle=0, name="centre")
    arms = M.snowflake(R, branches=((0.40, 0.30), (0.66, 0.22)))
    mains = [a for a in arms if a[1] > 2.0]
    sides = [a for a in arms if a[1] <= 2.0]
    # branches first, each pair sewn as one V (out along one, in from the other) starting
    # under where its arm will lie; the sky arms then cover the roots and the hop between
    for k in range(0, len(sides), 2):
        (pa, _, _), (pb, _, _) = sides[k], sides[k + 1]
        base, ta, tb = pa[0], pa[1], pb[1]
        ua = (ta - base) / np.linalg.norm(ta - base)
        ub = (tb - base) / np.linalg.norm(tb - base)
        a_in = np.array([ta, base + ua * 0.5])          # tip to root, root under the arm
        b_out = np.array([base + ub * 0.5, tb])
        d.satin(spline(a_in, 6), M.taper(spline(a_in, 6), 1.05, 1.6), C_["ice"], name="branch", underlay="none")
        d.satin(spline(b_out, 6), M.taper(spline(b_out, 6), 1.6, 1.05), C_["ice"], name="branch", underlay="none")
    for i in range(6):
        a = math.radians(90 + 60 * i)
        c = (R * 0.99 * math.cos(a), R * 0.99 * math.sin(a))
        diamond = rotate(regular_polygon(4, 2.6, c[0], c[1], rot=0), 60 * i, origin=c)
        d.fill(diamond, C_["ice"], angle=60 * i, underlay=False, name="tip crystal")
    for path, w0, w1 in mains:
        u = (path[1] - path[0]) / np.linalg.norm(path[1] - path[0])
        p = np.array([u * R * 0.15, u * R * 0.93])
        d.satin(spline(p, 8), M.taper(spline(p, 8), 2.4, 1.3), C_["sky"], name="arm", underlay="center")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
