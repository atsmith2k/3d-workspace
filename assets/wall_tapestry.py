"""Wall tapestry: a woven banner hanging from an iron rod, its picture from a generation service.

Spec:
  kind: prop
  size: 1.3 x 1.9 x 0.08 m (cloth 1.2 x 1.8 m)
  pivot: centre of the back face in X and Z (it hangs flat on a wall, facing -Z)
  budget: 200 triangles, two materials, 1024 px textures
  materials: cloth: a generated picture (a heraldic dragon, medieval tapestry style) as base
             colour, with a normal map from its brightness so the weave catches the light;
             forged iron rod and finials (procedural)
  features: cloth 20 mm thick with a pointed lower edge; rod 1.22 m long, 20 mm radius, a finial at each end
  use: dressing for dungeon walls, hung at 2.0 m; this is the kit's one asset whose look a
       script cannot draw, which is what the generative step is for
  engine: no body; rest_y 2.0
  generated: `dragon_banner` (cadkit.game.gen). Not in assets/gen/ until someone runs
             `cad game build assets/wall_tapestry.py --gen` with OPENAI_API_KEY set; uncleared
             until a person checks it
"""
from cadkit.game import *
from cadkit.game import gen

KIND = "prop"
DESCRIPTION = "wall tapestry with a generated heraldic picture"
PARAMS = dict(width=1.2, height=1.8)
BUDGET = dict(tris=200, texture=1024, materials=2)
ENGINE = dict(rest_y=2.0)
PRODUCT = dict(collection="dungeon_kit_generated", licence="CC0-1.0", tags=["tapestry", "banner", "wall", "generated"])

PROMPT = ("A medieval heraldic tapestry, portrait format, filling the whole frame edge to edge: a red dragon "
          "rampant on a gold field inside a dark blue woven border with a simple repeating knot pattern. "
          "Flat woven wool texture, visible weave, muted natural dyes, front-on, evenly lit, no perspective, "
          "no wall, no frame, no fringe, no text, no letters, no coat of arms of any real house or nation.")


def checks(p):
    return [size(x=(1.25, 1.35), y=(1.85, 1.95), z=(0.04, 0.1)), tris(max=200), pivot((0.5, None, 1.0)),
            materials(2), texture_size(1024),
            custom("the picture is a picture", lambda ctx: (
                float(np.asarray(ctx.model.materials[0].base).std()) > 0.08,
                "the cloth's base colour varies (std %.2f): it is an image, not a flat fill"
                % np.asarray(ctx.model.materials[0].base).std()))]


def build(p):
    art = gen.image(PROMPT, name="dragon_banner", size=(1024, 1536))
    cloth_mat = gen.material(art, "tapestry_cloth", roughness=0.92, relief=1.5, size=1024)
    w, h, t = p.width, p.height, 0.02
    # a pointed lower edge: a pentagon extruded 20 mm, hanging down from the rod at y=0
    cloth = prism([(-w / 2, 0), (w / 2, 0), (w / 2, -h + 0.25), (0, -h), (-w / 2, -h + 0.25)][::-1], t)
    front = np.abs(cloth.n[:, 2]) > 0.5
    face = np.c_[cloth.v[:, 0] / w + 0.5, -cloth.v[:, 1] / h]
    # the 20 mm edges take a sliver of the picture's border (with real UV area, so they shade)
    edge = np.c_[0.01 + 0.02 * ((cloth.v[:, 0] - cloth.v[:, 1]) / (w + h) + 0.5), 0.01 + 0.02 * (cloth.v[:, 2] / t + 0.5)]
    uv = np.where(front[:, None], face, edge)
    uv[cloth.n[:, 2] > 0.5, 0] = 1 - uv[cloth.n[:, 2] > 0.5, 0]              # the back shows it mirrored
    cloth = cloth.with_uv(uv).moved(0, 0, -t / 2 - 0.025)
    rod_len = w + 0.02
    rod = lathe([(0.02, 0), (0.02, rod_len)], 8).rotated(90, "z").moved(rod_len / 2, 0.02, -0.035)
    knobs = merge(*[lathe([(0.0, -0.04), (0.035, 0), (0.0, 0.04)], 8).rotated(90, "z").moved(x, 0.02, -0.035)
                    for x in (-rod_len / 2, rod_len / 2)])
    return Model((cloth, cloth_mat), (box_uv(merge(rod, knobs), 3.0), iron()))
