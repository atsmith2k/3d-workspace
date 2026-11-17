"""Footstep on stone: a dull heel thud with a little grit.

Spec:
  kind: sound
  length: 0.18 to 0.3 s, one-shot
  channels: mono, spatial
  character: low and short; a soft thump under a brief gritty scrape, no ring
  energy: at least half below 800 Hz
  level: peak about -6 dBFS (it repeats constantly, so it sits under everything else)
  use: one per step of walk and run on dungeon floors; vary pitch a little in the game; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "footstep on stone"
PARAMS = dict(seed=11)
BUDGET = dict(seconds=0.35, kb=40)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["footstep", "stone"])


def checks(p):
    return [duration(0.18, 0.3), peak(-7, -5), band(40, 800, at_least=0.5), band(6000, 20000, at_most=0.1)]


def build(p):
    d = 0.24
    thump = modes([82, 131, 205], [0.11, 0.08, 0.05], [1.0, 0.6, 0.3], d)
    body = lowpass(noise(d, p.seed), 900) * decay(d, 0.07)
    grit = bandpass(noise(d, p.seed + 1), 1800, 5200) * decay(d, 0.05) * adsr(d, 0.004, 0.03, 0.3, 0.05)
    return Sound(normalize(fade(thump + 0.9 * body + 0.35 * grit, 1, 30), -6))
