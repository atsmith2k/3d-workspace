"""Monogram patch: filled disc, initials as filled lettering, a running-stitch inner
ring and a satin border. The simplest complete design: change `letters` and colours.

Spec:
  object:       round monogram for a towel, tote or cap front
  overall:      `diameter` mm (default 70) stitched, hoop 4x4
  fabric:       towel (add a water-soluble topper), canvas, twill
  threads:      background, inner ring, letters, border (3 blocks: letters and
                border share navy and sew as one block)
  must have:    letters cap height 0.42 x diameter (29 mm at 70); border satin 3 mm;
                inner ring bean stitch 4 mm inside the border
  density:      max 3.5 layers (letters knocked out of the background), <= 15000 stitches
"""
from cadkit.stitch import *

DESCRIPTION = "Round monogram patch: filled disc, initials, inner ring, satin border"
HOOP = "4x4"

PARAMS = dict(
    letters="AS",
    diameter=70.0,
    border=3.0,
    background="cream",
    ring="gold",
    ink="navy",
    edge="navy",
    font="Georgia",
)


def checks(p):
    return [
        size(w=p.diameter, h=p.diameter, tol=1.5),
        hoop(),
        colors(len({p.background, p.ring, p.ink}) + (p.edge != p.ink)),
        max_density(3.5),
        long_stitches(7.0),
        min_feature(1.0),
        coverage(1.0),
        stitches(max=15000),
    ]


def design(p):
    R = p.diameter / 2 - p.border / 2
    disc = circle(0, 0, R + 0.3)
    letters = text_shape(p.letters, p.diameter * 0.42, font=p.font, bold=True)

    d = Design()
    d.fill(knockout(disc, letters), p.background, angle=45, name="background")
    d.run(circle_path(0, 0, R - p.border / 2 - 2.5), p.ring, bean=1, name="inner ring")
    d.fill(letters, p.ink, angle=-45 + 90, name="letters")
    d.satin(circle_path(0, 0, R), p.border, p.edge, name="border")
    return d
