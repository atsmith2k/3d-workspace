"""Shared dressed geometry for the river and fen objectives."""

from _frp import Material, ball, box, cylinder, lathe, normal_from_height, np, orm, tiled
from _olden_elimination_venues import beam, gable, solid


def water(name, base, current):
    """Tileable low relief with longer river ripples and shorter fen swells."""
    v, u = np.mgrid[:512, :512] / 512
    swell = .5 + .5 * np.sin(2 * np.pi * (current * u + v + .22 * np.sin(4 * np.pi * v)))
    ripple = .5 + .5 * np.cos(2 * np.pi * (19 * u - 3 * v + .37 * np.sin(6 * np.pi * v)))
    relief = .72 * swell + .28 * ripple
    color = np.asarray(base) + relief[..., None] * np.asarray([.036, .061, .056])
    return Material(
        name,
        base=color,
        normal=normal_from_height(relief, 1.1),
        orm=orm(1, .29 + .12 * ripple, 0),
        metallic=1,
        roughness=1,
    )


def slab(yard, surface, rectangle, height=0, depth=.24, walk=True):
    x0, x1, z0, z1 = rectangle
    yard.add(surface, box(x1 - x0, depth, z1 - z0, .55).moved(
        (x1 + x0) / 2, height - depth / 2, (z1 + z0) / 2,
    ), walk=walk)


def stake(yard, wood, stone, x, z):
    yard.add(stone, box(.42, .26, .44, .65).moved(x, .13, z))
    yard.add(wood, box(.19, 1.84, .20, .65).moved(x, 1.17, z))


def gate(yard, masonry, wood, roof, iron, z):
    """A timber toll barrier with iron straps and masonry jambs."""
    for side in (-1, 1):
        x = side * 2.02
        solid(yard, masonry, (x-.34, x+.34, z-.52, z+.52, 0, 3.14))
        yard.add(masonry, box(.79,.19,1.15,.57).moved(x,3.16,z))
        for j in range(7):
            plank = side * (.17 + j * .248)
            yard.add(wood, box(.235, 2.47, .19, .82).moved(plank, 1.24, z))
        for face in (-1, 1):
            for h in (.55, 1.78):
                yard.add(iron, box(1.65, .145, .07, .66).moved(side*.89,h,z+face*.122))
            yard.add(wood, tiled(beam((side*.14,.3,z+face*.13),
                                      (side*1.79,2.26,z+face*.13),.17,.10), .73))
    yard.add(wood, box(4.58,.22,.65,.62).moved(0,2.74,z))
    gable(yard, wood, roof, 0, z, 4.91, 1.52, 3.12, .83)


def bell(yard, masonry, wood, bronze, roof, z):
    """A rival signal bell hangs from a roofed beam above a stone landing."""
    pad = (-1.23,1.23,z-.72,z+.72)
    slab(yard, masonry, pad, .16, .19, walk=False)
    for side in (-1,1):
        x=side*.93
        yard.add(wood, box(.24, 3.56, .32, .64).moved(x,1.94,z),
                 beam((x,2.33,z),(x-side*.58,3.39,z),.16,.15))
    yard.add(wood, box(2.12,.26,.33,.68).moved(0,3.24,z))
    shape = [(0,0),(.55,0),(.55,.10),(.46,.15),(.32,.55),(.27,.72),(.15,.85),(0,.88)]
    yard.add(bronze, lathe(shape, 28).moved(0,2.17,z),
             cylinder(.032,.43,12).moved(0,2.04,z),
             ball(.091,12,8).moved(0,1.84,z))
    gable(yard,wood,roof,0,z,3.14,1.37,3.56,.57)
