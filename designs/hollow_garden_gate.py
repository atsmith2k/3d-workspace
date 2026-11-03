"""Garden Gate: a blue-painted picket gate between oak posts in a green hedge, sunflowers
nodding over the hedge, a straw bee skep on its bench and bees on a dotted flight path.

Spec:
  object:       a cottage garden gate (cozy fantasy / cottagecore, no named place) for
                tees, totes, aprons, garden gloves, cushions and framed hoops
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      emerald (hedge), leaf green (sunflower stems and leaves), sky blue
                (pickets), blue (rails, brace), light brown (posts, bench), khaki (skep),
                harvest gold (petals, bee bodies), dark brown (sunflower centres, skep
                coils, doorway), white (bee wings), black (bee stripes,
                heads): 10 colours
  must have:    a 38 mm gate of six pointed pickets on two rails with a diagonal brace,
                6 mm posts with ball caps; a hedge with a bumpy top across the whole
                scene, behind the gate; sunflowers 19 and 14 mm across on leafy stems
                over the hedge, one each side; a 22 mm skep with coil lines and a dark
                doorway on a bench at the right; three 6 mm bees; leafy highlight arcs on the hedge
  density:      hedge knocked out under the gate, posts, skep; skep coils are single runs,
                hedge highlights bean runs; max 3.5
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _hollow import C_, SIZES, backfill, close_gaps, fit, hoop_for, product, standard_checks, strip  # noqa: F401

DESCRIPTION = "Blue picket garden gate in a hedge with sunflowers, a bee skep and bees"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Cottage Garden Gate Embroidery Design",
    "A blue picket garden gate in a green hedge with nodding sunflowers, a straw bee skep and buzzing bees",
    ["garden gate", "cottage garden", "sunflowers", "bee skep", "beehive", "bees", "honey bee",
     "garden embroidery", "gardener gift", "cottagecore garden", "apron embroidery"],
    "The way into the prettiest garden on the hill: a blue-painted picket gate between oak posts "
    "in a thick green hedge, sunflowers nodding over the top, a straw bee skep on its bench and "
    "three bees buzzing home.\n\n"
    "Part of the Hearth & Hollow cozy fantasy collection. Great on aprons, totes, tees, "
    "cushions and framed hoops.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 10, 18000)


GROUND = -42.0


def hedge():
    bumps = [(-48, -4, 5), (-41, 0, 6), (-33, -1, 5.5), (-25, 1, 6), (-16, -0.5, 5.5), (-7, 1.5, 6),
             (2, 0, 5.5), (11, 1.5, 6), (20, -0.5, 5.5), (29, 0.5, 6), (38, -1.5, 5.5), (46, -4.5, 5)]
    return union(rect(100, 40, 0, GROUND + 20), *[circle(x, y, r) for x, y, r in bumps]) & rect(104, 60, 0, -14)


def gate():
    xs = np.linspace(-16, 16, 6)
    pickets = [union(rect(4.4, 48, x, GROUND + 2 + 24), poly([(x - 2.2, GROUND + 50), (x, GROUND + 54), (x + 2.2, GROUND + 50)]))
               for x in xs]
    rails = [rect(38, 3.6, 0, -30), rect(38, 3.6, 0, -5)]
    brace = strip(np.array([(-16.5, -29), (16.5, -6)]), 3.4)
    posts = [union(rect(6, 58, x, GROUND + 29), circle(x, GROUND + 61.5, 3.6)) for x in (-22.5, 22.5)]
    return pickets, rails, brace, posts


def sunflower(cx, cy, r, stem_to):
    head = circle(cx, cy, r * 0.42)
    petals = move(union(*M.petal_ring(n=14, r_in=r * 0.34, length=r * 0.66, width=r * 0.34)), cx, cy)
    sp = np.asarray(spline([(cx, cy - r * 0.4), (cx + 1.2, (cy + stem_to[1]) / 2), stem_to], samples=8))
    stem = strip(sp, 2.0)
    mid = sp[len(sp) // 2]
    lv = [move(rotate(M.leaf(9, 4.2, bend=0.15), 20), *mid), move(rotate(M.leaf(8, 4.0, bend=-0.15), 160), *mid)]
    return head, petals, stem, lv


def skep(cx, base):
    dome = smooth([(cx - 11, base), (cx - 11, base + 7), (cx - 8.5, base + 15), (cx - 4, base + 20), (cx, base + 21.5),
                   (cx + 4, base + 20), (cx + 8.5, base + 15), (cx + 11, base + 7), (cx + 11, base)], samples=8)
    door = union(rect(5.2, 2.4, cx, base + 1.2), circle(cx, base + 2.4, 2.6)) & dome
    coils = []
    for y in np.arange(base + 3.2, base + 20.5, 2.8):
        g = LineString([(cx - 14, y), (cx + 14, y)]).intersection(shrink(dome, 1.2)).difference(grow(door, 0.8))
        coils += [list(s.coords) for s in getattr(g, "geoms", [g]) if s.length > 1.5]
    return dome, door, coils


def bee(x, y, deg):
    body = ellipse(x, y, 3.0, 2.0)
    stripe = rect(1.3, 4.4, x + 0.2, y) & body
    head = circle(x + 3.4, y + 0.2, 1.3)
    wings = union(ellipse(x - 0.6, y + 2.6, 1.3, 1.8), ellipse(x + 1.3, y + 2.4, 1.1, 1.6))
    o = (x, y)
    return [rotate(g, deg, origin=o) for g in (body, stripe, head, wings)]


def art():
    d = Design()
    hd = hedge()
    pickets, rails, brace, posts = gate()
    gate_all = union(*pickets, *rails, brace, *posts)
    flowers = [sunflower(-36, 24, 19, (-35, -2)), sunflower(43, 16, 14, (43, -3))]
    sx, base = 37.0, GROUND + 3.2
    dome, door, coils = skep(sx, base)
    bench = union(rect(28, 2.8, sx, GROUND + 1.6), rect(2.4, 3.0, sx - 10, GROUND - 0.4), rect(2.4, 3.0, sx + 10, GROUND - 0.4))
    bees = [bee(-14, 31, 10), bee(4, 27, -12), bee(26, 18, 20)]
    wings = union(*[b[3] for b in bees])
    # leafy highlights on the hedge: short arcs, kept 2 mm inside it and clear of the gate
    tufts = []
    for x, y in ((-44, -12), (-36, -26), (-31, -8), (-41, -36), (30, -12), (44, -22), (31, -32), (46, -36)):
        g = LineString(arc(x, y - 3.0, 3.2, 40, 140)).intersection(shrink(hd, 2.0)).difference(
            grow(union(gate_all, dome, bench), 1.5))
        tufts += [list(q.coords) for q in getattr(g, "geoms", [g]) if q.geom_type == "LineString" and q.length > 2]

    heads = union(*[union(f[0], f[1]) for f in flowers])
    stems = union(*[union(f[2], *f[3]) for f in flowers])
    front_of_hedge = union(gate_all, dome, bench)
    hd = close_gaps(hd, front_of_hedge, stems, heads, r=1.6)

    # 1 hedge
    d.fill(knockout(hd, front_of_hedge, stems), C_["green"], angle=30, name="hedge")
    # 2 sunflower stems and leaves (over the hedge top, under the heads)
    for f in flowers:
        d.fill(knockout(union(f[2], *f[3]), heads), C_["leaf"], angle=70, name="sunflower stem")
    for t in tufts:
        d.run(t, C_["leaf"], bean=1, name="hedge highlight")
    # 3-4 the blue gate
    for g in pickets:
        d.fill(knockout(g, *rails, brace), C_["sky"], angle=90, name="picket")
    for g in rails:
        d.fill(knockout(g, brace), C_["blue"], angle=0, name="rail")
    d.fill(brace, C_["blue"], angle=35, name="brace")
    # 5 posts and the bench
    for g in posts:
        d.fill(g, C_["wood"], angle=90, name="post")
    d.fill(bench, C_["wood"], angle=0, name="bench")
    # 6 skep
    d.fill(knockout(dome, door), C_["khaki"], angle=0, name="skep")
    # 7 harvest gold: petals and bee bodies
    for f in flowers:
        d.fill(knockout(f[1], f[0]), C_["yellow"], angle=0, name="petals")
    for b in bees:
        d.fill(knockout(b[0], b[1], b[2], wings), C_["yellow"], angle=60, name="bee")
    # 8 dark brown: sunflower centres, skep coils and doorway, flight path
    for f in flowers:
        d.fill(f[0], C_["bark"], angle=45, name="sunflower centre")
    d.fill(door, C_["bark"], angle=0, name="skep door")
    for c in coils:
        d.run(c, C_["bark"], name="skep coil")
    # 9-10 bee wings, stripes and heads
    for b in bees:
        d.fill(b[3], C_["white"], angle=0, name="wings")
    for b in bees:
        d.fill(knockout(b[1], wings), C_["black"], angle=0, name="stripe")
        d.fill(b[2], C_["black"], angle=0, name="head")
    backfill(d, C_["green"], max_area=45)
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
