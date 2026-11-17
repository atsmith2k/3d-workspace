"""Mannequin: a jointed wooden figure on the pack's humanoid rig, holding a sword and a shield.

Spec:
  kind: character
  size: 1.80 m tall in the standard shape (1.35 stout, 1.10 slight, 2.05 tall); about 1 m across the hands
  pivot: feet at the origin (the body is centred in X; the sword and shield make the bounds lopsided); faces +Z
  budget: 6000 triangles, five materials (two of its own, three on the sword), 35 bones
  materials: pale wood segments, dark wood joints and shield; the sword brings its own
  features: every one of the 35 bones moves something (jaw, eyes, thumb, fingers, toes), so a
            wrong weight or a missing bone shows; the longsword sits in socket_hand.R and a round
            shield on socket_shield, each bound to its socket
  clips: idle 3.0 s, walk 1.0 s; loop in place; the walk strikes with the left foot at phase 0
  use: the rig's test figure and the fitting dummy for armour and weapons in all four body
       shapes: `--set shape=stout`. Not a product.
  engine: no body; rest_y 0. Cinder's world kit does not draw skinned models
"""
from _frp import *
from cadkit.game.rig import SHAPES, attach

import wpn_longsword_iron as sword

KIND = "character"
DESCRIPTION = "jointed wooden mannequin on the pack's humanoid rig"
PARAMS = dict(shape="standard")
BUDGET = dict(tris=6000, texture=1024, materials=5)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("heroes", "rig", "mannequin", sellable=False)


def checks(p):
    height = SHAPES[p.shape]["height"]

    def sockets(ctx):
        names = ctx.model.skeleton.names
        missing = [s for s in SOCKETS if s not in names]
        used = set()
        for j, wgt in ctx.model.skins:
            used |= set(np.unique(j[wgt > 0]).tolist())
        held = [s for s in ("socket_hand.R", "socket_shield") if names.index(s) in used]
        return not missing and len(held) == 2, (f"all {len(SOCKETS)} sockets exist; the sword and shield are bound to "
                                                + " and ".join(held) if not missing else f"missing sockets: {missing}")

    def sword_points_forward(ctx):
        sk = ctx.model.skeleton
        i = sk.index("socket_hand.R")
        mesh = np.vstack([m.v[(j[:, 0] == i) & (w[:, 0] > 0.99)] for (m, _), (j, w) in zip(ctx.model.parts, ctx.model.skins)])
        reach = mesh[:, 2].max() - sk.head("socket_hand.R")[2]
        return reach > 0.8, f"the blade reaches {reach:.2f} m ahead of the hand (+Z, the way the figure faces)"
    return [size(y=(height - 0.03, height + 0.03)), tris(max=6000), pivot((None, 0.0, None), tol=0.02), materials(5),
            clips("idle", "walk"), custom("sockets", sockets), custom("held item points forward", sword_points_forward),
            custom("35 bones", lambda ctx: (len(ctx.model.skeleton) == 35, f"{len(ctx.model.skeleton)} bones"))]


def tube(a, b, r0, r1, sides=8):
    length = float(np.linalg.norm(np.asarray(b) - np.asarray(a)))
    return along(merge(lathe([(r0, 0), (r1, length)], sides), disc(r0, 0, sides, up=False), disc(r1, length, sides)), a, b)


