"""Slip-casting kit for potters: a printed master and cottle (mold frame) for making a
one-piece plaster drop-out mold, then casting your own ceramics in it.

Choose the piece in the title: a small bowl (95 mm across and 45 mm tall after firing),
a tumbler (75 mm across the rim and 100 mm tall), an espresso cup (62 mm rim, 60 mm
tall), a fluted tumbler (78 mm rim, 100 mm tall, 20 flutes) or a fluted planter (95 mm
rim, 85 mm tall, 24 flutes; drill the drainage hole leather-hard). The master is already
scaled up for 12% clay shrinkage, so the fired piece comes out at those sizes, and it
carries a spare (pour reservoir) at the rim. Stand it on its base, slide the cottle tube
over, seal the joint with clay, and pour plaster to the rim: about 1.5 litres of mixed
plaster for the bowl, 1.8 litres for the tumbler (espresso cup 1.1, fluted tumbler 1.9,
fluted planter 2.1 litres). The finished mold has no undercuts,
so the leather-hard piece drops straight out. Both parts print with no supports (about 7 hours for the bowl kit, 9 for the tumbler).

Spec:
  object:       master on a base board + cottle tube for casting a one-piece plaster
                drop-out slip-casting mold
  overall:      bowl: base 175 mm across, 78 mm tall (7 mm base, 20 mm spare, master);
                tumbler: base 152 mm across, 141 mm tall; espresso cup, fluted tumbler and
                fluted planter bases all under 180 mm (fit the mini)
  casting:      fired bowl 95 x 45 mm, fired tumbler 75 mm rim / 60 mm foot x 100 mm,
                espresso cup 62 / 46 x 60 mm, fluted tumbler 78 / 62 x 100 mm with 20 flutes
                1.6 mm deep (wet), fluted planter 95 / 76 x 85 mm with 24 flutes 2 mm deep;
                master = fired size / (1 - 0.12 shrinkage); plaster 25 mm round and
                over the master
  mates with:   cottle bore slides over the base spigot, 0.25 mm clearance per side
  orientation:  master: base on the bed, master upside down (spare down, foot up);
                cottle: either end down; no supports
  must have:    no undercuts (bowl wall 17 deg off vertical at the rim, tumbler 4 deg);
                flutes run out through the foot and fade out 9-10 mm under the rim, so
                they only deepen in the pull direction; flute ridges rounded (~0.6 mm),
                no knife edges; planter foot carries a 6 mm drill-centre dimple;
                spare 3 mm wider than the rim so the trim line is clear; plaster volume
                reported by the build
  tolerances:   sliding 0.25 mm per side on the spigot

Units: mm. Z is up, each part sits on Z=0 in its print pose.
"""
import math

import numpy as np
from manifold3d import CrossSection, Manifold

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Slip-casting master and cottle for a one-piece plaster drop-out mold (bowl or tumbler)"

PRODUCT = dict(
    title="{piece} Slip Casting Mold Master",         # filled from params per variant
    category="molds",
    tags=["mold", "slip casting", "plaster mold", "ceramics", "pottery", "mold master", "bowl",
          "tumbler", "cup", "espresso cup", "fluted", "planter"],
    printers=["a1", "a1mini"],
    cast_material="pottery plaster (USG No. 1 or similar), then casting slip",
    post_processing=("Print the master at 0.12 mm layers or finer (the cottle is fine at 0.2). "
                     "Sand the master's layer lines smooth, or fill them with a primer, and seal it; "
                     "plaster copies every line. Coat master and cottle with mold soap, seal the "
                     "cottle-to-base joint with clay, mix about 1.5 litres (bowl), 1.8 litres "
                     "(tumbler), 1.1 (espresso cup), 1.9 (fluted tumbler) or 2.1 litres (fluted planter) "
                     "of plaster and pour to the rim. Dry the mold fully before the first cast."),
)
LICENSE_NOTES = None   # original design

PARAMS = dict(
    piece="bowl",       # bowl | tumbler | espresso_cup | fluted_tumbler | fluted_planter
    shrinkage=0.12,     # clay shrinkage from wet to fired
    plaster=25.0,       # plaster round and over the master
    spare_h=20.0,
    spare_step=3.0,     # spare this much wider than the rim (radius)
    wall=4.0,           # cast wall, for the render of the fired piece
    clearance=0.25,
)

PIECES = {
    # fired rim diameter, foot diameter, height, profile exponent (1 = straight side),
    # flutes: count and depth (wet), lip: plain band under the rim before the flutes start
    "bowl": dict(rim=95.0, foot=52.0, h=45.0, k=0.7),
    "tumbler": dict(rim=75.0, foot=60.0, h=100.0, k=1.0),
    "espresso_cup": dict(rim=62.0, foot=46.0, h=60.0, k=0.85),
    "fluted_tumbler": dict(rim=78.0, foot=62.0, h=100.0, k=1.0, flutes=20, depth=1.6, lip=9.0),
    "fluted_planter": dict(rim=95.0, foot=76.0, h=85.0, k=1.0, flutes=24, depth=2.0, lip=10.0),
}


