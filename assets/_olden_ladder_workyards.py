"""Textured workshop geometry at the authored ladder floor and obstacle bounds."""

from _frp import box, cylinder, ground, iron_rusted, paving, stone, thatch, timber, torus
from _olden_elimination_venues import Yard, beam, solid, tint_surface
from _olden_ticketed_venues import slab


ROPEWALK_FLOORS = ((-23, 23, -10, 10, 0),)
ROPEWALK_FIXTURES = (
    (-15, 5, -.65, .65, 0, 2.3),
    (9, 17, -.65, .65, 0, 2.3),
    (-11, -8, -7.1, -5.8, 0, 1.04),
    (0, 3, 5.8, 7.1, 0, 1.04),
    (-5, -2, 4.2, 5.1, 0, .86),
    (14, 17, -6, -4.8, 0, .91),
    (-20, -18, 6, 7.2, 0, .8),
    (19, 21, 4.5, 6, 0, .94),
)

TURNERS_FLOORS = (
    (-20, 20, -18, 18, 0),
    (-16, 16, -14, 14, .12),
    (-12, 12, -10, 10, .24),
    (-7, 7, -6, 6, .36),
)
TURNERS_FIXTURES = (
    (-3, -1, -1.4, 1.4, .36, 1.44),
    (1, 3, -1.4, 1.4, .36, 1.44),
    (-9, -7.8, -5, -3, .24, 1.22),
    (7.8, 9, 3, 5, .24, 1.22),
    (-7, -3, 11, 12.2, .12, 1.04),
    (3, 7, -12.2, -11, .12, 1.04),
    (-15, -13, -2, 1, .12, 1.3),
    (13, 15, -1, 2, .12, 1.3),
)


def workshop_materials():
    wood = timber(512, 34)
    planks = tint_surface(timber(512, 35), "old_workshop_boards", (.52, .30, .16), .48)
    masonry = tint_surface(stone(512, 36), "warm_workshop_wall", (.40, .34, .25), .42)
    earth = tint_surface(ground(512, 37), "trampled_workyard", (.37, .27, .14), .47)
    sett = tint_surface(paving(512, 38), "workyard_setts", (.48, .38, .28), .53)
    rope = tint_surface(ground(256, 39), "hemp_fiber", (.70, .53, .30), .81)
    roof = tint_surface(thatch(512, 40), "smoke_stained_shakes", (.35, .26, .13), .44)
    metal = iron_rusted(256, 41)
    return wood, planks, masonry, earth, sett, rope, roof, metal


def post(yard, wood, x, z, height=3.5):
    yard.add(wood, box(.22, height, .22, 1.9).moved(x, height / 2, z))


def perimeter(yard, wood, masonry, x_end, z_end, height):
    """Mount a split stone-and-timber enclosure just beyond walking clearance."""
    for side in (-1, 1):
        z = side * (z_end - .09)
        x = side * (x_end - .09)
        yard.add(masonry, box(2 * x_end, .58, .16, 1.25).moved(0, .29, z))
        yard.add(masonry, box(.16, .58, 2 * z_end, 1.25).moved(x, .29, 0))
        yard.add(wood, box(2 * x_end, height - .58, .16, 1.35).moved(0, (height + .58) / 2, z))
        yard.add(wood, box(.16, height - .58, 2 * z_end, 1.35).moved(x, (height + .58) / 2, 0))


def rope_reel(yard, wood, rope, bounds):
    x0, x1, z0, z1, y0, y1 = bounds
    x, z = (x0 + x1) / 2, (z0 + z1) / 2
    radius = min(.40, (x1 - x0) * .16, (z1 - z0) * .34)
    for fraction in (-.31, .31):
        station = x + fraction * (x1 - x0)
        for ring in range(4):
            yard.add(rope, torus(radius, .028, 20, 6).moved(station, y1 - .23 + .05 * ring, z))
        yard.add(wood, cylinder(radius * .74, .18, 12).moved(station, y1 - .18, z))


