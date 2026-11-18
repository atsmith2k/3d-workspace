"""Cottage hearth: a stone fireplace built against a wall, with a bed of embers.

Spec:
  kind: prop
  size: 1.68 x 1.30 x 0.75 m (the stone 1.60 m wide, the mantel 40 mm proud each side)
  pivot: base centre in X, on Y=0, at the back face in Z (it is built against a wall and
         reaches toward +Z into the room)
  budget: 3000 triangles, four materials, 1024 px textures
  materials: the pack's soot-stained stone; a timber mantel; soot-black firebox and logs;
             embers (emissive, strength 0.9: the light itself is a point light in the world)
  features: firebox opening 1.0 m wide and 0.9 m high; a hearth stone that reaches 0.15 m
            in front of the jambs; a mantel shelf at 1.22 m, proud of the stone on three
            sides; two charred logs on the ember bed
  use: interiors sub-pack; the cottage's light. Place a warm point light in front of it,
       1.0 m up and 1.3 m out from the wall (intensity about 38, range 7): any closer and it
       bleaches the soot and the jambs
  engine: body static, auto collider
"""
from _frp_interior import *

KIND = "prop"
DESCRIPTION = "stone hearth with embers"
PARAMS = dict(width=1.60, height=1.30, depth=0.75, opening=1.0)
BUDGET = dict(BUDGET_OF["large_prop"], materials=4)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("interiors", "furniture", "fireplace", "light", gameplay=dict(
    light=dict(kind="point", at=(0.0, 1.0, 1.3), color=(1.0, 0.55, 0.22), intensity=38, range=7), mantel_y=1.30))


def checks(p):
    def firebox(ctx):
        stone_v = ctx.model.parts[0][0].v
        front = stone_v[stone_v[:, 2] > 0.3]
        inside = front[(np.abs(front[:, 0]) < p.opening / 2 - 0.01) & (front[:, 1] > 0.09) & (front[:, 1] < 0.89)]
        return len(inside) == 0, f"the opening is {p.opening:.1f} m wide and 0.9 m high, with no stone across it"

    def embers(ctx):
        mesh, mat = ctx.model.parts[2]
        lo, hi = mesh.bounds
        return mat.emissive_strength <= 1.5 and hi[0] - lo[0] < p.opening and hi[1] < 0.3, \
            f"embers glow at strength {mat.emissive_strength} inside the firebox"
    return furniture_checks(p.width + 0.08, p.height, p.depth, BUDGET["tris"], 4, anchor=(0.5, 0.0, 0.0)) + [
        custom("firebox open", firebox), custom("embers", embers)]


def build(p):
    w, d, o = p.width, p.depth, p.opening
    jamb_w, body_d = (w - o) / 2, 0.6
    zc = body_d / 2                                                    # the body's centre in Z; the back face is Z = 0
    hearth_stone = block(w, 0.08, d, 0, 0, d / 2)
    back = block(w - 0.02, 1.142, 0.15, 0, 0.08 - SINK, 0.075 + 0.004)   # stops inside the mantel, 4 mm in from its back face
    jambs = [block(jamb_w, 0.9, body_d - 0.01, s * (o / 2 + jamb_w / 2), 0.08 - SINK, zc) for s in (-1, 1)]
    lintel = block(w, 0.24, body_d, 0, 0.98 - SINK, zc)
    stone_mesh = tiled(merge(hearth_stone, back, *jambs, lintel))
    mantel = boards_x(block(w + 0.08, 0.08, body_d + 0.1, 0, 1.22 - SINK, zc + 0.05))
    soot = merge(block(o + 0.02, 0.9, 0.02, 0, 0.08, 0.16), block(o + 0.02, 0.012, body_d - 0.16, 0, 0.08, 0.16 + (body_d - 0.16) / 2))
    logs = [along(cylinder(0.05, 0.62, 8), (-0.33, 0.165, 0.33), (0.29, 0.165, 0.41)),
            along(cylinder(0.045, 0.55, 8), (-0.2, 0.2, 0.47), (0.31, 0.25, 0.3))]
    ember = bevel_box(0.8, 0.07, 0.34, 0.03).moved(0, 0.125, 0.37)
    return Model((stone_mesh, stone()), (mantel, timber()),
                 (ember, flat_material("frp_embers", "blood_dried", roughness=0.9, emissive="ember", strength=0.9)),
                 (merge(soot, *logs), flat_material("frp_soot", "soot", roughness=0.95)))
