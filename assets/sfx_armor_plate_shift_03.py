"""Restrained hinge scrape and two damped plate contacts, variant 3.

Spec: original mono spatial SFX, one shot lasting 0.20-0.26 s, peak -8 dBFS.
Damped modes in 300-1150 Hz and contact partials in 1150-3900 Hz.
"""
from _frp import product
from _olden_armor_shift import shift_checks, shift_sound

KIND = "sound"
DESCRIPTION = "Restrained hinge scrape and two damped plate contacts, take 3"
PARAMS = dict(variant=3)
BUDGET = dict(seconds=.26, kb=26)
PRODUCT = product("sounds", "armor", "plate_shift",
                  gameplay=dict(family="armor_plate_shift", variant=3, of=3))


def build(p):
    return shift_sound("plate", p.variant)


def checks(p):
    return shift_checks("plate")
