"""Sound families for ash10's Fantasy RPG Pack.

A family is a set of numbered variants of one sound (`sfx_step_stone_01` .. `_04`) that a game
plays at random so no two in a row are the same. Variants share one recipe and differ in the
details a listener hears as "another step", not "another sound": timing of heel and toe, pitch of
the thud, how much grit. Every variant peaks at its family's level (`SOUND_PEAK`), so any step
works on any surface at the same volume setting.

Nobody in the pipeline can listen: each claim below is a `band` or family check.
"""
from _frp import SOUND_PEAK, product, sound_name
from cadkit.game.audio import *
from cadkit.game.sound import band, custom, duration, peak

VARIANTS = 4

# surface: thud band (Hz), thud decay (s), click band, click gain, grit band low edge, grit gain
SURFACES = dict(
    stone=dict(thud=(110, 650), ring=0.10, click=(1600, 5200), click_gain=0.6, grit=2600, grit_gain=0.14),
    wood=dict(thud=(90, 420), ring=0.16, click=(700, 2400), click_gain=0.35, grit=3000, grit_gain=0.06,
              click_ring=0.05, takes=16, rms=-23.0),            # the knock rings on in the boards
    dirt=dict(thud=(70, 380), ring=0.06, click=(900, 2200), click_gain=0.12, grit=1800, grit_gain=0.35,
              takes=16, rms=-23.0),
)
# `takes`: a burst of noise is loud or quiet by luck, so a family that must sit within 3 dB is
# chosen the way a foley editor chooses: several takes of each variant, keep the one nearest the
# family's level (`rms`, dB) that is also a full-length step. Stone was approved as its first take.


def step(surface, variant):
    """One footstep on a surface, mono, peaking at the family level."""
    s = SURFACES[surface]
    takes = [_take(surface, variant, t) for t in range(s.get("takes", 1))]
    if len(takes) == 1:
        return takes[0]
    lo, hi = s["thud"]
    clo, chi = s["click"]

    def in_character(x):                                       # the claims the checks hold, with room to spare
        return (0.13 * SR < len(x) < 0.34 * SR and share(x, lo * 0.8, hi * 1.3) > 0.52
                and share(x, clo * 0.9, chi * 1.2) > 1.4 * click_floor(s))
    full = [x for x in takes if in_character(x)] or takes
    return min(full, key=lambda x: abs(rms_db(x) - s["rms"]))


def share(x, lo, hi):
    """Share of a sound's energy between two frequencies."""
    e = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return float(e[(f >= lo) & (f < hi)].sum() / e.sum())


def click_floor(s):
    """Least share of the energy the contact click must carry: it grows with the square of its gain."""
    return 0.5 * s["click_gain"] ** 2 * 0.25


def _take(surface, variant, take=0):
    s = SURFACES[surface]
    rng = np.random.default_rng(1000 * (["dirt", "stone", "wood"].index(surface) + 1) + variant + 7919 * take)
    shift = 1 + rng.uniform(-0.12, 0.12)                       # each step a little higher or lower
    toe = rng.uniform(0.045, 0.085)                            # heel, then toe
    out = np.zeros(n(0.34))
    lo, hi = s["thud"]
    thud = bandpass(noise(0.22, int(rng.integers(1 << 30)), "brown"), lo * shift, hi * shift) * decay(0.22, s["ring"] * rng.uniform(0.85, 1.2))
    place(out, thud, 0.004, 1.0)
    clo, chi = s["click"]
    click = bandpass(noise(0.05, int(rng.integers(1 << 30))), clo * shift, chi * shift) * decay(0.05, s.get("click_ring", 0.022))
    place(out, click, 0.004, s["click_gain"] * rng.uniform(0.8, 1.2))
    place(out, thud[: n(0.12)] * decay(0.12, 0.04), toe, 0.62 * rng.uniform(0.85, 1.15))        # the toe coming down, softer
    place(out, click, toe, 0.5 * s["click_gain"] * rng.uniform(0.6, 1.2))
    grit_len = rng.uniform(0.07, 0.12)
    grit = bandpass(noise(grit_len, int(rng.integers(1 << 30))), s["grit"], s["grit"] * 2.6) * np.hanning(n(grit_len))
    place(out, grit, toe * rng.uniform(0.5, 1.1), s["grit_gain"] * rng.uniform(0.7, 1.3))
    out = lowpass(out, 8000)                                   # a boot has no sparkle
    live = np.nonzero(np.abs(out) > np.abs(out).max() * 10 ** (-45 / 20))[0]
    out = out[: min(live[-1] + n(0.012), len(out))]            # end where the sound does
    return normalize(fade(out, 1, 25), SOUND_PEAK["step"])


