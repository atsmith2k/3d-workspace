"""Ground tile: one 2 m cell of open ground, walking surface at Y=0.

Spec:
  kind: environment
  size: 2.0 x 0.5 x 2.0 m
  pivot: centre of the top face
  budget: 600 triangles, two materials, 1024 px textures
  materials: trodden earth and dying grass on top; bare soil and stones on the cut sides
  features: flat top; 0.5 m deep so slopes and banks beside it show soil, not a gap
  use: wilderness sub-pack: modular ground on the 2 m grid; edges are plain vertical cuts, so any
       tile meets any other
  engine: body static, auto collider
"""
from _frp import *

KIND = "environment"
DESCRIPTION = "ground tile, earth and dying grass"
PARAMS = dict(depth=0.5)
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
    return piece_checks(GRID, p.depth, GRID, kind="terrain", anchor="top")


def build(p):
    top, sides = split_top(block(GRID, p.depth, GRID, y=-p.depth))
    return Model((tiled(top, GROUND_TILE), ground()), (tiled(sides), earth()))
