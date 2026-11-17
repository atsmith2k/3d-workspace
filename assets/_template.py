"""DESCRIPTION_HERE

Spec:
  kind: prop
  size: 0.5 x 0.5 x 0.5 m
  pivot: centre of bounds (dynamic prop) | base centre (static piece)
  budget: 300 triangles, one material, 512 px textures
  materials: what each surface is
  use: what game, what it stands next to
  engine: body dynamic, box collider

Metres, Y up, -Z forward. Build: cad game build assets/<name>.py, then READ the preview.
"""
from cadkit.game import *

KIND = "prop"
DESCRIPTION = "DESCRIPTION_HERE"
PARAMS = dict(size=0.5, seed=1)
BUDGET = dict(tris=300, texture=512, materials=1)
ENGINE = dict(body="dynamic", collider="box")


def checks(p):
    return [size(x=p.size, y=p.size, z=p.size), tris(max=300), pivot("centre"), materials(1)]


def build(p):
    grain = fbm(256, cells=6, seed=p.seed)
    mat = Material("painted", base=tint(grain, (0.50, 0.33, 0.20), (0.66, 0.46, 0.28)),
                   orm=orm(1.0, 0.65 + 0.2 * grain, 0.0), normal=normal_from_height(grain, 3),
                   metallic=1.0, roughness=1.0)
    return Model((box(p.size, p.size, p.size), mat))
