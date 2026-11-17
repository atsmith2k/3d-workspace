"""Sound synthesis in numpy: `from cadkit.game.audio import *` in a sound script.

Everything is a float array at 48 kHz (Cinder mixes at 48 kHz), mono (N,) or stereo (N, 2),
nominally in -1..1. Every random source takes a seed. A sound script returns

    Sound(samples, loop=False, bus="sfx", spatial=True)

One-shots are mono (they are placed in 3D); music and ambience are stereo and not spatial.
A loop is the whole file (Cinder has no loop points), so its end must run into its start.
"""
from dataclasses import dataclass

import numpy as np
from scipy import signal

SR = 48000


@dataclass
class Sound:
    samples: np.ndarray
    loop: bool = False
    bus: str = "sfx"                  # the game's bus name: "sfx" or "music" in Cinder's sample
    spatial: bool = True              # placed in 3D (mono) or mixed centred (stereo allowed)
    streamed: bool = False            # decode while playing (music) instead of at load

    def __post_init__(self):
        self.samples = np.asarray(self.samples, np.float64)

    @property
    def channels(self):
        return 1 if self.samples.ndim == 1 else self.samples.shape[1]

    @property
    def duration(self):
        return len(self.samples) / SR


# ---------------------------------------------------------------- sources

def n(seconds):
    return int(round(seconds * SR))


def t(seconds):
    return np.arange(n(seconds)) / SR


def osc(freq, seconds, shape="sine", phase=0.0):
    """An oscillator. `freq` is a number or a per-sample array (then `seconds` is ignored)."""
    f = np.full(n(seconds), float(freq)) if np.isscalar(freq) else np.asarray(freq, float)
    ph = phase + np.cumsum(f) / SR
    if shape == "sine":
        return np.sin(2 * np.pi * ph)
    fr = ph - np.floor(ph)
    if shape == "saw":
        return 2 * fr - 1
    if shape == "square":
        return np.where(fr < 0.5, 1.0, -1.0)
    return 4 * np.abs(fr - 0.5) - 1                                # triangle


def glide(f0, f1, seconds, curve=1.0):
    """A per-sample frequency from f0 to f1 (exponential in pitch); curve > 1 moves early."""
    x = np.linspace(0, 1, n(seconds)) ** (1 / curve)
    return f0 * (f1 / f0) ** x


