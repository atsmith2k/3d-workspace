"""Wandering Wizard: a tall crooked wizard hat crossed with a crystal-topped wooden staff.

Spec:
  object:       a wandering wizard's pointed hat and staff (no character, no franchise) for
                tees, hoodies, dice bags, totes and game-night patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; dice bags and wovens with tear-away
  threads:      wood (staff), ice (crystal), white (crystal glint), navy (brim),
                blue (hat cone, brim edge run), purple (band), gold (stars, moon, staff collar,
                sparkles): 7 colours
  must have:    a 60 mm tall cone whose tip leans and droops right; an 84 x 18 mm brim;
                a 7.5 mm purple band curving with the brim; a 1.6 mm blue satin edge tapering at both ends on the brim; three gold stars (4-5.5 mm) and a 13 mm crescent moon
                on the cone; a 4.4 mm staff leaning behind the hat from lower right to
                upper left, a gold collar and a 19 mm faceted crystal at its top with a
                white glint; four four-point gold sparkles
  density:      every lower layer knocks out the ones on top; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Crooked wizard hat with stars and a moon, crossed with a crystal-topped staff"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Wandering Wizard Hat Embroidery Design",
    "A tall crooked blue wizard hat with gold stars and a crescent moon, crossed with a "
    "crystal-topped wooden staff",
    ["wizard hat", "wizard", "wizard staff", "magic", "spellcaster", "tabletop rpg",
     "game night", "dice bag", "crystal", "celestial"],
    "Every party needs a spellcaster: a tall, slightly crooked wizard hat in deep blue with a "
    "wide brim, a purple band and gold stars and a crescent moon, leaning on a wooden staff "
    "topped with a glowing ice-blue crystal and a scatter of sparkles.\n\n"
    "Great on hoodies, tees, dice bags, totes and game-night patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 14000)


STAFF0 = np.array([34.0, -48.0])   # foot (lower right)
STAFF1 = np.array([-32.0, 37.0])   # top, under the crystal


def _sparkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


def _moon(x, y, r, tilt=-25.0):
    m = circle(x, y, r).difference(circle(x + 0.42 * r, y + 0.18 * r, 0.82 * r))
    m = m.buffer(-0.7).buffer(0.7)          # round the horn tips off (no sub-mm points)
    return rotate(m, tilt, origin=(x, y))


def art():
    d = Design()
    cone = smooth([(-23, -28), (-19, -10), (-13, 8), (-6, 22), (2, 33), (11, 41), (21, 45),
                   (29, 41), (24, 39), (16, 34), (10, 24), (10, 8), (14, -10), (21, -28)],
                  10).buffer(0)
    brim = ellipse(0, -31, 42, 9)
    # the cone's base and band follow the brim's ellipse, so the hat sits in the brim
    above = lambda yc: union(ellipse(0, yc, 26, 5.5), rect(52, 120, 0, yc + 60))
    cone = cone.intersection(above(-28))
    band = cone.difference(above(-20.5))
    t = np.radians(np.linspace(196, 344, 41))
    rim = np.c_[39.6 * np.cos(t), -31 + 7.0 * np.sin(t)]          # just inside the brim's front edge
    rim_w = 0.5 + 1.1 * np.sin(np.linspace(0, np.pi, len(rim)))     # tapered both ends
    stars = [star(5, 5.5, 2.3, 4, -6, rot=100), star(5, 4.4, 1.9, -4, 11, rot=80),
             star(5, 3.6, 1.6, 4, 25)]
    moon = _moon(-9, -8, 6.5)
    # staff: a buffered line (fill) so the hat can knock it out where it passes behind
    u = (STAFF1 - STAFF0) / np.linalg.norm(STAFF1 - STAFF0)
    staff = LineString([STAFF0, STAFF1]).buffer(2.2, cap_style="flat")
    foot = circle(*(STAFF0 + u * 0.5), 2.6)
    collar = LineString([STAFF1 - u * 3.2, STAFF1 + u * 0.6]).buffer(3.4, cap_style="flat")
    cx, cy = STAFF1 + u * 11.0
    ang = np.degrees(np.arctan2(u[1], u[0])) - 90
    crystal = rotate(poly([(cx, cy - 8.5), (cx + 5.0, cy - 3.5), (cx + 4.2, cy + 4.0),
                           (cx, cy + 9.0), (cx - 4.2, cy + 4.0), (cx - 5.0, cy - 3.5)]),
                     ang, origin=(cx, cy))
    crystal = scale(crystal, 1.25, origin=(cx, cy))
    glint = rotate(poly([(cx - 2.6, cy - 1.5), (cx - 1.0, cy - 2.5), (cx - 0.6, cy + 4.5),
                         (cx - 2.0, cy + 3.5)]), ang, origin=(cx, cy))
    glint = scale(glint, 1.25, origin=(cx, cy))
    sparkles = [_sparkle(cx - 12, cy + 4, 4.5), _sparkle(cx + 9, cy + 10, 3.4),
                _sparkle(36, 30, 4.0), _sparkle(-38, -10, 3.6)]
    hat = union(cone, brim)
    gold = union(*stars, moon)

    d.fill(knockout(union(staff, foot), hat, collar, crystal), C_["wood"], angle=float(ang) + 90,
           name="staff")
    d.fill(knockout(crystal, glint, collar), C_["ice"], angle=float(ang) + 30, name="crystal")
    d.fill(glint, C_["white"], angle=float(ang), name="glint")
    d.fill(knockout(brim, cone), C_["navy"], angle=0, name="brim")
    d.fill(knockout(cone, band, gold), C_["blue"], angle=70, name="cone")
    d.satin(rim, list(rim_w), C_["blue"], name="brim rim", underlay="center", taper=True)
    d.fill(knockout(band, gold), C_["purple"], angle=0, name="band")
    d.fill(collar, C_["gold"], angle=float(ang), name="collar")
    for g in stars + [moon] + sparkles:
        d.fill(g, C_["gold"], angle=45, name="gold detail")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
