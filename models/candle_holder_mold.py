"""Mold for a cement or Jesmonite candle holder you pour straight into the print.

Choose the version in the title: a fluted tealight holder (75 mm across, 40 mm tall), a
faceted hexagon tealight holder, or a fluted holder for a 7/8 in taper candle (56 mm
across, 48 mm tall). The tealight pocket fits standard 38-39 mm tealights with room to
lift them out; the taper pocket narrows slightly so the candle wedges upright. Pour, tap
out the air, screed the back flat, and lift the holder out once cured: every wall is
tapered so it releases from the rigid mold. Prints opening-up with no supports in about
4-6 hours on a Bambu A1 or A1 mini.

Spec:
  object:       mold for a cement / Jesmonite candle holder, poured straight into the print
  overall:      tealight: holder 75 mm across, 40 mm tall; mold ~85 x 85 x 43 mm.
                taper: holder 56 mm across, 48 mm tall; mold ~66 x 66 x 51 mm
  mates with:   tealight cup 39.0 mm dia x 16 mm (standard 38-39 mm); pocket 40.5 at the
                bottom, 17 deep. Taper candle 7/8 in (22.2 mm) base; pocket 22.8 at the
                bottom widening to ~24.6, 22 deep so the candle wedges upright
  orientation:  opening up, flat floor on the bed, no supports
  must have:    shape fluted (20 rounded flutes), hex (faceted) or round; 2 deg draft on
                the body, 3 deg on the pocket boss (taper 2.5); floor 3, wall 3
  tolerances:   pocket +0.75 mm per side for tealights; the taper pocket is a wedge fit

Units: mm. Z is up, the mold sits on Z=0.
"""
import math

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Concrete candle holder mold, tealight or taper, fluted/hex/round"

PRODUCT = dict(
    title="{shape} {candle} Candle Holder Mold",   # filled from params per variant
    category="molds",
    tags=["mold", "concrete", "cement", "jesmonite", "candle holder", "tealight", "taper candle",
          "fluted", "home decor"],
    printers=["a1", "a1mini"],
    cast_material="cement, concrete or Jesmonite",
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    candle="tealight",      # tealight | taper
    shape="fluted",         # fluted | hex | round
    diameter=0.0,           # holder diameter at its top face (0 = default for the candle)
    height=0.0,             # holder height (0 = default for the candle)
    floor=3.0,
    wall=3.0,
    body_draft=2.0,
    flutes=20,
)

EMBED = 0.1
CANDLES = {
    # candle diameter, pocket depth, clearance per side at the pocket bottom, pocket draft,
    # default holder diameter and height
    "tealight": dict(d=39.0, depth=17.0, clear=0.75, draft=3.0, body_d=75.0, body_h=40.0),
    "taper": dict(d=22.2, depth=22.0, clear=0.3, draft=2.5, body_d=56.0, body_h=48.0),
}


def dims_for(p):
    c = CANDLES[p.candle]
    return c, (p.diameter or c["body_d"]), (p.height or c["body_h"])


def body_section(p, r):
    """Holder outline at radius r (circumradius for hex, outer flute tip for fluted)."""
    if p.shape == "round":
        return circle(0, 0, r)
    if p.shape == "hex":
        pts = [(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i)))
               for i in range(6)]
        return grow(grow(poly(pts), -2.0), 2.0)            # 2 mm rounded corners
    # fluted: a core plus rounded flutes around it, valleys softened so no knife edges
    n = p.flutes
    fr = r * math.sin(math.pi / n) * 1.05                    # flute radius, neighbours just overlap
    cs = circle(0, 0, r - fr)
    for i in range(n):
        a = 2 * math.pi * i / n
        cs += circle((r - fr) * math.cos(a), (r - fr) * math.sin(a), fr)
    return grow(grow(cs, 1.0), -1.0)


def checks(p):
    c, d, h = dims_for(p)
    lean = draft_offset(h, p.body_draft)
    pocket_r = c["d"] / 2 + c["clear"]
    outer = d + 2 * (lean + p.wall)
    return [
        dims(z=p.floor + h, x=(outer - 2, outer + 1)),
        empty(((pocket_r + d / 2) / 2, 0, p.floor + h / 2)),              # cavity between boss and wall
        solid((0, 0, p.floor + c["depth"] / 2)),                           # pocket boss
        solid((pocket_r - 0.3, 0, p.floor + c["depth"] - 0.3)),           # boss top is wide enough for the candle
        empty((0, 0, p.floor + c["depth"] + 1.0)),                         # boss stops at pocket depth
        thickness_at(((pocket_r + d / 2) / 2, 0, 0.5), p.floor - 0.2, direction=(0, 0, 1)),
        flat_base(math.pi * (d / 2) ** 2 * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    c, d, h = dims_for(p)
    r = d / 2
    lean = draft_offset(h, p.body_draft)
    # mold block follows the widest holder outline plus the wall
    mold = extrude(body_section(p, r + lean + p.wall), p.floor + h)
    # cavity widens toward the opening (the holder's base)
    mold -= tapered(body_section(p, r), p.floor, h + 1, lean * (h + 1) / h)
    # candle pocket: a boss on the floor, narrowing upward to the candle size
    pocket_r = c["d"] / 2 + c["clear"]
    boss_lean = draft_offset(c["depth"], c["draft"])
    mold += tapered(circle(0, 0, pocket_r + boss_lean), p.floor - EMBED, c["depth"] + EMBED, -boss_lean)
    return mold


def casting(p):
    """What the mold makes, for the shop's cast render: the holder the right way up."""
    return cast_of(build(p))
