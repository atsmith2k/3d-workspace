"""Crate impact: a wooden box knocking against stone or another crate.

Spec:
  kind: sound
  length: 0.3 to 0.5 s, one-shot
  channels: mono, spatial
  character: a hollow woody knock: a few short-lived partials between 190 and 1250 Hz over a
             burst of low noise; no metallic ring
  energy: at least 70 % between 100 Hz and 2 kHz
  level: peak about -3 dBFS
  use: physics contact between dynamic bodies (wooden_crate, oak_barrel); bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "wooden crate knock"
PARAMS = dict(seed=51)
BUDGET = dict(seconds=0.55, kb=60)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["impact", "wood", "physics"])


def checks(p):
    return [duration(0.3, 0.5), peak(-4, -2), band(100, 2000, at_least=0.7), band(5000, 20000, at_most=0.08)]


def build(p):
    d = 0.4
    knock = modes([191, 407, 723, 1251], [0.26, 0.17, 0.11, 0.07], [1.0, 0.75, 0.45, 0.25], d, p.seed)
    burst = lowpass(noise(d, p.seed + 1), 1800) * decay(d, 0.045)
    rattle = bandpass(noise(d, p.seed + 2), 1500, 3500) * decay(d, 0.12) * 0.12
    return Sound(normalize(fade(knock + 0.8 * burst + rattle, 0.5, 40), -3))
