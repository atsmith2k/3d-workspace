"""Iron key: a heavy door key, lying flat.

Spec:
  kind: prop
  size: 0.13 x 0.012 x 0.05 m
  pivot: on Y=0, at the middle of its length; it lies along X, bow at -X, bit at +X
  budget: 800 triangles, one material, no textures
  materials: dark iron (metallic, rough)
  features: a ring bow 50 mm across; a round shank; a bit of two teeth of different lengths;
            a collar between bow and shank
  use: items sub-pack (keys and quest items); opens vil_door and the dungeon doors; icon
       frame `key_iron`
  engine: no body (a pickup); rest_y 0
"""
from _frp_items import *

KIND = "prop"
DESCRIPTION = "iron door key"
PARAMS = dict(length=0.13)
BUDGET = ITEM_BUDGET
ENGINE = dict(rest_y=0.0)
PRODUCT = item("key_iron", "key", "quest", stack=1, opens="door")


def checks(p):
    def teeth(ctx):
        v = ctx.model.parts[0][0].v
        bit = v[(v[:, 0] > p.length / 2 - 0.035) & (v[:, 2] > 0.008)]
        reach = np.unique(np.round(bit[:, 2], 3))
        return len(reach) >= 2, f"the bit's teeth reach {', '.join(f'{r * 1000:.0f}' for r in reach[-2:])} mm: two lengths"
    return item_checks(p.length, 0.012, (0.045, 0.055), 1, tol=0.003) + [custom("two teeth", teeth)]


def build(p):
    L, t = p.length, 0.006
    x0 = -L / 2 + 0.025
    bow = torus(0.019, t, 14, 6).moved(x0, t, 0)
    shank = along(cylinder(0.005, L - 0.05 + 0.006, 7), (x0 + 0.019, t, 0), (L / 2, t, 0))
    collar = along(cylinder(0.006, 0.008, 7), (x0 + 0.024, t, 0), (x0 + 0.032, t, 0))
    bits = merge(block(0.008, 0.008, 0.02, L / 2 - 0.008, t - 0.004, 0.012), block(0.008, 0.008, 0.013, L / 2 - 0.024, t - 0.004, 0.0085))
    return Model((merge(bow, shank, collar, bits), flat_material("frp_key_iron", "iron", roughness=0.55, metallic=1.0)))
