"""Torch crackle: a small flame burning, as a seamless loop.

Spec:
  kind: sound
  length: 4.0 s, loop (the end runs into the start with no click)
  channels: mono, spatial (it sits at a wall_torch)
  character: a soft low roar that flutters, with sparse dry pops and snaps on top
  energy: the roar below 600 Hz carries at least 40 %; the pops put at least 3 % above 2 kHz, enough to hear over the roar
  level: peak about -8 dBFS (a bed, quiet under effects)
  use: one looping emitter per wall_torch, max distance about 8 m; bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "torch flame crackle, seamless loop"
PARAMS = dict(seconds=4.0, pops=44, seed=71)
BUDGET = dict(seconds=4.5, kb=420)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["fire", "torch", "loop", "ambience"])


def checks(p):
    return [duration(p.seconds), peak(-9, -7), band(30, 600, at_least=0.4), band(2000, 20000, at_least=0.03)]


def build(p):
    d = p.seconds
    tt = t(d)
    # brown noise shaped in the frequency domain is periodic over its own length, and the flutter
    # uses whole numbers of cycles, so the roar wraps exactly
    roar = noise(d, p.seed, "brown")
    spec = np.fft.rfft(roar)
    f = np.fft.rfftfreq(len(roar), 1 / SR)
    spec *= 1 / (1 + (f / 320.0) ** 2)                # a gentle roll-off, not a wall
    spec[f < 35] = 0
    roar = np.fft.irfft(spec, len(roar))
    flutter = 0.7 + 0.18 * np.sin(2 * np.pi * fit(1.3, d) * tt) + 0.12 * np.sin(2 * np.pi * fit(3.7, d) * tt + 1.0)
    out = 0.28 * roar / np.abs(roar).max() * flutter
    rng = np.random.default_rng(p.seed + 1)
    for _ in range(p.pops):
        length = rng.uniform(0.008, 0.035)
        lo = rng.uniform(1500, 4500)
        pop = bandpass(noise(length, int(rng.integers(1 << 30))), lo, lo * rng.uniform(2.0, 3.5)) * decay(length, length * 0.5)
        place(out, fade(pop, 0.3, 2), rng.uniform(0, d), gain=rng.uniform(0.5, 1.6), wrap=True)
    return Sound(normalize(out, -8), loop=True, bus="sfx", spatial=True)
