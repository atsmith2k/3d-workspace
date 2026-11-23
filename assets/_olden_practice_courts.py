"""Textured open-practice courts with collision derived from the authored layouts."""

from _frp import ball, box, cylinder, ground, paving, prism, stone, thatch, timber
from _olden_elimination_venues import Yard, beam, gable, route_fixture, solid, tint_surface
from _olden_ticketed_venues import slab


PLUMB_FLOOR = (-15, 15, -12, 12)
PLUMB_OBSTACLES = (
    (-15, -14.6, -12, 12, 0, 2.2),
    (14.6, 15, -12, 12, 0, 2.2),
    (-15, 15, -12, -11.6, 0, 2.7),
    (-15, -4, 11.6, 12, 0, 2.2),
    (4, 15, 11.6, 12, 0, 2.2),
    (-.45, .45, -11.6, -8.6, 0, 2.4),
)
PLUMB_RINGS = ((-7, -5, 2.9), (7, -5, 2.9), (-7, 5, 2.9), (7, 5, 2.9))
LINTEL_FLOOR = (-20, 20, -15, 15)
LINTEL_OBSTACLES = (
    (-19.5, -19.2, -13, 13, 0, 1),
    (19.2, 19.5, -13, 13, 0, 1),
    (-12, 12, 11, 12.2, 0, .7),
    (-11.5, 11.5, 12.2, 13.4, 0, 1.15),
    (-7, -6.4, -13.6, -12.9, 0, 2.4),
    (-3.6, -3, -13.6, -12.9, 0, 2.4),
    (-7, -3, -13.6, -12.9, 2.05, 2.68),
)
LINTEL_RINGS = ((-10, -7, 3.3), (6, -7, 3.3), (-10, 4, 3.3), (6, 4, 3.3))


def walls(yard, lower, upper, obstacles, cap):
    for x0, x1, z0, z1, bottom, top in obstacles:
        solid(yard, lower, (x0, x1, z0, z1, bottom, top - cap))
        solid(yard, upper, (x0, x1, z0, z1, top - cap, top))


def lodge(yard, masonry, wood, roof, x, z, width, depth, height):
    yard.add(masonry, box(width, height, depth, .77).moved(x, height / 2, z))
    for offset in (-width / 2 + .14, width / 2 - .14):
        yard.add(wood, box(.24, height, .24).moved(x + offset, height / 2, z - depth / 2))
    yard.add(wood, box(width, .24, .23, .94).moved(x, height - .12, z - depth / 2))
    roof_width, rise = width + .55, width * .28
    for end in (-1, 1):
        half_span = width / 2 - .02
        top = rise * (1 - (roof_width - width) / roof_width)
        yard.add(masonry, prism([(-half_span, 0), (half_span, 0), (0, top)], .18).moved(
            x, height, z + end * (depth / 2 - .08),
        ))
    gable(yard, wood, roof, x, z, roof_width, depth + .43, height, rise)


def plumb_court():
    setts = tint_surface(paving(512, 42), "court_worn_setts", (.50, .42, .32), .62)
    masonry = tint_surface(stone(512, 43), "court_rubble_stone", (.44, .43, .38), .52)
    coping = tint_surface(stone(256, 44), "court_limestone_coping", (.64, .60, .51), .67)
    wood = timber(512, 45)
    roof = tint_surface(thatch(512, 46), "court_dark_shakes", (.35, .25, .19), .53)
    yard = Yard()
    slab(yard, setts, PLUMB_FLOOR)
    slab(yard, masonry, (-19, 19, -16, 17), -.028, walk=False)
    walls(yard, masonry, coping, PLUMB_OBSTACLES, .16)
    for x in (-11.4, -6.9, 6.9, 11.4):
        lodge(yard, masonry, wood, roof, x, 14.65, 4.30, 3.35, 3.35)
    for x in (-12.3, -6.15, 0, 6.15, 12.3):
        lodge(yard, masonry, wood, roof, x, -14.68, 5.9, 3.35, 3.85)
    for z in (12.54, 13.96):
        for x in (-3.72, 3.72):
            yard.add(coping, box(.54, 3.94, .64, .7).moved(x, 1.97, z))
        yard.add(wood, box(8.0, .34, .44, 1.3).moved(0, 3.76, z))
        yard.add(wood, prism([(-3.98, 0), (3.98, 0), (0, 1.16)], .23).moved(0, 3.96, z))
    gable(yard, wood, roof, 0, 13.25, 8.10, 2.15, 3.97, 1.18)
    for side in (-1, 1):
        for plank in range(10):
            x = side * (.19 + .34 * plank)
            yard.add(wood, box(.328, 2.55, .20, 1.1).moved(x, 1.275, 12.71))
        for y in (.44, 2.11):
            yard.add(wood, box(3.44, .17, .24, .76).moved(side * 1.75, y, 12.54))
        yard.add(wood, beam((side * .13, .51, 12.47), (side * 3.39, 2.06, 12.47), .17, .14))
    return yard.finish()


