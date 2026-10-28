"""Silicone mold master for six wax melts: a printed box with six 30 mm melt shapes,
each topped with its own raised design (leaf, flower, heart, sprig, star and daisy).

Pour silicone into the box to just over the rim, let it cure and peel it out: you have a
six-cavity wax-melt mold that copies every design. The melts come out 30 x 30 mm and
14 mm thick with the design raised on their face. The build reports how much silicone to
mix. Prints in one piece, open side up, with no supports, on a Bambu A1 or A1 mini.

Spec:
  object:       one-piece silicone mold master (positive + mold box) for six wax melts
  overall:      box 126 x 88 x 22 mm; six melt shapes 30 x 30 x 14 mm in a 3 x 2 grid
  casting:      silicone 8 mm between and round the melts, 6 mm behind them; melts
                30 x 30 mm at the face, 2 deg draft, 4 mm rounded corners
  orientation:  floor on the bed, opening up; no supports
  must have:    six different raised designs, 0.8 mm high, lines 1.5 mm wide;
                silicone volume reported by the build
  tolerances:   none (casting)

Units: mm. Z is up, the part sits on Z=0.
"""
import math

import numpy as np

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Silicone mold master for six 30 mm wax melts with botanical reliefs"

PRODUCT = dict(
    title="Botanical Wax Melt Silicone Mold Master",
    category="molds",
    tags=["mold", "silicone mold", "wax melt mold", "mold master", "wax melts", "candle making",
          "botanical", "leaf", "flower", "heart"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then wax",
    post_processing=("Brush a sealer or spray release over the master; the silicone copies layer "
                     "lines. Mix the silicone volume the build reports, pour slowly into one corner "
                     "until it covers the melt shapes by about 6 mm, and demold after full cure."),
)
LICENSE_NOTES = None   # original artwork

PARAMS = dict(
    melt=30.0,          # melt size at its face
    melt_h=14.0,
    corner=4.0,
    draft=2.0,
    gap=8.0,            # silicone between melts and round them
    back=6.0,           # silicone behind the melts (over their tops)
    floor=2.0,
    wall=2.4,
    relief=0.8,         # design height
    line=1.5,           # design line width
)

EMBED = 0.1


def _star(r_out, r_in, n=5):
    return [(r * math.cos(math.pi / 2 + math.pi * i / n), r * math.sin(math.pi / 2 + math.pi * i / n))
            for i, r in enumerate([r_out, r_in] * n)]


def designs(w):
    """Six designs drawn in a 24 x 24 box, as stroke lists (scaled to the melt face)."""
    leaf_edge = list(catmull_rom_closed([(0, 11), (6, 4), (6, -4), (0, -11), (-6, -4), (-6, 4)], 10))
    leaf = [leaf_edge + [leaf_edge[0]], [(0, -11), (0, 10)]]
    leaf += [[(0, y), (s * 4.2, y + 3.5)] for y in (-5, 0, 4) for s in (1, -1)]
    flower = []
    for k in range(5):
        a = math.pi / 2 + 2 * math.pi * k / 5
        c, sn = math.cos(a), math.sin(a)
        pts = [(5.5 * c + 4.2 * math.cos(t) * c - 2.6 * math.sin(t) * -sn,
                5.5 * sn + 4.2 * math.cos(t) * sn - 2.6 * math.sin(t) * c) for t in np.linspace(0, 2 * math.pi, 25)]
        flower.append(pts)
    hp = np.asarray(heart(20).to_polygons()[0])
    heart_s = [list(map(tuple, np.r_[hp, hp[:1]]))]
    sprig = [list(map(tuple, bezier((0, -11), (2, 0), (-1, 11), n=14)))]
    for y, s in ((-6, 1), (-2, -1), (2, 1), (6, -1)):
        x0 = 0.5 + 0.1 * y
        sprig.append([(x0, y), (x0 + s * 6, y + 3)])
    st = _star(11, 4.6)
    star = [st + [st[0]]]
    daisy = [[(3.5 * math.cos(a), 3.5 * math.sin(a)), (10.5 * math.cos(a), 10.5 * math.sin(a))]
             for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
    k = (w - 6) / 24.0
    sets = [leaf, flower, heart_s, sprig, star, daisy]
    return [[[(x * k, y * k) for x, y in path] for path in s] for s in sets], [None, (0, 0, 2.2), None, None, None, (0, 0, 2.6)]


def centres(p):
    step = p.melt + p.gap
    return [((i - 1) * step, (0.5 - j) * step) for j in range(2) for i in range(3)]


def box_size(p):
    return 3 * p.melt + 4 * p.gap, 2 * p.melt + 3 * p.gap


def melt(p, k, cx=0.0, cy=0.0, z=0.0):
    """Melt k (0-5) as the master's raised shape: drafted block plus its design on top."""
    lean = draft_offset(p.melt_h, p.draft)
    sq = grow(CrossSection.square((p.melt - 2 * p.corner + 2 * lean, p.melt - 2 * p.corner + 2 * lean), center=True), p.corner)
    block = tapered(sq, 0, p.melt_h, -lean)
    paths, dots = designs(p.melt)
    art = CrossSection()
    for path in paths[k]:
        art += stroke(path, p.line)
    if dots[k]:
        art += circle(*dots[k][:2], dots[k][2])
    block += extrude(art, p.relief + EMBED, p.melt_h - EMBED)
    return block.translate((cx, cy, z))


def silicone_ml(p):
    bx, by = box_size(p)
    fill = bx * by * (p.melt_h + p.back) - (4 - math.pi) * p.corner ** 2
    return (fill - sum(melt(p, k).volume() for k in range(6))) / 1000.0


def checks(p):
    bx, by = box_size(p)
    top = p.floor + p.melt_h + p.back
    ml = silicone_ml(p)
    return [
        dims(x=bx + 2 * p.wall, y=by + 2 * p.wall, z=top),
        solid(*[(x, y, p.floor + p.melt_h / 2) for x, y in centres(p)]),
        empty(*[(x + p.melt / 2 + p.gap / 2, y, p.floor + 1) for x, y in centres(p)[:2]]),
        custom("silicone to mix", lambda ctx: (True, f"{ml:.0f} ml (about {ml * 1.1:.0f} g)")),
        flat_base(bx * by * 0.95),
        no_overhang(),
        single_body(),
    ]


def build(p):
    bx, by = box_size(p)
    top = p.floor + p.melt_h + p.back
    outer = grow(CrossSection.square((bx - 2 * p.corner, by - 2 * p.corner), center=True), p.corner + p.wall)
    inner = grow(CrossSection.square((bx - 2 * p.corner, by - 2 * p.corner), center=True), p.corner)
    mold = extrude(outer, top) - extrude(inner, top + 1, p.floor)
    for k, (x, y) in enumerate(centres(p)):
        mold += melt(p, k, x, y, p.floor - EMBED)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the six melts, design up."""
    out = None
    for k, (x, y) in enumerate(centres(p)):
        m = melt(p, k, x, y)
        out = m if out is None else out + m
    return out
