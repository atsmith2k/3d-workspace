"""Two-part cement mold for a small planter with a drainage hole: an outer cup and a core.

The planter is cast right side up. The outer cup forms the outside (widening upward, 2 deg)
and a pin on its floor forms the drainage hole. The core forms the inside: it hangs from a
flange that rests on the cup's rim, and a skirt around the flange slides over the outside
of the cup to centre it, so the wall comes out even. Four vents in the flange let air and
excess cement out as the core is pressed down. Weigh the core down while the cement cures.

Spec:
  object:       two-part mold for an 80 mm cement / Jesmonite planter with a drain hole
  overall:      planter 80 mm across the top, 75 mm tall, wall 8, floor 10, drain 10 mm;
                mold cup ~86 x 86 x 78 mm; core ~92 x 92 x 68 mm (both fit the A1 mini)
  mates with:   core skirt over the cup: cup outer 86 mm, skirt bore 86.6 (0.3 per side);
                core sits 0.3 mm above the drain pin so the pin never props it up
  orientation:  cup opening up on its floor; core flange down on the bed, frustum up;
                no supports for either
  must have:    fluted (24 flutes) or round outside; drain pin 10 mm, 4 vents 5 mm in the flange, core draft 3 deg,
                cup draft 2 deg, mold floor 3, cup wall 3
  tolerances:   sliding 0.3 mm/side on the skirt

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
import math

from manifold3d import Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Two-part fluted planter mold with a drainage hole, for cement or Jesmonite"

PRODUCT = dict(
    title="Fluted Planter Mold",
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "planter", "plant pot", "succulent",
          "drainage", "fluted", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="cement, concrete or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    shape="fluted",     # fluted | round (the planter's outside)
    flutes=24,
    top_d=80.0,         # planter diameter at the rim
    height=75.0,
    pot_wall=8.0,       # planter wall at the rim
    pot_floor=10.0,
    drain_d=10.0,
    floor=3.0,          # mold cup floor
    wall=3.0,           # mold cup wall at the rim
    body_draft=2.0,
    core_draft=3.0,
    flange_t=3.0,
    skirt_h=8.0,
    skirt_t=2.4,
    clearance=0.3,
    vent_d=5.0,
    pin_gap=0.3,        # core clears the drain pin by this much
)

EMBED = 0.1


def _sizes(p):
    R = p.top_d / 2
    cup_r = R + p.wall                      # cup outside (straight)
    core_r = R - p.pot_wall                 # core at the rim
    depth = p.height - p.pot_floor          # how far the core reaches down
    return R, cup_r, core_r, depth


def body_section(p, r):
    if p.shape == "round":
        return circle(0, 0, r)
    n = p.flutes
    fr = r * math.sin(math.pi / n) * 1.05
    cs = circle(0, 0, r - fr)
    for i in range(n):
        a = 2 * math.pi * i / n
        cs += circle((r - fr) * math.cos(a), (r - fr) * math.sin(a), fr)
    return grow(grow(cs, 1.0), -1.0)


def assembly(p):
    """The core flips over and rests its flange on the cup rim."""
    return {"core": (0, 0, p.floor + p.height + p.flange_t, 180, 0, 0)}


def checks(p):
    R, cup_r, core_r, depth = _sizes(p)
    top = p.floor + p.height
    vent_r = (core_r + R) / 2
    return {
        "cup": [
            dims(x=2 * cup_r, y=2 * cup_r, z=top),
            solid((0, 0, p.floor + 1), (0, 0, p.floor + p.pot_floor - 1)),       # drain pin
            empty((R - p.pot_wall / 2, 0, p.floor + 2), (0, 0, p.floor + p.pot_floor + 1)),
            thickness_at((R - p.pot_wall / 2, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
            flat_base(math.pi * cup_r ** 2 * 0.9),
            no_overhang(),
            single_body(),
        ],
        "core": [
            dims(x=2 * (cup_r + p.clearance + p.skirt_t), z=p.flange_t + depth),
            solid((0, 0, p.flange_t + depth / 2), (cup_r + p.clearance + p.skirt_t / 2, 0, p.flange_t + p.skirt_h / 2)),
            empty((vent_r, 0, p.flange_t / 2), (0, vent_r, p.flange_t / 2)),    # vents go through
            flat_base(math.pi * (cup_r + p.clearance + p.skirt_t) ** 2 * 0.6),
            no_overhang(),
            single_body(),
        ],
    }


def build(p):
    R, cup_r, core_r, depth = _sizes(p)
    lean = draft_offset(p.height, p.body_draft)
    top = p.floor + p.height
    # cup: straight outside, cavity widening upward to the rim
    cup = extrude(circle(0, 0, cup_r), top)
    # scaled extrusions keep the drafted sides smooth (no stair steps on the casting)
    r0 = R - lean
    cup -= Manifold.extrude(body_section(p, r0), p.height + 1, scale_top=((R + lean / p.height) / r0,) * 2).translate((0, 0, p.floor))
    pin_h = p.pot_floor - p.pin_gap
    pin_lean = draft_offset(pin_h, 2.0)
    cup += drafted(lambda f: circle(0, 0, p.drain_d / 2 + (1 - f) * pin_lean), p.floor - EMBED, pin_h + EMBED, steps=3)

    # core, print pose: flange on the bed, skirt and frustum rising from it
    outer = cup_r + p.clearance + p.skirt_t
    core = extrude(circle(0, 0, outer), p.flange_t)
    core += extrude(circle(0, 0, outer) - circle(0, 0, cup_r + p.clearance), p.skirt_h, p.flange_t - EMBED)
    core_lean = draft_offset(depth, p.core_draft)
    core += Manifold.extrude(circle(0, 0, core_r), depth + EMBED,
                             scale_top=((core_r - core_lean) / core_r,) * 2).translate((0, 0, p.flange_t - EMBED))
    vent_r = (core_r + R) / 2
    for k in range(4):
        a = math.pi / 2 * k
        core -= extrude(circle(vent_r * math.cos(a), vent_r * math.sin(a), p.vent_d / 2), p.flange_t + 2, -1)
    return {"cup": cup, "core": core}


def casting(p):
    """What the mold makes, for the shop's cast render: the planter, cast right side up,
    so the core is taken away in its assembled pose and nothing is flipped."""
    parts = build(p)
    dx, dy, dz, rx, ry, rz = assembly(p)["core"]
    core = parts["core"].rotate((rx, ry, rz)).translate((dx, dy, dz))
    return cast_of(parts["cup"], minus=core, flip=False)
