"""Ring in Shadow: a plain gold ring hanging on a silver chain, glowing in the dark, on an
oval night-blue patch.

Spec:
  object:       a plain enchanted gold ring, no inscription and no eye (an original
                piece) hanging from a fine chain, for tees, hoodies, totes and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens, canvas and patches with tear-away
  threads:      navy (night field), brass (light rays, inside of the band), gold (ring),
                yellow (highlight), white (glint), silver (chain, border): 6 colours
  must have:    a 72 x 92 mm oval patch with a 2.6 mm silver satin border; a navy field;
                a 36 mm gold ring seen a little from above, the inside of the band in
                brass, a yellow tapered highlight along its upper left and a white
                four-point glint; sixteen tapered brass satin rays of light round it,
                long and short, starting 2.6 mm off the band; two silver chains rising in a
                V from the ring to the border, alternating open oval links (two 1.4 mm
                satin arcs each) and side-on links (1.8 mm satins)
  density:      the field is knocked out under the rays, ring and chain; link
                arcs stop 0.8 mm clear of the side-on links; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _kingdom import C_, SIZES, fit, hoop_for, pieces, product, standard_checks, trim_path, widths_along

DESCRIPTION = "Plain gold ring on a silver chain glowing in the dark, on an oval night-blue patch"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Ring in Shadow Embroidery Design",
    "A plain gold ring hanging on a fine silver chain, glowing out of the darkness",
    ["gold ring", "magic ring", "enchanted ring", "ring on a chain", "dark fantasy",
     "fantasy jewelry", "quest", "night sky"],
    "One small ring, and all the darkness around it: a plain gold band hanging from a fine "
    "silver chain, glowing out of a midnight-blue oval field with rays of light, framed in "
    "silver.\n\n"
    "Great on hoodies, tees, tote bags, jackets and fantasy patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 20000)


RX, RY = 36.0, 46.0          # oval patch half axes
BW = 2.6
CX, CY = 0.0, -12.0          # ring centre
ORX, ORY = 18.0, 15.0        # ring outer (seen well from above: round, not almond)
IRX, IRY = 15.0, 11.6         # ring inner (the hole), lifted: the near side of the band is deeper
LIFT = 1.4


def ring():
    outer = ellipse(CX, CY, ORX, ORY, res=160)
    hole = ellipse(CX, CY + LIFT, IRX, IRY, res=160)
    band = outer - hole
    # inside of the band: the far half of the hole's rim, seen past the near edge
    inside = (hole - ellipse(CX, CY + LIFT - 2.8, IRX, IRY, res=160)) & rect(60, 30, CX, CY + LIFT + 15)
    return band, inside, hole


def highlight():
    a = np.radians(np.linspace(118, 168, 24))
    rx, ry = ORX - 1.3, ORY - 1.2
    return np.c_[CX + rx * np.cos(a), CY + ry * np.sin(a)]


def chain_links(side, n=4):
    """Links along a line from the ring's top up to the border, side = -1 left, +1 right."""
    start = np.array([CX + side * 5.0, CY + ORY - 4.6])     # the first link hooks over the band
    ang = math.radians(90 - side * 22)
    u = np.array([math.cos(ang), math.sin(ang)])
    nrm = np.array([-u[1], u[0]])
    ovals, bars = [], []
    pitch = 9.0
    for k in range(n + 2):
        c = start + u * (pitch * k + 4.5)
        if k % 2 == 0:
            ovals.append((c, u, nrm))
        else:
            bars.append(np.array([c - u * 5.6, c + u * 5.6]))
    return ovals, bars


def oval_arcs(c, u, nrm, a=5.6, b=3.0):
    """An open link face on: an ellipse along u, as two side arcs (ends broken where the
    side-on links pass through)."""
    t = np.radians(np.linspace(0, 360, 145))
    pts = c + np.outer(a * np.cos(t), u) + np.outer(b * np.sin(t), nrm)
    return pts


