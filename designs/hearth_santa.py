"""Santa: a jolly vintage Santa face with a floppy hat and a big curly beard.

Spec:
  object:       classic Santa Claus face for sweatshirts, stockings, pillows and towels
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; towels with a water-soluble topper
  threads:      blush (face), red (hat), white (fur brim, pompom, beard, moustache),
                silver (1.2 mm outlines of the white parts), pink (cheeks, nose),
                black (eyes): 6 colours
  must have:    a 30 mm face; a red hat flopping to the right with a 42 mm white fur brim
                and a 10 mm pompom; a scalloped 44 mm beard; a two-lobed moustache sewn
                across the beard's grain, its lower edge drawn in a silver bean run; a pink nose, rosy cheeks and two eyes
  density:      white parts knock out the face and hat; fills tuck under the outlines
"""
import numpy as np

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Jolly vintage Santa face with a floppy red hat and a curly white beard"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Vintage Santa Face Embroidery Design",
    "A jolly Santa face with a floppy red hat and a big curly white beard",
    ["santa", "santa claus", "vintage santa", "father christmas", "christmas stocking",
     "kids christmas"],
    "A jolly old Santa: rosy cheeks, a floppy red hat with a fluffy white brim and pompom, and "
    "a big scalloped white beard and moustache.\n\nGreat on stockings, sweatshirts, pillows and "
    "tea towels.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.2


def checks(p):
    return standard_checks(p, 6, 13000)


def _lower_edge(tache):
    """The moustache's lower edge, tip to tip, 0.6 mm inside it (its two lobes' axes
    tilt 12 deg down to the tips)."""
    pts = np.array(tache.buffer(-0.6).exterior.coords)[:-1]
    below = pts[:, 1] < 1.5 - 0.2126 * (np.abs(pts[:, 0]) - 6.5)
    i = int(np.argmin(below))                       # start the chain where it leaves the top
    pts, below = np.roll(pts, -i, axis=0), np.roll(below, -i)
    chain = pts[below]
    return chain[np.argsort(chain[:, 0])]


def art():
    d = Design()
    face = ellipse(0, 8, 15.5, 13)
    hat = smooth([(-18, 18), (-13, 31), (2, 40), (17, 38), (27, 28), (29, 18), (24, 17), (19, 27),
                  (9, 30), (17, 18)], 8).buffer(0)
    brim = rounded_rect(42, 9, 4.5, 0, 18)
    pom = circle(27, 14.5, 5.2)
    beard = union(ellipse(0, -12, 21, 17), circle(-14, -22, 8), circle(-5, -28, 8.5),
                  circle(6, -28, 8.5), circle(15, -21, 8), circle(-19, -10, 6.5), circle(19, -10, 6.5))
    beard = beard.buffer(0.6).buffer(-0.6)
    tache = union(rotate(ellipse(-6.5, 1.5, 7.5, 3.6), 12, origin=(-6.5, 1.5)),
                  rotate(ellipse(6.5, 1.5, 7.5, 3.6), -12, origin=(6.5, 1.5)))
    nose = circle(0, 7.8, 2.4)
    cheeks = [circle(-10.5, 6.5, 3.0), circle(10.5, 6.5, 3.0)]
    eyes = [ellipse(-5.5, 11.5, 1.5, 1.9), ellipse(5.5, 11.5, 1.5, 1.9)]
    whites = union(brim, pom, beard, tache)
    d.fill(knockout(face, grow(whites, BORDER / 2), nose, *cheeks, *eyes), C_["blush"], angle=0, name="face")
    d.fill(knockout(hat, grow(brim, BORDER / 2), grow(pom, BORDER / 2)), C_["red"], angle=60, name="hat")
    d.fill(tuck(knockout(beard, tache), BORDER), C_["white"], angle=70, name="beard")
    d.fill(tuck(brim, BORDER), C_["white"], angle=0, name="fur brim")
    d.fill(tuck(pom, BORDER), C_["white"], angle=45, name="pompom")
    d.fill(tuck(knockout(tache, nose), BORDER), C_["white"], angle=0, name="moustache")
    d.outline(union(beard, tache), C_["silver"], width=BORDER, name="beard edge")
    d.outline(brim, C_["silver"], width=BORDER, name="brim edge")
    d.outline(pom, C_["silver"], width=BORDER, name="pompom edge")
    d.run(_lower_edge(tache), C_["silver"], bean=1, name="moustache line", trim_after=True)
    for g in cheeks + [nose]:
        d.fill(g, C_["pink"], angle=45, underlay=False, name="rosy")
    for g in eyes:
        d.fill(g, C_["black"], angle=90, underlay=False, name="eye")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
