"""Kettle On, Boots Off: a cross-stitch-look sampler: KETTLE ON / BOOTS OFF in our block
lettering inside a border of true machine cross stitches, with cross-stitched hearts,
a round door, little trees and a toadstool.

Spec:
  object:       a homey motto sampler (our own wording, cozy fantasy / cottagecore) for
                tea towels, cushions, framed hoops, aprons and totes
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       wovens (linen, flour-sack towels, cotton) with tear-away; knits cut-away
  threads:      deep gold (cross-stitch border, door knob, toadstool stem), emerald (round door, trees, inner rule,
                KETTLE ON), red (hearts, toadstool cap), clay brown (BOOTS OFF): 4 colours
  must have:    a 96 x 75 mm border of cross stitches in 2.67 mm cells, each X two
                single stitches; a bean-run rule 3.2 mm inside it; an 11-cell round door with
                its frame and a gold knob flanked by two hearts at the top; KETTLE ON and BOOTS OFF in block
                lettering, 10 mm caps, at most 78 mm wide; two trees and a spotted toadstool
                along the bottom, all motifs cross-stitched in 2.0 mm cells
  technique:    cross stitch rows are sewn forward as one zigzag and back as the other
                (one connector stitch at the row end); lettering is fill, rows 0.35 mm
  density:      crosses are 2 layers where the diagonals meet; max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _hollow import C_, SIZES, centred, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Cross-stitch-look sampler: KETTLE ON / BOOTS OFF with hearts, a round door, trees and a toadstool"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Kettle On Boots Off Sampler Embroidery Design",
    "A cross-stitch-look sampler: KETTLE ON / BOOTS OFF with hearts, a round door, trees and a toadstool",
    ["sampler", "cross stitch look", "kettle on", "home sampler", "cozy quote", "tea towel embroidery",
     "farmhouse", "home decor embroidery", "tea lover", "welcome home"],
    "Home at last: KETTLE ON / BOOTS OFF in bold block letters, framed by a border of real "
    "machine cross stitches with a cross-stitched round door between two hearts, and little "
    "trees and a spotted toadstool along the bottom, like a sampler from a cottage wall.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tea towels, cushions, "
    "framed hoops, aprons and totes.",
    mockups=("tshirt", "tote"),
)

W, H = 96.0, 74.67
CB = W / 36            # border cell
CM = 2.0               # motif cell

HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
DOOR = ["...#####...", "..##...##..", ".##.###.##.", ".#.#####.#.", ".#.###K#.#.", ".#.#####.#.",
        "###########"]
TREE = ["...#...", "..###..", ".#####.", "..###..", ".#####.", "#######", "...#...", "...#..."]
SHROOM = ["..###..", ".#####.", "##.#.##", "#######", "..KKK..", "..KKK.."]


def checks(p):
    return standard_checks(p, 4, 14000)


def x_row(x0, y0, n, c):
    """One row of n cross stitches, cells c wide, bottom-left (x0, y0): forward zigzag,
    a connector up/down the last cell's edge, back along the other zigzag."""
    yb, yt = y0, y0 + c
    fwd = [(x0, yb)] + [(x0 + (k + 1) * c, yt if k % 2 == 0 else yb) for k in range(n)]
    end_other = yb if (n - 1) % 2 == 0 else yt          # where cell n-1's other diagonal ends
    back = [(x0 + n * c, end_other)] + [(x0 + k * c, yt if k % 2 == 0 else yb) for k in range(n - 1, -1, -1)]
    return fwd + back


def motif(rows, cx, cy, c=CM, mark="#"):
    """Row paths for the `mark` cells of a pixel motif centred on (cx, cy)."""
    h, w = len(rows), len(rows[0])
    x_left, y_top = cx - w * c / 2, cy + h * c / 2
    paths = []
    for r, line in enumerate(rows):
        y0 = y_top - (r + 1) * c
        k = 0
        while k < w:
            if line[k] == mark:
                j = k
                while j < w and line[j] == mark:
                    j += 1
                paths.append(x_row(x_left + k * c, y0, j - k, c))
                k = j
            else:
                k += 1
    return paths


def border():
    """Four sides of crosses; corners belong to the top and bottom rows."""
    x0, y0 = -W / 2, -H / 2
    nx, ny = round(W / CB), round(H / CB)
    paths = [x_row(x0, y0 + H - CB, nx, CB), x_row(x0, y0, nx, CB)]
    for x in (x0, x0 + W - CB):
        for k in range(1, ny - 1):
            pass
        # a column: rotate the row construction 90 degrees
        col = x_row(0, 0, ny - 2, CB)
        paths.append([(x + CB - py, y0 + CB + px) for px, py in col])
    return paths


def _fit_word(word, cap, max_w, y):
    t = block_text(word, cap=cap, stroke=2.5, tracking=1.6)
    x0, _, x1, _ = t.bounds
    k = min(1.0, max_w / (x1 - x0))
    t = scale(t, k, k)
    return centred(t, 0, y)


def art():
    d = Design()
    for p in border():
        d.run(p, C_["gold"], length=4.0, name="cross-stitch border")
    for p in motif(DOOR, 0, 23.5, mark="K") + motif(SHROOM, 0, -24.0, mark="K"):
        d.run(p, C_["gold"], length=4.0, name="knob and stem")
    rule = rect(W - 2 * CB - 6.4 + 2 * 1.6, H - 2 * CB - 6.4 + 2 * 1.6)
    d.run(outline_paths(rule)[0], C_["green"], bean=1, name="inner rule")
    for p in motif(DOOR, 0, 23.5):
        d.run(p, C_["green"], length=4.0, name="round door")
    for x in (-34, 34):
        for p in motif(TREE, x, -22.5):
            d.run(p, C_["green"], length=4.0, name="tree")
    kettle = _fit_word("KETTLE ON", 10, 78, 7.5)
    d.fill(kettle, C_["green"], angle=0, spacing=0.35, name="KETTLE ON")
    for x in (-20, 20):
        for p in motif(HEART, x, 23.5):
            d.run(p, C_["red"], length=4.0, name="heart")
    for p in motif(SHROOM, 0, -24.0):
        d.run(p, C_["red"], length=4.0, name="toadstool cap")
    boots = _fit_word("BOOTS OFF", 10, 78, -7.5)
    d.fill(boots, C_["rust"], angle=0, spacing=0.35, name="BOOTS OFF")

    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
