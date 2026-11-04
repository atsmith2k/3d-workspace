"""Sufganiyah: a plump golden jelly doughnut dusted with powdered sugar, red jam oozing
from a piping hole on its side, and a little blue Star of David pick.

Spec:
  object:       fun Hanukkah food design for aprons, tea towels, kids' tees, bibs
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7; the 4x4 keeps 5 mm
                clear of the hoop edge)
  fabric:       knits with cut-away; wovens (aprons, towels) with tear-away
  threads:      ginger (toasted crust), tan (golden lit side), red (jam), berry (jam
                shadow), white (powdered sugar, jam glints), blue (pick and Star of
                David): 6 colours
  must have:    a plump 68 x 60 mm doughnut ball: toasted ginger crust all round, widest
                on the shadow side, with a soft-edged golden tan lit area to the lower
                left so it reads round, not banded; a white powdered-sugar cap over the top with a
                cloudy, lumpy lower edge and a 1.6 mm crust rim left above it (no border
                ring: the crust is the edge); red jam squeezing out of a piping hole on
                the upper right side, past the outline, and running down the side in a
                drip that ends in a round drop, with a berry shadow edge and two white
                satin glints; a 1.2 mm blue satin pick rising to a 12 mm blue Star of David
  density:      each piece knocks out what is under it (0.4 mm overlap); max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Jelly doughnut with powdered sugar, oozing red jam and a Star of David pick"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Sufganiyah Jelly Doughnut Embroidery Design",
    "A plump jelly doughnut dusted with sugar, jam oozing out and a Star of David pick",
    ["sufganiyah", "sufganiyot", "jelly doughnut", "jelly donut", "hanukkah food",
     "hanukkah apron", "kitchen embroidery", "doughnut embroidery"],
    "A plump golden sufganiyah, the Hanukkah jelly doughnut: toasted on top, dusted with "
    "powdered sugar, with red jam oozing from its side and a little blue Star of David pick "
    "stuck in the top.\n\nSweet on aprons, tea towels, kids' tees and bibs.",
    mockups=("tshirt", "tote"),
)

RX, RY = 34.0, 30.0
RIM = 1.6


def checks(p):
    return standard_checks(p, 6, 12000)


def _above(fn, top=60.0, x0=-45.0, x1=45.0, n=121):
    """The area above the curve y=fn(x)."""
    xs = np.linspace(x0, x1, n)
    return poly(list(zip(xs, fn(xs))) + [(x1, top), (x0, top)])


def art():
    d = Design()
    body = ellipse(0, 0, RX, RY)

    # powdered sugar cap: its lower edge is a latitude line seen from above (sags in the
    # middle), made lumpy by overlapping puffs; a crust rim stays visible above it
    def cap_line(x):
        return 15.0 - 6.0 * np.sqrt(np.clip(1 - (x / RX) ** 2, 0, 1))

    rng = np.random.default_rng(5)
    xs = np.arange(-29.0, 30.0, 3.6)
    puffs = [circle(x + rng.uniform(-0.6, 0.6), cap_line(x) + rng.uniform(-0.6, 0.8), rng.uniform(1.8, 3.0))
             for x in xs]
    puffs += [circle(-12.0, cap_line(-12.0) - 2.2, 2.4), circle(6.0, cap_line(6.0) - 2.0, 2.2)]
    sugar = union(_above(cap_line), *puffs).buffer(0.9).buffer(-0.9).intersection(shrink(body, RIM))

    t = np.linspace(0, 2 * np.pi, 16, endpoint=False)
    r = 1 + rng.uniform(-0.05, 0.05, len(t))
    lit = smooth(list(zip(-6.0 + 26.0 * r * np.cos(t), -2.0 + 23.0 * r * np.sin(t))), 8).buffer(0)
    lit = lit.intersection(shrink(body, 1.6))

    # jam squeezing out of a piping hole on the upper right side and dripping down it
    blob = rotate(ellipse(27.5, 6.5, 8.4, 6.4), -35, origin=(27.5, 6.5))
    drip = LineString([(31.0, 3.0), (32.6, -2.0), (32.6, -4.5)]).buffer(2.4)
    drop = circle(32.4, -7.2, 3.6)
    jam = union(blob, drip, drop).buffer(1.0).buffer(-1.0)
    jam_shade = jam.difference(move(jam, -2.0, 0.0)).buffer(-0.7).buffer(0.7)
    glints = [line((23.6, 8.0), (26.6, 9.6)), line((30.4, -5.6), (30.6, -8.0))]
    glint_area = union(*[LineString(g).buffer(0.55) for g in glints])

    sx, sy = 13.0, 46.0
    star_ = star(6, 6.0, 6.0 / 3 ** 0.5, sx, sy).buffer(-0.25).buffer(0.25)
    top = RY * np.sqrt(1 - (8.0 / RX) ** 2)
    pick = line((8.0, top + 0.3), (sx - 0.4, sy - 3.0))

    d.fill(knockout(body, lit, sugar.difference(jam), jam), C_["ginger"], angle=135, name="toasted crust")
    d.fill(knockout(lit, sugar.difference(jam), jam), C_["tan"], angle=45, name="golden side")
    d.fill(knockout(jam, jam_shade, glint_area), C_["red"], angle=60, name="jam")
    d.fill(knockout(jam_shade, glint_area), C_["berry"], angle=150, name="jam shadow")
    d.fill(sugar.difference(shrink(jam, 0.4)), C_["white"], angle=45, name="powdered sugar")
    for g in glints:
        d.satin(g, 1.1, C_["white"], name="jam glint", trim_after=True)
    d.satin(pick, 1.2, C_["blue"], name="pick")
    d.fill(star_, C_["blue"], angle=0, name="Star of David")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
