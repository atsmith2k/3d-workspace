"""UI frames: 9-slice art for a panel and a button in three states.

Spec:
  kind: sprite
  frames: panel 48 x 48; button, button_hot, button_pressed 48 x 48
  9-slice: panel borders 16 px; buttons 12 px: corners keep their size, edges stretch one way,
           the centre stretches both, so one small image frames a box of any size
  style: the dungeon HUD's warm dark palette: near-black fill, a bronze rim, a soft inner
         highlight; hot is lighter, pressed is darker with the highlight moved to the bottom
  use: backgrounds for cinder.ui panels and buttons once it has an image node with 9-slice
  engine: built ahead; proven as unlit quads
"""
from cadkit.game.sprite import *

KIND = "sprite"
DESCRIPTION = "9-slice panel and three-state button"
PARAMS = dict(size=48)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "9-slice", "panel", "button", "2d"])

RIM, RIM_LIT = (150, 98, 44), (214, 152, 76)


def checks(p):
    def stretchable(ctx):
        """The centre row and column of each frame are uniform, so stretching them shows no seam."""
        bad = []
        for k, b in ctx.sheet.slices.items():
            img = ctx.sheet.frames[k]
            mid = img[b[1]:img.shape[0] - b[3], b[0]:img.shape[1] - b[2]]
            if np.abs(mid - mid[:1, :1]).max() > 0.02:
                bad.append(k)
        return not bad, f"centre not uniform: {bad}" if bad else "every centre region is one flat colour"
    return [frames("panel", "button", "button_hot", "button_pressed"), frame_size(p.size),
            nine_slice("panel"), nine_slice("button"), nine_slice("button_hot"), nine_slice("button_pressed"),
            custom("stretches cleanly", stretchable)]


def frame(size, radius, fill, rim, lit_top=True):
    c = Canvas(size)
    c.rect((0, 0, size, size), radius=radius, fill=(18, 12, 8))                       # outer dark edge
    c.rect((2, 2, size - 2, size - 2), radius=radius - 2, fill=rim)                  # bronze rim
    c.rect((5, 5, size - 5, size - 5), radius=radius - 4, fill=fill)                 # body
    y = 6 if lit_top else size - 8
    c.line([(radius, y), (size - radius, y)], tuple(min(255, v + 34) for v in fill), 2)   # inner highlight
    return c.image()


def build(p):
    s = p.size
    return SpriteSheet(
        dict(panel=frame(s, 12, (26, 22, 20), RIM), button=frame(s, 9, (58, 50, 44), RIM),
             button_hot=frame(s, 9, (84, 72, 60), RIM_LIT), button_pressed=frame(s, 9, (40, 34, 30), RIM, lit_top=False)),
        slices=dict(panel=(16, 16, 16, 16), button=(12, 12, 12, 12), button_hot=(12, 12, 12, 12),
                    button_pressed=(12, 12, 12, 12)))
