"""UI confirm: the sound of accepting a menu choice.

Spec:
  kind: sound
  length: 0.25 to 0.4 s, one-shot
  channels: mono, not spatial
  character: two soft rounded notes rising a fourth (E5 to A5), the second longer; friendly, not shrill
  energy: at least 80 % between 500 Hz and 4 kHz
  level: peak about -6 dBFS
  use: `ui_accept` in cinder.ui menus; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "menu confirm, two rising notes"
PARAMS = dict(note=659.3)
BUDGET = dict(seconds=0.45, kb=45)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["ui", "menu", "confirm"])


def checks(p):
    return [duration(0.25, 0.4), peak(-7, -5), band(500, 4000, at_least=0.8)]


def note(freq, seconds):
    tone = osc(freq, seconds, "tri") + 0.3 * osc(freq * 2, seconds, "sine")
    return lowpass(tone, 3500) * adsr(seconds, 0.004, 0.03, 0.55, seconds * 0.6)


def build(p):
    out = np.zeros(n(0.34))
    place(out, note(p.note, 0.12), 0.0)
    place(out, note(p.note * 4 / 3, 0.24), 0.09)
    return Sound(normalize(fade(out, 1, 30), -6), spatial=False)
