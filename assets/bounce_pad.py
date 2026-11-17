"""Bounce pad: a sprung launch plate with yellow chevrons, for the sandbox builder.

Spec:
  kind: prop
  size: 1.0 x 0.25 x 1.0 m
  pivot: base centre on Y=0
  budget: 300 triangles, one material (sandbox atlas)
  materials: dark metal base, steel springs, black-and-yellow chevron plate
  features: base 1.0 m square x 70 mm; four concertina springs 100 mm tall at the corners; top plate 0.92 m
            square x 90 mm with chevrons on every face; flat top
  use: on floors and platforms; whatever lands on it is launched upward
  engine: body static, box collider (flat top); the bounce itself is game logic: see gameplay
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "bounce pad with chevrons and springs"
PARAMS = dict(size=1.0, height=0.25)
BUDGET = dict(tris=300, texture=512, materials=1)
ENGINE = dict(body="static", collider="box", rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["bounce", "launch"],
               gameplay=dict(surface="bounce", restitution=1.0, launch_speed=9.0),
               notes="The engine does not read a surface type from a model. This manifest's gameplay block "
                     "is the signal: set restitution on the body, or launch what lands on it from game code.")


def checks(p):
    return block_checks(p.size, p.height, p.size, tris_max=300, anchor="base") + [
        custom("flat top", lambda ctx: (
            np.isclose(ctx.model.bounds[1][1], ctx.params["height"]),
            "the highest surface is the plate's flat top, so a box collider matches it"))]


def build(p):
    s = p.size
    base = tile(bevel_box(s, 0.07, s, 0.02).moved(0, 0.035, 0), T.DARK)
    e = s / 2 - 0.14
    springs = [tile(lathe([(0.07, 0.065), (0.045, 0.098), (0.07, 0.132), (0.045, 0.165)], 6,
                          smooth=False).moved(x, 0, z), T.STEEL)
               for x in (-e, e) for z in (-e, e)]
    plate = tile(bevel_box(s * 0.92, 0.09, s * 0.92, 0.02).moved(0, p.height - 0.045, 0), T.CHEVRON)
    return Model((merge(base, plate, *springs), atlas()))
