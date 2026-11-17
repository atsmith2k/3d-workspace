"""Door slide: a heavy door grinding aside over stone and stopping with a thud.

Spec:
  kind: sound
  length: 1.3 to 1.8 s, one-shot
  channels: mono, spatial (it plays at the door)
  character: low grinding rumble that swells and falls, a stutter of friction, a final thud
  energy: at least 70 % below 1 kHz
  level: peak about -3 dBFS
  use: world-kit `door_open` on dungeon_door (it slides 1.25 m at 1.5 m/s: about 0.85 s of travel); bus sfx
"""
from cadkit.game.audio import *
from cadkit.game.sound import band, duration, peak

KIND = "sound"
DESCRIPTION = "heavy door grinding open, ending in a thud"
PARAMS = dict(travel=1.1, seed=21)
BUDGET = dict(seconds=2.0, kb=200)
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["door", "stone", "mechanism"])


def checks(p):
    return [duration(1.3, 1.8), peak(-4, -2), band(30, 1000, at_least=0.7)]


def build(p):
    d = p.travel
    tt = t(d)
    swell = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.6                       # in, hold, out
    stutter = 0.75 + 0.25 * np.sign(np.sin(2 * np.pi * (14 + 6 * tt / d) * tt)) * lowpass(noise(d, p.seed + 2), 30)
    grind = bandpass(noise(d, p.seed, "brown"), 70, 900) * swell * np.clip(stutter, 0.3, 1.2)
    scrape = bandpass(noise(d, p.seed + 1), 900, 2600) * swell * 0.12
    out = np.zeros(n(d + 0.45))
    place(out, grind / np.abs(grind).max() + scrape, 0.0)
    thud = modes([58, 97, 151], [0.35, 0.25, 0.15], [1.0, 0.7, 0.35], 0.42) + 0.5 * lowpass(noise(0.42, p.seed + 3), 500) * decay(0.42, 0.1)
    place(out, thud, d - 0.03, gain=1.1)
    return Sound(normalize(fade(out, 20, 60), -3))
