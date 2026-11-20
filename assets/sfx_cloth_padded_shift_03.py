"""Weighty padded fabric fold and a short leather rub, variant 3.

Spec: original mono spatial SFX, one shot lasting 0.20-0.26 s, peak -8 dBFS.
Most energy is in 80-1000 Hz with little above 1800 Hz.
"""
from _frp import product
from _olden_armor_shift import shift_checks, shift_sound

KIND = "sound"
DESCRIPTION = "Weighty padded fabric fold and a short leather rub, take 3"
PARAMS = dict(variant=3)
BUDGET = dict(seconds=.26, kb=26)
PRODUCT = product("sounds", "cloth", "padded_shift",
                  gameplay=dict(family="cloth_padded_shift", variant=3, of=3))


def build(p):
    return shift_sound("padded", p.variant)


def checks(p):
    return shift_checks("padded")
