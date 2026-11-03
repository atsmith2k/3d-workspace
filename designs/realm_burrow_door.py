"""Hillside Burrow Door: a round green door set into a grassy mound, storybook style.

Spec:
  object:       cozy-fantasy burrow home (original art, no franchise) for tees, totes,
                pillows, tea towels and framed hoops
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7), about
                0.8 as tall as wide
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      moss (hill), leaf (front lawn, grass tufts), green (door), wood (door
                frame, window frame, path stones), yellow (lit window, lantern glass),
                red (flowers), gold (door knob, flower centres), bark (plank lines,
                frame joints, window bars, lantern post and cap): 8 colours
  must have:    a 96 mm grassy mound; a 38 mm round green door with a 5 mm timber
                frame cut by the ground line, plank lines as bean runs, a 5.6 mm brass
                knob in the centre; a 16 mm round lit window with a cross of bars to
                the left; a little lantern on a post to the right; four stepping
                stones down the lawn; red flowers; grass tufts along the mound
  density:      every layer knocked out under the ones in front; max 3.5 layers
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon, box

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Round green burrow door in a grassy hillside, with a lit window and lantern"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Hillside Burrow Door Embroidery Design",
    "A round green storybook door set into a grassy hill, with a glowing window and lantern",
    ["burrow door", "round door", "cozy fantasy", "fantasy door", "storybook",
     "cottagecore", "hillside home", "fantasy cottage"],
    "A cozy storybook burrow: a round green door with a brass knob and a timber frame, dug "
    "into a grassy hillside, with a warm lit window, a little lantern on its post, stepping "
    "stones across the lawn and red flowers by the door.\n\n"
    "Great on tees, totes, pillows, tea towels and framed hoops for every homebody adventurer.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 24000)


GROUND = -26.0            # where the lawn meets the hill
DX, DY, DR = 4.0, -6.0, 19.0     # door centre and radius
FR = 5.0                  # frame width
WX, WY, WR = -29.0, -4.0, 6.5    # window
LX = 33.0                 # lantern post x


def hill():
    t = np.linspace(0, math.pi, 120)
    x = 48 * np.cos(t)
    y = GROUND - 4 + 58 * np.sin(t) ** 0.8 + 1.2 * np.sin(5 * t)
    return Polygon(np.vstack([np.c_[x, y], [(-48, GROUND - 4)]])).buffer(0)


def lawn():
    x = np.linspace(-48, 48, 60)
    top = GROUND + 1.0 * np.sin(x / 7.0)
    return Polygon(np.vstack([np.c_[x, top], [(48, -40), (-48, -40)]]))


def flower(x, y, r=1.45):
    petals = union(*[circle(x + 1.25 * r * math.cos(math.radians(90 + 72 * i)),
                            y + 1.25 * r * math.sin(math.radians(90 + 72 * i)), r, res=32) for i in range(5)])
    return petals, circle(x, y, 1.1, res=32)


def art():
    d = Design()
    ground_cut = box(-60, GROUND - 1.0, 60, 60)      # door and frame stop just under the ground line
    door = circle(DX, DY, DR).intersection(ground_cut)
    frame = ring(DX, DY, DR + FR, DR - 0.4).intersection(box(-60, GROUND - 1.5, 60, 60))
    knob = circle(DX + 0.0, DY, 2.8)
    window = circle(WX, WY, WR)
    wframe = ring(WX, WY, WR + 2.6, WR - 0.4)
    stones = [rotate(ellipse(x, y, rx, ry), a, origin=(x, y)) for x, y, rx, ry, a in
              ((DX + 1, -29.5, 5.5, 1.9, 0), (DX - 4, -33.5, 5.8, 2.0, 6), (DX + 3, -37.6, 6.0, 2.1, -4))]
    post = line((LX, GROUND + 0.5), (LX, -4.0))
    lglass = rect(4.6, 6.0, LX, -0.4)
    lcap = Polygon([(LX - 4.0, 2.4), (LX + 4.0, 2.4), (LX, 6.4)])
    lbase = rect(6.4, 1.6, LX, -4.2)
    lantern = union(lglass.buffer(1.0, join_style="mitre"), lcap, lbase)
    flowers = [flower(x, y) for x, y in ((-40, -31), (-34, -34.5), (-21, -31), (-13, -35.5),
                                         (21, -31.5), (40, -33), (28, -36))]
    petals = [f[0] for f in flowers]
    centres = [f[1] for f in flowers]
    tuft_feet = [(-39, 6), (-22, 22), (-6, 28.5), (18, 26), (34, 13), (-19, GROUND + 2.6),
                 (26.5, GROUND + 2.6), (-41, GROUND + 3.0), (42, GROUND + 3.0)]

    H, L = hill(), lawn()
    front = union(door, frame, window, wframe, lantern)
    d.fill(knockout(H, L, front), C_["moss"], angle=20, name="hill")
    d.fill(knockout(L.intersection(box(-48, -40, 48, 10)), *stones, *petals), C_["leaf"], angle=-10, name="lawn")
    for fx, fy in tuft_feet:
        for k, (lean, hh) in enumerate(((-0.45, 4.2), (0.05, 5.4), (0.5, 4.0))):
            path, w = M.blade((fx + (k - 1) * 1.4, fy - 0.5), hh, lean=lean, width=2.3)
            d.satin(path, w, C_["leaf"], taper=True, underlay="none", name="grass tuft")
    d.fill(knockout(door, knob), C_["green"], angle=90, name="door")
    d.fill(frame, C_["wood"], angle=0, name="door frame")
    d.fill(wframe, C_["wood"], angle=45, name="window frame")
    for s in stones:
        d.fill(s, C_["wood"], angle=80, name="stepping stone")
    d.fill(window, C_["yellow"], angle=0, name="window glow")
    d.fill(lglass, C_["yellow"], angle=90, underlay=False, name="lantern glass")
    for pt, c in zip(petals, centres):
        d.fill(knockout(pt, c), C_["red"], angle=60, underlay=False, name="flower")
    d.fill(knob, C_["gold"], angle=30, name="knob")
    for c in centres:
        d.fill(c, C_["gold"], angle=0, underlay=False, name="flower centre")
    # bark: plank seams, frame joints, window bars, lantern
    inner = door.buffer(-1.2)
    for x in (DX - 12, DX - 6, DX + 6, DX + 12):
        seam = LineString([(x, GROUND), (x, DY + DR)]).intersection(inner)
        for part in getattr(seam, "geoms", [seam]):
            if part.length > 2:
                d.run(np.asarray(part.coords), C_["bark"], length=1.8, bean=1, name="plank seam", trim_after=True)
    for a in (20, 55, 90, 125, 160):
        r = math.radians(a)
        u = np.array([math.cos(r), math.sin(r)])
        c = np.array([DX, DY])
        d.run(np.array([c + u * (DR + 0.6), c + u * (DR + FR - 0.8)]), C_["bark"], length=1.5, bean=1,
              name="frame joint", trim_after=True)
    d.satin(line((WX - WR + 0.6, WY), (WX + WR - 0.6, WY)), 1.2, C_["bark"], underlay="center", name="window bar")
    d.satin(line((WX, WY - WR + 0.6), (WX, WY - 0.9)), 1.2, C_["bark"], underlay="center", name="window bar")
    d.satin(line((WX, WY + 0.9), (WX, WY + WR - 0.6)), 1.2, C_["bark"], underlay="center", name="window bar")
    d.satin(post, 1.8, C_["bark"], underlay="center", name="lantern post")
    d.fill(lbase, C_["bark"], angle=0, underlay=False, name="lantern base")
    d.outline(lglass, C_["bark"], width=1.4, name="lantern frame")
    d.fill(lcap, C_["bark"], angle=0, underlay=False, name="lantern cap")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