def noise(seconds, seed=0, color="white"):
    """White, pink (-3 dB per octave) or brown (-6 dB per octave) noise, peak about 1."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n(seconds))
    if color != "white":
        spec = np.fft.rfft(x)
        f = np.fft.rfftfreq(len(x), 1 / SR)
        shape = np.maximum(f, 20.0) ** (-0.5 if color == "pink" else -1.0)
        shape[f < 20.0] = 0.0          # nothing below hearing: 1/f noise is otherwise mostly slow drift
        spec *= shape
        x = np.fft.irfft(spec, len(x))
    return x / max(np.abs(x).max(), 1e-12)


def modes(freqs, decays, amps, seconds, seed=None):
    """A struck object: decaying sine partials. decays are the seconds to fall 60 dB."""
    tt = t(seconds)
    rng = np.random.default_rng(seed) if seed is not None else None
    out = np.zeros(len(tt))
    for f, d, a in zip(freqs, decays, amps):
        ph = rng.random() * 2 * np.pi if rng is not None else 0.0
        out += a * np.sin(2 * np.pi * f * tt + ph) * 10 ** (-3 * tt / d)
    return out


# ---------------------------------------------------------------- envelopes

def decay(seconds, t60):
    """Exponential fall of 60 dB over t60 seconds."""
    return 10 ** (-3 * t(seconds) / t60)


def adsr(seconds, attack=0.005, dec=0.05, sustain=0.6, release=0.05):
    k = n(seconds)
    a, d, r = n(attack), n(dec), n(release)
    s = max(k - a - d - r, 0)
    env = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, sustain, d, endpoint=False),
                          np.full(s, sustain), np.linspace(sustain, 0, r)])
    return np.pad(env, (0, max(k - len(env), 0)))[:k]


def fade(x, in_ms=2.0, out_ms=5.0):
    """Short raised-cosine fades so a sound starts and ends at zero (no click)."""
    x = np.array(x, float)
    for count, sl, ramp in ((n(in_ms / 1000), slice(None), 1), (n(out_ms / 1000), slice(None, None, -1), 1)):
        if count > 1:
            w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, min(count, len(x))))
            view = x[sl]
            if x.ndim == 2:
                view[:len(w)] *= w[:, None]
            else:
                view[:len(w)] *= w
    return x


# ---------------------------------------------------------------- filters and effects

def _sos(kind, hz, order):
    return signal.butter(order, np.asarray(hz) / (SR / 2), kind, output="sos")


def lowpass(x, hz, order=2):
    return signal.sosfilt(_sos("lowpass", hz, order), x, axis=0)


def highpass(x, hz, order=2):
    return signal.sosfilt(_sos("highpass", hz, order), x, axis=0)


def bandpass(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bandpass", (lo, hi), order), x, axis=0)


def reverb(x, seconds=1.2, mix=0.25, seed=0, damp=4000.0, wrap=False):
    """A room: convolution with decaying filtered noise. wrap=True folds the tail round to the
    start (circular convolution), which is what keeps a loop seamless. Without wrap the result
    is longer than the input by the tail."""
    ir = lowpass(noise(seconds, seed) * decay(seconds, seconds), damp)
    ir[: n(0.004)] = 0
    ir /= np.sqrt((ir ** 2).sum())

    def one(ch):
        if wrap:
            size = len(ch)
            wet = np.fft.irfft(np.fft.rfft(ch) * np.fft.rfft(_fold(ir, size)), size)
            return (1 - mix) * ch + mix * wet
        wet = signal.fftconvolve(ch, ir)
        dry = np.pad(ch, (0, len(wet) - len(ch)))
        return (1 - mix) * dry + mix * wet

    if x.ndim == 2:
        return np.stack([one(x[:, c]) for c in range(x.shape[1])], 1)
    return one(x)


def _fold(ir, size):
    out = np.zeros(size)
    for i in range(0, len(ir), size):
        part = ir[i:i + size]
        out[:len(part)] += part
    return out


def place(dst, src, at_seconds, gain=1.0, wrap=False):
    """Add `src` into `dst` starting at a time. wrap=True lets it run past the end and back to
    the start, for loops."""
    i = n(at_seconds)
    if wrap:
        idx = (i + np.arange(len(src))) % len(dst)
        np.add.at(dst, idx, gain * src)
    else:
        k = min(len(src), len(dst) - i)
        if k > 0:
            dst[i:i + k] += gain * src[:k]
    return dst


def stereo(x, pan=0.0):
    """Mono to stereo, equal power. pan -1 left .. 1 right."""
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def normalize(x, peak_db=-3.0):
    """Scale so the loudest sample sits at peak_db dBFS, after removing any DC offset."""
    x = x - x.mean(axis=0)
    return x * (10 ** (peak_db / 20) / max(np.abs(x).max(), 1e-12))


def loop_blend(x, ms=80.0):
    """Make a steady texture (crackle, wind) loop: crossfade its tail into its head. The result
    is shorter by the blend."""
    k = n(ms / 1000)
    w = np.linspace(0, 1, k)
    w = w if x.ndim == 1 else w[:, None]
    head = x[:k] * np.sqrt(w) + x[-k:] * np.sqrt(1 - w)
    return np.concatenate([head, x[k:-k]])


# ---------------------------------------------------------------- measuring

def db(v):
    return 20 * np.log10(max(float(v), 1e-12))


def band_share(x, lo, hi):
    """Share of a sound's energy between lo and hi Hz."""
    m = x if x.ndim == 1 else x.mean(1)
    p = np.abs(np.fft.rfft(m)) ** 2
    f = np.fft.rfftfreq(len(m), 1 / SR)
    return float(p[(f >= lo) & (f < hi)].sum() / max(p.sum(), 1e-20))


def centroid(x):
    """Spectral centroid in Hz: how bright the sound is."""
    m = x if x.ndim == 1 else x.mean(1)
    p = np.abs(np.fft.rfft(m)) ** 2
    f = np.fft.rfftfreq(len(m), 1 / SR)
    return float((p * f).sum() / max(p.sum(), 1e-20))


def swept_bandpass(x, freqs, q=3.0):
    """A band-pass whose centre moves: `freqs` is a per-sample centre frequency (use `glide`).
    A state-variable filter run sample by sample; fine for sounds up to a few seconds."""
    f = 2 * np.sin(np.pi * np.minimum(np.asarray(freqs, float), SR / 6.5) / SR)
    damp = 1.0 / q
    low = band_ = 0.0
    out = np.empty(len(x))
    for i in range(len(x)):
        low += f[i] * band_
        high = x[i] - low - damp * band_
        band_ += f[i] * high
        out[i] = band_
    return out


def fit(freq, seconds):
    """The nearest frequency that completes a whole number of cycles in `seconds`: a tone at
    this pitch loops without a click."""
    return round(freq * seconds) / seconds
