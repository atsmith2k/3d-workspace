"""Checkpoint flag: a pole on a round base with a green check-mark flag as its own mesh node.

Spec:
  kind: prop
  size: 0.80 x 1.56 x 0.30 m
  pivot: base centre of the pole on Y=0 (the flag flies toward +X)
  budget: 300 triangles, one material (sandbox atlas) in two mesh nodes: two draw calls
  materials: steel pole, dark base, gold ball on top; flag: green with a white check mark
  features: base 0.30 m across; pole 1.5 m; ball of 60 mm radius at the top as the marker seen
            across a level; flag 0.60 x 0.40 m, 20 mm thick, in the node `flag`
  use: spawn point and checkpoints in builder levels
  engine: body static, auto collider. The node `flag` spawns as its own entity from Mojo, so a
          game can wave it or swap its material (grey before activation, green after)
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "checkpoint flag on a pole, flag as a separate node"
PARAMS = dict(pole=1.5, flag_w=0.6, flag_h=0.4)
BUDGET = dict(tris=300, texture=512, materials=2)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["checkpoint", "spawn", "flag"],
               gameplay=dict(checkpoint=True, recolour_node="flag"),
               notes="Two mesh nodes: `checkpoint_flag` (base, pole, ball) and `flag`. The world kit draws "
                     "the file as one model and cannot move or recolour a node; from Mojo, spawn_gltf gives "
                     "each node its own entity. Both nodes use the one atlas material, so to grey the flag "
                     "out give that entity another material.")


def checks(p):
    return [size(x=(0.75, 0.85), y=(p.pole + 0.05, p.pole + 0.07), z=0.30), tris(max=300),
            pivot((None, 0.0, 0.5)), materials(2), texture_size(512),
            custom("flag is its own node", lambda ctx: (
                [n["name"] for n in ctx.summary["mesh_nodes"]] == ["checkpoint_flag", "flag"],
                f"mesh nodes {[n['name'] for n in ctx.summary['mesh_nodes']]}"))]


def build(p):
    base = tile(merge(lathe([(0.15, 0), (0.15, 0.04), (0.06, 0.08)], 12, smooth=False), disc(0.15, 0, 12, up=False)), T.DARK)
    pole = tile(lathe([(0.025, 0.07), (0.025, p.pole - 0.03)], 8), T.STEEL)
    top = tile(ball(0.06).moved(0, p.pole, 0), T.GOLD)
    flag = tile(box(p.flag_w, p.flag_h, 0.02).moved(0.02 + p.flag_w / 2, p.pole - 0.09 - p.flag_h / 2, 0), T.FLAG)
    return Model((merge(base, pole, top), atlas()), (flag, atlas(), "flag"))
