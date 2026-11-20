"""Weighty padded fabric fold and a short leather rub, variant 2.

Spec: original mono spatial SFX, one shot lasting 0.20-0.26 s, peak -8 dBFS.
Most energy is in 80-1000 Hz with little above 1800 Hz.
"""
from _frp import product
from _olden_armor_shift import shift_checks, shift_sound

KIND = "sound"
DESCRIPTION = "Weighty padded fabric fold and a short leather rub, take 2"
PARAMS = dict(variant=2)
BUDGET = dict(seconds=.26, kb=26)
PRODUCT = product("sounds", "cloth", "padded_shift",
                  gameplay=dict(family="cloth_padded_shift", variant=2, of=3))


def build(p):
    return shift_sound("padded", p.variant)


def checks(p):
    return shift_checks("padded")
