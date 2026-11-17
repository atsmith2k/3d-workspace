"""Print-in-place strap chains with hot-glue anchor tabs for the Boo's Door costume.

The chain is a real chain: closed oval links, each threaded through the next, so the
links cannot come apart (each pair is topologically linked, not just hooked over one
another). Neighbouring links stand at +45 and -45 deg about the chain axis, which
makes every face of a link either vertical, a 45 deg slope or a narrow chamfer, so the
whole chain prints in place without supports and bends freely in every direction to
lie over a shoulder. The wire is an octagon (6 x 5 mm with 1.2 mm chamfers), so the
edges that touch the wearer are blunt.

Strength: a link fails by bending at its ends, where the neighbour pulls on the middle
of the end arc and the arc runs across the print layers at 45 deg. So the wire is
wider in the link plane (6 mm, the bending direction) than across it (5 mm, which sets
the opening the neighbour passes through), and every link has a stud across its middle,
as in anchor chain: it stops the link pinching shut under load, which is what drives
the bending at the ends, and it halves the bridge span of each link's top rail.
Print time is dominated by the 45 deg faces and bridges of each link, not by the layer
count, so long links (34 mm pitch, 16 pieces per shoulder strap) keep it down.

style=shoulder (default): glue tab, chain, glue tab. Print two. Each tab is hot glued
(and optionally bolted, 1/4-20) to the inner face of a cardboard board; the chain runs
over the shoulder to the matching tab on the other board. Replaces the 30" webbing
straps of step 25 in the costume build instructions.

style=waist: a shorter side strap that hooks on and off. Part "strap" is a glue tab, a
chain and a flat ring; part "receiver" is a stand-off J hook on a glue plate. At the
waist the strap leaves the back board at about a right angle, so the pull is straight
out of the board: the hook's shank stands out of the board along that pull and its tip
turns up. Drop the ring over the tip so it lies on the shank; the strap pulls the ring's
far bar against the tip, and a lip on top of the tip, pointing back at the board, stops
it lifting off while there is tension. To unhook, slack the strap, push the ring toward
the board past the lip and lift. Print one of each per side (two sets).
The receiver prints on its side (hook profile flat on the bed) so the hook needs no
supports and its layers run along the hook, the strong way. Replaces the 1" webbing
waist tabs and buckles of step 26.

Spec:
  object:       over-the-shoulder strap linking the front (F) and back (B) costume boards
  overall:      printed as a U, about 208 x 226 x 17 mm; one strap, print it twice
  mates with:   cardboard boards, hot glued; tab hole 7.0 mm clears the planned 1/4-20 strap
                bolt (6.35 mm + 0.45 clearance + 0.2 print allowance) at (4-3/8", 3-1/4")
  length:       574 mm (22.6") hole-to-hole pulled taut; too long is fixed by gluing the
                tabs lower on the boards, too short is not fixable, so it errs long
  orientation:  flat on the bed as printed; links interlock as printed, no assembly
  links:        stud link, 46 x 22 mm outside, 34 x 10 mm inside, 6 x 5 mm octagonal wire,
                3.6 mm stud; taut pitch 34 mm, printed at 27 mm; alternate links tilted
                +-45 deg, each sunk 0.8 mm into the bed for a ~3 mm wide footprint
  tabs:         54 x 36 x 2.8 mm plate fused under the end link, 1/4-20 hole, four 5 mm
                glue-rivet holes
  supports:     none (the top rail of each link is a short bridge between its ends)
  tolerances:   >= 0.6 mm gap between neighbouring links everywhere as printed (U turn incl.)
  waist strap:  453 mm (17.8") tab hole to the hook tip, taut; glue the tab on the front
                board's inner face near its side edge (X 0-4"), wrap the chain round the
                side edges, glue the receiver on the back board's inner face wherever
                takes up the slack (further from the edge = tighter)
  latch:        ring plate: hole 22 x 24 mm (3 mm corner radii), 7.5 x 2.8 mm far bar (the one
                the hook catches), 6 x 4 mm side bars (48 mm2, about a link's 2 x 27 mm2),
                plate 4 mm under the end link
  receiver:     J hook 20 mm wide; 60 x 20 mm glue face on a 3 mm plate with two diamond
                glue-rivet holes; 6 mm thick shank standing 21 mm out of the board with a
                9 mm gusset under it; 12 mm bight (board face to tip); 6 mm tip leg rising
                16 mm above the shank; 3 mm lip toward the board with a 45 deg underside,
                leaving 9 mm under it for the 7.5 mm far bar; 1.2 mm root fillets
  mounting:     glue it to the back board's inner face with the tip pointing up
                and the shank straight out toward the front board

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
import math
from functools import lru_cache

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "Print-in-place shoulder strap chain with hot-glue anchor tabs for the Boo's Door costume"

PARAMS = dict(
    style="shoulder",    # shoulder: tab to tab; waist: tab to ring + hook receiver part
    length=586.0,        # shoulder: tab hole to tab hole, pulled taut
    waist_length=450.0,  # waist: tab hole to the hook tip, pulled taut
    wire=5.0,            # link wire thickness across the link plane (sets the opening width)
    wire_w=6.0,          # link wire width in the link plane (bending strength at the ends)
    chamfer=1.2,         # wire corners cut (octagon)
    inner_len=34.0,      # link opening; also the taut pitch
    inner_w=10.0,
    stud=3.6,            # cross bar at mid-link (stud-link chain); 0 for none
    tilt=45.0,           # links alternate +tilt / -tilt about the chain axis
    sink=0.8,            # links sunk into the bed for a wider footprint
    pitch=27.0,          # link spacing as printed
    turn_r=95.0,         # radius of the printed U turn
    bar_h=2.8,           # tab / ring plate thickness
    plate_len=50.0,      # tab plate length behind its link's centre
    plate_w=36.0,
    bolt_hole=7.0,
    glue_hole=5.0,
    ring_hole=22.0,      # ring opening along the strap
    ring_bar=7.5,        # ring far bar width (the bar the hook bends)
    hook_w=20.0,         # hook width (the receiver's print height)
)

HOOK_T = 3.0             # receiver glue plate thickness
SEAT = 6.0               # receiver shank thickness; its top is where the ring sits
TIP_IN = 15.0            # tip leg inner face, out from the glue face (bight = TIP_IN - HOOK_T)
TIP_T = 6.0              # tip leg thickness
TIP_H = 16.0             # tip height above the shank
LIP = 3.0                # lip reaching back from the tip toward the board
GLUE_V = (-15.0, 31.0)   # glue-rivet holes along the plate
PLATE_X = -2.0           # end plates stop here (link frame), clear of the next link
PAD_H = 4.0              # height of the pad fusing the end link to its plate
RING_SIDE = 6.0          # ring side bar width
CIRC = 48                # segments around a link end


def _box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def _octagon(p, cx, cy):
    """Wire section: wire_w along the first axis (in the link plane), wire along the second."""
    a, b, c = p.wire_w / 2, p.wire / 2, p.chamfer
    return CrossSection([[(cx + a, cy - b + c), (cx + a, cy + b - c), (cx + a - c, cy + b),
                          (cx - a + c, cy + b), (cx - a, cy + b - c), (cx - a, cy - b + c),
                          (cx - a + c, cy - b), (cx + a - c, cy - b)]])


def _ring(p):
    """Flat oval link in the XY plane, centred on the origin, long axis along X, with an
    optional stud across the middle (kept inside the wire's chamfers, no coplanar faces)."""
    rc = p.inner_w / 2 + p.wire_w / 2                    # wire centre-line radius at the ends
    ls = p.inner_len - p.inner_w                         # straight length
    half = Manifold.revolve(_octagon(p, rc, 0), CIRC, 180)   # +x -> +y -> -x, height = z
    ends = [half.rotate((0, 0, -90)).translate((ls / 2, 0, 0)),
            half.rotate((0, 0, 90)).translate((-ls / 2, 0, 0))]
    rails = []
    for y in (-rc, rc):
        r = Manifold.extrude(_octagon(p, y, 0), ls)      # (y, z) profile along +z
        rails.append(r.warp(lambda v: (v[2] - ls / 2, v[0], v[1])))   # cyclic: a rotation
    if p.stud:
        h = p.wire / 2 - p.chamfer
        rails.append(_box(-p.stud / 2, p.stud / 2, -rc, rc, -h, h))
    return Manifold.batch_boolean(ends + rails, OpType.Add)


def _floor(m, p):
    """Sit a tilted link on the bed, sunk p.sink and cut flat at z=0."""
    m = m.translate((0, 0, -m.bounding_box()[2] - p.sink))
    return m ^ _box(-100, 100, -100, 100, 0, 100)


@lru_cache(maxsize=8)
def _link(key, sign):
    p = type("P", (), dict(key))
    return _floor(_ring(p).rotate((sign * p.tilt, 0, 0)), p)


def link(p, k):
    return _link(_key(p), 1 if k % 2 == 0 else -1)


def _pad(p, k):
    """Block under link k's low rail (the side away from link k+1) that fuses it to a plate."""
    sy = -1 if k % 2 == 0 else 1                         # +tilt puts the low rail at -y
    return _box(-p.inner_len / 2 - 2, PLATE_X, *sorted((sy * 1.0, sy * 9.0)), 0, PAD_H)


def tab(p, k):
    """Link k fused onto a glue plate reaching back to -plate_len (link frame)."""
    t, pw = p.bar_h, p.plate_w / 2
    plate = _box(-p.plate_len, PLATE_X, -pw, pw, 0, t) + _pad(p, k)
    hx = -p.plate_len + 18
    holes = [circle(hx, 0, p.bolt_hole / 2)]
    for gx in (-p.plate_len + 6, -22):
        for gy in (-12, 12):
            holes.append(circle(gx, gy, p.glue_hole / 2))
    cut = extrude(CrossSection.batch_boolean(holes, OpType.Add), t + 2, -1)
    return (plate - cut) + link(p, k), -hx               # (solid, hole distance behind centre)


def _rrect(x0, x1, y0, y1, r):
    return CrossSection.square((x1 - x0 - 2 * r, y1 - y0 - 2 * r)).translate(
        (x0 + r, y0 + r)).offset(r, ROUND, circular_segments=32)


def ring_end(p, k):
    """Link k fused onto a flat ring plate behind it; the hook catches the ring's far bar.
    Only the far bar has to slide under the hook tip, so it stays bar_h thin; the side
    bars and the plate under the link stand PAD_H tall (they pass beside the hook), so
    the ring is as strong in tension as a link. Rounded hole corners, no notch to tear from."""
    hw = p.hook_w / 2 + 2
    near = p.inner_len / 2 + p.wire_w + 2                # hole starts clear of the link
    far = near + p.ring_hole                             # far bar inner face behind centre
    flat = (_rrect(-far - p.ring_bar, PLATE_X, -hw - RING_SIDE, hw + RING_SIDE, 6)
            - _rrect(-far, -near, -hw, hw, 3))
    plate = Manifold.extrude(flat, PAD_H) - _box(-200, -far, -100, 100, p.bar_h, 10)
    return (plate + _pad(p, k)) + link(p, k), far


def receiver(p):
    """Stand-off J hook in its print pose: the side profile below lies on the bed and is
    extruded hook_w up. Profile axes: u (x) out from the board, v (y) up as worn.
    The glue plate is the u=0 face. A shank stands straight out of the board, a tip
    leg rises from its end, and a lip on top of the tip points back at the board.
    Worn, the strap pulls straight out (+u): the ring's far bar sits on the shank in
    the bight, pressed against the tip leg, and the lip stops it lifting off. Slack
    the strap, push the ring toward the board past the lip and lift it off."""
    t, s, ti = HOOK_T, SEAT, TIP_IN
    prof = CrossSection.batch_boolean([
        CrossSection.square((t, 60)).translate((0, -22)),                 # glue plate
        CrossSection.square((ti + TIP_T, s)),                             # shank
        CrossSection.square((TIP_T, s + TIP_H)).translate((ti, 0)),       # tip leg
        CrossSection([[(ti - LIP, s + TIP_H - 3), (ti, s + TIP_H - 6),
                       (ti, s + TIP_H), (ti - LIP, s + TIP_H)]]),         # lip, 45 deg under
        CrossSection([[(t - 0.1, -9), (t + 9, 0.1), (t - 0.1, 0.1)]]),    # gusset under shank
    ], OpType.Add)
    prof = prof.offset(1.2, ROUND, circular_segments=24).offset(-1.2, ROUND, circular_segments=24)
    prof = prof.offset(-0.8, ROUND, circular_segments=24).offset(0.8, ROUND, circular_segments=24)
    hook = Manifold.extrude(prof, p.hook_w)
    # diamond glue-rivet holes through the plate (along u); 45 deg roofs as printed
    d = CrossSection([[(0, -2.5), (2.5, 0), (0, 2.5), (-2.5, 0)]])
    holes = [Manifold.extrude(d.translate((-p.hook_w / 2, gv)), t + 2)   # (x, y, z) -> (z-1, y, -x)
             .warp(lambda v: (v[2] - 1, v[1], -v[0])) for gv in GLUE_V]   # is a rotation
    return hook - Manifold.batch_boolean(holes, OpType.Add)


def _waist(p):
    return p.style == "waist"


def _path(p, n_joints):
    """Centre line of the printed U: straight leg along +x, half turn, leg back along -x.
    Link k's centre sits at arc length k * pitch."""
    R = p.turn_r
    total = n_joints * p.pitch
    leg = (total - math.pi * R) / 2

    def at(s):
        if s <= leg:
            return s, 0.0, 0.0
        if s <= leg + math.pi * R:
            th = -math.pi / 2 + (s - leg) / R
            return leg + R * math.cos(th), R + R * math.sin(th), th + math.pi / 2
        return leg - (s - leg - math.pi * R), 2 * R, math.pi
    return at


def _ends(p):
    """Distances from each end link's centre back to its bolt hole / the hook post."""
    d = tab(p, 0)[1]
    return (d, ring_end(p, 0)[1]) if _waist(p) else (d, d)


def joints(p):
    length = p.waist_length if _waist(p) else p.length
    return max(2, round((length - sum(_ends(p))) / p.inner_len))


@lru_cache(maxsize=4)
def _elements(key):
    p = type("P", (), dict(key))
    nj = joints(p)
    at = _path(p, nj)
    out = []
    for k in range(nj + 1):
        if k == 0:
            m = tab(p, k)[0]
        elif k == nj:
            far = ring_end(p, k)[0] if _waist(p) else tab(p, k)[0]
            m = far.rotate((0, 0, 180)).mirror((0, 1, 0))  # plate ahead; mirror keeps k's tilt
        else:
            m = link(p, k)
        x, y, a = at(k * p.pitch)
        out.append(m.rotate((0, 0, math.degrees(a))).translate((x, y, 0)))
    return out


def _key(p):
    return tuple(sorted((k, getattr(p, k)) for k in PARAMS))


def min_link_gap(p):
    els = _elements(_key(p))
    g = 99.0
    for i in range(len(els)):
        for j in (i + 1, i + 2):
            if j < len(els):
                g = min(g, els[i].min_gap(els[j], 3.0))
    return g


def height(p):
    return _link(_key(p), 1).bounding_box()[5]


def hook_pose(p):
    """Last link centre and strap heading at the end of the second leg (print pose)."""
    nj = joints(p)
    return _path(p, nj)(nj * p.pitch)


def assembly(p):
    """Worn: the ring lies flat on the hook's shank (strap print pose as is) with its far
    bar 1 mm off the tip leg (clear of the 1.2 mm root fillet it rides on under load). The receiver stands up (rx 90: v up, u along x) and
    turns so u points back along the strap, toward the chain."""
    if not _waist(p):
        return {}
    x, y, a = hook_pose(p)
    h = (math.cos(a), math.sin(a))
    lat = (-math.sin(a), math.cos(a))                    # where the receiver's w axis goes
    d = _ends(p)[1] - 1.0 + TIP_IN                       # glue face; far bar 1 mm off the tip (its fillet)
    ox = x + d * h[0] - p.hook_w / 2 * lat[0]
    oy = y + d * h[1] - p.hook_w / 2 * lat[1]
    return {"receiver": (ox, oy, -SEAT - 0.1, 90, 0, math.degrees(a) + 180)}


def checks(p):
    nj = joints(p)
    target = p.waist_length if _waist(p) else p.length
    length = nj * p.inner_len + sum(_ends(p))
    strap = [
        dims(z=height(p)),
        custom("link_gap", lambda c: (min_link_gap(p) >= 0.6, f"min gap {min_link_gap(p):.2f} mm")),
        custom("taut_length", lambda c: (abs(length - target) <= p.inner_len,
                                         f"{length:.0f} mm end to end, {nj + 1} pieces")),
        custom("bodies", lambda c: (c.report.bodies == nj + 1 and c.report.watertight,
                                    f"{c.report.bodies} separate links, {'watertight' if c.report.watertight else 'NOT watertight'}")),
        no_overhang(),
        fits_bed(),
    ]
    if not _waist(p):
        return strap
    w = p.hook_w
    free = TIP_IN - LIP - HOOK_T                         # bight width under the lip
    return {"strap": strap, "receiver": [
        dims(x=TIP_IN + TIP_T, y=60, z=w),
        single_body(),
        no_overhang(),
        flat_base(300),
        solid((18, 15, w / 2), (13.5, 20.5, w / 2), (8, 3, w / 2), (4.5, -4, w / 2)),  # tip, lip, shank, gusset
        empty((8, 12, w / 2), (13.5, 10, w / 2)),                        # bight, under the lip
        empty(*[(1.5, gv, w / 2) for gv in GLUE_V]),                     # glue holes
        custom("ring_clears_lip", lambda c: (free >= p.ring_bar + 1,
               f"far bar {p.ring_bar} mm, {free:.1f} mm free under the lip")),
    ]}


def build(p):
    strap = Manifold.batch_boolean(list(_elements(_key(p))), OpType.Add)
    return {"strap": strap, "receiver": receiver(p)} if _waist(p) else strap
