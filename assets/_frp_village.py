"""Village building grammar: timber frame and plaster, on the pack's ruler.

A house is assembled from pieces on the 2 m grid, one storey (3 m) at a time:

    walls      stand on cell edges, centred, 0.3 m thick: plaster panels between timbers that
               stand 30-40 mm proud on both faces, so a wall reads the same from inside
    corners    a post on every grid corner hides the joint where two walls meet
    floors     boards, walking surface at the piece's origin (Y = 0 of its storey); a ground
               floor is placed 20 mm above the ground it stands on, never level with it (two
               surfaces in one plane flicker, and from above the ground wins)
    roofs      one slope piece per 2 m of wall, rising 45 degrees to the ridge, 0.4 m of eave
    gables     the triangular wall that closes a roof end

Every piece is its own entity in a world, so a top-down game hides roofs (and upper storeys)
by name, a first-person game walks inside (both wall faces are finished, openings are real),
and a third-person game sees the same house from the street.
"""
from _frp import *

POST, BEAM, PLASTER_T = 0.32, 0.30, 0.24          # thickness through the wall: posts proud of beams proud of plaster
PITCH_RISE, EAVE, THATCH_T = 2.0, 0.4, 0.3         # a slope rises 2 m over 2 m (45 degrees)


def timber_wall(width=GRID, opening=None):
    """(plaster mesh, timber mesh) for one wall run. opening: None, "door" or "window"."""
    w, h = width, STOREY
    plaster_parts, timbers, uprights = [], [], []

    def pl(sx, sy, x=0.0, y=0.0):
        plaster_parts.append(block(sx, sy, PLASTER_T, x, y))

    def tb(sx, sy, x=0.0, y=0.0, t=BEAM):
        (uprights if sy > sx else timbers).append(block(sx, sy, t, x, y))       # grain follows the timber

    for s in (-1, 1):                                             # half posts: two neighbours make one post
        tb(0.1, h, s * (w / 2 - 0.05), 0, POST)
    tb(w, 0.18, 0, h - 0.18)                                      # top plate
    if opening is None:
        pl(w, h)
        tb(w, 0.18)                                               # sill beam
        tb(w, 0.12, 0, 1.44)                                      # mid rail
    else:
        ow, o0, o1 = (DOOR_W, 0.0, DOOR_H) if opening == "door" else (WINDOW_W, WINDOW_SILL, WINDOW_SILL + WINDOW_H)
        side = (w - ow) / 2
        for s in (-1, 1):
            x = s * (ow / 2 + side / 2)
            pl(side, h, x)
            tb(side, 0.18, x)                                     # sill beam, not across the opening
            tb(side, 0.12, x, 1.44)
            tb(0.1, o1 - o0 + 0.1, s * (ow / 2 + 0.05), o0, POST)  # jamb
        pl(ow, h - o1, 0, o1)                                     # above the opening
        tb(ow + 0.2, 0.12, 0, o1, POST)                           # lintel
        if opening == "window":
            pl(ow, o0, 0, 0)                                      # below it
            tb(ow, 0.18)
            tb(ow + 0.2, 0.1, 0, o0 - 0.1, POST + 0.06)           # window sill, proud
            for x in (-ow / 6, ow / 6):                           # leaded lattice: bars, since Cinder draws no glass
                uprights.append(block(0.03, o1 - o0, 0.04, x, o0))
            timbers.append(block(ow, 0.03, 0.04, 0, o0 + (o1 - o0) / 2))
    return tiled(merge(*plaster_parts)), merge(tiled(merge(*timbers)), grain_up(merge(*uprights)))


def roof_slope(width=GRID):
    """A thatched slope: `width` along X, rising toward +Z from the wall line (origin) to the ridge."""
    pts = ccw([(-EAVE, -EAVE), (PITCH_RISE, PITCH_RISE), (PITCH_RISE, PITCH_RISE + THATCH_T), (-EAVE, -EAVE + THATCH_T)])
    m = prism(pts, width).rotated(-90, "y")                       # the profile's run axis becomes +Z
    down = (m.v[:, 2] + m.v[:, 1]) / 2 ** 0.5                     # distance up the slope
    return directed_uv(m, np.c_[m.v[:, 0] / TILE, -down / TILE], (0, 1, -1))   # strands run down the slope


def gable(depth=2 * GRID):
    """(plaster, timber) for the triangular end wall of a roof over a building `depth` deep."""
    half = depth / 2
    tri = prism(ccw([(-half, 0), (half, 0), (0, half * PITCH_RISE / GRID)]), PLASTER_T)
    timbers = merge(tiled(block(depth, 0.18, BEAM)), grain_up(block(0.2, half - 0.1, POST)))
    return tiled(tri), timbers
