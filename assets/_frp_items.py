"""Items and loot: what everything in an inventory shares.

An item is a world model (lying on a table, dropped on the ground) and an icon. The model is
small, so it is flat palette colours with no textures: twenty items on a shelf then cost no
samplers. It lies or stands as it would be found, origin on what it rests on. The icon is the
frame of `ui_item_icons` named after the item without its prefix, drawn from the same shapes
and colours; `PRODUCT["gameplay"]["icon"]` names it, and `ui_item_icons` checks that every
`itm_` asset has one.
"""
from _frp import *

ITEM_BUDGET = dict(BUDGET_OF["small_prop"], materials=3)


def item(name, *tags, **gameplay):
    """PRODUCT for an item: the items sub-pack, with its icon frame named after it."""
    return product("items", *tags, gameplay=dict(icon=f"ui_item_icons:{name}", **gameplay))


def item_checks(x, y, z, mats, tol=0.006):
    """Size, the small-prop budget, standing or lying on Y=0, draw calls, and no textures."""
    def untextured(ctx):
        n = sum(len(m.textures()) for m in ctx.model.materials)
        return n == 0, f"{n} textures: an item costs a scene no samplers"
    return [size(x=x, y=y, z=z, tol=tol), tris(max=ITEM_BUDGET["tris"]), pivot((None, 0.0, None)), materials(mats),
            custom("no textures", untextured)]


def flask(radius, height, draught, glow):
    """A stoppered flask: (body filled with the draught, glass neck, cork). The body shows its
    contents as its colour, because Cinder draws no transparency."""
    r, k = radius, height / 0.19
    body = merge(lathe([(r * 0.6, 0.0), (r, 0.03 * k), (r, 0.075 * k), (r * 0.55, 0.115 * k), (0.02, 0.125 * k)], 12),
                 disc(r * 0.6, 0.0, 12, up=False))
    neck = lathe([(0.02, 0.125 * k), (0.02, 0.155 * k), (0.028, 0.165 * k), (0.028, 0.17 * k), (0.019, 0.17 * k)], 12)
    cork = merge(lathe([(0.019, 0.165 * k), (0.021, height)], 8), disc(0.021, height, 8))
    return Model((body, flat_material(f"frp_draught_{draught}", draught, roughness=0.2, emissive=glow, strength=0.4)),
                 (neck, flat_material("frp_glass", "glass", roughness=0.15)),
                 (cork, flat_material("frp_cork", "wood_light", roughness=0.9)))
