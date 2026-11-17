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
from _frp_body import Params, dress, idle_clip, walk_clip
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


def build(p):
    sk = humanoid(p.shape)
    ch = Character(sk)
    wood = flat_material("frp_mannequin_wood", "wood_pale", roughness=0.7)
    joint = flat_material("frp_mannequin_joint", "wood_dark", roughness=0.8)
    dress(ch, sk, p.shape, dict(wood=wood, joint=joint))                 # the shared body, nothing worn
    attach(ch, sword.build(Params(**sword.PARAMS)).parts, "socket_hand.R")
    shield = merge(lathe([(0.0, 0.03), (0.30, 0.0)], 12), lathe([(0.30, 0.0), (0.30, -0.02), (0.0, -0.02)], 12, smooth=False),
                   ball(0.05, 8, 3).moved(0, 0.035, 0)).rotated(-90, "z")          # its face looks along +X, off the left arm
    attach(ch, [(shield, joint), ], "socket_shield")
    ch.clips = [idle_clip(), walk_clip()]
    return ch
