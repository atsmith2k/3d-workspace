"""Ground slope: rises 1 m over one 2 m cell, climbing toward -Z.

Spec:
  kind: environment
  size: 2.0 x 1.0 x 2.0 m
  pivot: base centre on Y=0
  budget: 600 triangles, two materials, 1024 px textures
  materials: trodden earth and dying grass on top; bare soil and stones on the cut sides
  features: a straight 26.6 degree slope the character controller walks; its low edge meets a ground tile at Y=0 and its high edge one at Y=1
  use: wilderness sub-pack: modular ground on the 2 m grid; edges are plain vertical cuts, so any
       tile meets any other
  engine: body static, auto collider
"""
from _frp import *

KIND = "environment"
DESCRIPTION = "ground slope, 1 m rise"
PARAMS = dict(rise=1.0)
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
    return piece_checks(GRID, p.rise, GRID, kind="terrain", anchor="base")


def build(p):
    top, sides = split_top(wedge(GRID, p.rise, GRID))
    return Model((tiled(top, GROUND_TILE), ground()), (tiled(sides), earth()))