def build(p):
    spec = SHAPES[p.shape]
    h, wd = spec["height"] / 1.75, spec["width"]
    sk = humanoid(p.shape)
    ch = Character(sk)
    wood = flat_material("frp_mannequin_wood", "wood_pale", roughness=0.7)
    joint = flat_material("frp_mannequin_joint", "wood_dark", roughness=0.8)

    def at(name):
        return sk.head(name)

    def tip(name):
        return sk.tail(sk.index(name))

    ch.add(bevel_box(0.30 * h * wd, 0.18 * h, 0.20 * h * wd, 0.03).moved(0, at("hips")[1] - 0.01, 0), wood, bind="hips")
    ch.add(ball(0.085 * h * wd).moved(*at("spine")), joint, bind="spine")
    mid = (at("spine")[1] + at("neck")[1]) / 2
    ch.add(bevel_box(0.40 * h * wd, 0.42 * h, 0.24 * h * wd, 0.05).moved(0, mid + 0.02 * h, 0), wood, bind="chest")
    ch.add(tube(at("neck") - [0, 0.02, 0], at("head") + [0, 0.02, 0], 0.045 * h, 0.045 * h), joint, bind="neck")
    head_c = at("head") + [0, 0.115 * h, 0.01 * h]
    ch.add(ball(0.115 * h, 10, 6).scaled(0.9, 1.1, 1.0).moved(*head_c), wood, bind="head")
    ch.add(box(0.11 * h, 0.035 * h, 0.07 * h).moved(*(at("jaw") + [0, -0.025 * h, 0.035 * h])), joint, bind="jaw")
    for s in "LR":
        ch.add(ball(0.016 * h, 6, 3).moved(*tip(f"eye.{s}")), joint, bind=f"eye.{s}")
        sh, el, wr = at(f"upper_arm.{s}"), at(f"lower_arm.{s}"), at(f"hand.{s}")
        ch.add(ball(0.07 * h).moved(*sh), joint, bind=f"upper_arm.{s}")
        ch.add(tube(sh, el, 0.052 * h, 0.046 * h), wood, bind=f"upper_arm.{s}")
        ch.add(ball(0.055 * h).moved(*el), joint, bind=f"lower_arm.{s}")
        ch.add(tube(el, wr, 0.046 * h, 0.038 * h), wood, bind=f"lower_arm.{s}")
        ch.add(ball(0.045 * h).moved(*wr), joint, bind=f"hand.{s}")
        ch.add(tube(wr, at(f"fingers.{s}"), 0.034 * h, 0.036 * h, 6), wood, bind=f"hand.{s}")
        ch.add(tube(at(f"fingers.{s}"), tip(f"fingers.{s}"), 0.034 * h, 0.022 * h, 6), wood, bind=f"fingers.{s}")
        ch.add(tube(at(f"thumb.{s}"), tip(f"thumb.{s}"), 0.016 * h, 0.012 * h, 6), wood, bind=f"thumb.{s}")
        hp, kn, an = at(f"upper_leg.{s}"), at(f"lower_leg.{s}"), at(f"foot.{s}")
        ch.add(ball(0.08 * h).moved(*hp), joint, bind=f"upper_leg.{s}")
        ch.add(tube(hp, kn, 0.068 * h, 0.058 * h), wood, bind=f"upper_leg.{s}")
        ch.add(ball(0.062 * h).moved(*kn), joint, bind=f"lower_leg.{s}")
        ch.add(tube(kn, an, 0.056 * h, 0.044 * h), wood, bind=f"lower_leg.{s}")
        ch.add(ball(0.05 * h).moved(*an), joint, bind=f"foot.{s}")
        ch.add(bevel_box(0.10 * h, 0.07 * h, 0.14 * h, 0.015).moved(an[0], 0.035 * h, 0.03 * h), wood, bind=f"foot.{s}")
        ch.add(bevel_box(0.10 * h, 0.05 * h, 0.09 * h, 0.012).moved(an[0], 0.025 * h, 0.15 * h), wood, bind=f"toe.{s}")
    attach(ch, sword.build(SimpleParams(**sword.PARAMS)).parts, "socket_hand.R")
    shield = merge(lathe([(0.0, 0.03), (0.30, 0.0)], 12), lathe([(0.30, 0.0), (0.30, -0.02), (0.0, -0.02)], 12, smooth=False),
                   ball(0.05, 8, 3).moved(0, 0.035, 0)).rotated(-90, "z")          # its face looks along +X, off the left arm
    attach(ch, [(shield, joint), ], "socket_shield")
    ch.clips = [idle(), walk()]
    return ch


class SimpleParams:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def walk():
    return Clip.cycle("walk", 1.0, lambda ph: biped_gait(ph, stride=26, knee=55, arm=22, elbow=16, lean=4,
                                                          bob=0.012, twist=5), keys=16)


def idle():
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