def lintel_green():
    turf = tint_surface(ground(512, 56), "trampled_green", (.24, .35, .12), .73)
    bank = tint_surface(ground(512, 57), "green_bank_earth", (.34, .24, .13), .52)
    leaf = tint_surface(ground(256, 58), "green_coppice_leaf", (.21, .35, .11), .87)
    masonry = tint_surface(stone(512, 59), "green_fieldstone", (.42, .40, .29), .49)
    wood = timber(512, 60)
    roof = thatch(512, 61)
    yard = Yard()
    slab(yard, turf, LINTEL_FLOOR)
    slab(yard, turf, (-29, 29, -23, 23), -.028, walk=False)
    walls(yard, masonry, wood, LINTEL_OBSTACLES[:2], .12)
    walls(yard, bank, turf, LINTEL_OBSTACLES[2:4], .15)
    walls(yard, wood, masonry, LINTEL_OBSTACLES[4:], .11)
    for x in (-13.8, 0, 13.8):
        lodge(yard, wood, wood, roof, x, 17.7, 4.4, 2.65, 2.40)
    tree_groves = (
        (-24, -10), (-24.6, -4), (-25, 2), (-24.4, 8), (-23.6, 14),
        (23.6, -11), (24.7, -4), (25, 3), (24.1, 9), (24.3, 16),
        (-20, 19), (-10, 20), (8, 20.1), (19.4, 19.5),
        (-20, -18), (-14, -20), (-1, -20.1), (7, -19), (19, -19),
    )
    for i, (x, z) in enumerate(tree_groves):
        height = 3.5 + .35 * (i % 5)
        yard.add(wood, cylinder(.21, height, 8).moved(x, 0, z))
        crown = 1.8 + .14 * (i % 4)
        lean = (-1, 1)[i % 2]
        branch_top = (x + lean * .89, height * .89, z + .55)
        yard.add(wood, beam((x, height * .58, z), branch_top, .14, .14))
        yard.add(leaf, ball(crown, 10, 7).moved(x, height + .22, z))
        yard.add(leaf, ball(crown * .74, 9, 7).moved(*branch_top))
        yard.add(leaf, ball(crown * .63, 9, 7).moved(x - lean * .88, height * .78, z - .51))
    return yard.finish()


def clear_ring_routes(model, rings, passage):
    """Sample the whole sparring footprint and the crossing between rings."""
    strips = [(x - r, x + r, z - r, z + r) for x, z, r in rings]
    return route_fixture(model, strips + list(passage), 2.25)


def scenery_inside_collision(model, floor, obstacles):
    """Keep backdrop outside the arena and interior shapes in their collision boxes."""
    x0, x1, z0, z1 = floor
    for low, high in model.obstacles:
        if (high[0] <= x0 + .001 or low[0] >= x1 - .001
                or high[2] <= z0 + .001 or low[2] >= z1 - .001 or high[1] <= 0):
            continue
        if not any(
            low[0] >= a - .002 and high[0] <= b + .002
            and low[2] >= c - .002 and high[2] <= d + .002
            and low[1] >= bottom - .002 and high[1] <= top + .002
            for a, b, c, d, bottom, top in obstacles
        ):
            return False, f"Scenery outside collision: {low} to {high}"
    return True, "Scenery stays in the authored collision boxes or outside the arena"
