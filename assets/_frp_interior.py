"""Interiors and furniture: what the pieces of a furnished room share.

Furniture is joiner's work in the pack's dark timber: square legs, pegged stretchers, tops of
boards. It is sized against the ruler's person (1.8 m): a seat is 0.45 m high, a table 0.75 m,
a bed 1.9 m long, a shelf within reach at 1.8 m. Things at hand height carry the detail, because
a first-person camera stands 1.6 m up and looks down on them.

    block(...)       every piece of timber and stone has its edges eased by a few millimetres:
                     a razor-sharp corner is the first thing that says "computer" in a lit room,
                     and an eased one catches the firelight as a thin bright line
    planked(...)     a top made of separate boards, each its own length, thickness and stretch
                     of grain, with a dark gap between them
    boards_x(mesh)   horizontal timber: grain along X, boards 0.2 m wide
    upright(mesh)    vertical timber: grain up the piece
    Joints sink 2 mm into each other; nothing shares a plane.
"""
from _frp import *

SEAT_H, TABLE_H, BED_L = 0.45, 0.75, 1.9
FINE = 0.8                          # metres per repeat of timber on furniture: boards 0.2 m wide
SINK = 0.002
EASE = 0.006                        # how far a worked edge is eased


def block(sx, sy, sz, x=0.0, y=0.0, z=0.0, ease=EASE):
    """A piece standing on Y=y with its base centre at (x, y, z), every edge eased. Its flat
    faces still reach the full size, so joints and sizes are what the numbers say."""
    return bevel_box(sx, sy, sz, min(ease, 0.3 * min(sx, sy, sz))).moved(x, y + sy / 2, z)


def planked(length, thick, depth, y, boards=5, seed=0, gap=0.004, along="x"):
    """A top of `boards` separate boards lying along X, side by side in Z, on Y=y: each a few
    millimetres longer, shorter, thicker or thinner than its neighbour and cut from a different
    stretch of grain. The overall size is exactly length x thick x depth."""
    rng = np.random.default_rng(seed)
    w = (depth - gap * (boards - 1)) / boards
    out = []
    for i in range(boards):
        z = -depth / 2 + w / 2 + i * (w + gap)
        edge = i in (0, boards - 1)
        short = 0.0 if i == rng.integers(boards) else rng.uniform(0.002, 0.012)     # one board runs the full length
        low = 0.0 if edge else rng.uniform(0.0, 0.0025)                             # the outer boards set the height
        b = tiled(block(length - short, thick - low, w, 0, y, z), FINE)
        out.append(b.with_uv(b.uv + [rng.uniform(0, 1), rng.uniform(0, 1)]))
    full = out[0].bounds[1][0] - out[0].bounds[0][0]
    if max(m.bounds[1][0] - m.bounds[0][0] for m in out) < length - 1e-9:           # make sure one does
        out[0] = tiled(block(length, thick, w, 0, y, -depth / 2 + w / 2), FINE)
    return merge(*out)


def boards_x(mesh):
    """Timber lying along X (a top, a rail, a shelf)."""
    return tiled(mesh, FINE)


def boards_z(mesh):
    """Timber lying along Z (a side rail, a bed's long side): the same, turned a quarter about Y."""
    return tiled(mesh.rotated(90, "y"), FINE).rotated(-90, "y")


def upright(mesh):
    """Timber standing up (a leg, a post, a side panel)."""
    return grain_up(mesh, FINE)


def legs(sx, sz, h, t=0.07, inset=0.04):
    """Four square legs under a top `sx` by `sz`, `h` high."""
    xs, zs = sx / 2 - inset - t / 2, sz / 2 - inset - t / 2
    return upright(merge(*[block(t, h, t, x, 0, z) for x in (-xs, xs) for z in (-zs, zs)]))


def furniture_checks(x, y, z, tris_max, mats, anchor="base", tol=0.01):
    return [size(x=x, y=y, z=z, tol=tol), tris(max=tris_max), pivot(anchor), materials(mats), texture_size(1024)]


def top_height(part=0):
    """The highest point of a part of the model: where a hand or a plate rests."""
    return lambda ctx: float(ctx.model.parts[part][0].v[:, 1].max())