CREST = 0.22         # flute ridge softness (0 = knife edge); ~0.6 mm crest radius at these sizes
DRILL_MARK = dict(d=6.0, depth=1.2)   # cone dimple on the planter foot: drill centre on every cast


def wet(p):
    s = PIECES[p.piece]
    g = 1 / (1 - p.shrinkage)
    return s["rim"] / 2 * g, s["foot"] / 2 * g, s["h"] * g, s["k"]


def profile(p, inset=0.0, top_cut=0.0):
    """(r, z) outline of the master body in print pose: rim at z=0, foot at z=H."""
    R, F, H, k = wet(p)
    t = np.linspace(0, 1, 60)
    r = F + (R - F) * (1 - t) ** k - inset
    z = t * (H - top_cut)
    return np.c_[np.r_[0, r, 0], np.r_[0, z, z[-1]]]


def body(p, inset=0.0, top_cut=0.0):
    sp = PIECES[p.piece]
    n = sp.get("flutes", 0)
    solid_ = Manifold.revolve(CrossSection([profile(p, inset, top_cut).tolist()]), 360 if n else 128)
    if not n:
        return solid_
    R, F, H, k = wet(p)
    depth, lip, fade = sp["depth"], sp["lip"], 6.0
    rmin = (F - inset) * 0.6

    e = CREST
    norm = math.sqrt(1 + e * e) - e

    def warp(v):
        # concave flutes with softly rounded ridges between them (a knife ridge becomes a
        # V in the plaster that slip will not fill, and chips once fired). Full depth
        # through the foot and fading out toward the rim: the groove only gets deeper in
        # the direction the cast leaves the mold, so the plaster ridge never catches
        x, y, z = v
        r = math.hypot(x, y)
        if r < rmin:
            return v
        t = min(1.0, max(0.0, (z - lip) / fade))
        w = t * t * (3 - 2 * t)
        a = math.atan2(y, x)
        sn = math.sin(n * a / 2)
        d = depth * w * (math.sqrt(sn * sn + e * e) - e) / norm
        f = (r - d) / r
        return (x * f, y * f, z)

    return solid_.warp(warp)


def _box(p):
    R, F, H, k = wet(p)
    return mold_box(R + p.spare_step + p.plaster, p.spare_h + H + p.plaster, clearance=p.clearance)


def plaster_ml(p):
    R, F, H, k = wet(p)
    rc = R + p.spare_step + p.plaster
    fill = math.pi * rc ** 2 * (p.spare_h + H + p.plaster)
    spare = math.pi * (R + p.spare_step) ** 2 * p.spare_h
    return (fill - spare - body(p).volume()) / 1000.0


def assembly(p):
    """The cottle slides down over the spigot and rests on the base flange."""
    return {"cottle": (0, 0, 3.0, 0, 0, 0)}


def checks(p):
    R, F, H, k = wet(p)
    base, tube, z0 = _box(p)
    ml = plaster_ml(p)
    return {
        "master": [
            dims(z=z0 + p.spare_h + H),
            solid((0, 0, z0 + p.spare_h / 2), (0, 0, z0 + p.spare_h + H / 2), (R + 1, 0, z0 + p.spare_h / 2)),
            empty((R + p.spare_step + p.plaster / 2, 0, z0 + 2),
                  *([(0, 0, z0 + p.spare_h + H - 0.4)] if p.piece == "fluted_planter" else [])),
            custom("plaster to mix", lambda ctx: (True, f"{ml:.0f} ml of mixed plaster")),
            flat_base(math.pi * (R + p.spare_step + p.plaster) ** 2 * 0.9),
            no_overhang(),
            single_body(),
        ],
        "cottle": [
            dims(z=4.0 + p.spare_h + H + p.plaster),
            empty((0, 0, 5)),
            no_overhang(),
            single_body(),
        ],
    }


def build(p):
    R, F, H, k = wet(p)
    base, tube, z0 = _box(p)
    spare = extrude(circle(0, 0, R + p.spare_step), p.spare_h + 0.1, z0 - 0.1)
    master = base + spare + body(p).translate((0, 0, z0 + p.spare_h))
    if p.piece == "fluted_planter":
        # a shallow cone pocket in the foot: the plaster gets a nub, every cast a dimple
        # in the middle of its floor to centre the drainage hole drill on (leather-hard)
        dm = DRILL_MARK
        cone = Manifold.cylinder(dm["depth"] + 0.5, 0.0, dm["d"] / 2 * (dm["depth"] + 0.5) / dm["depth"])
        master -= cone.translate((0, 0, z0 + p.spare_h + H - dm["depth"]))
    return {"master": master, "cottle": tube}


def casting(p):
    """What the kit makes, for the shop's cast render: the fired piece, right way up."""
    R, F, H, k = wet(p)
    floor = p.wall * 1.2
    shell = body(p) - body(p, inset=p.wall, top_cut=floor).translate((0, 0, -0.01))
    shell = shell.scale((1 - p.shrinkage,) * 3).rotate((180, 0, 0))
    return shell.translate((0, 0, -shell.bounding_box()[2]))
