"""Iron longsword: a plain soldier's sword, the pack's weapon convention in one asset.

Spec:
  kind: prop
  size: 0.22 x 1.16 x 0.05 m (blade 0.86 m)
  pivot: the centre of the grip. Convention for every held item: origin where the hand closes,
         the blade or shaft along +Y, the guard across X, the flat of the blade facing Z
  budget: 1500 triangles, two materials, 1024 px textures (1024 px per metre: it is held close
          in first person)
  materials: scratched steel blade; rusted iron guard and pommel; dark leather grip
  features: tapered point; a 20 cm grip for one or two hands; a guard 22 cm across; round pommel
  use: weapons sub-pack, common tier; held at socket_hand.R, sheathed at socket_hip.L
  engine: no body (held or carried); rest_y is its lowest point on a table
"""
from _frp import *

KIND = "prop"
DESCRIPTION = "iron longsword, common tier"
PARAMS = dict(blade=0.86, grip=0.20, guard=0.22)
BUDGET = BUDGET_OF["weapon"]
ENGINE = dict()
PRODUCT = product("weapons", "sword", "melee", "one-handed", gameplay=dict(
    grip="origin", axis="+y", socket="socket_hand.R", sheath="socket_hip.L", reach_m=1.0, weapon_class="one_handed"))


def checks(p):
    def grip(ctx):
        v = np.vstack([m.v for m, _ in ctx.model.parts])
        near = v[np.abs(v[:, 1]) < ctx.params["grip"] / 2 - 0.01]
        r = float(np.hypot(near[:, 0], near[:, 2]).max())
        return r < 0.03, f"within the grip, nothing is more than {r * 1000:.0f} mm from the axis: a hand closes round it"
    return [size(x=p.guard, y=(1.1, 1.22), z=(0.03, 0.06)), tris(max=BUDGET["tris"]), materials(3),
            texture_size(1024), custom("grip at the origin", grip),
            custom("points along +Y", lambda ctx: (ctx.model.bounds[1][1] > 3 * -ctx.model.bounds[0][1],
                                                  "the blade is on the +Y side of the hand"))]


def build(p):
    g = p.grip / 2
    blade = prism(ccw([(-0.026, 0), (0.026, 0), (0.022, p.blade - 0.1), (0, p.blade), (-0.022, p.blade - 0.1)]), 0.012)
    blade = blade.moved(0, g + 0.028, 0)
    blade = directed_uv(blade, np.c_[blade.v[:, 0] * 4 + 0.5, blade.v[:, 1]], "z")       # scratches run along the blade
    guard = bevel_box(p.guard, 0.03, 0.045, 0.008).moved(0, g + 0.014, 0)
    pommel = lathe([(0.0, -0.022), (0.024, 0.0), (0.0, 0.022)], 8).moved(0, -g - 0.02, 0)
    grip = lathe([(0.015, -g), (0.018, 0.0), (0.015, g)], 8)
    return Model((blade, steel_blade()), (box_uv(merge(guard, pommel), 6.0), iron_rusted()),
                 (grip, flat_material("frp_grip_leather", "leather_dark", roughness=0.85)))
