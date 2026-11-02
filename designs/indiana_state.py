"""State of Indiana silhouette with "Indiana" in a script font across it.

Spec:
  object:       state-shape design for a tote, jacket back, pillow or framed piece
  overall:      state `height` mm tall (default 160) plus the border (~163 sewn), width
                follows the state (~104 mm), hoop 5x7
  source:       boundary from the PublicaMundi us-states GeoJSON (derived from US Census
                cartographic boundaries, public domain), 46 points, projected
                equirectangular at 39.77 N (cos-latitude scaled longitude)
  fabric:       medium woven (canvas, twill, denim) with tear-away; knits want cut-away
  threads:      1 state fill (navy), 2 halo (white), 3 border + lettering (gold): 3 blocks
  must have:    state fill, row angle 45; gold satin border 2.5 mm, one continuous ring
                (no breaks: `coverage` fails on any bare patch over 1 mm2); lettering "Indiana"
                in Segoe Script Bold, `text_width` mm wide (default 70: the state is ~84 mm
                wide at mid-height, less border and halo), tilted `tilt` deg, centred on
                the state's own width at `text_y` (it sits right of the bounding-box
                centre there), with a 1.2 mm white halo
  density:      lettering and halo knocked out of the state fill (no stacked fills), the
                fill pulled back under the border to 0.6 mm overlap,
                max 3.5 thread layers, <= 40000 stitches
"""
from pathlib import Path

import numpy as np

from cadkit.stitch import *

DESCRIPTION = "Indiana state silhouette with 'Indiana' in script lettering"
HOOP = "5x7"

PARAMS = dict(
    height=160.0,
    label="Indiana",
    text_width=70.0,
    tilt=8.0,
    text_y=0.0,                 # lettering centre, mm above the state's centre
    border=2.5,
    halo=1.2,
    state="#13294b",
    halo_color="#ffffff",
    gold="#f2b705",
    font="Segoe Script",
    font_file="segoescb.ttf",   # Segoe Script Bold (Windows); "" to use `font` by name
)

# (lon, lat) clockwise from the north-west corner of the Lake Michigan shore
INDIANA = [
    (-85.9901, 41.7597), (-84.8070, 41.7597), (-84.8070, 41.6940), (-84.8016, 40.5000),
    (-84.8180, 39.1034), (-84.8947, 39.0596), (-84.8125, 38.7857), (-84.9878, 38.7803),
    (-85.1740, 38.6872), (-85.4314, 38.7310), (-85.4205, 38.5338), (-85.5902, 38.4517),
    (-85.6560, 38.3257), (-85.8312, 38.2764), (-85.9243, 38.0245), (-86.0394, 37.9587),
    (-86.2639, 38.0518), (-86.3022, 38.1669), (-86.5213, 38.0409), (-86.5049, 37.9313),
    (-86.7294, 37.8930), (-86.7952, 37.9916), (-87.0471, 37.8930), (-87.1293, 37.7889),
    (-87.3812, 37.9368), (-87.5127, 37.9040), (-87.6003, 37.9752), (-87.6824, 37.9040),
    (-87.9344, 37.8930), (-88.0275, 37.7999), (-88.0603, 37.8656), (-88.0001, 38.1011),
    (-87.9234, 38.1504), (-87.9508, 38.2764), (-87.8358, 38.2928), (-87.6551, 38.5064),
    (-87.6222, 38.6379), (-87.4962, 38.7803), (-87.5127, 38.9555), (-87.6386, 39.1691),
    (-87.5291, 39.3499), (-87.5236, 41.7104), (-87.4250, 41.6447), (-87.1183, 41.6447),
    (-86.8226, 41.7597),
]


def state_shape(height):
    ll = np.array(INDIANA)
    lat0 = (ll[:, 1].min() + ll[:, 1].max()) / 2
    xy = np.c_[ll[:, 0] * np.cos(np.radians(lat0)), ll[:, 1]]
    xy *= height / np.ptp(xy[:, 1])
    return centered(poly(xy))


def band_center(shape, y):
    """x midway across the shape at height y."""
    x0, _, x1, _ = shape.bounds
    cut = shape.intersection(rect(x1 - x0 + 10, 0.01, (x0 + x1) / 2, y))
    bx0, _, bx1, _ = cut.bounds
    return (bx0 + bx1) / 2


def lettering(p):
    fp = Path("C:/Windows/Fonts") / p.font_file if p.font_file else None
    fp = str(fp) if fp and fp.exists() else None
    t = text_shape(p.label, 20.0, font=p.font, bold=True, font_path=fp)
    x0, _, x1, _ = t.bounds
    t = scale(t, p.text_width / (x1 - x0))
    return move(rotate(centered(t), p.tilt), band_center(state_shape(p.height), p.text_y), p.text_y)


def checks(p):
    return [
        size(h=p.height + p.border, w=(95, 110), tol=1.5),   # border centred on the edge
        hoop(),
        colors(3),
        max_density(3.5),
        long_stitches(7.0),
        min_feature(1.0),
        coverage(1.0),
        stitches(max=40000),
        custom("lettering inside the border", lambda c: _inside(c.design, p)),
    ]


def _inside(d, p):
    st = next(e.geom for e in d.elements if e.name == "state")
    txt = next(e.geom for e in d.elements if e.name == "lettering")
    clear = state_shape(p.height).buffer(-p.border / 2 - 1.0)
    out = txt.buffer(p.halo).difference(clear).area
    return out < 0.5, f"{out:.1f} mm2 of lettering+halo outside the border"


def design(p):
    st = state_shape(p.height)
    txt = lettering(p)
    halo = knockout(txt.buffer(p.halo, quad_segs=12), txt, overlap=0.3)

    d = Design()
    d.fill(knockout(tuck(st, p.border), txt.buffer(p.halo)), p.state, angle=45, name="state")
    d.fill(halo, p.halo_color, angle=-20, spacing=0.4, underlay=False, name="halo")
    d.outline(st, p.gold, width=p.border, name="border")
    d.fill(txt, p.gold, angle=75, spacing=0.35, name="lettering")
    return d
