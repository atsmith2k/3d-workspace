"""Drawer pull: a planar U handle whose grip bar swells in the middle (a loft through
five rounded-rectangle sections), with two legs that take M4 machine screws from
behind the drawer front. Prints lying flat on its back.

Spec:
  object:       cabinet / drawer handle, 96 mm hole spacing
  overall:      110 mm long, 34 mm standoff, 10 mm thick
  mates with:   two M4 screws from behind, self-tapping into 3.5 mm pilot holes 12 deep
  orientation:  flat on its side (the whole U on the bed); no overhangs
  must have:    bar 18 mm tall at the middle, 12 at the ends, smooth transition
  tolerances:   pilot holes snug (no allowance)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
from cadkit.checks import *
from cadkit.hardware import self_tap
from cadkit.recipes import u_handle

DESCRIPTION = "Drawer pull with a lofted grip bar and M4 pilot holes (loft recipe demo)"

PARAMS = dict(
    length=110.0,
    bar_h=12.0,
    bar_mid_h=18.0,
    leg_h=28.0,
    leg_w=14.0,
    t=10.0,
    corner=2.0,
    bolt="M4",
    bolt_depth=12.0,
)


def checks(p):
    bar_y = p.leg_h + p.bar_h / 2
    x_leg = p.length / 2 - p.leg_w / 2
    return [
        dims(x=p.length, y=(bar_y + p.bar_mid_h / 2 - 0.3, bar_y + p.bar_mid_h / 2 + 0.3), z=p.t),
        solid((0, bar_y + p.bar_mid_h / 2 - 0.8, p.t / 2)),                  # bar is full height mid-span
        empty((0, bar_y + p.bar_h / 2 + 1.0, p.t / 2)) if p.bar_mid_h < p.bar_h else solid((0, bar_y, p.t / 2)),
        empty((p.length / 2 - 0.5, bar_y + p.bar_h / 2 + 1.0, p.t / 2)),     # ends are only bar_h tall
        empty((0, p.leg_h / 2, p.t / 2)),                                     # open between the legs
        *[hole(self_tap(p.bolt), at=(sx * x_leg, p.t / 2), axis="y", span=(0.3, p.bolt_depth - 0.5)) for sx in (-1, 1)],
        flat_base(p.length * p.bar_h * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    return u_handle(p.length, p.bar_h, p.bar_mid_h, p.leg_h, p.leg_w, p.t, p.corner, p.bolt, p.bolt_depth)
