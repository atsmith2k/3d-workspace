"""manifold3d helpers for decorative / relief / mold work.

Mesh-based booleans: fast and never fail on intricate art (hundreds of strokes, spots,
offsets), but no true fillets or STEP output. Use build123d (cadkit.cad) for
engineered parts instead.

Import in a model with:  from cadkit.relief import *
"""
import math

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold, OpType

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


def tapered(cs, z, height, lean):
    """Smooth drafted solid: `cs` at the bottom, grown by about `lean` at the top, with
    straight sides (no stair steps, unlike `drafted`). Scales per axis about the shape's
    centre, so the draft is exact on straight and round sides and close elsewhere; use
    `drafted` for spiky outlines where scaling would move thin features sideways."""
    x0, y0, x1, y1 = cs.bounds()
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    m = Manifold.extrude(cs.translate((-cx, -cy)), height,
                         scale_top=((w + 2 * lean) / w, (h + 2 * lean) / h))
    return m.translate((cx, cy, z))


def text(string, size, font="Arial", bold=False, font_path=None, mirror=False):
    """Text as a 2D CrossSection centred on the origin, for reliefs and molds: use it
    like any other shape here (extrude, grow, drafted, mirror_x...). `size` is the
    cap height in mm. `mirror=True` flips it so a casting reads correctly.
    Glyph outlines come from build123d's font engine, via a 1 mm extrusion sliced
    at mid-height."""
    import numpy as np
    from build123d import Align, FontStyle, Text, extrude as _extrude
    from manifold3d import Mesh
    from .mesh import to_trimesh
    sk = Text(string, font_size=size, font=font, font_path=font_path,
              font_style=FontStyle.BOLD if bold else FontStyle.REGULAR,
              align=(Align.CENTER, Align.CENTER))
    tm = to_trimesh(_extrude(sk, amount=1.0), tolerance=0.02)
    m = Manifold(Mesh(vert_properties=tm.vertices.astype(np.float32),
                      tri_verts=tm.faces.astype(np.uint32)))
    cs = m.slice(0.5)
    return cs.mirror((1, 0)) if mirror else cs


def draft_offset(height, degrees):
    """How far a wall of this height moves sideways at this draft angle."""
    return height * math.tan(math.radians(degrees))


def cast_of(mold, minus=None, flip=True):
    """The piece a mold makes, for the shop's cast render: every opening in the mold's
    top face, extruded down through the mold, minus the mold (and `minus`, e.g. a core
    in its assembled pose). Assumes the cavity is widest at the opening, as a drafted
    mold is. `flip=True` turns it over (face-down casts), so the face the mold floor
    shaped is on top; the result sits on Z=0."""
    lo, hi = mold.bounding_box()[2], mold.bounding_box()[5]
    rim = hi - 0.25                     # just under the rim: pins may stand a hair proud of it
    polys = mold.slice(rim).to_polygons()
    holes = [q for q in polys if _signed_area(q) < 0]
    if not holes:
        return Manifold()
    fill = Manifold()
    for q in holes:
        fill += Manifold.extrude(poly(q), rim - lo).translate((0, 0, lo))
    cast = (fill - mold) - minus if minus is not None else fill - mold
    # anything reaching down to the mold's base lies outside it (e.g. round a foot)
    cast = Manifold.batch_boolean([c for c in cast.decompose() if c.bounding_box()[2] > lo + 0.01] or [Manifold()],
                                  OpType.Add)
    if flip:
        cast = cast.rotate((180, 0, 0))
    return cast.translate((0, 0, -cast.bounding_box()[2]))


def _signed_area(q):
    q = np.asarray(q, float)
    return 0.5 * np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
