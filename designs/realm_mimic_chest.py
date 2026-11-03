"""Treasure Chest Mimic: a toothy treasure chest with a lolling tongue, one eye and spilled coins.

Spec:
  object:       a cute-creepy chest monster (generic tabletop mimic) for tees, dice bags,
                totes, hoodies and game-night patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; dice bags and wovens with tear-away
  threads:      wood (planks), pewter (metal bands and rims), white (teeth, eye),
                bark (mouth, plank seams, slit pupil, chest outline), wine (tongue),
                gold (coins, lock plate), brass (coin rims): 7 colours
  must have:    a 76 x 32 mm chest base and an 80 mm wide domed lid raised over a 70 x 22 mm
                dark mouth; eight 7 x 8 mm lower and seven 7 x 7 mm upper teeth (offset); 6 mm
                pewter bands at x = +-27 on base and lid, 3 mm pewter rims along the mouth;
                a tongue widening from 9.6 to 13.6 mm, in two halves (a centre fold) lolling over the front past the chest's foot; a 16 x 12 mm
                eye with a slit pupil on the lid; a 10 x 10 mm gold lock plate; three
                8-9 mm coins with 1.2 mm brass rims spilled on the left
  density:      lower fills knock out everything sewn over them; plank seams stop 1.5 mm
                clear of bands, lock and tongue; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Treasure chest mimic with sharp teeth, a long tongue, one eye and spilled coins"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Treasure Chest Mimic Embroidery Design",
    "A wooden treasure chest that bites back: sharp teeth, a long pink tongue, one slit eye "
    "and gold coins spilling out",
    ["mimic", "treasure chest", "chest monster", "tabletop rpg", "dungeon crawl",
     "game night", "dungeon master", "dice bag", "cute creepy", "monster"],
    "Never trust a treasure chest: this one has a mouthful of sharp white teeth, a long pink "
    "tongue lolling over its iron bands, a single slit eye on the lid and a few gold coins "
    "spilled as bait. Cute, creepy and instantly recognisable to any dungeon crawler.\n\n"
    "Great on tees, hoodies, dice bags, totes and game-night patches.",
    mockups=("tshirt", "tote"),
)

OUT = 1.6    # chest outline satin
RIM = 1.2    # coin rim satin


def checks(p):
    return standard_checks(p, 7, 16000)


def _round(g, r=0.5):
    return g.buffer(-r).buffer(r)


def _seams(paths, avoid):
    """Plank seams as bean runs, cut 1.5 mm clear of everything in `avoid`."""
    out = []
    for pts in paths:
        cut = LineString(pts).difference(avoid.buffer(1.5))
        for seg in getattr(cut, "geoms", [cut]):
            if seg.length > 3.0:
                out.append(np.asarray(seg.coords))
    return out


def art():
    d = Design()
    base = rounded_rect(76, 32, 3, 0, -24)                       # y -40..-8
    lid = union(rect(80, 13, 0, 17.5), ellipse(0, 24, 40, 15).intersection(rect(90, 30, 0, 39)))
    lid = _round(lid, 1.5)                                        # y 11..39
    mouth = rounded_rect(70, 22, 7, 0, 1.5)                       # y -9.5..12.5
    chest = union(base, lid)
    base_rim = base.intersection(rect(80, 3.2, 0, -9.6))
    lid_rim = lid.intersection(rect(84, 3.2, 0, 12.6))
    bands = union(*[base.intersection(rect(6, 40, x, -24)) for x in (-27, 27)],
                  *[lid.intersection(rect(6, 40, x, 27)) for x in (-27, 27)])
    metal = union(base_rim, lid_rim, bands)
    lower = [_round(poly([(x - 3.5, -8.6), (x, -0.6), (x + 3.5, -8.6)]), 0.4)
             for x in np.arange(-24.5, 25, 7.0)]
    upper = [_round(poly([(x - 3.5, 11.6), (x, 4.6), (x + 3.5, 11.6)]), 0.4)
             for x in np.arange(-21.0, 22, 7.0)]
    teeth = union(*lower, *upper)
    tongue_path = LineString(spline(np.array([(14, 1), (18, -9), (19.5, -22), (16.5, -34),
                                              (18, -43)]), 10))
    pts = np.asarray(tongue_path.coords)
    rad = np.linspace(4.8, 6.8, len(pts))                     # narrow root, broad round tip
    tongue = union(*[circle(x, y, r) for (x, y), r in zip(pts, rad)],
                   *[LineString(pts[i:i + 2]).buffer(min(rad[i], rad[i + 1]))
                     for i in range(len(pts) - 1)]).simplify(0.05)
    # two halves sewn at different angles read as the tongue's centre fold
    t_left = tongue.intersection(tongue_path.buffer(8.0, single_sided=True))
    t_right = tongue.difference(t_left)
    eye = ellipse(0, 26, 8, 6)
    pupil = ellipse(0, 26, 1.6, 4.8)
    lock = rounded_rect(10, 10, 1.6, 0, -17)
    keyhole = union(circle(0, -16, 1.4), rect(1.4, 3.5, 0, -18.2))
    coins = [circle(-33, -46.5, 4.5), circle(-22.5, -47.5, 4.0), circle(-43.5, -45, 4.0)]
    gold = union(lock.difference(keyhole), *coins)
    seams = _seams([[(-38, -19), (38, -19)], [(-38, -30), (38, -30)],
                    [(-40, 20), (40, 20)], [(-38, 30), (38, 30)]],
                   union(metal, lock, tongue, eye, mouth))

    d.fill(knockout(tuck(chest, OUT), mouth, metal, eye, tongue, gold), C_["wood"], angle=0,
           name="planks")
    # the outline satin is centred on the chest edge: nothing else sews under it
    ring = chest.boundary.buffer(OUT / 2)
    d.fill(knockout(metal, mouth, tongue, ring), C_["pewter"], angle=90, name="bands")
    d.fill(knockout(teeth, tongue, ring), C_["white"], angle=90, name="teeth")
    d.fill(knockout(eye, pupil), C_["white"], angle=0, name="eye")
    d.fill(knockout(mouth, teeth, tongue, ring), C_["bark"], angle=0, name="mouth")
    for s in seams:
        d.run(s, C_["bark"], bean=1, name="plank seam", trim_after=True)
    d.fill(pupil, C_["bark"], angle=90, name="pupil")
    d.outline(chest, C_["bark"], width=OUT, name="chest outline")
    d.fill(t_left, C_["wine"], angle=65, spacing=0.42, name="tongue")
    d.fill(t_right, C_["wine"], angle=115, spacing=0.42, name="tongue")
    d.fill(lock.difference(keyhole), C_["gold"], angle=45, name="lock")
    for c in coins:
        d.fill(tuck(c, RIM), C_["gold"], angle=30, name="coin")
    for c in coins:
        d.outline(c, C_["brass"], width=RIM, name="coin rim")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
