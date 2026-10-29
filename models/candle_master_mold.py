"""Silicone mold kit for a pillar candle: print the master and the housing, pour silicone,
and you have a reusable candle mold.

Choose the style in the title: ribbed (24 rounded ribs, 70 mm across, 90 mm tall),
faceted (a ten-sided pillar with a gentle spiral, 65 x 85 mm) or twisted (a six-lobed
pillar turning a third of a turn, 60 x 100 mm). The master stands on a base board; slide
the housing tube over the base, seal the joint with a little clay, and pour silicone to
the rim. The pin on top of the master leaves a ready-made wick hole through the silicone.
Demold, and pour wax into the silicone through its open end, which forms the candle's
flat base. Mix about 300 ml of silicone (ribbed 303 ml, faceted 275 ml, twisted 315 ml).
Both parts print with no supports, about 2.5 hours each, on a Bambu A1 or A1 mini.

Spec:
  object:       two-part master + housing for casting a silicone pillar-candle mold
  overall:      ribbed: master on a 101 mm base, 97 mm tall plus a 10.5 mm wick pin;
                housing 96 mm across, 104 mm tall (fits the A1 mini)
  casting:      candle = the master body; silicone wall 10 mm round the candle and
                10 mm over its top; wick hole 2.5 mm through the top
  mates with:   housing bore slides over the base spigot, 0.25 mm clearance per side,
                and rests on the base flange
  orientation:  master: base board on the bed, candle and wick pin up; housing: either
                end down; no supports
  must have:    styles ribbed / faceted / twisted; 2 mm chamfer round the candle top;
                wick pin 2.5 mm; silicone needed reported by the build (275-315 ml)
  tolerances:   sliding 0.25 mm per side on the spigot

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
import math

from manifold3d import Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Silicone mold kit for a pillar candle: printed master on a base board plus housing"

PRODUCT = dict(
    title="{style} Pillar Candle Silicone Mold Kit",   # filled from params per variant
    category="molds",
    tags=["mold", "silicone mold", "candle mold", "mold master", "candle making", "pillar candle",
          "wax", "soy candle", "mold box", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then candle wax",
    post_processing=("Lightly sand the master's visible layer lines or brush on a sealer; the "
                     "silicone copies every line. Spray release on the master and housing, seal "
                     "the housing-to-base joint with modelling clay, then mix about 300 ml of "
                     "silicone (ribbed 303, faceted 275, twisted 315 ml) and pour slowly into one "
                     "corner. Demold after full cure."),
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    style="ribbed",     # ribbed | faceted | twisted
    diameter=0.0,       # candle diameter (0 = the style's default)
    height=0.0,         # candle height (0 = the style's default)
    silicone=10.0,      # silicone wall round the candle and over its top
    chamfer=2.0,        # round the candle's top edge
    wick_d=2.5,
    clearance=0.25,
)

EMBED = 0.1
STYLES = {
    # default candle size and the section's shape
    "ribbed": dict(d=70.0, h=90.0),
    "faceted": dict(d=65.0, h=85.0),
    "twisted": dict(d=60.0, h=100.0),
}


def size(p):
    s = STYLES[p.style]
    return (p.diameter or s["d"]), (p.height or s["h"])


def section(p, r):
    """Candle cross-section, `r` = outer radius."""
    if p.style == "ribbed":
        n = 24
        fr = r * math.sin(math.pi / n) * 1.05
        cs = circle(0, 0, r - fr)
        for i in range(n):
            a = 2 * math.pi * i / n
            cs += circle((r - fr) * math.cos(a), (r - fr) * math.sin(a), fr)
        return grow(grow(cs, 1.0), -1.0)
    if p.style == "faceted":
        pts = [(r * math.cos(2 * math.pi * i / 10), r * math.sin(2 * math.pi * i / 10)) for i in range(10)]
        return grow(grow(poly(pts), -1.0), 1.0)
    # twisted: six round lobes on a core
    lobe = r * 0.36
    cs = circle(0, 0, r - lobe * 1.2)
    for i in range(6):
        a = 2 * math.pi * i / 6
        cs += circle((r - lobe) * math.cos(a), (r - lobe) * math.sin(a), lobe)
    return grow(grow(cs, 2.0), -2.0)


TWIST = {"ribbed": 0.0, "faceted": 36.0, "twisted": 120.0}


def candle(p):
    """The candle (the master's body), standing on Z=0."""
    d, h = size(p)
    r = d / 2
    body_h = h - p.chamfer
    twist = TWIST[p.style]
    body = Manifold.extrude(section(p, r), body_h, n_divisions=max(1, int(abs(twist) / 2)),
                            twist_degrees=twist)
    # chamfered top: the last `chamfer` mm narrows by the same amount, carrying the twist on
    top_twist = twist * p.chamfer / body_h
    top = Manifold.extrude(section(p, r), p.chamfer + 0.01, n_divisions=2, twist_degrees=top_twist,
                           scale_top=((r - p.chamfer) / r,) * 2)
    top = top.rotate((0, 0, twist)).translate((0, 0, body_h - 0.01))
    return body + top


def _box(p):
    d, h = size(p)
    return mold_box(d / 2 + p.silicone, h + p.silicone, clearance=p.clearance)


def silicone_ml(p):
    base, tube, z0 = _box(p)
    d, h = size(p)
    fill = math.pi * (d / 2 + p.silicone) ** 2 * (h + p.silicone)
    return (fill - candle(p).volume()) / 1000.0


def assembly(p):
    """The housing slides down over the spigot and rests on the base flange."""
    return {"housing": (0, 0, 3.0, 0, 0, 0)}


def checks(p):
    d, h = size(p)
    base, tube, z0 = _box(p)
    ml = silicone_ml(p)
    top = z0 + h
    return {
        "master": [
            dims(z=top + p.silicone + 0.5),
            solid((0, 0, z0 + h / 2), (0, 0, top + p.silicone / 2)),            # candle, wick pin
            empty((d / 2 + p.silicone / 2, 0, z0 + h / 2)),                        # room for silicone
            custom("silicone to mix", lambda ctx: (True, f"{ml:.0f} ml (about {ml * 1.1:.0f} g)")),
            flat_base(math.pi * (d / 2 + p.silicone) ** 2 * 0.9),
            no_overhang(),
            single_body(),
        ],
        "housing": [
            dims(z=4.0 + h + p.silicone),
            empty((0, 0, 5)),
            no_overhang(),
            single_body(),
        ],
    }


def build(p):
    d, h = size(p)
    base, tube, z0 = _box(p)
    master = base + candle(p).translate((0, 0, z0 - EMBED))
    pin = extrude(circle(0, 0, p.wick_d / 2), p.silicone + 0.5 + EMBED, z0 + h - EMBED)
    return {"master": master + pin, "housing": tube}


def casting(p):
    """What the kit makes, for the shop's cast render: the candle."""
    return candle(p)
