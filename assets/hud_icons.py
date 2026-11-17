"""HUD icons: eight 64 px pictograms for counts and states in a dungeon game's interface.

Spec:
  kind: sprite
  frames: heart, gem, key, coin, star, skull, shield, potion; each 64 x 64 px
  style: flat colour with one highlight and a 4 px dark outline, so each reads at 24 px on any
         background; transparent outside the outline
  atlas: one power-of-two PNG, 2 px between frames, straight alpha
  use: beside the counts in dungeon_hud once cinder.ui can draw images; until then on quads
  engine: built ahead (no UI images or sprites in Cinder 0.1.1); proven as unlit quads
"""
from cadkit.game.sprite import *

KIND = "sprite"
DESCRIPTION = "eight 64 px HUD icons"
PARAMS = dict(size=64)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "icons", "hud", "2d"])

NAMES = ("heart", "gem", "key", "coin", "star", "skull", "shield", "potion")
INK_ = (30, 22, 26)


def checks(p):
    def readable(ctx):
        """Each icon fills its frame (so it survives being shown small) and keeps a clear margin."""
        bad = []
        for k, img in ctx.sheet.frames.items():
            a = img[..., 3] > 0.5
            ys, xs = np.nonzero(a)
            if (xs.max() - xs.min()) < 0.6 * img.shape[1] and (ys.max() - ys.min()) < 0.6 * img.shape[0]:
                bad.append(f"{k} is small in its frame")
            if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
                bad.append(f"{k} touches the frame edge")
        return not bad, "; ".join(bad) or "every icon spans over 60 % of its frame and clears the edge"

    def distinct(ctx):
        """No two icons share a dominant colour and silhouette: the mean colours differ."""
        cols = {k: (img[..., :3] * img[..., 3:4]).sum((0, 1)) / img[..., 3].sum() for k, img in ctx.sheet.frames.items()}
        close = [(a, b) for i, a in enumerate(NAMES) for b in NAMES[i + 1:]
                 if np.abs(cols[a] - cols[b]).max() < 0.04 and
                 np.abs((ctx.sheet.frames[a][..., 3] > 0.5).astype(float) - (ctx.sheet.frames[b][..., 3] > 0.5)).mean() < 0.1]
        return not close, f"icons too alike: {close}" if close else "no two icons share colour and shape"
    return [frames(*NAMES), frame_size(p.size), custom("readable", readable), custom("distinct", distinct)]


def star_points(cx, cy, r, inner=0.45, n=5, rot=-90):
    return [(cx + np.cos(np.radians(rot + i * 180 / n)) * (r if i % 2 == 0 else r * inner),
             cy + np.sin(np.radians(rot + i * 180 / n)) * (r if i % 2 == 0 else r * inner)) for i in range(2 * n)]


def heart():
    c = Canvas(64)
    for col, grow in ((INK_, 4), ((222, 48, 62), 0)):
        c.circle((22, 24), 13 + grow, fill=col).circle((42, 24), 13 + grow, fill=col)
        c.polygon([(8 - grow, 30), (56 + grow, 30), (32, 57 + grow * 1.3)], fill=col)
    c.circle((19, 20), 4.5, fill=(255, 150, 160))
    return c.image()


def gem():
    c = Canvas(64)
    out = [(32, 5), (55, 22), (32, 59), (9, 22)]
    c.polygon(out, fill=(60, 190, 230), outline=INK_, width=4)
    c.polygon([(32, 9), (20, 23), (44, 23)], fill=(170, 235, 250))
    c.polygon([(20, 23), (44, 23), (32, 54)], fill=(40, 150, 200))
    c.line([(12, 22), (52, 22)], INK_, 2)
    return c.image()


def key():
    c = Canvas(64)
    gold, dark = (240, 190, 50), INK_
    c.circle((20, 20), 14, fill=dark).circle((20, 20), 10, fill=gold).circle((20, 20), 4.5, fill=dark)
    c.polygon([(27, 30), (33, 24), (58, 49), (52, 55)], fill=gold, outline=dark, width=4)
    c.polygon([(44, 47), (50, 41), (57, 48), (51, 54)], fill=gold)
    c.polygon([(40, 52), (46, 46), (50, 50), (44, 56)], fill=gold, outline=dark, width=3)
    c.circle((20, 20), 4.5, fill=dark)
    return c.image()


def coin():
    c = Canvas(64)
    c.circle((32, 32), 27, fill=INK_).circle((32, 32), 23, fill=(245, 190, 40)).circle((32, 32), 17, fill=(215, 150, 20))
    c.polygon(star_points(32, 33, 13), fill=(255, 225, 110))
    return c.image()


def star():
    c = Canvas(64)
    c.polygon(star_points(32, 34, 28), fill=(255, 215, 60), outline=INK_, width=4)
    c.polygon(star_points(32, 34, 13), fill=(255, 240, 150))
    return c.image()


def skull():
    c = Canvas(64)
    bone = (232, 228, 214)
    c.circle((32, 27), 23, fill=INK_).rect((18, 34, 46, 58), radius=5, fill=INK_)
    c.circle((32, 27), 19, fill=bone).rect((22, 36, 42, 54), radius=3, fill=bone)
    c.circle((24, 28), 6, fill=INK_).circle((40, 28), 6, fill=INK_)
    c.polygon([(32, 34), (28, 41), (36, 41)], fill=INK_)
    for x in (27, 32, 37):
        c.line([(x, 46), (x, 54)], INK_, 2)
    return c.image()


def shield():
    c = Canvas(64)
    out = [(32, 5), (55, 13), (53, 36), (32, 59), (11, 36), (9, 13)]
    c.polygon(out, fill=(150, 156, 168), outline=INK_, width=4)
    c.polygon([(32, 12), (48, 18), (47, 34), (32, 51), (17, 34), (16, 18)], fill=(56, 104, 200))
    c.polygon([(32, 12), (32, 51), (17, 34), (16, 18)], fill=(84, 136, 226))
    return c.image()


def potion():
    c = Canvas(64)
    c.circle((32, 40), 21, fill=INK_).rect((23, 8, 41, 30), radius=3, fill=INK_)
    c.circle((32, 40), 17, fill=(200, 230, 240)).rect((27, 12, 37, 30), fill=(200, 230, 240))
    c.circle((32, 42), 14, fill=(214, 60, 120))
    c.rect((18, 26, 46, 40), fill=(200, 230, 240))                 # liquid level
    c.circle((32, 40), 17, outline=INK_, width=0)
    c.circle((32, 42), 14, fill=None)
    c.polygon([(19, 40), (45, 40), (43, 50), (36, 55), (28, 55), (21, 50)], fill=(214, 60, 120))
    c.rect((25, 6, 39, 13), radius=2, fill=(150, 100, 60), outline=INK_, width=2)
    c.circle((26, 46), 3, fill=(255, 170, 200))
    return c.image()


def build(p):
    return SpriteSheet({n: globals()[n]() for n in NAMES})
