"""Round hiking badge: sky, sun, two mountain ranges with snow caps, a banner with
lettering, satin border. Shows the layering approach: every fill is knocked out under
whatever sews on top of it, so the badge stays soft and nothing stacks.

Spec:
  object:       sew-on / iron-on patch, or a direct design on a jacket or backpack
  overall:      90 mm diameter stitched (border included), hoop 4x4 (100 x 100)
  fabric:       twill patch blank or medium woven; tear-away (patch) / cut-away (knit)
  threads:      sky, sun, far range, near range, snow, banner, lettering, border (8 blocks)
  must have:    border satin 3.5 mm; banner text cap height 7 mm (fill); sun 16 mm
  density:      max 3.5 thread layers (knockouts: no stacked fills), <= 20000 stitches
  orientation:  sky rows horizontal, mountains slanted along their slopes
"""
from cadkit.stitch import *

DESCRIPTION = "Round hiking badge: sky, sun, mountains, banner lettering, satin border"
HOOP = "4x4"

PARAMS = dict(
    diameter=90.0,
    label="HIKE",
    text_size=9.0,
    border=3.5,
    sky="#8ecae6", sun="#ffb703", far="#577590", near="#2d6a4f", snow="#ffffff",
    banner="#bc4749", lettering="#ffffff", edge="#1d3557",
)


def checks(p):
    return [
        size(w=p.diameter, h=p.diameter, tol=1.5),
        hoop(),
        colors(8),
        max_density(3.5),
        long_stitches(7.0),
        min_feature(1.0),
        stitches(max=20000),
    ]


def design(p):
    R = p.diameter / 2 - p.border / 2          # border centreline
    disc = circle(0, 0, R + 0.3)                # fills run under the border by 0.3 + half its width

    sun = circle(R * 0.32, R * 0.36, 8.0)
    far = poly([(-R - 2, -6), (-R * 0.55, 12), (-R * 0.25, 4), (R * 0.05, 22),
                (R * 0.5, 2), (R + 2, 10), (R + 2, -14), (-R - 2, -14)]) & disc
    near = poly([(-R - 2, -10), (-R * 0.7, -2), (-R * 0.35, 14), (0, -2), (R * 0.3, 6),
                 (R + 2, -8), (R + 2, -22), (-R - 2, -22)]) & disc
    caps = (poly([(-R * 0.35 - 6.3, 4.5), (-R * 0.35, 14), (-R * 0.35 + 5.3, 6), (-R * 0.35, 8.5)])
            | poly([(R * 0.05 - 5.5, 15), (R * 0.05, 22), (R * 0.05 + 6.2, 14), (R * 0.05, 16.5)]))
    band_y = -R * 0.55
    banner = rect(2 * R + 4, p.text_size + 6, 0, band_y) & disc
    letters = text_shape(p.label, p.text_size)
    letters = move(letters, 0, band_y)

    d = Design()
    d.fill(knockout(disc, sun, far, near, banner), p.sky, angle=0, name="sky")
    d.fill(knockout(sun, far, near), p.sun, angle=60, name="sun")
    d.fill(knockout(far, near, caps, banner), p.far, angle=35, name="far range")
    d.fill(knockout(near, caps, banner), p.near, angle=-30, name="near range")
    d.fill(caps, p.snow, angle=70, spacing=0.45, name="snow caps")
    d.fill(knockout(banner, letters, overlap=0.3), p.banner, angle=0, name="banner")
    d.fill(letters, p.lettering, angle=80, spacing=0.35, underlay=False, name="lettering")
    d.satin(circle_path(0, 0, R), p.border, p.edge, name="border")
    return d
