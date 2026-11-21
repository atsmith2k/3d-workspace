"""Collision-aware building and canopy details for the Olden Times elimination venues."""

from collections import defaultdict
from copy import deepcopy

from _frp import Model, along, ball, bevel_box, box, cylinder, merge, np, tiled


class Yard:
    """Batch static objects by material while keeping clearance geometry available."""

    def __init__(self):
        self.surfaces = {}
        self.groups = defaultdict(list)
        self.walk = []
        self.fixtures = []

    def add(self, surface, *meshes, walk=False):
        self.surfaces[surface.name] = surface
        self.groups[surface.name].extend(meshes)
        if walk:
            self.walk.extend(meshes)
        else:
            self.fixtures.extend(mesh.bounds for mesh in meshes)

    def finish(self):
        model = Model()
        for name, meshes in self.groups.items():
            model.add(merge(*meshes), self.surfaces[name], name)
        model.walkable = self.walk
        model.obstacles = self.fixtures
        return model


def beam(a, b, width, depth):
    length = np.linalg.norm(np.asarray(b) - a)
    return along(box(width, length, depth).moved(0, length / 2, 0), a, b)


def tint_surface(source, name, colour, mix):
    material = deepcopy(source)
    material.name = name
    luminance = .55 + material.base.mean(axis=2, keepdims=True)
    material.base = np.clip(material.base * (1 - mix) + np.asarray(colour) * luminance * mix, 0, 1)
    return material


def route_fixture(model, strips, clearance):
    """Sample the level routes against upward floor triangles and scenery bounds."""
    triangles = np.vstack([mesh.v[mesh.f] for mesh in model.walkable])
    a, b, c = triangles[np.cross(triangles[:, 1] - triangles[:, 0],
                               triangles[:, 2] - triangles[:, 0])[:, 1] > .00001].transpose(1, 0, 2)
    denominator = (b[:, 2] - c[:, 2]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 2] - c[:, 2])
    low = np.array([lo for lo, hi in model.obstacles])
    high = np.array([hi for lo, hi in model.obstacles])
    count = 0
    for x0, x1, z0, z1 in strips:
        for x in np.linspace(x0, x1, int(np.ceil((x1 - x0) * 4)) + 1):
            for z in np.linspace(z0, z1, int(np.ceil((z1 - z0) * 4)) + 1):
                u = ((b[:, 2] - c[:, 2]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (z - c[:, 2])) / denominator
                v = ((c[:, 2] - a[:, 2]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (z - c[:, 2])) / denominator
                w = 1 - u - v
                floor = (u >= -1e-5) & (v >= -1e-5) & (w >= -1e-5)
                if not np.any(floor):
                    return False, f"floor gap at ({x:.2f}, {z:.2f})"
                height = np.max((u * a[:, 1] + v * b[:, 1] + w * c[:, 1])[floor])
                if abs(height) > .012:
                    return False, f"uneven route at ({x:.2f}, {z:.2f})"
                crossing = (low[:, 0] < x) & (high[:, 0] > x) & (low[:, 2] < z) & (high[:, 2] > z)
                if np.any(crossing & (low[:, 1] < height + clearance) & (high[:, 1] > height + .015)):
                    return False, f"blocked route at ({x:.2f}, {z:.2f})"
                count += 1
    return True, f"{count} floor and {clearance:g} m headroom samples at <=0.25 m spacing"


def solid(yard, surface, bounds):
    """Place a textured solid at the authoritative fixture bounds."""
    x0, x1, z0, z1, y0, y1 = bounds
    return yard.add(surface, box(x1 - x0, y1 - y0, z1 - z0, 0.55).moved(
        (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2,
    ))


def gable(yard, wood, roof, x, z, width, depth, eave, rise):
    for side in (-1, 1):
        ridge = (x, eave + rise, z)
        foot = (x + side * width / 2, eave, z)
        yard.add(roof, tiled(beam(ridge, foot, 0.15, depth), 1.35))
        for end in (-1, 1):
            offset = end * (depth / 2 - 0.12)
            yard.add(wood, tiled(beam(
                (ridge[0], ridge[1], z + offset),
                (foot[0], foot[1], z + offset), 0.19, 0.15,
            ), 1.4))
    yard.add(wood, box(.22, .22, depth + .22, 1.2).moved(x, eave + rise, z))


def crate_stack(yard, wood, iron, x, z, scale):
    crate = tiled(bevel_box(1.08 * scale, .87 * scale, .97 * scale, .045), .65)
    for height, offset in ((.435, 0), (1.305, .08)):
        yard.add(wood, crate.moved(x + offset, height * scale, z))
        for side in (-1, 1):
            yard.add(iron, box(.052, .83 * scale, .025, .9).moved(
                x + offset + side * .38 * scale, height * scale, z + .49 * scale,
            ))


def apple_tree(yard, bark, leaf, fruit, x, z, spread):
    yard.add(bark, cylinder(.21, 2.65, 9, r_top=.12).moved(x, 1.325, z))
    for side in (-1, 1):
        yard.add(bark, tiled(beam((x, 1.84, z), (x + side * .81, 2.94, z + side * .48), .17, .16), 1))
    for dx, dy, dz, radius in ((0, 3.65, 0, 1.36), (-.85, 3.15, .18, .96),
                               (.8, 3.22, -.17, 1.02), (.05, 3.13, .71, .78)):
        yard.add(leaf, ball(radius, 11, 7).scaled(spread, .76, .93).moved(x + dx * spread, dy, z + dz))
    for dx, dy, dz in ((-.93, 2.69, .61), (.39, 2.85, .9), (.86, 2.72, -.28), (-.28, 2.68, -.77)):
        yard.add(fruit, ball(.095, 8, 5).moved(x + dx * spread, dy, z + dz))
