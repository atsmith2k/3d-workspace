"""Gingerbread Man: an iced gingerbread cookie with gumdrop buttons and a bow tie.

Spec:
  object:       gingerbread cookie for kids' wear, aprons, tea towels, stockings
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens (aprons, towels) with tear-away
  threads:      ginger (cookie), white (icing zigzags and smile), pink (cheeks),
                red (bow tie, buttons), green (middle button), cocoa (1.4 mm satin cookie
                edge and eyes): 6 colours
  must have:    a 90 mm gingerbread figure; white bean-stitch icing zigzags across each
                wrist and ankle, 2 mm inside the edge, zigzagging forward (never back
                over their own holes); two eyes, an icing smile, pink cheeks; a red bow
                tie at the neck; three gumdrop buttons (red, green, red); a continuous
                cocoa satin edge
  density:      details knock out the cookie; the fill tucks under the edge; max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, product, standard_checks

DESCRIPTION = "Iced gingerbread man with gumdrop buttons and a red bow tie"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Gingerbread Man Embroidery Design",
    "An iced gingerbread cookie with gumdrop buttons and a bow tie",
    ["gingerbread man", "gingerbread", "christmas cookie", "christmas baking", "kids christmas"],
    "A freshly iced gingerbread man: white icing zigzags on his arms and legs, a sweet smile, "
    "rosy cheeks, a red bow tie and gumdrop buttons, all framed by a crisp brown cookie edge.\n\n"
    "Great on kids' wear, aprons, tea towels and stockings.",
    mockups=("tshirt", "tote"),
)

H = 90.0
BORDER = 1.4


def checks(p):
    return standard_checks(p, 6, 12000)


def _zigzag(p0, p1, amp, n):
    """A zigzag from p0 to p1, `n` teeth of half-height `amp` across the line."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    u = p1 - p0
    v = np.array([-u[1], u[0]]) / np.linalg.norm(u)
    pts = [p0 + u * (i / (2 * n)) + v * amp * (1 if i % 2 else -1) * (0 < i < 2 * n) for i in range(2 * n + 1)]
    return np.array(pts)


def art():
    d = Design()
    cookie = M.gingerbread(H)
    eyes = [circle(-5.5, 30, 2.2), circle(5.5, 30, 2.2)]
    cheeks = [circle(-9.5, 24, 2.3), circle(9.5, 24, 2.3)]
    smile = arc(0, 27, 6, 215, 325)
    tie = union(poly([(0, 11.5), (-7.5, 15.5), (-7.5, 7.5)]), poly([(0, 11.5), (7.5, 15.5), (7.5, 7.5)]),
                circle(0, 11.5, 2.2))
    buttons = [(circle(0, y, 2.8), c) for y, c in ((1, "red"), (-7, "green"), (-15, "red"))]
    # icing across wrists (arms end near x = +-40) and ankles (legs end near y = -42)
    icing = [_zigzag((-36, 11.5), (-36, 1.5), 1.8, 3), _zigzag((36, 1.5), (36, 11.5), 1.8, 3),
             _zigzag((-25.5, -34), (-17.5, -39.5), 1.8, 3), _zigzag((17.5, -39.5), (25.5, -34), 1.8, 3)]
    over = union(*eyes, *cheeks, tie, *[b for b, _ in buttons])
    d.fill(knockout(tuck(cookie, BORDER), over), C_["ginger"], angle=80, name="cookie")
    for z in icing:
        d.run(z, C_["white"], bean=1, name="icing", trim_after=True)
    d.run(smile, C_["white"], bean=1, name="smile", trim_after=True)
    for g in cheeks:
        d.fill(g, C_["pink"], angle=45, underlay=False, name="cheek")
    d.fill(tie, C_["red"], angle=0, name="bow tie")
    for b, c in buttons:
        if c == "red":
            d.fill(b, C_["red"], angle=45, name="gumdrop")
    for b, c in buttons:
        if c == "green":
            d.fill(b, C_["green"], angle=45, name="gumdrop")
    d.outline(cookie, C_["cocoa"], width=BORDER, name="cookie edge")
    for g in eyes:
        d.fill(g, C_["cocoa"], angle=45, underlay=False, name="eye")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
