"""Original shallow-water foley. Seeded noise and oscillators provide every layer."""
import numpy as np

from _frp import SOUND_PEAK
from cadkit.game.audio import Sound, bandpass, decay, fade, glide, n, noise, normalize, osc, place
from cadkit.game.sound import band, custom, duration, peak


def water_step(variant):
    rng = np.random.default_rng(81000 + variant)
    length = (0.384, 0.402, 0.417, 0.392)[variant - 1]
    out = np.zeros(n(length))

    def spray(seconds, low, high):
        x = bandpass(noise(seconds, int(rng.integers(1 << 30))), low, high)
        return x / np.sqrt(np.mean(x*x))

    # Heel loading the bed, the initial water slap, then water thrown forward off the toe.
    heel = spray(.080, 80, 380) * decay(.080, .10)
    place(out, fade(heel, 3, 8), .003, .70)
    slap = spray(.105, 850, 6800) * decay(.105, .17)
    place(out, fade(slap, 4, 10), rng.uniform(.010, .019), .71)
    wash = spray(.10, 500, 3000) * np.hanning(n(.10))
    place(out, wash, rng.uniform(.066, .084), .40)

    # Short upward glides model entrained air bubbles after displaced water falls back.
    for i, fraction in enumerate((.43, .55, .66, .78, .89)):
        seconds = rng.uniform(.030, .046)
        f0 = rng.uniform(480, 1200)
        bubble = osc(glide(f0, f0 * rng.uniform(1.28, 1.72), seconds), seconds)
        droplet = (.85 * bubble + .15 * spray(seconds, 1100, 4400)) * decay(seconds, .075)
        place(out, fade(droplet, 2, 4), length*fraction + rng.uniform(-.006, .006), .78 - .105*i)
    return Sound(normalize(fade(out, 2, 8), SOUND_PEAK["step"]), bus="sfx", spatial=True)


def water_checks():
    def settling(ctx):
        x = ctx.sound.samples
        tail = float(np.sum(x[n(.20):]**2) / np.sum(x**2))
        return .012 < tail < .35, f"{tail:.1%} of energy in settling droplets after 200 ms"

    return [duration(.37, .43), peak(-8.2, -7.8),
            band(70, 650, at_least=.07, name="boot and bed"),
            band(900, 6800, at_least=.30, name="water slap"),
            custom("settling ripples", settling)]