def step_sound(surface, variant):
    return Sound(step(surface, variant), bus="sfx", spatial=True)


def rms_db(x):
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12))


def likeness(a, b):
    """Peak of the normalised cross-correlation of two sounds: 1.0 is the same waveform."""
    from scipy.signal import correlate
    c = correlate(a, b, mode="full", method="fft")
    return float(np.abs(c).max() / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def step_checks(surface, variant):
    s = SURFACES[surface]

    def family(ctx):
        all_ = [step(surface, v) for v in range(1, VARIANTS + 1)]
        mine = all_[variant - 1]
        loud = [rms_db(x) for x in all_]
        like = max(likeness(mine, x) for i, x in enumerate(all_) if i != variant - 1)
        ok = max(loud) - min(loud) < 3.0 and like < 0.6
        return ok, (f"{VARIANTS} variants within {max(loud) - min(loud):.1f} dB of each other (RMS); this one is at most "
                    f"{like:.2f} like another (1.0 = identical)")

    def two_beats(ctx):
        env = np.abs(step(surface, variant))
        k = n(0.01)
        e = np.convolve(env, np.ones(k) / k, "same")
        first = e[: n(0.03)].max()
        later = e[n(0.04): n(0.12)].max()
        return later > 0.2 * first, f"heel then toe: the second beat is {later / first:.0%} of the first"
    lo, hi = s["thud"]
    return [duration(0.12, 0.36), peak(SOUND_PEAK["step"] - 0.6, SOUND_PEAK["step"] + 0.6),
            band(lo * 0.8, hi * 1.3, at_least=0.45 if surface != "stone" else 0.35, name="thud"),
            band(9000, 20000, at_most=0.2, name="no hiss"),
            band(s["click"][0] * 0.9, s["click"][1] * 1.2, at_least=click_floor(s), name="click"), custom("family", family), custom("heel and toe", two_beats)]


STEP_DOC = '''"""Footstep on {surface}, variant {v} of {n}: one of a family played at random.

Spec:
  kind: sound
  length: 0.12 to 0.36 s, one-shot
  channels: mono, spatial (it plays at the walker's feet)
  character: a boot on {surface}: a low thud at the heel, a softer one as the toe comes down
             50-85 ms later, {extra}
  energy: the thud band carries the weight; almost nothing above 9 kHz
  level: peak -8 dBFS (the pack's level for steps: heard constantly)
  family: within 3 dB RMS of the other variants and plainly a different step from each
  use: played from Mojo on a foot-strike (phase 0 and 0.5 of every gait); bus sfx
"""
from _frp_sound import *

SURFACE, VARIANT = "{surface}", {v}
KIND = "sound"
DESCRIPTION = "footstep on {surface}, variant {v} of {n}"
PARAMS = dict(seed=0)
BUDGET = dict(seconds=0.5, kb=60)
PRODUCT = product("sounds", "footstep", "{surface}", gameplay=dict(family="step_{surface}", variant={v}, of={n}))


def checks(p):
    return step_checks(SURFACE, VARIANT)


def build(p):
    return step_sound(SURFACE, VARIANT)
'''
EXTRA = dict(stone="a hard click and a little grit under the sole", wood="a hollow knock that rings on in the boards",
             dirt="hardly any click and a soft crunch of soil")


def write_family(surface, folder):
    """Write the asset scripts of a step family (run once; the files are the source)."""
    from pathlib import Path
    names = []
    for v in range(1, VARIANTS + 1):
        name = sound_name("step", surface, v)
        Path(folder, f"{name}.py").write_text(STEP_DOC.format(surface=surface, v=v, n=VARIANTS, extra=EXTRA[surface]),
                                              encoding="utf-8", newline="\n")
        names.append(name)
    return names
