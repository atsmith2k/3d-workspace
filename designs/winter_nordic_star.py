"""Nordic Star: an eight-point Scandinavian folk star in red, white and green.

Spec:
  object:       folk-style Christmas star for sweaters, stockings, tea towels and cushions
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7), octagonal
  fabric:       knits and sweatshirts with cut-away; wovens (linen, canvas) with tear-away
  threads:      red (big star and point diamonds' surround), white (inner star, point
                diamonds, border), green (centre and inner dots): 3 colours
  must have:    an eight-point red star with a continuous white satin border (1.8 mm);
                a white eight-point inner star turned half a point; a white diamond in
                each big point; a green centre disc with a ring of eight green dots
  density:      every upper fill knocks out the one under it; max 3.5 layers
"""
import math

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Eight-point Scandinavian folk star in red, white and green"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Nordic Folk Star Embroidery Design",
    "An eight-point Scandinavian folk star in red, white and green",
    ["nordic star", "scandi christmas", "folk art", "scandinavian embroidery", "christmas sweater"],
    "A bold eight-point folk star in the Scandinavian style: a red star with a white satin border, "
    "a white inner star, a diamond in every point and a green centre ringed with dots. Classic "
    "Christmas-jumper charm that reads from across the room.\n\nGreat on sweaters, stockings, "
    "cushions and tea towels.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 3, 9000)


def art():
    d = Design()
    R = 46.0
    BORDER = 1.8
    big = M.folk_star(R, R * 0.50)
    inner = M.folk_star(R * 0.46, R * 0.24, start=90 + 22.5)
    diamonds = []
    for i in range(8):
        a = math.radians(90 + 45 * i)
        c = (R * 0.64 * math.cos(a), R * 0.64 * math.sin(a))
        diamond = scale(regular_polygon(4, 3.6, c[0], c[1], rot=90), 0.6, 1.0, origin=c)
        diamonds.append(rotate(diamond, 45 * i, origin=c))
    centre = circle(0, 0, R * 0.11)
    dots = [circle(R * 0.19 * math.cos(math.radians(22.5 + 45 * i)),
                   R * 0.19 * math.sin(math.radians(22.5 + 45 * i)), 1.0) for i in range(8)]
    whites = union(inner, *diamonds)
    greens = union(centre, *dots)
    d.fill(knockout(tuck(big, BORDER), whites), C_["red"], angle=30, name="star")
    d.fill(knockout(inner, greens), C_["white"], angle=120, name="inner star")
    for g in diamonds:
        d.fill(g, C_["white"], angle=0, underlay=False, name="diamond")
    d.outline(big, C_["white"], width=BORDER, name="border")
    d.fill(centre, C_["green"], angle=45, name="centre")
    for g in dots:
        d.fill(g, C_["green"], angle=45, underlay=False, name="dot")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
