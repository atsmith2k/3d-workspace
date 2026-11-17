"""The fitting dummy's body and the pack's armour, both drawn from a skeleton's joints.

Nothing here has a fixed size: every part is placed from the bones of the `humanoid(shape)` it is
given, so a piece authored once fits the standard, stout, slight and tall shapes. That is what
"fitted by the build" means in the style guide.

    parts = body(sk, shape)                      # [Part(mesh, "wood"|"joint", bone, region)]
    worn  = armour(sk, shape, "iron")            # [Piece(mesh, "plate"|"trim", bone, slot)]
    dress(ch, sk, shape, mats, worn)             # adds the body minus what the armour hides

Regions of the body: head, torso, hips, arms, hands, legs, feet, joints (shoulders and neck:
never hidden). `HIDES` says which regions each armour slot covers.
"""
from collections import namedtuple

from _frp import *
from cadkit.game.rig import SHAPES

Part = namedtuple("Part", "mesh mat bone region")
Piece = namedtuple("Piece", "mesh mat bone slot")

HIDES = dict(head=(), shoulders=(), chest=("torso",), arms=("arms",), hands=("hands",), belt=(),
             legs=("hips", "legs"), feet=("feet",), cloak=(), robe=("torso", "hips", "legs"))


def tube(a, b, r0, r1, sides=8):
    length = float(np.linalg.norm(np.asarray(b) - np.asarray(a)))
    return along(merge(lathe([(r0, 0), (r1, length)], sides), disc(r0, 0, sides, up=False), disc(r1, length, sides)), a, b)


def _dims(sk, shape):
    spec = SHAPES[shape]
    return spec["height"] / 1.75, spec["width"]


def body(sk, shape):
    """The jointed wooden figure, part by part."""
    h, wd = _dims(sk, shape)
    at, tip = sk.head, lambda name: sk.tail(sk.index(name))
    out = []

    def add(mesh, mat, bone, region):
        out.append(Part(mesh, mat, bone, region))

    add(bevel_box(0.30 * h * wd, 0.18 * h, 0.20 * h * wd, 0.03).moved(0, at("hips")[1] - 0.01, 0), "wood", "hips", "hips")
    add(ball(0.085 * h * wd, 8, 4).moved(*at("spine")), "joint", "spine", "joints")
    mid = (at("spine")[1] + at("neck")[1]) / 2
    add(bevel_box(0.40 * h * wd, 0.42 * h, 0.24 * h * wd, 0.05).moved(0, mid + 0.02 * h, 0), "wood", "chest", "torso")
    add(tube(at("neck") - [0, 0.02, 0], at("head") + [0, 0.02, 0], 0.045 * h, 0.045 * h), "joint", "neck", "joints")
    add(ball(0.115 * h, 10, 6).scaled(0.9, 1.1, 1.0).moved(*(at("head") + [0, 0.115 * h, 0.01 * h])), "wood", "head", "head")
    add(box(0.11 * h, 0.035 * h, 0.07 * h).moved(*(at("jaw") + [0, -0.025 * h, 0.035 * h])), "joint", "jaw", "head")
    for s in "LR":
        add(ball(0.016 * h, 6, 3).moved(*tip(f"eye.{s}")), "joint", f"eye.{s}", "head")
        sh, el, wr = at(f"upper_arm.{s}"), at(f"lower_arm.{s}"), at(f"hand.{s}")
        add(ball(0.07 * h, 8, 4).moved(*sh), "joint", f"upper_arm.{s}", "joints")
        add(tube(sh, el, 0.052 * h, 0.046 * h), "wood", f"upper_arm.{s}", "arms")
        add(ball(0.055 * h, 8, 4).moved(*el), "joint", f"lower_arm.{s}", "arms")
        add(tube(el, wr, 0.046 * h, 0.038 * h), "wood", f"lower_arm.{s}", "arms")
        add(ball(0.045 * h, 8, 4).moved(*wr), "joint", f"hand.{s}", "hands")
        add(tube(wr, at(f"fingers.{s}"), 0.034 * h, 0.036 * h, 6), "wood", f"hand.{s}", "hands")
        add(tube(at(f"fingers.{s}"), tip(f"fingers.{s}"), 0.034 * h, 0.022 * h, 6), "wood", f"fingers.{s}", "hands")
        add(tube(at(f"thumb.{s}"), tip(f"thumb.{s}"), 0.016 * h, 0.012 * h, 6), "wood", f"thumb.{s}", "hands")
        hp, kn, an = at(f"upper_leg.{s}"), at(f"lower_leg.{s}"), at(f"foot.{s}")
        add(ball(0.08 * h, 8, 4).moved(*hp), "joint", f"upper_leg.{s}", "hips")
        add(tube(hp, kn, 0.068 * h, 0.058 * h), "wood", f"upper_leg.{s}", "legs")
        add(ball(0.062 * h, 8, 4).moved(*kn), "joint", f"lower_leg.{s}", "legs")
        add(tube(kn, an, 0.056 * h, 0.044 * h), "wood", f"lower_leg.{s}", "legs")
        add(ball(0.05 * h, 8, 4).moved(*an), "joint", f"foot.{s}", "feet")
        add(bevel_box(0.10 * h, 0.07 * h, 0.14 * h, 0.015).moved(an[0], 0.035 * h, 0.03 * h), "wood", f"foot.{s}", "feet")
        add(bevel_box(0.10 * h, 0.05 * h, 0.09 * h, 0.012).moved(an[0], 0.025 * h, 0.15 * h), "wood", f"toe.{s}", "feet")
    return out


