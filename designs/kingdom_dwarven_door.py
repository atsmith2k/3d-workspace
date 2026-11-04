"""Dwarven Hall Door: an arched stone door under a band of runes, with a hammer and anvil
in the middle and an interlaced knot border, on a stepped threshold.

Spec:
  object:       the great door of a mountain hall of dwarven smiths (original door:
                genuine Elder Futhark runes spelling nothing, our own knotwork) for tees,
                hoodies, totes, journal covers and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      charcoal (door face), pewter (stone frame, upper step), gray (lower step), silver (knot border,
                frame lines, anvil, door seam), gold (runes, hammer head, sparks), wood
                (hammer haft): 6 colours
  must have:    a 64 x 86 mm round-topped stone frame 8 mm wide, eleven gold runes 5 mm
                tall on its arch (one-stroke Elder Futhark, bean stitch); a silver 1.8 mm
                satin on the frame's outer edge and 1.4 mm on its inner edge; inside, an
                interlaced two-strand knot border (1.5 mm satins, over/under, the under
                strand stopping 0.7 mm clear of the over strand); a 26 mm silver anvil with
                a gold-headed hammer raised over it and three gold sparks; a bean-stitch
                seam between the two door leaves; two stone steps under the door (pewter, gray)
  density:      the door face and frame are knocked out under every satin band and the
                emblem; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString
from shapely.geometry import Point as Point_

from cadkit.stitch import *

from _kingdom import C_, SIZES, band, fit, hoop_for, pieces, product, resample, standard_checks

DESCRIPTION = "Arched dwarven stone door with runes, knotwork, hammer and anvil"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Dwarven Hall Door Embroidery Design",
    "An arched stone door with a band of gold runes, a silver knotwork border and a hammer over an anvil",
    ["dwarf", "dwarven", "dwarf door", "mountain hall", "runes", "elder futhark", "knotwork",
     "hammer and anvil", "blacksmith", "forge", "viking", "nordic"],
    "The great door of a mountain hall of smiths: an arched stone frame carved with gold "
    "runes, an interlaced silver knotwork border, and a hammer raised over an anvil "
    "throwing sparks, on a stepped stone threshold.\n\n"
    "Great on hoodies, tees, tote bags, journal covers and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 22000)


CY = 12.0                     # arch centre
RO, RI = 32.0, 24.0           # frame outer / inner radius (and half widths)
BOT = -40.0                   # frame foot
SILL = 3.4                    # the door stands on a sill of frame stone this high
OW, IW = 1.8, 1.4             # frame line satins


def arch(r, bottom=BOT):
    a = np.radians(np.linspace(0, 180, 90))
    top = np.c_[r * np.cos(a), CY + r * np.sin(a)]
    return poly([(r, bottom)] + [tuple(q) for q in top] + [(-r, bottom)])


RUNES = {  # one-stroke Elder Futhark letters in a 0.6 x 1 box (x, y)
    "uruz": [(0, 0), (0, 1), (0.55, 0.72), (0.55, 0)],
    "thurisaz": [(0, 0), (0, 0.28), (0.45, 0.5), (0, 0.72), (0, 1)],
    "raido": [(0, 0), (0, 1), (0.45, 0.8), (0, 0.56), (0.5, 0)],
    "kaunan": [(0.4, 0.9), (0, 0.6), (0.4, 0.3)],
    "isa": [(0, 0), (0, 1)],
    "sowilo": [(0.45, 1), (0, 0.66), (0.45, 0.34), (0, 0)],
    "ehwaz": [(0, 0), (0, 1), (0.3, 0.66), (0.6, 1), (0.6, 0)],
    "laguz": [(0, 0), (0, 1), (0.45, 0.72)],
    "ingwaz": [(0.3, 0.05), (0.6, 0.5), (0.3, 0.95), (0, 0.5), (0.3, 0.05)],
    "dagaz": [(0, 0), (0, 1), (0.7, 0), (0.7, 1), (0, 0)],
    "tiwaz": [(0, 0.72), (0.3, 1), (0.6, 0.72), (0.3, 1), (0.3, 0)],
}
ORDER = ["dagaz", "raido", "uruz", "ehwaz", "isa", "ingwaz", "isa", "laguz", "thurisaz", "sowilo", "kaunan"]
RUNE_H = 5.0


def _dense(pts, step=1.8):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out += [a + (b - a) * k / n for k in range(1, n + 1)]
    return np.array(out)


def runes():
    """Runes round the arch, feet toward the door, read left to right."""
    rc = (RO + RI) / 2
    out = []
    n = len(ORDER)
    for i, name in enumerate(ORDER):
        g = np.asarray(RUNES[name], float)
        if name == "tiwaz":
            g = np.asarray([(0, 0.72), (0.3, 1), (0.6, 0.72)], float)
        g[:, 0] -= (g[:, 0].min() + g[:, 0].max()) / 2
        g[:, 1] -= 0.5
        g *= RUNE_H
        a = math.radians(168 - i * (156 / (n - 1)))
        radial = np.array([math.cos(a), math.sin(a)])
        tang = np.array([math.sin(a), -math.cos(a)])
        pts = np.array([0, CY]) + radial * rc + g[:, :1] * tang + g[:, 1:] * radial
        out.append(_dense(pts))
    return out


def knot_path(off=4.2):
    """Centreline of the knot border: up the left side, round the arch, down the right."""
    r = RI - off
    y0 = BOT + SILL + 3.4
    a = np.radians(np.linspace(180, 0, 120))
    pts = [(-r, y0), (-r, CY)] + [(r * math.cos(t), CY + r * math.sin(t)) for t in a] + [(r, y0)]
    return resample(np.array(pts), 0.25)


def knot(amp=2.4, lam=11.0, w=1.5, gap=0.7):
    """Two strands weaving round the knot path, crossing every half wave and alternating
    over and under; the under strand stops where its column would come within `gap` mm
    of the over strand's. Returns satin pieces [(path, strand)]."""
    c = knot_path()
    seg = np.linalg.norm(np.diff(c, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    L = s[-1]
    n_half = int(L / (lam / 2))
    lam = 2 * L / n_half                          # whole number of half waves: ends on a crossing
    t = np.gradient(c, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    nrm = np.c_[-t[:, 1], t[:, 0]]
    ph = np.sin(2 * np.pi * s / lam)
    strands = [c + nrm * (amp * ph)[:, None], c - nrm * (amp * ph)[:, None]]
    cross = np.arange(1, n_half) * lam / 2       # interior crossings (ends are open)
    out = []
    for k in (0, 1):
        keep = np.ones(len(c), bool)
        over = strands[1 - k]
        for j, x in enumerate(cross):
            if j % 2 != k:
                continue                          # strand k is over here
            near = np.abs(s - x) < lam / 4
            idx = np.where(near)[0]
            seg_over = LineString(over[idx])
            for i in idx:
                # the column end is square, so its corner (w/2 off the centreline) must clear too
                if seg_over.distance(Point_(strands[k][i])) < w + gap:
                    keep[i] = False
        # split into runs
        runs, cur = [], []
        for i, kp in enumerate(keep):
            if kp:
                cur.append(i)
            elif cur:
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for r in runs:
            if len(r) > 4:
                pth = strands[k][r]
                # pull each cut end back a further w/2 for the square column corner
                from _kingdom import trim_path
                a0 = 0.0 if r[0] == 0 else 0.5
                b0 = 0.0 if r[-1] == len(c) - 1 else 0.5
                out.append((trim_path(pth, a0, b0), k))
    return out


def anvil(x, y):
    """Anvil about 26 mm wide: horn to the left, a waist and a spread foot."""
    face = [(-13.0, 5.0), (8.5, 5.0), (8.5, 1.4), (4.0, 0.0), (3.0, -4.5), (6.5, -7.5),
            (6.5, -9.5), (-6.5, -9.5), (-6.5, -7.5), (-3.0, -4.5), (-4.0, 0.0), (-7.0, 1.6),
            (-10.5, 2.0)]
    return move(poly(face).buffer(0.5).buffer(-0.5), x, y)


def hammer(x, y, ang=-35.0):
    """Hammer head (gold) and haft centreline (wood), the head above the anvil face."""
    head = rounded_rect(11.0, 5.2, 1.0, 0, 0)
    haft = np.array([[0.0, -2.0], [0.0, -15.0]])
    head = move(rotate(head, ang), x, y)
    a = math.radians(ang)
    R_ = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return head, haft @ R_.T + (x, y)


def art():
    d = Design()
    outer = arch(RO)
    inner = arch(RI, BOT + SILL)
    frame = outer - inner
    steps = [rect(72.0, 4.2, 0, BOT - 6.0), rect(66.0, 4.2, 0, BOT - 2.0)]
    av = anvil(0.0, -20.0)
    hd, haft = hammer(4.0, -2.5)
    sparks = [star(4, 2.6, 0.8, x, y, rot=90 + r) for x, y, r in ((-12, -8, 10), (-8.5, -2, -15), (12.5, -7.5, 5))]
    kn = knot()
    rn = runes()

    bands = [band(pth, 1.5 + 0.0, cap="round") for pth, _ in kn]
    bands += [outer.exterior.buffer(OW / 2), inner.exterior.buffer(IW / 2)]
    haft_band = band(haft, 3.0)
    face_cover = union(*bands, av, hd, haft_band, *sparks)
    d.fill(knockout(inner, face_cover), C_["charcoal"], angle=90, name="door face")
    d.fill(knockout(frame, *bands), C_["pewter"], angle=0, name="stone frame")
    d.fill(knockout(steps[1], outer.exterior.buffer(OW / 2)), C_["pewter"], angle=0, name="upper step")
    # silver: knot border, door seam, anvil, frame lines
    for pth, k in kn:
        d.satin(pth, 1.5, C_["silver"], underlay="center", name=f"knot {k}", trim_after=True)
    seam_top = LineString([(0, -9.0), (0, CY + RI - 6.8)]).difference(union(hd.buffer(1.6), haft_band.buffer(1.4)))
    for q in pieces(seam_top, 2.0):
        d.run(q, C_["silver"], bean=1, length=1.6, name="door seam", trim_after=True)
    d.run(np.array([(0, BOT + SILL + 0.9), (0, -30.5)]), C_["silver"], bean=1, length=1.6, name="door seam",
          trim_after=True)
    d.fill(av, C_["silver"], angle=0, name="anvil")
    d.outline(inner, C_["silver"], width=IW, name="frame inner line")
    d.outline(outer, C_["silver"], width=OW, name="frame outer line")
    d.fill(knockout(steps[0], steps[1]), C_["gray"], angle=0, name="lower step")
    d.satin(haft, 3.0, C_["wood"], underlay="center", name="haft")
    d.fill(hd, C_["gold"], angle=55, name="hammer head")
    for sp in sparks:
        d.fill(sp, C_["gold"], angle=45, name="spark")
    for r_ in rn:
        d.run(r_, C_["gold"], bean=1, length=1.8, name="rune", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
