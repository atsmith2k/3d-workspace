"""Coin spin: an eight-frame sprite sheet of a gold coin turning about its vertical axis.

Spec:
  kind: sprite
  frames: coin_0 .. coin_7, each 64 x 64 px
  animation: spin, 8 frames at 12 fps, looping (0.67 s a turn)
  style: matches the hud_icons coin: dark outline, gold face with a star; the face narrows to
         an edge-on sliver and widens again; the star shows only when the face is wide enough
  use: a 2D pickup or a HUD flourish when a coin is collected
  engine: built ahead (no sprite renderer in Cinder 0.1.1); proven as unlit quads, one per frame
"""
from cadkit.game.sprite import *

KIND = "sprite"
DESCRIPTION = "eight-frame spinning coin sprite sheet"
PARAMS = dict(size=64, count=8, fps=12)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["sprite", "animation", "coin", "2d"])


def checks(p):
    def turns(ctx):
        """The drawn width falls to a sliver and comes back: it reads as a turn, not a pulse."""
        widths = []
        for i in range(ctx.params["count"]):
            cols = (ctx.sheet.frames[f"coin_{i}"][..., 3] > 0.5).any(0)
            widths.append(int(cols.sum()))
        ok = widths[0] == max(widths) and min(widths) <= 14 and widths[1] < widths[0] and widths[-1] < widths[0]
        return ok, f"widths in pixels over the turn: {widths}"
    return [frames(*[f"coin_{i}" for i in range(p.count)]), frame_size(p.size), animation("spin", p.count, p.fps),
            custom("turns", turns)]


def face(size, turn):
    """One frame: `turn` is the fraction of a full rotation."""
    c = Canvas(size)
    cx = cy = size / 2
    k = abs(np.cos(2 * np.pi * turn))                     # 1 face-on, 0 edge-on
    rx = max(3.0, 27 * k)
    edge = 3.5 * (1 - k)                                  # the rim shows as the coin turns away
    side = 1 if np.sin(2 * np.pi * turn) >= 0 else -1
    c.ellipse((cx, cy), rx + edge, 27, fill=(30, 22, 26))
    c.ellipse((cx + side * edge * 0.5, cy), max(1.5, rx - 4 + edge * 0.4), 23, fill=(190, 130, 20))   # rim
    c.ellipse((cx - side * edge * 0.5, cy), max(1.2, rx - 4), 23, fill=(245, 190, 40))               # face
    if rx > 12:
        c.ellipse((cx - side * edge * 0.5, cy), max(1.0, rx - 10), 17, fill=(215, 150, 20))
        pts = [(cx - side * edge * 0.5 + np.cos(np.radians(-90 + i * 36)) * (13 if i % 2 == 0 else 5.8) * k,
                cy + 1 + np.sin(np.radians(-90 + i * 36)) * (13 if i % 2 == 0 else 5.8)) for i in range(10)]
        c.polygon(pts, fill=(255, 225, 110))
    return c.image()


def build(p):
    names = [f"coin_{i}" for i in range(p.count)]
    return SpriteSheet({n: face(p.size, i / (2 * p.count)) for i, n in enumerate(names)},
                       animations=dict(spin=dict(frames=names, fps=p.fps, loop=True)))
