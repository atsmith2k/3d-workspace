"""Wall torch: an iron bracket and cup with a burning flame, mounted on a wall.

Spec:
  kind: prop
  size: 0.12 x 0.42 x 0.27 m
  pivot: centre of the back face in X and Z (it mounts flat against a wall and hangs out toward -Z)
  budget: 300 triangles, two materials, 256 px textures
  materials: forged iron; flame (emissive orange, strength 1.8)
  features: backplate 120 x 300 mm; arm 200 mm; cup 60 mm radius; flame 270 mm tall
  use: on walls at about 1.8 m; pair it with a point light 0.3 m in front
  engine: no body; rest_y 1.8 (mount height)
"""
from _dungeon import *

KIND = "prop"
DESCRIPTION = "wall torch, iron bracket and flame"
PARAMS = dict(reach=0.2, glow=1.8)
BUDGET = dict(tris=300, texture=256, materials=2)
ENGINE = dict(rest_y=1.8)


def checks(p):
    return [size(x=0.12, y=(0.38, 0.46), z=(0.24, 0.30)), tris(max=300), pivot((0.5, None, 1.0)),
            materials(2), texture_size(256)]


def build(p):
    z = -p.reach
    plate = box(0.12, 0.30, 0.02).moved(0, 0, -0.01)
    arm = box(0.035, 0.035, p.reach).moved(0, -0.09, z / 2 - 0.01)
    cup = lathe([(0.018, -0.11), (0.06, 0.02)], 10).moved(0, 0, z)
    rim = lathe([(0.06, 0.02), (0.045, 0.02), (0.012, -0.10)], 10, smooth=False).moved(0, 0, z)
    flame = lathe([(0.0, 0.0), (0.05, 0.05), (0.038, 0.14), (0.0, 0.27)], 8).moved(0, 0.0, z)
    fire = Material("torch_flame", color=(1.0, 0.55, 0.15), roughness=0.4,
                    emissive=(1.0, 0.30, 0.03), emissive_strength=p.glow)
    return Model((box_uv(merge(plate, arm, cup, rim), 3.0), iron()), (flame, fire))
