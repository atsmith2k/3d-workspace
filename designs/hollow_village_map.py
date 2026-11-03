"""Hillside Village: a storybook map vignette in a vintage oval frame: rolling hills with
round doors and windows, a winding lane over a stone bridge, a river, round trees, a
great tree with lanterns on the hilltop, a compass star and birds in the sky.

Spec:
  object:       an original hillside village (no named place) drawn like an old map
                vignette, for tees, totes, cushions, framed hoops and journal covers
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      moss (far hills), leaf green (hills), dark olive (near hills), emerald (trees), sky blue
                (river), gray (bridge), khaki (lane), red, harvest gold (round doors,
                windows), deep gold (lanterns, compass points, inner ring), dark brown
                (trunks, door frames, compass, birds, frame): 11 colours
  must have:    a 92 x 80 mm oval with a 2.8 mm dark satin frame and a 1.2 mm
                gold satin ring just inside it; three bands of hills; four round doors 6.4-7.2 mm
                across, 1.4 mm frames, with round windows set into the hills; a 2.6 mm lane winding
                from the foreground up to the hilltop, crossing a 4.5 mm river on an
                arched bridge; five round trees; a 22 mm great tree with gold lanterns;
                a 12 mm compass star; two birds
  density:      hills knocked out under everything on them; frame sews last; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _hollow import C_, SIZES, backfill, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Storybook map of a hillside village with round doors, in a vintage oval frame"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Hillside Village Map Vignette Embroidery Design",
    "A storybook hillside village of round doors, a winding lane, a stone bridge and a lantern tree, in an oval frame",
    ["hillside village", "round door", "storybook map", "fantasy map", "village map", "vintage frame",
     "oval vignette", "countryside", "rolling hills", "journal cover", "framed hoop"],
    "Somewhere over the next hill: a little village of round doors and round windows tucked into "
    "rolling green hills, a lane winding up over an arched stone bridge, round trees, and the great "
    "lantern tree on the hilltop where every party is held, drawn like an old storybook map inside "
    "a vintage oval frame with a compass star.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on tees, totes, cushions, "
    "journal covers and framed hoops.",
    mockups=("tshirt", "tote"),
)

RX, RY = 46.0, 40.0
FRAME_W = 2.8


def checks(p):
    return standard_checks(p, 11, 20000)


def _band(top_pts, bottom=-50):
    xs = [x for x, _ in top_pts]
    return smooth(list(top_pts) + [(xs[-1], bottom), (xs[0], bottom)], samples=8)


def art():
    d = Design()
    oval = ellipse(0, 0, RX, RY, res=256)
    inner = tuck(oval, FRAME_W + 2.2)        # under the gold ring too
    clip = lambda g: g & inner

    far = clip(_band([(-50, 4), (-34, 14), (-16, 10), (2, 22), (20, 12), (34, 16), (50, 6)]))
    mid = clip(_band([(-50, -6), (-32, 2), (-14, -2), (6, 4), (26, -4), (40, -1), (50, -8)]))
    near = clip(_band([(-50, -20), (-30, -14), (-8, -22), (14, -18), (34, -26), (50, -22)]))

    river = clip(strip(np.asarray(spline([(-50, -9), (-30, -12), (-12, -17), (4, -21), (18, -29), (30, -44)], samples=10)), 4.5))
    lane_path = np.asarray(spline([(-18, -46), (-10, -32), (-2, -24), (6, -14), (2, -4), (8, 6), (4, 14), (2, 21)], samples=10))
    lane = clip(strip(lane_path, np.linspace(3.2, 1.6, len(lane_path))))
    # the bridge where the lane meets the river
    bx, by = -1.2, -19.2
    bridge = rotate(union(rect(9.0, 3.2, bx, by + 1.0), ellipse(bx, by + 1.0, 4.5, 2.6)).difference(ellipse(bx, by - 0.9, 2.6, 1.8)),
                    -28, origin=(bx, by))
    # round doors in the hills: (x, y, r, colour)
    doors = [(-30, -1.5, 3.6, "red"), (-15, -8.5, 3.4, "yellow"), (22, -10.0, 3.6, "red"), (29, 8.0, 3.2, "yellow")]
    door_g = [(circle(x, y, r), None, circle(x + r + 3.4, y + 0.8, 1.8), c)
              for x, y, r, c in doors]
    # trees: canopies and trunks
    trees = [(-38, 8, 4.2), (-24, 6, 3.6), (16, 2, 3.8), (38, 2, 3.4), (-36, -18, 3.6)]
    canopies = [circle(x, y + r * 0.9, r) for x, y, r in trees]
    trunks = [rect(1.4, r * 0.9 + 0.6, x, y + r * 0.45 - 0.3) for x, y, r in trees]
    # the great lantern tree on the hilltop
    gx, gy = 2.0, 13.5
    crown = union(circle(gx - 6, gy + 9, 6.0), circle(gx + 5.5, gy + 9.5, 6.4), circle(gx, gy + 14.5, 6.6),
                  circle(gx - 9.5, gy + 4.5, 4.0), circle(gx + 9.5, gy + 5.0, 4.0))
    trunk = union(poly([(gx - 2.0, gy - 0.6), (gx - 1.2, gy + 6), (gx + 1.2, gy + 6), (gx + 2.0, gy - 0.6)]),
                  strip(np.array([(gx, gy + 4), (gx - 4.5, gy + 7.5)]), 1.4),
                  strip(np.array([(gx, gy + 4.5), (gx + 4.8, gy + 8)]), 1.4))
    lanterns = [circle(gx + dx, gy + dy, 1.0) for dx, dy in ((-7, 6), (-2.5, 10), (3, 13.5), (7.5, 7.5), (-6, 13), (2, 6.5))]
    trunk = trunk.difference(crown.buffer(-0.0)).union(trunk & crown.buffer(-3.5))
    # compass star and birds
    cx, cy = 30.0, 26.0
    cx, cy = -25.0, 22.0
    comp = star(4, 6.2, 2.6, cx, cy, rot=90)
    comp_small = circle(cx, cy, 2.3)
    birds = [[(18 + dx, 22 + dy), (20 + dx, 23.4 + dy), (21.4 + dx, 22.2 + dy), (22.8 + dx, 23.4 + dy), (25 + dx, 22 + dy)]
             for dx, dy in ((0, 0), (8, 3.5))]

    things = union(comp, river, lane, bridge, *[union(grow(a, 0.7), c_) for a, b, c_, _ in door_g], *canopies, *trunks, crown, trunk)
    # 1-3 hills
    d.fill(knockout(far, mid, things), C_["moss"], angle=10, name="far hills")
    d.fill(knockout(mid, near, things), C_["leaf"], angle=-15, name="hills")
    d.fill(knockout(near, things), C_["olive"], angle=20, name="near hills")
    # river, bridge, lane
    d.fill(knockout(river, bridge, lane), C_["sky"], angle=-30, name="river")
    d.fill(bridge, C_["gray"], angle=0, name="bridge")
    d.fill(knockout(lane, bridge), C_["khaki"], angle=60, name="lane")
    # trees and the great tree
    for g in canopies:
        d.fill(g, C_["green"], angle=45, name="tree")
    d.fill(knockout(crown, *lanterns), C_["green"], angle=45, name="great tree")
    # doors and windows
    for col in ("red", "yellow"):
        for door, frame, win, c in door_g:
            if c == col:
                d.fill(door, C_[col], angle=90, name="round door")
    for door, frame, win, c in door_g:
        d.fill(win, C_["yellow"], angle=0, name="round window")
    d.fill(knockout(comp, comp_small), C_["gold"], angle=90, name="compass")
    for g in lanterns:
        d.fill(g, C_["gold"], angle=0, name="lantern")
    d.outline(shrink(oval, FRAME_W / 2 + 0.55), C_["gold"], width=1.2, name="gold frame")
    # dark brown: trunks, door frames, compass, birds, frame
    for g in trunks:
        d.fill(g, C_["bark"], angle=90, name="trunk")
    d.fill(knockout(trunk, *lanterns), C_["bark"], angle=90, name="great trunk")
    for door, frame, win, c in door_g:
        d.outline(door, C_["bark"], width=1.4, name="door frame")
    d.fill(comp_small, C_["bark"], angle=0, name="compass")
    for b in birds:
        d.run(b, C_["bark"], bean=1, name="bird")
    d.outline(oval, C_["bark"], width=FRAME_W, name="frame")
    backfill(d, C_["bark"])
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
