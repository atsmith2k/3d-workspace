"""Pressure plate press: a click and a metallic clunk as the plate sinks and a mechanism catches.

Spec:
  kind: sound
  length: 0.25 to 0.4 s, one-shot
  channels: mono, spatial
  character: a sharp tick, then 40 ms later a short ringing clunk of bronze on stone with a low thump
  energy: spread: some below 300 Hz (the thump), most between 300 Hz and 6 kHz (the clunk)
  level: peak about -3 dBFS
  use: world-kit `trigger_held` on pressure_plate; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "pressure plate click and clunk"
PARAMS = dict(seed=31)
BUDGET = dict(seconds=0.45, kb=50)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["mechanism", "trigger", "metal"])


def checks(p):
    return [duration(0.25, 0.4), peak(-4, -2), band(300, 6000, at_least=0.5), band(40, 300, at_least=0.05)]


def build(p):
    out = np.zeros(n(0.34))
    tick = bandpass(noise(0.02, p.seed), 2200, 7000) * decay(0.02, 0.012)
    place(out, tick, 0.0, gain=0.7)
    clunk = modes([412, 1127, 2213, 3340], [0.2, 0.14, 0.09, 0.05], [1.0, 0.55, 0.3, 0.15], 0.28, p.seed)
    thump = modes([96, 148], [0.16, 0.1], [1.0, 0.5], 0.28)
    place(out, (clunk + 0.8 * thump) * adsr(0.28, 0.001, 0.02, 1.0, 0.05), 0.04)
    return Sound(normalize(fade(out, 1, 30), -3))
