"""Chest open: a latch click, a wooden creak as the lid lifts, and the lid knocking back.

Spec:
  kind: sound
  length: 0.9 to 1.3 s, one-shot
  channels: mono, spatial
  character: click, then a rising creak (a rough tone sliding from about 180 to 330 Hz with a
             wavering squeak above it), then a hollow wooden knock
  energy: mostly 150 Hz to 3 kHz
  level: peak about -3 dBFS
  use: world-kit `goal` at treasure_chest, or any chest interaction; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "chest latch, creak and lid knock"
PARAMS = dict(seed=41)
BUDGET = dict(seconds=1.4, kb=140)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["chest", "wood", "creak"])


def checks(p):
    return [duration(0.9, 1.3), peak(-4, -2), band(150, 3000, at_least=0.7)]


def build(p):
    out = np.zeros(n(1.1))
    latch = modes([1850, 3100], [0.05, 0.03], [1.0, 0.5], 0.06) + 0.5 * bandpass(noise(0.06, p.seed), 2000, 6000) * decay(0.06, 0.02)
    place(out, latch, 0.0, gain=0.5)
    d = 0.62
    waver = 1 + 0.035 * lowpass(noise(d, p.seed + 1), 14) * 6                 # hinge friction is not steady
    creak = osc(glide(180, 330, d, 1.6) * waver, d, "saw")
    creak = bandpass(creak, 300, 2600) + 0.4 * swept_bandpass(noise(d, p.seed + 2), glide(900, 1900, d), 8)
    grip = np.clip(0.55 + 2.5 * lowpass(noise(d, p.seed + 3), 22), 0.1, 1.0)       # stick and slip
    place(out, creak * grip * np.sin(np.pi * t(d) / d) ** 0.7, 0.09, gain=1.6)
    knock = modes([172, 318, 590, 1040], [0.22, 0.16, 0.1, 0.06], [1.0, 0.7, 0.4, 0.2], 0.3, p.seed)
    knock += 0.4 * lowpass(noise(0.3, p.seed + 4), 1500) * decay(0.3, 0.05)
    place(out, knock, 0.76)
    return Sound(normalize(fade(out, 1, 50), -3))
