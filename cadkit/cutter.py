"""Polymer-clay cutters: an outline blade, optional cut-through inner blades and imprint
blades, support bars across the back, and a matching pusher. Generalised from
`models/pumpkin_clay_cutter.py`; models supply only the artwork.

    from cadkit.cutter import *
    art = Art(outline=heart(30), cutouts=[...], imprints=[path, ...], bars_x=[0], bars_y=[2])
    parts = cutter_set(art, p)        # {"cutter_20": ..., "pusher_20": ..., ...}

Art is drawn at any scale; each cutter scales it so the outline's longest side is the
size named in `p.sizes` (mm). Blade thickness never scales: blades are 3 lines (outer)
and 2 lines (inner) of a 0.4 mm nozzle at the base, tapering over the top `taper_h` to a
single 0.45 mm line. The cutting face is vertical on the keep side and the taper sits on
the waste side.

Every cutter prints back plane and finger flange on the bed, edge up; every pusher
prints plate down, prongs up. Neither has overhangs.

`CUTTER_PARAMS` holds the defaults models merge into PARAMS; `cutter_checks(p)` and
`cutter_assembly(p)` give the matching checks and fit poses. Models set
`MIN_WALL = CUTTER_MIN_WALL` so the blade edges don't raise the thin-wall warning.
"""
from dataclasses import dataclass, field

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

from cadkit.checks import custom, dims, flat_base, no_overhang, single_body

CUTTER_PARAMS = dict(
    sizes=(20.0, 28.0, 36.0),  # longest side of each cut piece; one cutter + pusher per size
    height=12.0,          # back plane to cutting edge
    tip=0.45,             # cutting edge thickness (one 0.4 mm-nozzle line)
    outer_base=1.35,      # outer blade thickness below the taper (3 lines)
    inner_base=0.9,       # cut-through and imprint blade thickness below the taper (2 lines)
    taper_h=4.0,          # height of the tapered zone at the top of every blade
    imprint_recess=1.5,   # imprint blades stop this far short of the cutting edge
    flange_w=2.0,         # finger flange outside the outer blade
    flange_t=1.6,
    bar_w=1.8,            # support bars across the back
    bar_h=3.0,
    pusher_clearance=0.3,  # per side, between prongs and blades/bars
    pusher_plate=2.4,
)
CUTTER_MIN_WALL = 0.4     # blade edges are a single 0.45 mm line by design
SEG = 72


@dataclass
class Art:
    outline: CrossSection
    cutouts: list = field(default_factory=list)   # CrossSections removed from the piece
    imprints: list = field(default_factory=list)  # polylines pressed into the piece
    bars_x: list = field(default_factory=list)    # vertical support bars at these x (art units)
    bars_y: list = field(default_factory=list)    # horizontal support bars at these y
    cut_round: float = 0.3                        # corner rounding of cutouts, mm at final size


def off(cs, d):
    return cs.offset(d, JoinType.Round, 2.0, SEG) if d else cs


def rect(x0, y0, x1, y1):
    return CrossSection([[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]])


def rounded(cs, r):
    """Round convex then concave corners by r."""
    return off(off(off(off(cs, -r), r), r), -r)