def art():
    d = Design()
    patch = ellipse(0, 0, RX, RY, res=256)
    inner = tuck(patch, BW)
    band, inside, hole = ring()
    ring_all = band
    outer_e = ellipse(CX, CY, ORX, ORY, res=160)
    halo_in = ellipse(CX, CY, ORX + 3.0, ORY + 3.0, res=160)
    halo_out = ellipse(CX, CY, ORX + 7.5, ORY + 7.0, res=160)
    # chains
    chains = [chain_links(s) for s in (-1, 1)]
    bar_paths = []
    arcs = []
    clip = inner.buffer(-1.0)
    for ovals, bars in chains:
        for b in bars:
            q = LineString(b).intersection(clip)
            bar_paths += pieces(q, 2.0)
        for c, u, nrm in ovals:
            arcs.append(oval_arcs(c, u, nrm))
    bar_band = union(*[LineString(b).buffer(0.9 + 0.8, cap_style="flat") for b in bar_paths])
    arc_paths = []
    for pts in arcs:
        ls = LineString(pts).difference(bar_band).difference(ellipse(CX, CY, ORX + 1.0, ORY + 1.0)).intersection(clip)
        arc_paths += pieces(ls, 1.5)
    chain_area = union(*[LineString(p).buffer(0.7) for p in arc_paths],
                       *[LineString(b).buffer(0.9, cap_style="flat") for b in bar_paths])

    rays = []
    for i in range(16):
        a = math.radians(90 + i * 22.5 + 11.25)
        long_ = i % 2 == 0
        r0, r1 = 1.0, (1.62 if long_ else 1.40)
        u = np.array([math.cos(a), math.sin(a)])
        # along the halo's own ellipse: start just inside its edge
        e0 = np.array([CX, CY]) + u * np.array([ORX + 2.6, ORY + 2.6])
        e1 = np.array([CX, CY]) + u * np.array([(ORX + 2.6) * r1 * 1.12, (ORY + 2.6) * r1 * 1.12])
        pth = np.array([e0 + (e1 - e0) * k / 12 for k in range(13)])
        keep = LineString(pth).difference(chain_area.buffer(1.4)).intersection(inner.buffer(-1.8))
        for q in pieces(keep, 3.0):
            if np.linalg.norm(q[0] - e0) < 0.3:
                rays.append(q)
    ray_w = [widths_along(q, 1.8, 1.2, 0.5) for q in rays]
    from _kingdom import tube
    ray_area = union(*[tube(q, w) for q, w in zip(rays, ray_w)])
    ray_cut = union(*[tube(trim_path(q, 1.2, 0.0), w[1:]) for q, w in zip(rays, ray_w)])
    d.fill(knockout(inner, ring_all, chain_area, ray_cut), C_["navy"], angle=15, name="night")
    for q, w in zip(rays, ray_w):
        d.satin(q, w, C_["brass"], taper=True, underlay="center", name="ray", trim_after=True)
    d.fill(knockout(inside, chain_area.buffer(0.3)), C_["brass"], angle=0, name="inside of band")
    glint = star(4, 3.4, 0.9, CX - 14.5, CY + 9.5, rot=90)
    hl = highlight()
    hl_w = widths_along(hl, 0.8, 1.5, 0.8)
    from _kingdom import tube as _tube
    d.fill(knockout(band, inside, chain_area.buffer(0.3), _tube(hl, hl_w).buffer(0.2), glint), C_["gold"], angle=70, name="ring")
    d.satin(hl, hl_w, C_["yellow"], taper=True, underlay="center", name="highlight")
    d.fill(glint, C_["white"], angle=45, name="glint")
    for pth in arc_paths:
        d.satin(pth, 1.4, C_["silver"], underlay="center", name="link", trim_after=True)
    for b in bar_paths:
        d.satin(b, 1.8, C_["silver"], underlay="center", name="link", trim_after=True)
    d.outline(patch, C_["silver"], width=BW, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
