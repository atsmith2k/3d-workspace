"""Two-part SD card box: an open tray with grooves in its long walls and a flat lid
that slides in from one end, with a thumb notch. Both parts print flat.

Spec:
  object:       box for full-size SD cards (32 x 24 x 2.1 mm), about 15 cards
  overall:      70 x 45 x 15 mm tray, wall 2, floor 2; lid 1.5 thick
  mates with:   lid slides in a 1.9 mm groove cut 1 mm into each long wall, 0.2 mm
                clearance per side; a 1.2 mm lip above the groove retains it
  orientation:  tray open side up, lid flat; no overhangs (groove roof is 1 mm wide
                bridging, fine at this span)
  must have:    one end wall cut down to the groove so the lid can enter; thumb notch
  tolerances:   sliding 0.2 mm/side

Units: mm. Z is up, both parts sit on Z=0 in print pose.
"""
from build123d import *

from cadkit.checks import *
from cadkit.recipes import shell_box

DESCRIPTION = "SD card box with a sliding lid (two parts)"

PARAMS = dict(
    length=70.0,
    width=45.0,
    height=15.0,
    wall=2.5,            # groove_depth is cut from this; what remains must stay >= 1.2
    floor=2.0,
    lid_t=1.5,
    groove_depth=1.0,    # into each long wall
    lip=1.6,             # wall left above the groove (it bridges the groove, keep >= 1.2)
    clearance=0.2,
    notch_r=6.0,
    corner=2.0,
)


def _groove(p):
    groove_h = p.lid_t + 2 * p.clearance
    z0 = p.height - p.lip - groove_h
    return groove_h, z0


def checks(p):
    groove_h, z0 = _groove(p)
    lid_len = p.length - p.wall + p.groove_depth - p.clearance
    lid_w = p.width - 2 * p.wall + 2 * p.groove_depth - 2 * p.clearance
    return {
        "tray": [dims(x=p.length, y=p.width, z=p.height), flat_base(p.length * p.width * 0.8),
                 no_overhang(), single_body(),
                 empty((0, 0, p.height / 2)),
                 empty((0, p.width / 2 - p.wall + 0.5, z0 + groove_h / 2)),      # groove is cut
                 solid((0, p.width / 2 - 0.5, p.height - p.lip / 2)),             # lip remains
                 empty((p.length / 2 - 1, 0, p.height - 0.5))],                   # entry end is open
        "lid": [dims(x=lid_len, y=lid_w, z=p.lid_t), flat_base(lid_len * lid_w * 0.7),
                no_overhang(), single_body(),
                empty((lid_len / 2 - 1, 0, p.lid_t / 2))],                       # thumb notch
    }


def assembly(p):
    groove_h, z0 = _groove(p)
    lid_len = p.length - p.wall + p.groove_depth - p.clearance
    # lid centred between the far groove end and the open end
    x_far = -p.length / 2 + p.wall - p.groove_depth + p.clearance
    return {"lid": (x_far + lid_len / 2, 0, z0 + p.clearance, 0, 0, 0)}


def build(p):
    groove_h, z0 = _groove(p)
    tray = shell_box(p.length, p.width, p.height, wall=p.wall, r=p.corner, floor=p.floor)
    # groove along both long walls, into the far wall by groove_depth, out the open end
    gx0 = -p.length / 2 + p.wall - p.groove_depth
    tray -= Box(p.length / 2 + 1 - gx0, p.width - 2 * p.wall + 2 * p.groove_depth, groove_h,
                align=(Align.MIN, Align.CENTER, Align.MIN)).moved(Location((gx0, 0, z0)))
    # open end: remove the lip above the groove so the lid can slide in
    tray -= Box(p.wall + 1, p.width - 2 * p.wall + 2 * p.groove_depth, p.lip + 1,
                align=(Align.MIN, Align.CENTER, Align.MIN)).moved(Location((p.length / 2 - p.wall, 0, z0 + groove_h)))

    lid_len = p.length - p.wall + p.groove_depth - p.clearance
    lid_w = p.width - 2 * p.wall + 2 * p.groove_depth - 2 * p.clearance
    lid = Box(lid_len, lid_w, p.lid_t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lid -= Cylinder(p.notch_r, p.lid_t + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)) \
        .moved(Location((lid_len / 2, 0, -1)))
    return {"tray": tray, "lid": lid}
