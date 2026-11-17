"""Item icons: the pack's icon style, with the first item drawn from its own model's shapes.

Spec:
  kind: sprite
  frames: health_potion, longsword; each 128 x 128 px (shown at 64 and 32)
  style: the model seen front-on, flat palette colour, one highlight, a 6 px near-black outline;
         transparent outside; fills at least 60 % of the frame
  use: inventory, shop and loot screens once cinder.ui draws images; one frame per item, named
       after the item without its prefix
  engine: built ahead; proven as unlit quads
"""
from cadkit.game.sprite import *

KIND = "sprite"
DESCRIPTION = "item icons in the pack style"
PARAMS = dict(size=128)
PRODUCT = dict(collection="frp_interface", licence="ash10 Fantasy RPG Pack licence", tags=["fantasy", "rpg", "icons"])

INK_ = (22, 16, 18)
RED, RED_LIT, GLASS, CORK = (178, 15, 20), (232, 90, 96), (140, 173, 168), (153, 128, 92)
STEEL, STEEL_LIT, IRON, LEATHER = (150, 156, 166), (212, 216, 222), (70, 62, 60), (60, 40, 26)


def checks(p):
    def fills(ctx):
        bad = []
        for k, img in ctx.sheet.frames.items():
            ys, xs = np.nonzero(img[..., 3] > 0.5)
            if max(xs.max() - xs.min(), ys.max() - ys.min()) < 0.6 * img.shape[0]:
                bad.append(k)
        return not bad, f"small in the frame: {bad}" if bad else "every icon spans over 60 % of its frame"
    return [frames("health_potion", "longsword"), frame_size(p.size), custom("fills the frame", fills)]


def health_potion(s):
    c = Canvas(s)
    k = s / 128
    for col, grow in ((INK_, 6 * k), (GLASS, 0)):                # outline pass, then glass
        c.circle((64 * k, 82 * k), 36 * k + grow, fill=col)
        c.rect(((52 * k) - grow, (20 * k) - grow, (76 * k) + grow, 60 * k), fill=col)
        c.rect(((46 * k) - grow, (30 * k) - grow, (82 * k) + grow, 40 * k), radius=3 * k, fill=col)
    c.circle((64 * k, 84 * k), 30 * k, fill=RED)
    c.rect((34 * k, 52 * k, 94 * k, 76 * k), fill=GLASS)          # the level of the draught
    c.polygon([(36 * k, 76 * k), (92 * k, 76 * k), (90 * k, 96 * k), (76 * k, 110 * k), (52 * k, 110 * k), (38 * k, 96 * k)], fill=RED)
    c.circle((52 * k, 92 * k), 6 * k, fill=RED_LIT)
    c.rect((54 * k, 10 * k, 74 * k, 24 * k), radius=3 * k, fill=CORK, outline=INK_, width=3 * k)
    return c.image()


def longsword(s):
    c = Canvas(s)
    k = s / 128
    blade = [(88 * k, 12 * k), (108 * k, 8 * k), (104 * k, 28 * k), (48 * k, 84 * k), (40 * k, 76 * k)]
    c.polygon(blade, fill=STEEL, outline=INK_, width=6 * k)
    c.polygon([(100 * k, 14 * k), (104 * k, 12 * k), (46 * k, 78 * k), (44 * k, 76 * k)], fill=STEEL_LIT)
    c.polygon([(28 * k, 70 * k), (38 * k, 60 * k), (62 * k, 84 * k), (52 * k, 94 * k)], fill=IRON, outline=INK_, width=5 * k)
    c.polygon([(30 * k, 90 * k), (40 * k, 100 * k), (24 * k, 116 * k), (14 * k, 106 * k)], fill=LEATHER, outline=INK_, width=5 * k)
    c.circle((16 * k, 112 * k), 9 * k, fill=IRON, outline=INK_, width=4 * k)
    return c.image()


def build(p):
    return SpriteSheet(dict(health_potion=health_potion(p.size), longsword=longsword(p.size)))
