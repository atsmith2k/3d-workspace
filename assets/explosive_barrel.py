"""Explosive barrel: a red steel drum with a hazard band and a warning label.

Spec:
  kind: prop
  size: 0.62 m across x 0.90 m tall
  pivot: centre of bounds (dynamic)
  budget: 800 triangles, one material (sandbox atlas)
  materials: red drum, yellow-and-black hazard band round the middle, warning triangle label
             front and back, dark lid recessed 15 mm with a bung
  features: 16 sides; two rolled ribs; the hazard band between them; labels 0.22 m square
  use: a physics prop to stack, knock over and detonate; told apart from oak_barrel by colour and markings
  engine: body dynamic, box collider (the world kit has no cylinder collider; it will not roll)
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "red explosive barrel with hazard markings"
PARAMS = dict(radius=0.30, height=0.90, sides=16)
BUDGET = dict(tris=800, texture=512, materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["barrel", "explosive", "hazard"],
               gameplay=dict(explosive=True, collider_wanted="cylinder", radius=0.30, height=0.90),
               notes="Box collider in the world kit (it offers box, sphere, mesh). From Mojo give it a "
                     "cylinder shape so it rolls when knocked over.")


def checks(p):
    return [size(x=(0.60, 0.65), y=p.height, z=(0.60, 0.67)), tris(max=800), pivot("centre", tol=0.02),
            materials(1), texture_size(512),
            custom("reads as a hazard", lambda ctx: (
                ctx.model.parts[0][0].uv[:, 1].max() > 0.5,
                "the mesh uses the hazard and warning tiles of the atlas, not just red"))]


def build(p):
    r, h, n = p.radius, p.height, p.sides
    lo = lathe([(r - 0.03, 0), (r, 0.03), (r, 0.30), (r + 0.012, 0.315), (r + 0.012, 0.335), (r, 0.35)], n)
    band = lathe([(r, 0.35), (r, 0.55)], n, u_repeat=6.0)
    hi = lathe([(r, 0.55), (r + 0.012, 0.565), (r + 0.012, 0.585), (r, 0.60), (r, h - 0.03), (r - 0.015, h),
                (r - 0.03, h), (r - 0.03, h - 0.016)], n)          # rim, then the inner wall down to the lid
    lid = merge(disc(r - 0.03, h - 0.015, n), disc(r - 0.03, 0, n, up=False),
                lathe([(0.035, h - 0.016), (0.035, h - 0.002), (0.0, h - 0.002)], 8, smooth=False).moved(0.14, 0, 0))
    labels = [box(0.22, 0.22, 0.012).moved(0, 0.74, z) for z in (r - 0.002, -(r - 0.002))]
    drum = merge(tile(merge(lo, hi), T.RED), tile(band, T.HAZARD), tile(lid, T.DARK),
                 *[tile(m, T.WARNING) for m in labels])
    return Model((drum.moved(0, -h / 2, 0), atlas()))
