"""manifold3d helpers for decorative / relief / mold work.

Mesh-based booleans: fast and never fail on intricate art (hundreds of strokes, spots,
offsets), but no true fillets or STEP output. Use build123d (cadkit.cad) for
engineered parts instead.

Import in a model with:  from cadkit.relief import *
"""
import math

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold

ROUND = JoinType.Round
CIRC = 48  # segments per full circle


def catmull_rom_closed(points, samples=14):
    """Smooth closed curve through the points, as an (N, 2) array."""
    pts = np.asarray(points, float)
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for t in np.linspace(0, 1, samples, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)


def poly(points):
    """Filled polygon from 2D points (either winding)."""
    pts = np.asarray(points, float)
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    return CrossSection([(pts if area > 0 else pts[::-1]).tolist()])


def smooth_shape(points, samples=14):
    return poly(catmull_rom_closed(points, samples))


def circle(x, y, r):
    return CrossSection.circle(r, CIRC).translate((x, y))


def ellipse(x, y, rx, ry):
    a = np.linspace(0, 2 * math.pi, CIRC, endpoint=False)
    return poly(np.c_[x + rx * np.cos(a), y + ry * np.sin(a)])


def mirror_x(cs):
    """Shape plus its mirror image across the Y axis (left/right symmetry)."""
    return cs + cs.mirror((1, 0))


def bezier(p0, c, p1, n=16):
    """Quadratic bezier as an (n, 2) array of points."""
    t = np.linspace(0, 1, n)[:, None]
    p0, c, p1 = map(np.asarray, (p0, c, p1))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t ** 2 * p1


def stroke(path, width):
    """Thick polyline with round caps and joins."""
    r = width / 2
    out = CrossSection()
    for a, b in zip(path[:-1], path[1:]):
        out += CrossSection.batch_hull([circle(*a, r), circle(*b, r)])
    return out


def grow(cs, amount):
    """Offset outward (negative shrinks) with rounded corners."""
    return cs.offset(amount, ROUND)


def extrude(cs, height, z=0.0):
    return Manifold.extrude(cs, height).translate((0, 0, z))


def drafted(section_at, z, height, steps=8):
    """Tapered solid built from stacked slices. section_at(f) returns the 2D section at
    fraction f of the height (0 = bottom, 1 = top), e.g.
        drafted(lambda f: grow(outline, f * 0.9), z=5, height=25)   # widens upward
    Slices overlap slightly so they fuse into one solid."""
    out = Manifold()
    h = height / steps
    for k in range(steps):
        cs = section_at((k + 0.5) / steps).simplify(0.01)
        out += Manifold.extrude(cs, h + 0.05).translate((0, 0, z + k * h))
    return out


def draft_offset(height, degrees):
    """How far a wall of this height moves sideways at this draft angle."""
    return height * math.tan(math.radians(degrees))
