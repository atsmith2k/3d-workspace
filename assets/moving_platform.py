"""Moving platform: a steel deck with hazard-striped edges and a glowing arrow along its travel.

Spec:
  kind: prop
  size: 2.0 x 0.2 x 1.0 m
  pivot: centre of bounds (the world kit moves a kinematic body about its centre)
  budget: 300 triangles, two materials (sandbox atlas; arrow glow)
  materials: steel deck; black-and-yellow hazard trim on all four edges; cyan emissive arrow
  features: trim 40 mm wide in 0.5 m segments so the stripes keep their angle; deck top 5 mm
            under the trim; arrow 0.9 m long pointing +X, the direction of travel
  use: carries the player across gaps; give it a world-kit `patrol` along its X
  engine: body kinematic, box collider (flat top that carries what stands on it)
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "moving platform with hazard trim and a direction arrow"
PARAMS = dict(length=2.0, width=1.0, thick=0.2, trim=0.04)
BUDGET = dict(tris=300, texture=512, materials=2)
ENGINE = dict(body="kinematic", collider="box")
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["platform", "moving", "kinematic"],
               gameplay=dict(moves=True, travel_axis="+x"))


def checks(p):
    return block_checks(p.length, p.thick, p.width, tris_max=300)[:3] + [materials(2), texture_size(512),
            custom("arrow glows", lambda ctx: (any(any(m.emissive) for m in ctx.model.materials),
                                              "the arrow is emissive, so the direction reads in the dark"))]


def build(p):
    L, W, t, k = p.length, p.width, p.thick, p.trim
    deck = tile(box(L - 2 * k + 0.004, t - 0.005, W - 2 * k + 0.004).moved(0, -0.0025, 0), T.STEEL)
    trims = []
    for i in range(4):                                         # long edges, 0.5 m segments
        x = -L / 2 + 0.25 + 0.5 * i
        for z in (-(W / 2 - k / 2), W / 2 - k / 2):
            trims.append(box(0.5, t, k).moved(x, 0, z))
    for j in range(2):                                         # short edges, between the long ones
        z = -(W - 2 * k) / 2 + (W - 2 * k) / 4 + (W - 2 * k) / 2 * j
        for x in (-(L / 2 - k / 2), L / 2 - k / 2):
            trims.append(box(k, t, (W - 2 * k) / 2).moved(x, 0, z))
    arrow_pts = [(-0.45, -0.07), (0.15, -0.07), (0.15, -0.2), (0.45, 0.0), (0.15, 0.2), (0.15, 0.07), (-0.45, 0.07)]
    arrow = prism(arrow_pts, 0.004, centre=(0.1, 0.0)).rotated(-90, "x").moved(0, t / 2 - 0.005 + 0.002, 0)
    glow = Material("platform_arrow", color=(0.2, 0.9, 1.0), roughness=0.4, emissive=(0.1, 0.8, 1.0),
                    emissive_strength=1.5)
    return Model((merge(deck, tile(merge(*trims), T.HAZARD)), atlas()), (arrow, glow))
