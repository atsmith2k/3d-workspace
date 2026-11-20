"""Shallow-water footstep, variant 2.

Spec: mono spatial one-shot, 0.37-0.43 s, -8 dBFS peak. Low boot impact and
broadband splash followed by discrete settling droplets beyond 200 ms.
"""
from _frp import product
from _olden_water_step import water_checks, water_step

KIND = "sound"
DESCRIPTION = "Boot through shallow water with settling droplets, take 2"
PARAMS = dict(variant=2)
BUDGET = dict(seconds=.43, kb=44)
PRODUCT = product("sounds", "footstep", "water", gameplay=dict(family="step_water", variant=2, of=4))


def build(p):
    return water_step(p.variant)


def checks(p):
    return water_checks()
