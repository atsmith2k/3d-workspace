"""UI click: the tick of moving between menu items.

Spec:
  kind: sound
  length: 0.05 to 0.09 s, one-shot
  channels: mono, not spatial (interface sounds are mixed centred)
  character: a soft, short, pitched tick dropping from about 1.8 to 1.2 kHz; not harsh
  energy: at least 80 % between 800 Hz and 4 kHz
  level: peak about -8 dBFS (it is heard dozens of times in a menu)
  use: `ui_up` / `ui_down` focus moves in cinder.ui menus; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "menu move tick"
PARAMS = dict(pitch=1800.0)
BUDGET = dict(seconds=0.1, kb=12)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "menu", "click"])


def checks(p):
    return [duration(0.05, 0.09), peak(-9, -7), band(800, 4000, at_least=0.8)]


def build(p):
    d = 0.07
    tone = osc(glide(p.pitch, p.pitch * 0.66, d, 2.0), d, "sine") + 0.25 * osc(glide(p.pitch * 2, p.pitch * 1.32, d, 2.0), d, "sine")
    return Sound(normalize(fade(tone * decay(d, 0.05), 1, 15), -8), spatial=False)
