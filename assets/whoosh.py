"""Whoosh: air cut by a fast swing or a thrown object.

Spec:
  kind: sound
  length: 0.35 to 0.5 s, one-shot
  channels: mono, spatial
  character: breathy noise whose pitch rises then falls (about 500 Hz up to 2.6 kHz and back),
             swelling to the middle; no thump, no tone
  energy: at least 70 % between 400 Hz and 5 kHz
  level: peak about -4 dBFS
  use: a weapon swing, a jump, a fast door; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "air whoosh of a fast swing"
PARAMS = dict(seed=61)
BUDGET = dict(seconds=0.55, kb=60)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["whoosh", "swing", "air"])


def checks(p):
    return [duration(0.35, 0.5), peak(-5, -3), band(400, 5000, at_least=0.7), band(20, 200, at_most=0.05)]


def build(p):
    d = 0.42
    up, down = glide(500, 2600, d * 0.45), glide(2600, 700, d * 0.55)
    centre = np.concatenate([up, down])[: n(d)]
    air = swept_bandpass(noise(d, p.seed), centre, 2.2) + 0.3 * swept_bandpass(noise(d, p.seed + 1), centre * 1.9, 3.0)
    swell = np.sin(np.pi * t(d) / d) ** 1.6
    return Sound(normalize(fade(highpass(air, 250) * swell, 5, 40), -4))
