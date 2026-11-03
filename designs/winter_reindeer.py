"""Woodland Reindeer: a sweet front-facing reindeer head with antlers and a holly sprig.

Spec:
  object:       cute reindeer face (generic, no named character: brown nose, not red)
                for kids' wear, sweatshirts, stockings, towels
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; towels with tear-away and a topper
  threads:      tan (antlers), ginger (head and ears), cream (muzzle), pink (inner ears
                and cheeks), cocoa (eyes and nose), green (holly), red (berries): 7
  must have:    a 34 x 46 mm head; two antlers as tapered satin beams (3.2 to 1.6 mm)
                with two tines each, every tine starting 1.6 mm clear of its beam; ears
                angled out with pink insides; a cream muzzle, a cocoa nose, two eyes and
                pink cheeks; a holly sprig with three berries at the left antler's base
  density:      every part knocks out what it covers; max 3.5 layers
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _winter import C_, SIZES, fit, holly_sprig, product, standard_checks

DESCRIPTION = "Sweet front-facing reindeer with antlers and a holly sprig"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Woodland Reindeer Embroidery Design",
    "A sweet reindeer face with branching antlers and a holly sprig",
    ["reindeer", "woodland christmas", "kids christmas", "reindeer face", "christmas deer"],
    "A sweet woodland reindeer looking straight at you: branching antlers, soft ears, rosy "
    "cheeks, a cream muzzle and a sprig of holly tucked by one antler.\n\nGreat on kids' wear, "
    "sweatshirts, stockings and tea towels.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 12000)


def _antler(sign):
    """(beam path, [tine paths]) for one antler, mirrored by `sign`."""
    beam = spline(np.array([(5, 24), (9, 34), (16, 44), (22, 54)]), 8)
    tines = [np.array([(9.8, 36.0), (3.5, 47.0)]), np.array([(15.6, 44.5), (26.5, 46.5)])]
    k = np.array([sign, 1.0])
    return beam * k, [t * k for t in tines]


def _away(path, mm):
    """Start a tine `mm` along itself, clear of the beam it grows from."""
    a, b = path
    u = (b - a) / np.linalg.norm(b - a)
    return np.array([a + u * mm, b])


def art():
    d = Design()
    head = ellipse(0, 6, 17, 23)
    muzzle = ellipse(0, -8, 12, 9.5)
    ears, inner = [], []
    for sign in (-1, 1):
        e = rotate(ellipse(sign * 22, 22, 9.5, 4.6), sign * 28, origin=(sign * 22, 22))
        ears.append(e)
        inner.append(rotate(ellipse(sign * 22.6, 22.2, 6.0, 2.2), sign * 28, origin=(sign * 22, 22)))
    eyes = [circle(-7, 11, 2.4), circle(7, 11, 2.4)]
    nose = ellipse(0, -3.5, 5.2, 3.6)
    cheeks = [circle(-11, 0.5, 2.6), circle(11, 0.5, 2.6)]
    leaves, veins, berries = holly_sprig(-10, 25, deg=180, length=14)
    holly = union(*leaves, *berries)
    for sign in (-1, 1):
        beam, tines = _antler(sign)
        for t in tines:
            p = _away(t, 1.6)
            d.satin(spline(p, 5), M.taper(spline(p, 5), 2.0, 1.2), C_["tan"], name="tine", underlay="none")
        d.satin(beam, M.taper(beam, 3.2, 1.6), C_["tan"], name="antler", underlay="center")
    for e, i in zip(ears, inner):
        d.fill(knockout(e, i, head), C_["ginger"], angle=0, name="ear")
    d.fill(knockout(head, muzzle, *eyes, *cheeks, holly), C_["ginger"], angle=90, name="head")
    d.fill(knockout(muzzle, nose, *cheeks), C_["cream"], angle=0, name="muzzle")
    for g in inner + cheeks:
        d.fill(g, C_["pink"], angle=45, underlay=False, name="pink")
    for g in eyes:
        d.fill(g, C_["cocoa"], angle=45, underlay=False, name="eye")
    d.fill(nose, C_["cocoa"], angle=0, name="nose")
    for g in leaves:
        d.fill(knockout(g, *berries), C_["green"], name="holly leaf")
    for b in berries:
        d.fill(b, C_["red"], angle=45, underlay=False, name="berry")
    return d


def design(p):
    return fit(art(), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