def ropewalk():
    wood, planks, masonry, earth, sett, rope, roof, metal = workshop_materials()
    yard = Yard()
    slab(yard, earth, (-23, 23, -10, 10))
    for side in (-1, 1):
        z0, z1 = sorted((side * 1.2, side * 3.45))
        slab(yard, sett, (-23, 23, z0, z1), .004, .14)
    perimeter(yard, wood, masonry, 23, 10, 2.48)
    for x in range(-20, 23, 6):
        for side in (-1, 1):
            z = side * 9.82
            post(yard, wood, x, z)
            yard.add(roof, beam((x, 4.55, 0), (x, 3.48, z), .21, .16))
        yard.add(wood, box(.21, .18, 19.90, 1.5).moved(x, 3.62, 0))
    for side in (-1, 1):
        # A covered edge and an open central roof slot admit daylight into both running lanes.
        for band in range(5):
            a = side * (5.80 + band * .80)
            b = side * (6.61 + band * .80)
            ay = 4.55 - abs(a) * .099
            by = 4.55 - abs(b) * .099
            yard.add(roof, beam((0, ay, a), (0, by, b), 46, .13))
    for start, stop, z0, z1, low, high in ROPEWALK_FIXTURES[:2]:
        solid(yard, planks, (start, stop, z0, z1, low, high))
        for x in range(int(start) + 1, int(stop), 2):
            for z in (-.60, .60):
                yard.add(wood, box(.16, high, .10, 1.05).moved(x, high / 2, z))
                yard.add(rope, cylinder(.038, 1.54, 8).moved(x + .46, .40, z * .97))
        yard.add(metal, box(stop - start, .11, 1.29, 1.40).moved((start + stop) / 2, high - .06, 0))
    for fixture in ROPEWALK_FIXTURES[2:]:
        x0, x1, z0, z1, low, high = fixture
        solid(yard, planks, (x0, x1, z0, z1, low, high - .25))
        rope_reel(yard, wood, rope, fixture)
        yard.add(wood, box(x1 - x0, .16, z1 - z0, 1.25).moved(
            (x0 + x1) / 2, high - .31, (z0 + z1) / 2
        ))
    return yard.finish()


def turners_yard():
    wood, planks, masonry, earth, sett, rope, roof, metal = workshop_materials()
    yard = Yard()
    for region, material in zip(TURNERS_FLOORS, (earth, sett, planks, sett)):
        slab(yard, material, region[:4], region[4])
    perimeter(yard, wood, masonry, 20, 18, 2.53)
    for z_side in (-1, 1):
        for x in (-16, -12, -8, -4, 4, 8, 12, 16):
            post(yard, wood, x, z_side * 17.82, 3.86)
            yard.add(roof, beam(
                (x, 3.82, z_side * 17.9), (x, 3.14, z_side * 15.52), 3.73, .16
            ))
    for x_side in (-1, 1):
        for z in (-12, -8, -4, 4, 8, 12):
            post(yard, wood, x_side * 19.82, z, 3.86)
            yard.add(roof, beam(
                (x_side * 19.90, 3.82, z), (x_side * 17.52, 3.14, z), .16, 3.73
            ))
    for x0, x1, z0, z1, low, high in TURNERS_FIXTURES:
        center_x, center_z = (x0 + x1) / 2, (z0 + z1) / 2
        width, depth = x1 - x0, z1 - z0
        solid(yard, planks, (x0, x1, z0, z1, low, high - .32))
        for side in (-1, 1):
            yard.add(wood, box(.14, .31, depth - .10, 1.2).moved(
                center_x + side * (width / 2 - .13), high - .165, center_z
            ))
        for fraction in (-.25, .25):
            axle = width - .20
            blank = width * .55
            yard.add(metal, cylinder(.085, axle, 12).moved(0, -axle / 2, 0).rotated(90, "z").moved(
                center_x, high - .15, center_z + depth * fraction
            ))
            yard.add(wood, cylinder(.14, blank, 14).moved(0, -blank / 2, 0).rotated(90, "z").moved(
                center_x, high - .15, center_z + depth * fraction
            ))
    return yard.finish()


def fixture_bounds(model, fixtures, edge_x, edge_z):
    """Check that low decorative geometry cannot protrude into a walkable lane."""
    tolerance = .002
    for low, high in model.obstacles:
        if low[1] >= 2.65:
            continue
        if (high[0] <= -edge_x + .32 or low[0] >= edge_x - .32
                or high[2] <= -edge_z + .32 or low[2] >= edge_z - .32):
            continue
        if not any(
            low[0] >= x0 - tolerance and high[0] <= x1 + tolerance
            and low[2] >= z0 - tolerance and high[2] <= z1 + tolerance
            and low[1] >= y0 - tolerance and high[1] <= y1 + tolerance
            for x0, x1, z0, z1, y0, y1 in fixtures
        ):
            return False, f"Dressing extends outside the authored boxes: {low} to {high}"
    return True, "Low interior props stay inside the authored collision boxes"
