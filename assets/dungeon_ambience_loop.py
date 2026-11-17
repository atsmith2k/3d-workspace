"""Dungeon ambience: a slow, dark music bed that loops seamlessly.

Spec:
  kind: sound
  length: 32.0 s, loop: eight 4 s bars; every tone completes whole cycles and every tail wraps
          round, so the end runs into the start
  channels: stereo, not spatial, streamed
  character: a low D drone with its fifth, a slow breathing pad, and sparse bell notes from
             D minor (D F G A C) falling in a wide stereo field with a long reverb
  energy: at least 30 % below 300 Hz (the drone); bells between 290 Hz and 1.2 kHz
  level: peak about -4 dBFS
  use: background music for dungeon levels; bus music
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, custom, duration, peak

KIND = "sound"
DESCRIPTION = "dark dungeon music bed, seamless 32 s loop"
PARAMS = dict(bars=8, bar=4.0, seed=81)
BUDGET = dict(seconds=34, kb=6400)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["music", "ambience", "loop", "dark"])

D2, A2 = 73.42, 110.0
SCALE = (293.66, 349.23, 392.0, 440.0, 523.25, 587.33)          # D4 F4 G4 A4 C5 D5


def checks(p):
    return [duration(p.bars * p.bar), peak(-5, -3), band(30, 300, at_least=0.3), band(280, 1300, at_least=0.05),
            custom("stereo field", lambda ctx: (
                0.3 < float(np.corrcoef(ctx.sound.samples[:, 0], ctx.sound.samples[:, 1])[0, 1]) < 0.995,
                "left and right correlate %.2f: above 0.3 it survives a mono speaker, below 0.995 it has width"
                % np.corrcoef(ctx.sound.samples[:, 0], ctx.sound.samples[:, 1])[0, 1]))]


def build(p):
    d = p.bars * p.bar
    tt = t(d)
    rng = np.random.default_rng(p.seed)

    def tone(freq, shape="sine", phase=0.0):
        return osc(fit(freq, d), d, shape, phase)

    breathe = 0.65 + 0.35 * np.sin(2 * np.pi * tt / (2 * p.bar) - 1.2)            # one breath per two bars
    drone = tone(D2) + 0.5 * tone(D2 * 2, "tri") + 0.45 * tone(A2) + 0.2 * tone(D2 * 3)
    left = drone * (0.8 + 0.2 * np.sin(2 * np.pi * tt / d * 3))
    right = drone * (0.8 + 0.2 * np.sin(2 * np.pi * tt / d * 3 + 1.5))
    # pad: detuned saws an octave up, filtered in the frequency domain (periodic, so it wraps)
    pad = sum(tone(f, "saw", ph) for f, ph in ((D2 * 2 * 0.996, 0.0), (D2 * 2 * 1.004, 0.3), (A2 * 2 * 1.002, 0.6)))
    spec = np.fft.rfft(pad)
    fr = np.fft.rfftfreq(len(pad), 1 / SR)
    spec *= 1 / (1 + (fr / 500.0) ** 4)
    pad = np.fft.irfft(spec, len(pad)) * breathe
    left, right = left + 0.5 * pad, right + 0.5 * pad
    bed = np.stack([left, right], 1) * 0.5           # dry: the same phase in both ears, safe in mono
    mix = np.zeros_like(bed)                         # bells only: these go through the reverb
    # bells: one or two per bar, off the beat, long tails that wrap
    for bar in range(p.bars):
        for _ in range(int(rng.integers(1, 3))):
            f = SCALE[int(rng.integers(len(SCALE)))]
            length = 3.2
            bell = modes([f, f * 2.0, f * 3.01, f * 4.2], [length, length * 0.5, length * 0.3, length * 0.18],
                         [1.0, 0.35, 0.18, 0.08], length) * adsr(length, 0.01, 0.1, 1.0, 0.4)
            at = bar * p.bar + rng.choice([0.5, 1.0, 1.5, 2.5, 3.0])
            pan = rng.uniform(-0.7, 0.7)
            for c, g in enumerate(stereo(np.ones(1), pan)[0]):
                place(mix[:, c], bell, at, gain=0.28 * g, wrap=True)
    # A reverb gives a steady tone an arbitrary phase per channel: on the drone that put left
    # and right out of phase (correlation -0.3), so only the bells are sent through it.
    wet = np.stack([reverb(mix[:, 0], 3.0, 0.5, p.seed + 5, 3200, wrap=True),
                    reverb(mix[:, 1], 3.0, 0.5, p.seed + 6, 3200, wrap=True)], 1)
    return Sound(normalize(bed + 2.2 * wet, -4), loop=True, bus="music", spatial=False, streamed=True)
