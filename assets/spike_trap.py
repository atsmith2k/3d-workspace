"""Spike trap: a dark metal base with nine steel spikes as their own mesh node.

Spec:
  kind: prop
  size: 1.0 x 0.6 x 1.0 m (base 0.3 m, spikes to 0.6 m)
  pivot: base centre on Y=0
  budget: 400 triangles, one material (sandbox atlas) in two mesh nodes: two draw calls
  materials: dark metal base; bright steel spikes
  features: base chamfered 30 mm; nine four-sided spikes in a 3 x 3 grid, 0.22 m across at the
            root, rising 0.3 m to a point; the spikes are the node `spikes`
  use: a hazard in obstacle courses and dungeon rooms, beside the pressure plate
  engine: body static, auto collider. The node `spikes` spawns as its own entity from Mojo, so a
          game can retract it and put the hazard volume on the spikes alone
"""
from _sandbox import *

KIND = "prop"
DESCRIPTION = "spike trap, spikes as a separate node"
PARAMS = dict(size=1.0, base=0.3, spike=0.3, grid=3)
BUDGET = dict(tris=400, texture=512, materials=2)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = dict(PRODUCT, tags=PRODUCT["tags"] + ["hazard", "spikes", "trap"],
               gameplay=dict(hazard=True, hazard_node="spikes", hazard_box_m=[0.9, 0.3, 0.9], hazard_centre_y=0.45,
                             retract_by_m=0.3),
               notes="Two mesh nodes: `spike_trap` (the base) and `spikes`. In the world kit use a `hazard` "
                     "with radius 0.6 at the entity; from Mojo move the `spikes` entity down 0.3 m to retract.")


def checks(p):
    return [size(x=p.size, y=p.base + p.spike, z=p.size), tris(max=400), pivot("base"), materials(2),
            texture_size(512),
            custom("spikes are their own node", lambda ctx: (
                [n["name"] for n in ctx.summary["mesh_nodes"]] == ["spike_trap", "spikes"],
                f"mesh nodes {[n['name'] for n in ctx.summary['mesh_nodes']]}")),
            custom("sharp", lambda ctx: (
                int((ctx.model.parts[1][0].v[:, 1] > ctx.params["base"] + ctx.params["spike"] - 1e-6).sum()) >= 9,
                "every spike comes to a point at the full height"))]


def build(p):
    base = tile(bevel_box(p.size, p.base, p.size, 0.03).moved(0, p.base / 2, 0), T.DARK)
    step = (p.size - 0.16) / p.grid
    r = step * 0.5 * 0.92
    spikes = []
    for i in range(p.grid):
        for j in range(p.grid):
            x, z = (i - (p.grid - 1) / 2) * step, (j - (p.grid - 1) / 2) * step
            cone = flat(lathe([(r * 2 ** 0.5 * 0.72, p.base - 0.004), (0.0, p.base + p.spike)], 4, phase=45))
            spikes.append(cone.moved(x, 0, z))
    return Model((base, atlas()), (tile(merge(*spikes), T.STEEL), atlas(), "spikes"))
