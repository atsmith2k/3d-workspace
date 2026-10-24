"""Round plaster coaster mold, 4 in, with an oak leaf in relief on the coaster face.

The coaster is cast face-down: the leaf is a shallow pocket in the mold floor (so it
stands proud on the coaster) and its veins are ribs on the pocket floor (so they are
grooves in the raised leaf). Everything the plaster touches is drafted so it releases.

Spec:
  object:       mold for a 4 in (101.6 mm) round plaster coaster, 8 mm thick
  overall:      dish ~110 mm across, 13 mm tall; floor 5, wall 3
  must have:    leaf raised 1.5 mm on the coaster, vein grooves 1.0 deep, 1.6 wide;
                2 deg draft on the cavity wall, 8 deg on the pocket, 10 deg on ribs
  orientation:  opening up, flat floor on the bed, no overhangs
  tolerances:   none (casting)

Units: mm. Z is up, the mold sits on Z=0.
"""
from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "4 in round plaster coaster mold with oak leaf relief"

PARAMS = dict(
    diameter=101.6,     # coaster diameter at its face
    thickness=8.0,      # coaster thickness = cavity depth
    floor=5.0,
    wall=3.0,
    wall_draft=2.0,
    leaf_height=1.5,    # how far the leaf stands proud of the coaster
    vein_depth=1.0,     # groove depth in the leaf
    vein_width=1.6,
    leaf_scale=0.85,    # leaf length as a fraction of the diameter
    pocket_draft=8.0,
    rib_draft=10.0,
)

EMBED = 0.1

# right half of an oak leaf, tip up, in a 100-unit-tall design space (mirrored about x=0)
LEAF_HALF = [(0, 50), (6, 42), (14, 38), (10, 30), (17, 22), (12, 16), (18, 8), (13, 2),
             (18, -8), (11, -14), (14, -24), (7, -30), (3, -36), (0, -38)]
MIDRIB = [(0, -36), (0, 46)]
SIDE_VEINS = [((0, 30), (6, 36), (13, 37)), ((0, 16), (7, 20), (16, 21)), ((0, 2), (8, 5), (17, 7)),
              ((0, -12), (7, -10), (17, -9)), ((0, -26), (6, -25), (13, -23))]
STEM = [(0, -38), (0, -47)]


def leaf_outline():
    return mirror_x(smooth_shape(LEAF_HALF, samples=10))


def veins(width):
    out = stroke(MIDRIB, width) + stroke(STEM, width * 1.6)
    for a, c, b in SIDE_VEINS:
        out += mirror_x(stroke(bezier(a, c, b, n=10), width))
    return out


def checks(p):
    h = p.floor + p.thickness
    r = p.diameter / 2
    return [
        dims(z=h, x=(p.diameter + 2 * p.wall, p.diameter + 2 * p.wall + 4)),
        empty((0, 0, p.floor + p.thickness / 2 + 2)),            # cavity is open
        solid((r * 0.8, 0, p.floor / 2)),                           # floor under the plain face
        thickness_at((0, 0, 0.5), p.floor - p.leaf_height - 0.2, direction=(0, 0, 1)),  # floor under the pocket
        flat_base(3.14 * r * r * 0.9),
        no_overhang(),
        single_body(),
    ]


def build(p):
    r = p.diameter / 2
    h = p.floor + p.thickness
    lean = draft_offset(p.thickness, p.wall_draft)
    # dish: outer cylinder minus a cavity that widens toward the opening
    mold = extrude(circle(0, 0, r + lean + p.wall), h)
    mold -= drafted(lambda f: circle(0, 0, r + f * lean), p.floor, p.thickness + 1, steps=6)
    # leaf pocket in the floor, narrowing downward (8 deg): raised leaf on the coaster
    k = p.leaf_scale * p.diameter / 100.0
    leaf = leaf_outline().scale((k, k))
    pocket_lean = draft_offset(p.leaf_height, p.pocket_draft)
    mold -= drafted(lambda f: grow(leaf, (f - 1) * pocket_lean), p.floor - p.leaf_height,
                    p.leaf_height + 1, steps=4)
    # vein ribs standing on the pocket floor, sunk EMBED so the union is clean
    rib_lean = draft_offset(p.vein_depth, p.rib_draft)
    pocket_floor = p.floor - p.leaf_height
    mold += drafted(lambda f: grow(veins(p.vein_width / k + 2 * rib_lean / k * 0.0).scale((k, k)),
                                   -f * rib_lean),
                    pocket_floor - EMBED, p.vein_depth + EMBED, steps=4)
    return mold
