"""Knight's Crest: a heraldic heater shield with two longswords crossed behind it and a
crown above.

Spec:
  object:       heraldic knight's badge (original arms, no real house or franchise) for
                tees, jackets, hoodies, totes and sew-on patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; patches and wovens with tear-away
  threads:      navy (field), silver (chevron, blades), pewter (fullers), wood (grips),
                gold (stars, shield border, crown, crossguards, pommels), brass (crown
                band), red (gems): 7 colours, one block each
  must have:    a 50 x 58 mm heater shield, navy field with a silver chevron between
                three gold five-point stars; a 2.6 mm gold satin border; two longswords
                crossed behind it, tips out at the top corners and hilts out at the
                lower sides: 7 mm silver blades with a 1.6 mm pewter fuller, 19 mm gold
                crossguards (bowed toward the blade, tapered, round finials), satin-wrapped brown grips, gold pommels with red gems;
                a three-point gold crown with a brass band and red gems above the shield
  density:      blades stop under the border, field tucked under it, chevron and stars
                knocked out of the field; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Heraldic heater shield with crossed longswords and a crown"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Knight's Crest Embroidery Design",
    "A navy heater shield with a silver chevron and gold stars, crossed longswords and a crown",
    ["knight", "heraldry", "coat of arms", "crest", "shield", "sword", "crossed swords",
     "crown", "medieval", "high fantasy", "renaissance faire"],
    "Raise your banner: a classic heater shield in deep navy with a silver chevron between "
    "three gold stars, framed in gold, with two longswords crossed behind it and a royal "
    "crown above.\n\n"
    "Great on jackets, hoodies, tees, totes and sew-on patches for faire days and game nights.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 16000)


BW = 2.6            # shield border satin
TOP, BOT, HW = 20.0, -36.0, 25.0   # shield top, point, half width


def shield():
    """Heater shield: flat top, straight sides down to y=2, then curves to the point."""
    # top corners rounded (r 5): a 90 deg mitre in the border sews 7+ mm stitches at 5x7
    rc = 5.0
    arc_r = [(HW - rc + rc * math.cos(a), TOP - rc + rc * math.sin(a))
             for a in np.radians(np.linspace(90, 0, 7))]
    pts = [(-x, y) for x, y in arc_r[::-1]] + arc_r + [(HW, 2.0)]
    pts += [tuple(q) for q in bezier((HW, 2.0), (HW, -16.0), (12.0, -28.0), (0.0, BOT), 24)[1:]]
    right = pts[len(arc_r) * 2:]
    left = [(-x, y) for x, y in right][::-1]
    return poly(pts + left[1:-1])


TIP = np.array([34.0, 37.0])
CROSS = np.array([0.0, -4.0])


def _sword(sign):
    """Axis unit vector (hilt to tip), tip and crossguard centre of one sword."""
    tip = TIP * (sign, 1)
    u = (tip - CROSS * (sign, 1)) / np.linalg.norm(tip - CROSS * (sign, 1))
    # crossguard 5 mm outside where the axis leaves the shield below
    sh = shield()
    far = CROSS * (sign, 1) - u * 80
    hit = LineString([tuple(CROSS * (sign, 1)), tuple(far)]).intersection(sh.exterior)
    exitp = np.array(hit.coords[0]) if hit.geom_type == "Point" else np.array(hit.geoms[0].coords[0])
    guard = exitp - u * (BW / 2 + 5.0)
    return u, tip, guard


def _blade(u, tip, guard, hw=3.4, point=11.0):
    """Blade with straight edges that curve smoothly into a 1.2 mm wide point."""
    n = np.array([-u[1], u[0]])
    base = guard + u * 0.6
    sh = tip - u * point
    side = []
    for sgn in (1, -1):
        e = bezier(tuple(sh + n * hw * sgn), tuple(sh + n * hw * sgn + u * point * 0.55),
                   tuple(tip - u * point * 0.25 + n * 1.2 * sgn), tuple(tip + n * 0.6 * sgn), 14)
        side.append([tuple(base + n * hw * sgn)] + [tuple(q) for q in e])
    return poly(side[0] + side[1][::-1])


def _guard(u, guard, half=8.0, bend=1.0):
    """Crossguard centreline bowing toward the blade, its widths (3.0 mm in the middle,
    1.9 at the ends) and the two finial centres just past the ends."""
    n = np.array([-u[1], u[0]])
    t = np.linspace(-1, 1, 25)
    path = np.array([guard + n * half * k + u * bend * k * k for k in t])
    w = 1.9 + 1.1 * (1 - np.abs(t)) ** 0.7
    fin = []
    for end, prev in ((path[0], path[1]), (path[-1], path[-2])):
        d_ = (end - prev) / np.linalg.norm(end - prev)
        fin.append(end + d_ * 1.0)
    return path, w, fin


def crown():
    band = rect(26.0, 4.2, 0, 26.6)
    body = poly([(-12.4, 28.0), (-14.0, 36.4), (-7.0, 31.8), (0.0, 38.8), (7.0, 31.8),
                 (14.0, 36.4), (12.4, 28.0)])
    balls = [circle(-14.0, 36.6, 1.8), circle(0.0, 39.0, 2.0), circle(14.0, 36.6, 1.8)]
    gems = [ellipse(x, 26.6, 1.5 if x else 1.9, 1.3) for x in (-7.5, 0.0, 7.5)]
    return union(body, *balls), band, gems


def art():
    d = Design()
    sh = shield()
    field = tuck(sh, BW)
    # chevron: apex near the middle, legs out to the lower sides
    chev = poly([(-30, -14), (0, 12), (30, -14), (30, -22), (0, 3), (-30, -22)]) & field
    stars = [star(5, 5.0, 2.1, -12.5, 10.5), star(5, 5.0, 2.1, 12.5, 10.5),
             star(5, 5.6, 2.35, 0, -18.5)]

    swords = [_sword(s) for s in (-1, 1)]
    outside = sh.buffer(BW / 2 - 0.6, join_style="mitre", mitre_limit=3.0)
    blades = [_blade(*sw).difference(outside) for sw in swords]
    cbody, band, gems = crown()

    d.fill(knockout(field, chev, *stars), C_["navy"], angle=0, name="field")
    d.fill(chev, C_["silver"], angle=90, name="chevron")
    for (u, tip, guard), b in zip(swords, blades):
        # rows across the blade: their ends trace the edges and the point cleanly
        ang = math.degrees(math.atan2(u[1], u[0])) + 90
        d.fill(b, C_["silver"], angle=ang, name="blade")
    # fullers: satin down the blade centre, stopping 1.6 mm clear of the shield border
    # and of the crossguard, and well short of the point
    clear = sh.buffer(BW / 2 + 1.6)
    for u, tip, guard in swords:
        ax = LineString([tuple(guard + u * 3.2), tuple(tip - u * 11.0)]).difference(clear)
        segs = [ax] if ax.geom_type == "LineString" else list(ax.geoms)
        for sgm in segs:
            if sgm.length > 2.5:
                d.satin(np.array(sgm.coords), 1.6, C_["pewter"], name="fuller", underlay="center")
    for u, tip, guard in swords:
        d.satin(line(tuple(guard - u * 0.6), tuple(guard - u * 10.6)), 3.2, C_["wood"],
                name="grip", underlay="center")
    for s in stars:
        d.fill(s, C_["gold"], angle=45, spacing=0.4, name="star")
    d.outline(sh, C_["gold"], width=BW, name="border")
    d.fill(knockout(cbody, band), C_["gold"], angle=90, name="crown")
    for u, tip, guard in swords:
        gp, gw, fins = _guard(u, guard)
        d.satin(gp, gw, C_["gold"], name="crossguard", underlay="center")
        for fc in fins:
            d.fill(circle(fc[0], fc[1], 1.5), C_["gold"], angle=0, name="finial")
        pc = guard - u * 13.4
        d.fill(knockout(circle(pc[0], pc[1], 3.4), circle(pc[0], pc[1], 1.5)), C_["gold"],
               angle=math.degrees(math.atan2(u[1], u[0])) + 90, name="pommel")
    d.fill(knockout(band, *gems), C_["brass"], angle=0, name="crown band")
    for g in gems:
        d.fill(g, C_["red"], angle=60, name="crown gem")
    for u, tip, guard in swords:
        pc = guard - u * 13.4
        d.fill(circle(pc[0], pc[1], 1.5), C_["red"], angle=60, name="pommel gem")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
