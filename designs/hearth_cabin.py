"""Winter Cabin: a log cabin with a snowy roof and a lit window between two pines.

Spec:
  object:       cosy cabin scene for sweatshirts, pillows, totes and cabin decor
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      green (pines), ginger (log walls), cocoa (log lines, chimney), red (door),
                gold (window panes, door knob), white (snow roof, drift), silver (1.2 mm
                snow outlines, chimney smoke): 7 colours
  must have:    a 40 mm log cabin with a gable, cocoa bean-run log lines 3.6 mm apart;
                a 5.6 mm thick snow-covered roof; a four-pane gold window; a red door with
                a knob; a chimney with three silver smoke curls; two tiered pines 40 and
                32 mm tall; a snow drift along the bottom with a silver
                satin edge along its crest
  density:      runs lie on the walls only; everything in front knocks out what is behind
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _hearth import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Log cabin with a snowy roof and a glowing window between two pines"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Winter Log Cabin Embroidery Design",
    "A cosy log cabin with a snowy roof, a glowing window and two pines",
    ["log cabin", "winter cabin", "cabin christmas", "snowy cabin", "woodland winter",
     "cozy winter"],
    "A cosy log cabin under a thick snowy roof, its window glowing gold and smoke curling from "
    "the chimney, between two pine trees in the snow.\n\nGreat on sweatshirts, pillows, totes "
    "and cabin decor.",
    mockups=("tshirt", "tote"),
)

BORDER = 1.2


def checks(p):
    return standard_checks(p, 7, 13000, between_mm2=2.0)


def _pine(x, base, h, w):
    tiers = [poly([(x, base + h - k * h * 0.27), (x - w * (0.55 + 0.15 * k), base + h * 0.52 - k * h * 0.27),
                   (x + w * (0.55 + 0.15 * k), base + h * 0.52 - k * h * 0.27)]) for k in range(3)]
    return union(*tiers, rect(4, 6, x, base + 1.5)).buffer(0.6).buffer(-0.6)


def art():
    d = Design()
    # the wall runs down under the drift (which knocks it out), so no sliver of fabric
    # is left between the bottom log and the dip in the drift's crest
    # and fills the sharp wedge under each eave (a 1.2 mm sliver there opens once sewn)
    eaves = [poly([(s * 20, 1.5), (s * 20, -2.5), (s * 22.8, -1.0)]) for s in (-1, 1)]
    wall = union(rect(40, 26, 0, -11), poly([(-20, 1.9), (0, 17), (20, 1.9)]), *eaves)
    roof = LineString([(-26.5, -0.5), (0, 20), (26.5, -0.5)]).buffer(2.8, cap_style="round", join_style="round")
    chimney = rect(5.5, 10, 12, 16)
    panes = [rect(3.8, 3.4, -9 + dx, -5 + dy) for dx in (-2.3, 2.3) for dy in (-2.1, 2.1)]
    door = rounded_rect(9, 13.5, 1.5, 8, -13.25)
    knob = circle(10.5, -13.5, 1.0)
    crest = spline([(-46, -22), (-30, -18), (-12, -21), (8, -19), (28, -21.5), (46, -18.5)], samples=10)
    drift = poly([*crest, (46, -30), (-46, -30)])
    pines = [_pine(-35, -24, 42, 11), _pine(35, -24, 34, 10)]
    logs = []
    holes = union(roof, door, *panes).buffer(0.8)
    for y in np.arange(-17.2, 12, 3.6):
        seg = LineString([(-21, y), (21, y)]).intersection(wall.buffer(-1.2)).difference(holes)
        for g in getattr(seg, "geoms", [seg]):
            if not g.is_empty and g.length > 2.5:
                logs.append(np.array(g.coords))
    smoke = [spline([(12, 22), (14, 26), (11, 30), (13.5, 34)], samples=8),
             spline([(15, 30), (17.5, 33.5), (15, 37), (17, 40)], samples=8)]
    front = union(wall, roof, drift)
    for g in pines:
        d.fill(knockout(g, front), C_["green"], angle=75, name="pine")
    d.fill(knockout(wall, grow(roof, BORDER / 2), door, *panes, drift), C_["ginger"], angle=0, name="log wall")
    for l in logs:
        d.run(l, C_["cocoa"], bean=1, name="log line", trim_after=True)
    d.fill(knockout(chimney, grow(roof, BORDER / 2)), C_["cocoa"], angle=90, name="chimney")
    d.fill(knockout(door, knob, drift), C_["red"], angle=90, name="door")
    for g in panes:
        d.fill(g, C_["gold"], angle=45, underlay=False, name="window pane")
    d.fill(knob, C_["gold"], angle=0, underlay=False, name="knob")
    d.fill(tuck(roof, BORDER), C_["white"], angle=None, name="snow roof")
    d.fill(knockout(drift, LineString(crest).buffer(BORDER / 2 - 0.6)), C_["white"], angle=0, name="snow drift")
    d.outline(roof, C_["silver"], width=BORDER, name="roof edge")
    d.satin(crest, BORDER, C_["silver"], name="drift edge", trim_after=True)
    for s in smoke:
        d.run(s, C_["silver"], bean=1, name="smoke", trim_after=True)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
