"""Latke Love: a stack of three golden potato latkes with crisp brown edges on a blue
plate, topped with a dollop of sour cream and chives, over "LATKE LOVE".

Spec:
  object:       fun Hanukkah food design for aprons, tea towels, oven mitts, sweatshirts
  overall:      `size` mm wide (95 for the 4x4 hoop, 160 for 5x7; the 4x4 keeps 5 mm
                clear of the hoop edge)
  fabric:       wovens (aprons, towels) with tear-away; knits with cut-away
  threads:      blue (plate, lettering), tan (latkes), ginger (crisp edges, shred
                texture), white (sour cream), cream (its shadow side and edge), leaf
                (chives): 6 colours
  must have:    three wobbly-edged latkes about 60 x 15 mm stacked on a 76 x 10 mm blue
                plate, each with a 2 mm ginger crisp edge band and a wavy ginger bean-run
                shred line 2 mm inside; a 22 mm sour-cream dollop with a curled peak, white
                rows at 45 deg (they catch the light), a cream (Beige) shadow crescent on
                its lower right and a 1 mm cream satin edge (no silver); three 1.2 mm green chive bits;
                "LATKE LOVE" in the house block lettering (`lettering.block_text`), 10 mm
                cap, 0.35 mm rows
  density:      upper latkes knock out lower ones, edges knock out the latke bodies, the
                dollop knocks out the top latke, the shadow knocks out the white, chives
                lie on the cream; max 3.5
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

from _lights import C_, SIZES, fit, hoop_for, product, standard_checks  # noqa: F401

DESCRIPTION = "Stack of golden potato latkes with sour cream over Latke Love lettering"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Latke Love Embroidery Design",
    "A stack of crispy golden latkes with sour cream and \"Latke Love\"",
    ["latke", "latke love", "potato latkes", "hanukkah food", "hanukkah apron",
     "tea towel embroidery", "kitchen embroidery", "funny hanukkah"],
    "A stack of three golden potato latkes with crispy brown edges, served on a blue plate "
    "with a dollop of sour cream and a sprinkle of chives, over \"Latke Love\" in blue block "
    "letters.\n\nMade for the kitchen: aprons, tea towels and oven mitts, and just as fun on "
    "a Hanukkah sweatshirt.",
    mockups=("tshirt", "tote"),
)

EDGE = 2.0


def checks(p):
    return standard_checks(p, 6, 12000)


def _latke(x, y, rx, ry, seed):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, 18, endpoint=False)
    r = 1 + rng.uniform(-0.05, 0.05, len(t))
    return smooth(list(zip(x + rx * r * np.cos(t), y + ry * r * np.sin(t))), 8).buffer(0)


def _shreds(x, y, rx, amp, n):
    """A wavy line across a latke, the grated-potato texture."""
    xs = np.linspace(x - rx, x + rx, n * 8 + 1)
    ys = y + amp * np.sin(np.linspace(0, n * 2 * np.pi, len(xs)))
    return np.c_[xs, ys]


def art():
    d = Design()
    # bottom to top: (x, y, rx, ry, seed)
    specs = [(0.0, -11.0, 31.0, 7.0, 3), (-2.0, -3.5, 29.5, 7.0, 7), (1.0, 5.0, 28.5, 8.5, 11)]
    latkes = [_latke(*s) for s in specs]
    dollop = union(ellipse(0.5, 10.5, 11, 4.6),
                   smooth([(-6, 11), (-4, 16), (0, 19.5), (2.6, 21.6), (4.0, 21.0), (3.4, 18.5), (6, 14), (6, 11)], 8).buffer(0)
                   ).buffer(0.8).buffer(-0.8).buffer(-0.9).buffer(0.9)
    plate = ellipse(0, -16.5, 38, 5.0)
    word = move(centered(block_text("LATKE LOVE", cap=10, stroke=2.4)), 0, -33)
    # what of each latke shows: everything above it covers it
    above = [union(*latkes[i + 1:]) if i < 2 else None for i in range(3)]
    shown = []
    for i, lk in enumerate(latkes):
        cover = above[i]
        if i == 2:
            cover = grow(dollop, 0.9)
        shown.append(knockout(lk, cover) if cover is not None else lk)
    edges = [s.difference(shrink(lk, EDGE)) for s, lk in zip(shown, latkes)]
    bodies = [knockout(s, e) for s, e in zip(shown, edges)]
    shreds = [_shreds(0.0, -14.2, 21.0, 0.8, 4), _shreds(-2.0, -6.9, 20.0, 0.8, 4)]
    shreds.append(_shreds(specs[2][0] - 2.0, specs[2][1] - 4.0, 17.0, 1.2, 4))
    chives = [((-4.5, 9.0), (-2.2, 10.0)), ((2.0, 12.6), (4.4, 12.0)), ((-1.5, 14.8), (0.4, 16.2))]

    d.fill(word, C_["blue"], angle=0, spacing=0.35, name="Latke Love")
    d.fill(knockout(plate, latkes[0]), C_["blue"], angle=0, name="plate")
    for i, b in enumerate(bodies):
        d.fill(b, C_["tan"], angle=(15, 165, 20)[i], name=f"latke {i + 1}")
    for i, e in enumerate(edges):
        d.fill(e, C_["ginger"], angle=(60, 120, 60)[i], name=f"crisp edge {i + 1}")
    for s in shreds:
        d.run(s, C_["ginger"], bean=1, name="shreds", trim_after=True)
    inner = tuck(dollop, 1.0)
    shade = dollop.difference(move(dollop, -2.4, 2.2)).buffer(-0.6).buffer(0.6).intersection(inner)
    d.fill(knockout(inner, shade), C_["white"], angle=45, name="sour cream")
    d.fill(shade, C_["cream"], angle=135, name="cream shadow")
    d.outline(dollop, C_["cream"], width=1.0, name="cream edge")
    for a, b in chives:
        d.satin(line(a, b), 1.2, C_["leaf"], name="chive", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