def armour(sk, shape, slots=("head", "shoulders", "chest", "arms", "hands", "legs", "feet")):
    """A footman's plate harness, piece by piece, for the slots asked for. Plates are faceted
    (hammered, not turned) and stand 12-20 mm off the body they cover."""
    h, wd = _dims(sk, shape)
    at, tip = sk.head, lambda name: sk.tail(sk.index(name))
    out = []

    def add(mesh, mat, bone, slot):
        if slot in slots:
            out.append(Piece(mesh, mat, bone, slot))

    # head: a kettle helm, a dome with a brim, and a nasal bar
    crown = at("head") + [0, 0.115 * h, 0.01 * h]
    r = 0.128 * h
    dome = lathe([(r * 1.32, -0.01 * h), (r * 1.02, 0.0), (r * 1.0, 0.045 * h), (r * 0.8, 0.105 * h), (r * 0.42, 0.14 * h),
                  (0.0, 0.15 * h)], 10)
    brim = lathe([(r * 1.0, -0.004 * h), (r * 1.32, -0.014 * h)], 10)          # the underside of the brim
    add(merge(dome, brim).moved(crown[0], crown[1] + 0.012 * h, crown[2]), "plate", "head", "head")
    add(box(0.022 * h, 0.09 * h, 0.012 * h).moved(crown[0], crown[1] - 0.02 * h, crown[2] + r * 0.98), "trim", "head", "head")
    # chest: breast and back in one shell, with a flared waist, and a gorget ring at the neck
    mid = (at("spine")[1] + at("neck")[1]) / 2 + 0.02 * h
    add(bevel_box(0.44 * h * wd, 0.45 * h, 0.285 * h * wd, 0.06).moved(0, mid, 0), "plate", "chest", "chest")
    add(bevel_box(0.36 * h * wd, 0.05 * h, 0.30 * h * wd, 0.015).moved(0, mid - 0.2 * h, 0), "trim", "chest", "chest")
    add(lathe([(0.075 * h, -0.02 * h), (0.062 * h, 0.03 * h)], 10).moved(*(at("neck") + [0, -0.005 * h, 0])), "trim", "chest", "chest")
    for sgn, s in ((1, "L"), (-1, "R")):
        sh, el, wr = at(f"upper_arm.{s}"), at(f"lower_arm.{s}"), at(f"hand.{s}")
        # shoulders: a pauldron, a flattened dome over the joint
        add(ball(0.105 * h, 8, 4).scaled(1.0, 0.72, 1.05).moved(sh[0] + sgn * 0.012 * h, sh[1] + 0.022 * h, sh[2]),
            "plate", f"upper_arm.{s}", "shoulders")
        # arms: rerebrace, elbow cop, vambrace
        d = (el - sh) / np.linalg.norm(el - sh)
        add(tube(sh + d * 0.085 * h, el, 0.066 * h, 0.060 * h), "plate", f"upper_arm.{s}", "arms")
        add(ball(0.068 * h, 8, 4).moved(*el), "trim", f"lower_arm.{s}", "arms")
        d = (wr - el) / np.linalg.norm(wr - el)
        add(tube(el + d * 0.035 * h, wr, 0.060 * h, 0.050 * h), "plate", f"lower_arm.{s}", "arms")
        # hands: a cuff, a plate over the back of the hand, a mitten over the fingers
        add(tube(wr - d * 0.03 * h, wr + d * 0.03 * h, 0.060 * h, 0.052 * h), "trim", f"hand.{s}", "hands")
        add(tube(wr + d * 0.01 * h, at(f"fingers.{s}"), 0.046 * h, 0.046 * h, 6), "plate", f"hand.{s}", "hands")
        add(tube(at(f"fingers.{s}"), tip(f"fingers.{s}"), 0.046 * h, 0.030 * h, 6), "plate", f"fingers.{s}", "hands")
        add(tube(at(f"thumb.{s}"), tip(f"thumb.{s}"), 0.022 * h, 0.016 * h, 6), "plate", f"thumb.{s}", "hands")
        # legs: cuisse, knee cop, greave
        hp, kn, an = at(f"upper_leg.{s}"), at(f"lower_leg.{s}"), at(f"foot.{s}")
        add(tube(hp + [0, -0.04 * h, 0], kn, 0.084 * h, 0.072 * h), "plate", f"upper_leg.{s}", "legs")
        add(ball(0.076 * h, 8, 4).moved(kn[0], kn[1], kn[2] + 0.008 * h), "trim", f"lower_leg.{s}", "legs")
        add(tube(kn + [0, -0.035 * h, 0], an, 0.070 * h, 0.056 * h), "plate", f"lower_leg.{s}", "legs")
        # feet: sabatons
        add(bevel_box(0.125 * h, 0.15 * h, 0.17 * h, 0.02).moved(an[0], 0.075 * h, 0.03 * h), "plate", f"foot.{s}", "feet")
        add(bevel_box(0.12 * h, 0.065 * h, 0.105 * h, 0.018).moved(an[0], 0.0325 * h, 0.155 * h), "plate", f"toe.{s}", "feet")
    # legs: a skirt of plate over the hips (faulds), with a belt
    hips = at("hips")
    add(lathe([(0.21 * h * wd, -0.16 * h), (0.175 * h * wd, 0.05 * h)], 10).scaled(1.0, 1.0, 0.78).moved(0, hips[1], 0),
        "plate", "hips", "legs")
    add(lathe([(0.182 * h * wd, 0.03 * h), (0.182 * h * wd, 0.09 * h)], 10).scaled(1.0, 1.0, 0.8).moved(0, hips[1], 0),
        "trim", "hips", "legs")
    return out


