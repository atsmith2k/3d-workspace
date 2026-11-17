"""Beast growl: a low warning growl from something large, the pack's first generated sound.

A growl is the kind of sound synthesis does badly and a generative model does well: a living
throat. The recording comes from ElevenLabs sound effects (cached in assets/gen/); this script
only trims it, shapes its ends and sets its level, and checks that what came back is a growl.

Spec:
  kind: sound
  length: 0.8 to 3.0 s, one-shot
  channels: mono, spatial (it comes from the creature)
  character: a low guttural growl, close and dry: no music, no words, no room echo
  energy: at least half below 1.2 kHz; under a fifth above 6 kHz
  level: peak -3 dBFS (the pack's level for creatures)
  use: a monster noticing the player; non-verbal by the pack's rule; bus sfx
  needs: one generated input (`--gen`, ElevenLabs), not cleared: not for sale until a person
         has listened to it and cleared it
"""
from _frp_sound import *
from cadkit.game import gen

KIND = "sound"
DESCRIPTION = "low warning growl of a large beast (generated recording, trimmed and levelled)"
PARAMS = dict(seconds=2.0)
BUDGET = dict(seconds=3.2, kb=320)
PRODUCT = product("sounds", "creature", "growl", "generated", sellable=False,
                  gameplay=dict(family="creature_growl", variant=1, of=1))

PROMPT = ("A single low guttural warning growl from a large beast, very close, dry studio recording, "
          "no music, no speech, no echo, no background noise")


def checks(p):
    def alive(ctx):
        """A throat, not a hum: the loudness moves, and the tone is not one steady pitch."""
        x = trimmed(p)
        k = n(0.03)
        env = np.sqrt(np.convolve(x * x, np.ones(k) / k, "same"))[k:-k]
        wobble = float(env.std() / max(env.mean(), 1e-9))
        return wobble > 0.15, f"loudness varies by {wobble:.0%} of its mean through the growl"
    return [duration(0.8, 3.0), peak(SOUND_PEAK["creature"] - 0.6, SOUND_PEAK["creature"] + 0.6),
            band(40, 1200, at_least=0.5, name="low"), band(6000, 20000, at_most=0.2, name="not hissy"),
            custom("alive", alive)]


def trimmed(p):
    x = gen.sound(PROMPT, name="frp_growl_01", seconds=p.seconds)
    x = highpass(x - x.mean(), 30)                                   # no rumble, no DC
    k = n(0.01)
    env = np.sqrt(np.convolve(x * x, np.ones(k) / k, "same"))
    loud = np.nonzero(env > env.max() * 10 ** (-36 / 20))[0]         # drop the silence at both ends
    x = x[max(loud[0] - n(0.01), 0): min(loud[-1] + n(0.05), len(x))]
    return normalize(fade(x, 5, 60), SOUND_PEAK["creature"])


def build(p):
    return Sound(trimmed(p), bus="sfx", spatial=True)