def prism(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate((0, 0, z0))


def slices(make, z0, z1, steps, top_extra=0.0):
    """Stack of extruded slices from z0 to z1; make(f) gives the section, f in (0, 1].
    Slices overlap 0.05 mm so they fuse; the top one can run past z1 by top_extra."""
    out = Manifold()
    h = (z1 - z0) / steps
    for k in range(steps):
        cs = make((k + 1) / steps).simplify(0.002)
        if cs.is_empty():
            continue
        top = z0 + (k + 1) * h + (0.05 if k < steps - 1 else top_extra)
        out += Manifold.extrude(cs, top - (z0 + k * h)).translate((0, 0, z0 + k * h))
    return out


def stroke_cs(path, width):
    from cadkit.relief import stroke
    return stroke(path, width)


def _cutter(art, size, p):
    x0, y0, x1, y1 = art.outline.bounds()
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    s = size / max(x1 - x0, y1 - y0)
    xf = lambda cs: cs.translate((-c[0], -c[1])).scale((s, s))

    O = xf(art.outline)
    F = CrossSection()
    for cut in art.cutouts:
        F += rounded(xf(cut), art.cut_round)
    paths = [(np.asarray(path, float) - c) * s for path in art.imprints]
    H, T = p.height, p.taper_h
    zt = H - T
    steps = max(4, int(round(T / 0.2)))
    lerp = lambda a, b, f: a + (b - a) * f

    outer = (prism(off(O, p.outer_base + p.flange_w), 0, p.flange_t)
             + prism(off(O, p.outer_base), p.flange_t - 0.1, zt + 0.05)
             + slices(lambda f: off(O, lerp(p.outer_base, p.tip, f)), zt, H, steps))
    outer -= prism(O, -1, H + 1)
    cutter = outer

    if not F.is_empty():
        inner = prism(F, 0, H)
        inner -= prism(off(F, -p.inner_base), -1, zt + 0.05)
        inner -= slices(lambda f: off(F, -lerp(p.inner_base, p.tip, f)), zt, H, steps, top_extra=1.0)
        cutter += inner

    # imprint lines may run past the outline; they are clipped to the middle of the
    # outer blade, so they always join it and never stick out of the cutter
    Hr = H - p.imprint_recess
    keep = off(O, p.outer_base / 2)
    ribs_cs = CrossSection()
    for path in paths:
        ribs_cs += stroke_cs(path, p.inner_base) ^ keep
        cutter += prism(stroke_cs(path, p.inner_base) ^ keep, 0, Hr - T + 0.05)
        cutter += slices(lambda f, path=path: stroke_cs(path, lerp(p.inner_base, p.tip, f)) ^ keep,
                         Hr - T, Hr, steps)

    bars_cs = CrossSection()
    big = 2 * size
    for x in art.bars_x:
        x = (x - c[0]) * s
        bars_cs += rect(x - p.bar_w / 2, -big, x + p.bar_w / 2, big)
    for y in art.bars_y:
        y = (y - c[1]) * s
        bars_cs += rect(-big, y - p.bar_w / 2, big, y + p.bar_w / 2)
    if not bars_cs.is_empty():
        bars_cs = bars_cs ^ off(O, p.outer_base / 2)
        cutter += prism(bars_cs, 0, p.bar_h)

    # pusher: prongs fill every open gap in the back, clear of blades and bars
    clr = p.pusher_clearance
    blocked = off(F + ribs_cs + bars_cs, clr) if not (F + ribs_cs + bars_cs).is_empty() else CrossSection()
    room = off(O, -clr) - blocked
    if not F.is_empty():
        room += off(F, -p.inner_base - clr) - off(bars_cs, clr)
    room = off(off(room, -0.6), 0.6)  # drop slivers too thin to print as a 12 mm prong
    prongs = CrossSection()
    for piece in room.decompose():
        if piece.area() >= 3.0:
            prongs += piece
    plate = off(O, p.outer_base + p.flange_w)
    pusher = (prism(plate, 0, p.pusher_plate)
              + prism(prongs, p.pusher_plate - 0.1, p.pusher_plate + H - 0.2))
    return cutter, pusher


def _tag(size):
    return f"{size:g}".replace(".", "_")


def cutter_set(art, p):
    """{"cutter_<size>": Manifold, "pusher_<size>": Manifold} for every size in p.sizes."""
    out = {}
    for size in p.sizes:
        cutter, pusher = _cutter(art, float(size), p)
        out[f"cutter_{_tag(size)}"] = cutter
        out[f"pusher_{_tag(size)}"] = pusher
    return out


def cutter_checks(p, extra=None):
    """Per-part checks: overall size (outline + blade + flange), height, one body, flat on
    the bed, no overhangs, and a pusher that reaches through to within 0.2 mm of the edge.
    `extra` maps a size to more checks for that cutter (e.g. solid()/empty() probes)."""
    rim = 2 * (p.outer_base + p.flange_w)
    out = {}
    for size in p.sizes:
        long_side = (size + rim - 0.6, size + rim + 0.6)
        fit_long = custom(f"longest side {size:g} mm + rim",
                          lambda ctx, lo=long_side: lo[0] <= max(ctx.tm.extents[:2]) <= lo[1])
        out[f"cutter_{_tag(size)}"] = [fit_long, dims(z=p.height), single_body(), flat_base(20),
                                        no_overhang()] + list((extra or {}).get(size, []))
        out[f"pusher_{_tag(size)}"] = [fit_long, dims(z=p.pusher_plate + p.height - 0.2),
                                        single_body(), flat_base(20), no_overhang()]
    return out


def cutter_assembly(p, spacing=80.0):
    """Each pusher sits under its cutter with the prongs pushed fully in; the sizes are
    spread along X so only matching cutter/pusher pairs are compared."""
    out = {}
    for i, size in enumerate(p.sizes):
        out[f"cutter_{_tag(size)}"] = (i * spacing, 0, 0, 0, 0, 0)
        out[f"pusher_{_tag(size)}"] = (i * spacing, 0, -p.pusher_plate - 0.2, 0, 0, 0)
    return out