def dress(ch, sk, shape, mats, worn=(), plate_scale=3.0):
    """Add the body to a Character, leaving out every region the worn pieces hide, then the
    pieces. `mats` maps "wood", "joint", "plate", "trim" to Materials. Returns the body parts
    that were hidden (for the checks)."""
    hidden_regions = {r for piece in worn for r in HIDES[piece.slot]}
    hidden = []
    for part in body(sk, shape):
        if part.region in hidden_regions:
            hidden.append(part)
        else:
            ch.add(part.mesh, mats[part.mat], bind=part.bone)
    for piece in worn:
        mesh = piece.mesh
        if getattr(mats[piece.mat], "base", None) is not None:                 # a textured plate: faceted, box-mapped
            mesh = box_uv(flat(mesh), plate_scale)
        ch.add(mesh, mats[piece.mat], bind=piece.bone)
    return hidden


def walk_clip():
    return Clip.cycle("walk", 1.0, lambda ph: biped_gait(ph, stride=26, knee=55, arm=22, elbow=16, lean=4,
                                                          bob=0.012, twist=5), keys=16)


def idle_clip():
    def pose(ph):
        s = np.sin(2 * np.pi * ph)
        out = {"hips:move": (0, -0.004 - 0.004 * s, 0), "chest": euler(x=1.4 * s), "head": euler(y=6 * s),
               "jaw": euler(x=4 + 4 * np.sin(4 * np.pi * ph)),
               "upper_leg.L": euler(x=-1.5), "upper_leg.R": euler(x=-1.5), "lower_leg.L": euler(x=3.0), "lower_leg.R": euler(x=3.0)}
        for side, sign in (("L", 1.0), ("R", -1.0)):
            out[f"upper_arm.{side}"] = euler(x=1.5 * s, z=-sign * 22)
            out[f"lower_arm.{side}"] = euler(x=-14)
            out[f"fingers.{side}"] = euler(x=-10 - 6 * s)
        return out
    return Clip.cycle("idle", 3.0, pose, keys=12)


class Params:
    def __init__(self, **kw):
        self.__dict__.update(kw)
