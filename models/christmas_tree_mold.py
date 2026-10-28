"""One-piece cement mold for a star-section Christmas tree: an eight-pointed star that tapers
from the base to a small flat tip, the modern faceted look.

Cast upside down: the tip sits at the bottom of the mold and the pour face becomes the
tree's flat base. The taper itself is the draft (about 8 deg on the star points), so the
casting lifts straight out. The mold's outer cone keeps a constant wall over the star points,
and a disc at the bottom keeps it stable and stuck to the bed.

Spec:
  object:       mold for a cement / plaster / Jesmonite tabletop Christmas tree
  overall:      tree 60 mm across the star points at the base, 100 mm tall, 6 mm tip;
                mold ~66 x 66 x 103 mm (fits the A1 mini)
  mates with:   nothing
  orientation:  opening up, tip down, base disc on the bed, no supports
  must have:    8-point star section, inner/outer radius 0.72, linear taper (smooth sides),
                floor 3 under the tip, wall 3 over the star points
  tolerances:   none (casting)

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from manifold3d import Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Faceted star-section Christmas tree cement mold, 100 mm tall"

PRODUCT = dict(
    title="Christmas Tree Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "plaster", "jesmonite", "christmas", "christmas tree",
          "holiday decor", "modern"],
    printers=["a1", "a1mini"],
    cast_material="cement, plaster or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    height=100.0,
    base_d=60.0,        # across the star points at the base
    tip_d=6.0,          # across the star points at the tip
    points=8,
    inner=0.72,         # valley radius / point radius
    floor=3.0,
    wall=3.0,
    foot_d=50.0,        # stabilising disc at the bottom of the mold
    foot_h=3.0,
)

EMBED = 0.1


def star(p, r):
    n = p.points
    pts = []
    for i in range(2 * n):
        rr = r if i % 2 == 0 else r * p.inner
        a = math.pi * i / n + math.pi / 2
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return poly(pts)


def checks(p):
    R = p.base_d / 2
    top = p.floor + p.height
    return [
        dims(z=top, x=(p.base_d + 2 * p.wall - 2, p.base_d + 2 * p.wall + 2)),
        fits_bed(),
        empty((0, 0, p.floor + 1), (0, 0, p.floor + p.height / 2), (0, R * 0.9, top - 2)),     # tip, middle, a star point at the base
        solid((0, 0, p.floor / 2), (0, R + p.wall / 2, top - 2)),
        thickness_at((0, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(math.pi * (p.foot_d / 2) ** 2 * 0.8),
        no_overhang(),
        single_body(),
    ]


def build(p):
    R, r = p.base_d / 2, p.tip_d / 2
    h = p.height
    top = p.floor + h
    # cavity: the star at tip size, scaled up linearly to the base size (smooth sides)
    cavity = Manifold.extrude(star(p, r), h + 1, scale_top=((R + (R - r) / h) / r,) * 2)
    cavity = cavity.translate((0, 0, p.floor))
    # outer cone: radius grows at the same rate as the star points, so the wall stays even
    a = r + p.wall - p.floor * (R - r) / h
    outer = Manifold.extrude(circle(0, 0, a), top, scale_top=((R + p.wall) / a,) * 2)
    foot = extrude(circle(0, 0, p.foot_d / 2), p.foot_h)
    return outer + foot - cavity
