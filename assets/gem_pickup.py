"""Gem pickup: a bright two-note chime, the reward sound for collecting a gem.

Spec:
  kind: sound
  length: 0.6 to 0.9 s, one-shot
  channels: mono, spatial (it plays where the gem was)
  character: bell-like, bright: a rising fifth (E6 then B6) with glassy partials and a short tail
  energy: most of it above 1 kHz
  level: peak about -3 dBFS
  use: world-kit `pickup`; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "bright two-note chime for a gem pickup"
PARAMS = dict(note=1318.5, seed=1)
BUDGET = dict(seconds=1.0, kb=100)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["pickup", "chime", "reward"])


def checks(p):
    return [duration(0.6, 0.9), peak(-4, -2), band(1000, 12000, at_least=0.85)]


def bell(freq, seconds, seed):
    ratios = (1.0, 2.76, 5.4, 8.93)                 # a small bell's inharmonic partials
    return modes([freq * r for r in ratios], [seconds, seconds * 0.6, seconds * 0.35, seconds * 0.2],
                 [1.0, 0.5, 0.25, 0.12], seconds, seed) * adsr(seconds, 0.002, 0.02, 1.0, 0.02)


def build(p):
    out = np.zeros(n(0.8))
    place(out, bell(p.note, 0.5, p.seed), 0.0)
    place(out, bell(p.note * 1.5, 0.68, p.seed + 1), 0.11, gain=0.9)
    return Sound(normalize(fade(out, 1, 60), -3), bus="sfx", spatial=True)
