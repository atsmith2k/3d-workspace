"""Silicone mold kit for a pillar candle: print the master and the housing, pour silicone,
and you have a reusable candle mold.

Choose the style in the title: ribbed (24 rounded ribs, 70 mm across, 90 mm tall),
faceted (a ten-sided pillar with a gentle spiral, 65 x 85 mm), twisted (a six-lobed
pillar turning a third of a turn, 60 x 100 mm), bubble (a 3 x 3 x 3 bubble cube, 62 mm
square, 59 mm tall) or twisted taper (a five-lobed spiral taper turning one and a half
times, 6 in tall on a plain 7/8 in foot that fits standard taper holders). The master stands on a base board; slide
the housing tube over the base, seal the joint with a little clay, and pour silicone to
the rim. The pin on top of the master leaves a ready-made wick hole through the silicone.
Demold, and pour wax into the silicone through its open end, which forms the candle's
flat base. Mix about 300 ml of silicone (ribbed 303 ml, faceted 275 ml, twisted 315 ml,
bubble 325 ml; the twisted taper needs only 192 ml).
Both parts print with no supports, about 2.5 hours each.

Spec:
  object:       two-part master + housing for casting a silicone pillar-candle mold
  overall:      ribbed: master on a 101 mm base, 97 mm tall plus a 10.5 mm wick pin;
                housing 96 mm across, 104 mm tall (fits a 180 mm bed)
  casting:      candle = the master body; silicone wall 10 mm round the candle and
                10 mm over its top; wick hole 2.5 mm through the top
  mates with:   housing bore slides over the base spigot, 0.25 mm clearance per side,
                and rests on the base flange
  orientation:  master: base board on the bed, candle and wick pin up; housing: either
                end down; no supports
  must have:    styles ribbed / faceted / twisted / bubble / twisted_taper; 2 mm chamfer
                round the pillar tops; bubble necks filleted 2.2 mm and under 45 deg (no
                supports); taper foot 18 mm plain, 21.4 mm at the bottom to 22.2 mm (7/8 in)
                so it wedges into holders, then a 5 mm shoulder into the spiral; silicone 10 mm past the furthest
                point (the bubble cube's corners);
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
    title="{style} {candle} Silicone Mold Kit",   # filled from params per variant
    category="molds",
    tags=["mold", "silicone mold", "candle mold", "mold master", "candle making", "pillar candle",
          "wax", "soy candle", "mold box", "home decor", "bubble candle", "taper candle"],
    printers=["a1", "a1mini"],
    cast_material="silicone (Shore 20-30A, platinum or tin cure), then candle wax",
    post_processing=("Print the master at 0.12 mm layers or finer (the housing is fine at 0.2); "
                     "give the tall twisted-taper housing a 5 mm brim. "
                     "Lightly sand the master's visible layer lines or brush on a sealer; the "
                     "silicone copies every line. Spray release on the master and housing, seal "
                     "the housing-to-base joint with modelling clay, then mix about 300 ml of "
                     "silicone (ribbed 303, faceted 275, twisted 315, bubble 325, twisted taper 192 ml) "
                     "and pour slowly into one "
                     "corner. Demold after full cure."),
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    style="ribbed",     # ribbed | faceted | twisted | bubble | twisted_taper
    candle="pillar_candle",  # title label only: bubble -> cube_candle, twisted_taper -> candle
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
    "bubble": dict(d=62.0, h=58.8),          # 3 x 3 x 3 bubble cube (h follows from d)
    "twisted_taper": dict(d=22.2, h=150.0),  # 7/8 in base for standard taper holders, 6 in tall
}
TAPER_BASE = 18.0    # plain 7/8 in cylinder at the foot of the taper, for the holder socket
TAPER_TOP = 0.62     # taper's top diameter as a share of the base
TAPER_FOOT_D = 21.4  # foot diameter at the very bottom: drafted 0.4 mm a side so it wedges
                     # into 7/8 in (22.2 mm) holders snugly
TAPER_SHOULDER = 5.0 # cone from the foot into the spiral, so the lobes grow out of it
BUBBLE_BLEND = 2.2   # fillet radius at the bubble cube's necks
BUBBLE_EDGE = 0.35   # SDF grid for the bubble cube (finer = smoother, heavier STL)


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
    if p.style == "twisted_taper":
        # five round lobes, the classic spiral taper
        lobe = r * 0.34
        cs = circle(0, 0, r - lobe * 1.1)
        for i in range(5):
            a = 2 * math.pi * i / 5
            cs += circle((r - lobe) * math.cos(a), (r - lobe) * math.sin(a), lobe)
        return grow(grow(cs, 0.6), -0.6)
    # twisted: six round lobes on a core
    lobe = r * 0.36
    cs = circle(0, 0, r - lobe * 1.2)
    for i in range(6):
        a = 2 * math.pi * i / 6
        cs += circle((r - lobe) * math.cos(a), (r - lobe) * math.sin(a), lobe)
    return grow(grow(cs, 2.0), -2.0)


TWIST = {"ribbed": 0.0, "faceted": 36.0, "twisted": 120.0, "bubble": 0.0, "twisted_taper": 540.0}


def bubble_cube(p):
    """3 x 3 x 3 bubbles on a 1.38 r grid, every neck filleted (smooth union, BUBBLE_BLEND
    mm): sharp creases where bubbles meet would leave thin silicone fins that tear on the
    first demold, and the softened necks stay under 45 deg so the master prints without
    supports. Flat base cut through the bottom row (the pour end)."""
    import numpy as np
    from cadkit.sdf import build_sdf, _smax

    d, h = size(p)
    r = d / (2 + 2 * 1.38)
    s = 1.38 * r
    z_bottom = h - 2 * s - r                  # bottom row centre above the cut (~0.6 r)
    centres = [(i * s, j * s, z_bottom + k * s) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in range(3)]

    def f(x, y, z):
        out = None
        for cx, cy, cz in centres:
            g = r - np.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
            out = g if out is None else _smax(out, g, BUBBLE_BLEND)
        # solid core: the centre of each group of 8 bubbles sits 1.2 r from them, so the
        # spheres alone leave sealed voids inside and pits in the pour face
        top = z_bottom + 2 * s
        core = np.minimum(np.minimum(s - np.abs(x), s - np.abs(y)), top - z)
        out = np.maximum(out, core)
        return np.minimum(out, h - z)          # crown trimmed to exactly h

    half = s + r + 1
    # the level set comes out ~780k triangles; a 0.02 mm simplify (a tenth of a layer)
    # takes it to ~175k so the STL stays light for Tinkercad and slicers
    return build_sdf(f, (-half, -half, -1.0, half, half, h + 1), edge=BUBBLE_EDGE).simplify(0.02)


def taper(p):
    """Twisted taper candle: a plain, slightly drafted 7/8 in foot for the holder, a
    shoulder cone the lobes grow out of, then five lobes turning one and a half times as
    the candle narrows to a soft point."""
    d, h = size(p)
    r = d / 2
    foot = Manifold.cylinder(TAPER_BASE + 0.1, TAPER_FOOT_D / 2, r, 128)
    shoulder = Manifold.cylinder(TAPER_SHOULDER, r, r * 0.5, 128).translate((0, 0, TAPER_BASE))
    tip_h = 6.0
    body_h = h - TAPER_BASE - tip_h
    body = Manifold.extrude(section(p, r), body_h, n_divisions=int(body_h), twist_degrees=TWIST[p.style],
                            scale_top=(TAPER_TOP, TAPER_TOP)).translate((0, 0, TAPER_BASE))
    # the tip carries the lobes and the twist on, narrowing faster to a soft point
    tip_twist = TWIST[p.style] * tip_h / body_h
    tip = Manifold.extrude(section(p, r * TAPER_TOP), tip_h + 0.01, n_divisions=6,
                           twist_degrees=tip_twist, scale_top=(0.45, 0.45))
    tip = tip.rotate((0, 0, TWIST[p.style])).translate((0, 0, TAPER_BASE + body_h - 0.01))
    return foot + shoulder + body + tip


def candle(p):
    """The candle (the master's body), standing on Z=0."""
    if p.style == "bubble":
        return bubble_cube(p)
    if p.style == "twisted_taper":
        return taper(p)
    d, h = size(p)
    r = d / 2
    body_h = h - p.chamfer
    twist = TWIST[p.style]
    # at least one division per mm: coarser steps bend each flat facet into visible
    # diagonal bands (the faceted style)
    body = Manifold.extrude(section(p, r), body_h,
                            n_divisions=max(1, int(abs(twist) / 2), int(body_h) if twist else 1),
                            twist_degrees=twist)
    # chamfered top: the last `chamfer` mm narrows by the same amount, carrying the twist on
    top_twist = twist * p.chamfer / body_h
    top = Manifold.extrude(section(p, r), p.chamfer + 0.01, n_divisions=2, twist_degrees=top_twist,
                           scale_top=((r - p.chamfer) / r,) * 2)
    top = top.rotate((0, 0, twist)).translate((0, 0, body_h - 0.01))
    return body + top


def reach(p):
    """Furthest the candle reaches from its axis (the bubble cube's corner bubbles)."""
    d, h = size(p)
    if p.style == "bubble":
        r = d / (2 + 2 * 1.38)
        return 1.38 * r * math.sqrt(2) + r
    return d / 2


def _box(p):
    d, h = size(p)
    return mold_box(reach(p) + p.silicone, h + p.silicone, clearance=p.clearance)


def silicone_ml(p):
    base, tube, z0 = _box(p)
    d, h = size(p)
    fill = math.pi * (reach(p) + p.silicone) ** 2 * (h + p.silicone)
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
            empty((reach(p) + p.silicone / 2, 0, z0 + h / 2)),                     # room for silicone
            custom("silicone to mix", lambda ctx: (True, f"{ml:.0f} ml (about {ml * 1.1:.0f} g)")),
            flat_base(math.pi * (reach(p) + p.silicone) ** 2 * 0.9),
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
    pin = extrude(circle(0, 0, p.wick_d / 2), p.silicone + 1.5, z0 + h - 1.0)   # sunk 1 mm: the bubble cube's crown is a point
    return {"master": master + pin, "housing": tube}


def casting(p):
    """What the kit makes, for the shop's cast render: the candle."""
    return candle(p)
