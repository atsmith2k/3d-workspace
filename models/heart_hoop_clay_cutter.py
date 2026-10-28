"""Heart hoop polymer-clay cutter set: an open heart (a heart with a heart-shaped window)
for statement earrings, in three sizes with a pusher for each.

Press the cutter into rolled clay, lift, and push the piece out with the pusher: the
window comes out with it in one go, so both hearts in a pair match. Each cutter has a
flat back and a finger flange, a sharp single-line edge, and support bars across the
back that sit well clear of the clay. Prints edge-up with no supports on a Bambu A1 or
A1 mini, about 15 minutes per cutter.

Spec:
  object:       polymer-clay cutter set, open heart (hoop) earring shape
  overall:      cut pieces 20, 28 and 36 mm across; cutters 6.7 mm larger (blade + flange),
                12 mm tall; pushers 14.2 mm tall
  mates with:   its pusher: prongs 0.3 mm clear of every blade and bar per side
  orientation:  cutter back plane on the bed, cutting edge up; pusher plate down, prongs up;
                no supports
  must have:    heart outline blade; heart window cut through (rim 26% of the width);
                0.45 mm cutting edge; finger flange 2 mm
  tolerances:   cut size +-0.3 mm; blade edge one 0.4 mm-nozzle line

Units: mm. Z is up. Don't scale the STL to resize (it changes blade thickness):
use --set sizes=18,24,30.
"""
from cadkit.checks import *
from cadkit.cutter import *
from cadkit.relief import heart

DESCRIPTION = "Open heart (hoop) polymer-clay earring cutter set, 3 sizes with pushers"

PRODUCT = dict(
    title="Heart Hoop Polymer Clay Cutter Set (3 sizes)",
    category="clay-cutters",
    tags=["polymer clay cutter", "clay cutter", "earring cutter", "heart", "valentine",
          "open heart", "hoop", "jewelry making", "clay earrings", "cutter set"],
    printers=["a1", "a1mini"],
    cast_material="polymer clay (Sculpey, Fimo, Cernit) rolled 2-3 mm",
    post_processing=("Print in PLA at 0.20 mm. Dust the edge with cornstarch so clay releases. "
                     "Press, wiggle, lift, then push the piece out with the matching pusher."),
)
LICENSE_NOTES = None   # original design
MIN_WALL = CUTTER_MIN_WALL

PARAMS = dict(CUTTER_PARAMS, window=0.48)   # window width as a share of the heart width


def art(p):
    outer = heart(30)
    window = heart(30 * p.window).translate((0, -1.6))
    return Art(outline=outer, cutouts=[window], bars_x=[0], bars_y=[-2.0])


def checks(p):
    return cutter_checks(p)


def assembly(p):
    return cutter_assembly(p)


def build(p):
    return cutter_set(art(p), p)
