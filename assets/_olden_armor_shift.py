"""Original procedural armor foley. No recordings or sampled instruments."""
import numpy as np

from _frp import SOUND_PEAK
from cadkit.game.audio import Sound, bandpass, decay, fade, modes, n, noise, normalize, place
from cadkit.game.sound import band, duration, peak


def _friction(rng, length, low, high):
    grain = noise(length, int(rng.integers(1 << 30)), "pink")
    return bandpass(grain, low, high) * np.hanning(n(length))


def _padded(rng, variant):
    length = (0.235, 0.252, 0.220)[variant - 1]
    out = np.zeros(n(length))
    # A broad fold compresses, followed by a shorter strap rubbing back.
    place(out, _friction(rng, length * .68, 120, 780), 0, 1.4)
    place(out, _friction(rng, length * .51, 380, 1700), length * .48, .65)
    leather = _friction(rng, .037, 75, 390)
    place(out, leather, rng.uniform(.025, .048), 1.6)
    return out


def _plate(rng, variant):
    length = (0.215, 0.233, 0.207)[variant - 1]
    out = np.zeros(n(length))
    place(out, _friction(rng, .085, 310, 1600), .002, .7)
    first = rng.uniform(.042, .056)
    second = first + rng.uniform(.060, .080)
    # A restrained pair of broad-plate knocks. Damping truncates each resonance.
    for at, gain in ((first, 1.0), (second, .66)):
        shift = rng.uniform(.82, 1.18)
        freqs = np.array([470, 810, 1470, 2350]) * shift
        contact = modes(freqs, [.092, .072, .048, .038], [.45, .47, .39, .14],
                        .090, seed=int(rng.integers(1 << 30)))
        click = bandpass(noise(.090, int(rng.integers(1 << 30))), 1350, 4400)
        place(out, fade(contact + click * decay(.090, .027), 1.1, 3), at, gain)
    return out


def shift_sound(family, variant):
    rng = np.random.default_rng((42000 if family == "padded" else 53000) + variant)
    samples = (_padded if family == "padded" else _plate)(rng, variant)
    return Sound(normalize(fade(samples, 3, 9), SOUND_PEAK["cloth"]), bus="sfx", spatial=True)


def shift_checks(family):
    checks = [duration(.20, .26), peak(-8.2, -7.8)]
    if family == "padded":
        return checks + [band(80, 1000, at_least=.68, name="fabric body"),
                         band(1800, 20000, at_most=.09, name="muted leather")]
    return checks + [band(300, 1150, at_least=.45, name="damped plate modes"),
                     band(1150, 3900, at_least=.10, name="metal contact")]
