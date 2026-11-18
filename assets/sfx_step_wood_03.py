"""Footstep on wood, variant 3 of 4: one of a family played at random.

Spec:
  kind: sound
  length: 0.12 to 0.36 s, one-shot
  channels: mono, spatial (it plays at the walker's feet)
  character: a boot on wood: a low thud at the heel, a softer one as the toe comes down
             50-85 ms later, a hollow knock that rings on in the boards
  energy: the thud band carries the weight; almost nothing above 9 kHz
  level: peak -8 dBFS (the pack's level for steps: heard constantly)
  family: within 3 dB RMS of the other variants and plainly a different step from each
  use: played from Mojo on a foot-strike (phase 0 and 0.5 of every gait); bus sfx
"""
from _frp_sound import *

SURFACE, VARIANT = "wood", 3
KIND = "sound"
DESCRIPTION = "footstep on wood, variant 3 of 4"
PARAMS = dict(seed=0)
BUDGET = dict(seconds=0.5, kb=60)
PRODUCT = product("sounds", "footstep", "wood", gameplay=dict(family="step_wood", variant=3, of=4))


def checks(p):
    return step_checks(SURFACE, VARIANT)


def build(p):
    return step_sound(SURFACE, VARIANT)
