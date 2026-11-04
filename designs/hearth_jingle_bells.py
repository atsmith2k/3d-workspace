"""Jingle Bells: two gold sleigh bells hanging from a red bow with holly.

Spec:
  object:       jingle bells for stockings, napkins, sweatshirts and gift bags
  overall:      `size` mm tall (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens with tear-away
  threads:      green (holly), gold (bells), tan (rims, highlights), cocoa (clappers),
                berry (berries), red (bow): 6 colours
  must have:    two 24 x 30 mm bells swung out +-22 deg, each with a tan rim band, a tan
                highlight and a cocoa clapper; a 32 mm red bow over their tops; two holly
                leaves and three berries behind the bow, and a third leaf hanging down
                between the bells
  density:      the bow knocks out the bells and holly; details knock out the bells
  coverage:     the tails run on into the slim wedges between them and the loops (bare,
                they opened up once the fabric pulled in); the slot allowance stays 5 mm2
"""
from shapely.affinity import rotate as _rot, translate as _tr

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hearth import C_, SIZES, fit, holly_sprig, hoop_for, product, standard_checks

DESCRIPTION = "Two gold jingle bells hanging from a red bow with holly"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Jingle Bells Embroidery Design",
    "Two gold jingle bells hanging from a red bow with a sprig of holly",
    ["jingle bells", "christmas bells", "sleigh bells", "holly", "christmas stocking",
     "christmas napkin"],
    "A pair of gold jingle bells swinging from a red ribbon bow with a sprig of holly and "
    "berries.\n\nGreat on stockings, napkins, sweatshirts and gift bags.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 12000, between_mm2=5.0)   # the bow's loop/tail wedges


def _bell():
    """One bell, mouth down, its top at (0, 14): (bell, rim, highlight, clapper)."""
    bell = smooth([(0, 14), (5, 12.5), (7.5, 6), (8.5, -2), (12, -9), (12.5, -12), (-12.5, -12), (-12, -9),
                   (-8.5, -2), (-7.5, 6), (-5, 12.5)], 8).buffer(0)
    rim = rounded_rect(25.5, 3.6, 1.6, 0, -11.2).intersection(bell.buffer(0.2))
    hi = smooth([(-4.0, 10), (-5.2, 5), (-6.2, -2), (-8.0, -7), (-6.4, -7.4), (-4.4, -1.5), (-3.2, 6)], 6).buffer(0)
    clapper = circle(0, -13.6, 2.4)
    return bell, rim, hi, clapper


def _hang(g, deg, x, y):
    return _tr(_rot(g, deg, origin=(0, 14)), x, y - 14)


def art():
    d = Design()
    bells = []
    for deg, x in ((-22, -7), (22, 7)):
        bells.append([_hang(g, deg, x, 15) for g in _bell()])
    bow = [move(g, 0, 15) for g in M.bow(32)]
    # each tail runs on into the slim wedge between it and its loop (under 1 mm across;
    # left bare it was 2-3 mm2 at 5x7 and grew past 4 once the fabric pulled in), and
    # its knockout keeps its tip (min_width 0.5, not 1.0: rounded off, the tail left a
    # notch at the knot)
    lo, ro, knot, lt, rt = bow
    wedges = union(*bow).buffer(0.5).buffer(-0.5).difference(union(*bow))
    for w in getattr(wedges, "geoms", [wedges]):
        if w.area > 0.5:                         # the two loop/tail wedges, not the specks
            if w.distance(lt) <= w.distance(rt):
                lt = lt.union(w.buffer(0.05))
            else:
                rt = rt.union(w.buffer(0.05))
    bow = [lo, ro, knot, lt, rt]
    bow_all = union(*bow)
    leaves, veins, berries = holly_sprig(0, 18, deg=0, length=16)
    leaves.append(move(rotate(M.holly_leaf(21, 8.5, spikes=3), -90, origin=(0, 0)), 0, 14))   # fills the V
    left, right = bells
    d.fill(knockout(union(*leaves), bow_all, *berries, left[0], right[0]), C_["green"], angle=None, name="holly")
    for b, rim, hi, cl in bells:
        d.fill(knockout(b, rim, hi, cl, bow_all), C_["gold"], angle=90, name="bell")
    for b, rim, hi, cl in bells:
        d.fill(knockout(rim, bow_all), C_["tan"], angle=0, name="rim")
        d.fill(knockout(hi, bow_all), C_["tan"], angle=80, underlay=False, name="highlight")
    for b, rim, hi, cl in bells:
        d.fill(knockout(cl, b), C_["cocoa"], angle=45, name="clapper")
    for g in berries:
        g = knockout(g, bow_all)
        if not g.is_empty and g.area > 2:
            d.fill(g, C_["berry"], angle=45, underlay=False, name="berry")
    # sew_bow's order and angles, with the tails' tips kept (above)
    d.fill(knockout(lt, lo, ro, knot, min_width=0.5), C_["red"], angle=75, name="bow tail")
    d.fill(knockout(rt, lo, ro, knot, min_width=0.5), C_["red"], angle=105, name="bow tail")
    d.fill(knockout(lo, knot), C_["red"], angle=150, name="bow loop")
    d.fill(knockout(ro, knot), C_["red"], angle=30, name="bow loop")
    d.fill(knot, C_["red"], angle=90, name="bow knot")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
