"""Item icons: the pack's icon style, with the first item drawn from its own model's shapes.

Spec:
  kind: sprite
  frames: one per itm_ asset (health_potion, mana_potion, bread, cheese, key_iron, coin_pouch,
          candle, tankard, scroll) and longsword; each 128 x 128 px (shown at 64 and 32)
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
BLUE, BLUE_LIT, CRUST, CRUST_LIT, CRUMB = (36, 82, 204), (120, 160, 240), (128, 80, 40), (168, 114, 62), (206, 196, 170)
CHEESE, RIND, IRON_LIT, LEATHER_LIT, GOLD = (204, 168, 70), (148, 108, 38), (120, 116, 118), (118, 78, 46), (200, 158, 60)
TALLOW, FLAME, WOOD, PARCHMENT, RIBBON = (214, 204, 172), (255, 150, 40), (112, 78, 48), (198, 184, 150), (140, 34, 30)


def checks(p):
    def fills(ctx):
        bad = []
        for k, img in ctx.sheet.frames.items():
            ys, xs = np.nonzero(img[..., 3] > 0.5)
            if max(xs.max() - xs.min(), ys.max() - ys.min()) < 0.6 * img.shape[0]:
                bad.append(k)
        return not bad, f"small in the frame: {bad}" if bad else "every icon spans over 60 % of its frame"
    def every_item(ctx):
        from pathlib import Path
        items = sorted(f.stem[4:] for f in Path(__file__).parent.glob("itm_*.py"))
        missing = [i for i in items if i not in ctx.sheet.frames]
        return not missing, f"no icon for: {missing}" if missing else f"all {len(items)} itm_ assets have an icon"
    return [frames(*ICONS), frame_size(p.size), custom("fills the frame", fills), custom("an icon per item", every_item)]


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


def mana_potion(s):
    c = Canvas(s)
    k = s / 128
    for col, grow in ((INK_, 6 * k), (GLASS, 0)):                # taller and narrower than the health potion
        c.ellipse((64 * k, 80 * k), 27 * k + grow, 36 * k + grow, fill=col)
        c.rect(((54 * k) - grow, (14 * k) - grow, (74 * k) + grow, 52 * k), fill=col)
        c.rect(((48 * k) - grow, (24 * k) - grow, (80 * k) + grow, 33 * k), radius=3 * k, fill=col)
    c.ellipse((64 * k, 84 * k), 21 * k, 28 * k, fill=BLUE)
    c.rect((40 * k, 46 * k, 88 * k, 68 * k), fill=GLASS)
    c.polygon([(44 * k, 68 * k), (84 * k, 68 * k), (84 * k, 92 * k), (74 * k, 110 * k), (54 * k, 110 * k), (44 * k, 92 * k)], fill=BLUE)
    c.circle((55 * k, 86 * k), 5 * k, fill=BLUE_LIT)
    c.rect((56 * k, 6 * k, 72 * k, 18 * k), radius=3 * k, fill=CORK, outline=INK_, width=3 * k)
    return c.image()


def bread(s):
    c = Canvas(s)
    k = s / 128
    c.ellipse((64 * k, 72 * k), 54 * k, 40 * k, fill=CRUST, outline=INK_, width=6 * k)
    c.ellipse((56 * k, 58 * k), 30 * k, 14 * k, fill=CRUST_LIT)
    c.line([(34 * k, 74 * k), (94 * k, 62 * k)], CRUMB, 7 * k)
    c.line([(58 * k, 46 * k), (72 * k, 92 * k)], CRUMB, 7 * k)
    return c.image()


def cheese(s):
    c = Canvas(s)
    k = s / 128
    c.polygon([(10 * k, 84 * k), (112 * k, 44 * k), (118 * k, 64 * k), (118 * k, 98 * k), (10 * k, 108 * k)], fill=CHEESE, outline=INK_, width=6 * k)
    c.polygon([(10 * k, 84 * k), (112 * k, 44 * k), (118 * k, 64 * k), (14 * k, 90 * k)], fill=RIND, outline=INK_, width=4 * k)
    for x, y, r in ((44, 96, 6), (74, 84, 8), (98, 90, 5)):
        c.circle((x * k, y * k), r * k, fill=RIND)
    return c.image()


def key_iron(s):
    c = Canvas(s)
    k = s / 128
    c.line([(46 * k, 82 * k), (106 * k, 22 * k)], INK_, 20 * k)
    c.polygon([(92 * k, 22 * k), (110 * k, 40 * k), (122 * k, 28 * k), (104 * k, 10 * k)], fill=INK_)
    c.polygon([(76 * k, 38 * k), (90 * k, 52 * k), (98 * k, 44 * k), (84 * k, 30 * k)], fill=INK_)
    c.circle((34 * k, 94 * k), 28 * k, fill=INK_)
    c.line([(46 * k, 82 * k), (106 * k, 22 * k)], IRON_LIT, 8 * k)
    c.polygon([(96 * k, 24 * k), (108 * k, 36 * k), (116 * k, 28 * k), (104 * k, 16 * k)], fill=IRON_LIT)
    c.polygon([(80 * k, 40 * k), (88 * k, 48 * k), (93 * k, 43 * k), (85 * k, 35 * k)], fill=IRON_LIT)
    c.circle((34 * k, 94 * k), 22 * k, fill=IRON_LIT)
    c.circle((34 * k, 94 * k), 11 * k, fill=INK_)
    return c.image()


def coin_pouch(s):
    c = Canvas(s)
    k = s / 128
    c.ellipse((64 * k, 84 * k), 46 * k, 36 * k, fill=LEATHER_LIT, outline=INK_, width=6 * k)
    c.polygon([(44 * k, 52 * k), (84 * k, 52 * k), (96 * k, 16 * k), (64 * k, 26 * k), (32 * k, 16 * k)], fill=LEATHER_LIT, outline=INK_, width=6 * k)
    c.rect((40 * k, 44 * k, 88 * k, 56 * k), radius=5 * k, fill=CRUMB, outline=INK_, width=4 * k)
    c.ellipse((50 * k, 76 * k), 14 * k, 9 * k, fill=(150, 104, 64))
    c.circle((86 * k, 100 * k), 9 * k, fill=GOLD, outline=INK_, width=3 * k)
    return c.image()


def candle(s):
    c = Canvas(s)
    k = s / 128
    c.ellipse((64 * k, 108 * k), 46 * k, 12 * k, fill=IRON, outline=INK_, width=6 * k)
    c.rect((50 * k, 44 * k, 78 * k, 106 * k), radius=4 * k, fill=TALLOW, outline=INK_, width=6 * k)
    c.rect((56 * k, 50 * k, 62 * k, 96 * k), radius=2 * k, fill=(240, 232, 208))
    c.polygon([(64 * k, 6 * k), (78 * k, 30 * k), (64 * k, 44 * k), (50 * k, 30 * k)], fill=FLAME, outline=INK_, width=5 * k)
    c.polygon([(64 * k, 20 * k), (70 * k, 31 * k), (64 * k, 38 * k), (58 * k, 31 * k)], fill=(255, 226, 140))
    return c.image()


def tankard(s):
    c = Canvas(s)
    k = s / 128
    c.rect((84 * k, 44 * k, 118 * k, 98 * k), radius=12 * k, fill=IRON, outline=INK_, width=6 * k)
    c.rect((92 * k, 56 * k, 106 * k, 86 * k), radius=5 * k, fill=INK_)
    c.polygon([(18 * k, 22 * k), (92 * k, 22 * k), (96 * k, 114 * k), (14 * k, 114 * k)], fill=WOOD, outline=INK_, width=6 * k)
    for x in (38, 56, 74):
        c.line([(x * k, 28 * k), (x * k, 110 * k)], (74, 50, 30), 3 * k)
    for y in (38, 96):
        c.rect((14 * k, (y - 6) * k, 96 * k, (y + 6) * k), fill=IRON, outline=INK_, width=3 * k)
    c.ellipse((55 * k, 20 * k), 37 * k, 9 * k, fill=(232, 222, 196), outline=INK_, width=4 * k)
    return c.image()


def scroll(s):
    c = Canvas(s)
    k = s / 128
    c.polygon([(18 * k, 78 * k), (92 * k, 20 * k), (112 * k, 46 * k), (38 * k, 104 * k)], fill=PARCHMENT, outline=INK_, width=6 * k)
    c.line([(34 * k, 78 * k), (94 * k, 31 * k)], (236, 226, 200), 5 * k)
    c.circle((28 * k, 91 * k), 15 * k, fill=PARCHMENT, outline=INK_, width=5 * k)
    c.circle((28 * k, 91 * k), 6 * k, fill=INK_)
    c.polygon([(56 * k, 46 * k), (72 * k, 34 * k), (92 * k, 60 * k), (76 * k, 72 * k)], fill=RIBBON, outline=INK_, width=4 * k)
    c.circle((72 * k, 50 * k), 8 * k, fill=RIBBON, outline=INK_, width=3 * k)
    return c.image()


ICONS = dict(health_potion=health_potion, longsword=longsword, mana_potion=mana_potion, bread=bread, cheese=cheese,
             key_iron=key_iron, coin_pouch=coin_pouch, candle=candle, tankard=tankard, scroll=scroll)


def build(p):
    return SpriteSheet({name: draw(p.size) for name, draw in ICONS.items()})
