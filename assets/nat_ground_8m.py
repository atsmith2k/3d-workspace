"""Large ground tile: sixteen 2 m cells of open ground in one piece, walking surface at Y=0.

Spec:
  kind: environment
  size: 8.0 x 0.5 x 8.0 m
  pivot: centre of the top face
  budget: 600 triangles, two materials, 1024 px textures
  materials: trodden earth and dying grass on top; bare soil and stones on the cut sides
  features: flat top; 0.5 m deep. One piece in place of sixteen: a Cinder world holds about 250
            textures counting every placed copy of every model, so open ground is laid in large tiles
  use: wilderness sub-pack: modular ground on the 2 m grid; edges are plain vertical cuts, so any
       tile meets any other
  engine: body static, auto collider
"""
from _frp import *

KIND = "environment"
DESCRIPTION = "large ground tile, 8 m, earth and dying grass"
PARAMS = dict(depth=0.5, span=8.0)
BUDGET = BUDGET_OF["terrain"]
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("wilderness", "terrain", "ground")


def split_top(mesh):
    """(faces that look up, the rest): the top takes grass, the sides take soil."""
    up = mesh.n[mesh.f].mean(1)[:, 1] > 0.4
    def part(mask):
        idx = np.unique(mesh.f[mask])
        remap = -np.ones(len(mesh.v), int)
        remap[idx] = np.arange(len(idx))
        return Mesh(mesh.v[idx], remap[mesh.f[mask]], mesh.n[idx], mesh.uv[idx])
    return part(up), part(~up)


def checks(p):
    return piece_checks(p.span, p.depth, p.span, kind="terrain", anchor="top")


def build(p):
    top, sides = split_top(block(p.span, p.depth, p.span, y=-p.depth))
    return Model((tiled(top, GROUND_TILE), ground()), (tiled(sides), earth()))
