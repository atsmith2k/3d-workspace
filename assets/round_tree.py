"""Round tree: a low-poly tree with a brown trunk and a round green canopy.

Spec:
  kind: environment
  size: 1.5 m canopy x 2.5 m tall
  pivot: base centre of the trunk on Y=0
  budget: 500 triangles, one material (sandbox atlas)
  materials: bark brown trunk; warm leaf green canopy
  features: six-sided trunk tapering from 0.16 to 0.10 m radius, 1.2 m to the canopy; a
            faceted canopy 1.5 m across, a smaller crown on top for a rounder outline
  use: outdoor scenery for gardens and parks; stands on a 2 m grid cell
  engine: no body in the world kit: its colliders are the whole model's box or mesh, and either
          would make the canopy solid. The trunk collider wanted is in gameplay
"""
from _sandbox import *

KIND = "environment"
DESCRIPTION = "low-poly tree with a round canopy"
PARAMS = dict(height=2.5, canopy=1.5, trunk=0.16)
BUDGET = dict(tris=500, texture=512, materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["tree", "nature", "scenery"],
               gameplay=dict(collider_wanted="cylinder", radius=0.16, height=1.2, on="trunk only"),
               notes="Delivered without a body: the world kit can only make the whole model solid (box or "
                     "triangle mesh), which would block the player under the canopy. From Mojo, add a "
                     "static cylinder of radius 0.16 and height 1.2 at the trunk. In a kit world, an "
                     "invisible collider is not possible; leave the tree walk-through or accept a mesh body.")


def checks(p):
    return [size(x=p.canopy, y=p.height, z=(p.canopy * 0.85, p.canopy + 0.01), tol=0.02), tris(max=500),
            pivot("base", tol=0.02), materials(1), texture_size(512),
            custom("canopy clears a player", lambda ctx: (
                ctx.model.parts[0][0].v[np.linalg.norm(ctx.model.parts[0][0].v[:, [0, 2]], axis=1) > 0.3][:, 1].min() > 1.0,
                "nothing wider than the trunk is lower than 1.0 m"))]


def build(p):
    r = p.canopy / 2
    trunk = tile(lathe([(p.trunk, 0), (p.trunk * 0.78, 0.45), (p.trunk * 0.62, 1.3)], 6, smooth=False), T.BARK)
    canopy = flat(lathe([(0.0, 1.05), (r * 0.66, 1.2), (r, 1.62), (r * 0.82, 2.08), (r * 0.42, 2.38)], 8))
    crown = flat(lathe([(r * 0.5, 2.25), (r * 0.36, 2.44), (0.0, p.height)], 8, phase=22.5))
    return Model((merge(trunk, tile(merge(canopy, crown), T.LEAF)), atlas()))
