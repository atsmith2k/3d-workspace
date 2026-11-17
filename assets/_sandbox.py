"""Sandbox kit (CinderCore builder props, from the Hive suggestions): what every piece shares.

One 512 px atlas of sixteen 128 px tiles carries every colour and marking in the kit, with a
matching roughness/metallic map, so every piece is one material and the same image bytes.
(Cinder 0.1.1 still uploads that image once per model: models cannot share a texture yet.)

`tile(mesh, T.RED)` maps a mesh whose UVs span 0..1 per face into one tile. Flat colour tiles
have a lighter rim, so each face of a block reads as a panel.

Grid: 1 m and 2 m. Dynamic pieces have their origin at the centre of their bounds; static ones
stand on Y=0.
"""
from functools import lru_cache

from PIL import Image, ImageDraw

from cadkit.game import *

PRODUCT = dict(collection="sandbox_kit", licence="CC0-1.0", tags=["sandbox", "builder", "cindercore"])
N, CELL, MARGIN = 512, 128, 6


class T:
    """Tile indices, row by row."""
    BLUE, ORANGE, GREEN, GREY = 0, 1, 2, 3
    HAZARD, CHEVRON, RED, DARK = 4, 5, 6, 7
    STEEL, GOLD, WARNING, PURPLE = 8, 9, 10, 11
    CHECKER, BARK, LEAF, FLAG = 12, 13, 14, 15


FLAT = {T.BLUE: (0.16, 0.42, 0.85), T.ORANGE: (0.95, 0.52, 0.12), T.GREEN: (0.25, 0.68, 0.32),
        T.GREY: (0.78, 0.80, 0.82), T.RED: (0.82, 0.12, 0.10), T.DARK: (0.14, 0.15, 0.17),
        T.STEEL: (0.62, 0.64, 0.67), T.GOLD: (0.95, 0.72, 0.20), T.PURPLE: (0.52, 0.30, 0.78),
        T.BARK: (0.38, 0.25, 0.15), T.LEAF: (0.28, 0.58, 0.22)}
METAL = {T.DARK: (1.0, 0.5), T.STEEL: (1.0, 0.35), T.GOLD: (1.0, 0.3)}       # tile -> (metallic, roughness)
YELLOW, BLACK, WHITE = (245, 200, 20), (22, 22, 24), (240, 240, 240)


def _u8(rgb):
    return tuple(int(round(c * 255)) for c in rgb)


@lru_cache(maxsize=None)
def atlas():
    img = Image.new("RGB", (N, N))
    d = ImageDraw.Draw(img)
    for i, rgb in FLAT.items():
        x, y = (i % 4) * CELL, (i // 4) * CELL
        rim = tuple(min(255, int(c * 1.18 + 14)) for c in _u8(rgb))
        d.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=rim)
        d.rectangle([x + 11, y + 11, x + CELL - 12, y + CELL - 12], fill=_u8(rgb))

    def cell(i):
        return (i % 4) * CELL, (i // 4) * CELL

    x, y = cell(T.HAZARD)                                   # diagonal yellow and black
    d.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=YELLOW)
    for k in range(-CELL, CELL, 64):
        d.polygon([(x + k, y + CELL), (x + k + 32, y + CELL), (x + k + 32 + CELL, y), (x + k + CELL, y)], fill=BLACK)
    x, y = cell(T.CHEVRON)                                  # two chevrons pointing up
    d.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=BLACK)
    for top in (14, 68):
        d.polygon([(x + 12, y + top + 40), (x + 64, y + top), (x + 116, y + top + 40), (x + 116, y + top + 62),
                   (x + 64, y + top + 22), (x + 12, y + top + 62)], fill=YELLOW)
    x, y = cell(T.WARNING)                                  # warning triangle on red
    d.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=_u8(FLAT[T.RED]))
    d.polygon([(x + 64, y + 12), (x + 118, y + 112), (x + 10, y + 112)], fill=YELLOW)
    d.polygon([(x + 64, y + 34), (x + 98, y + 100), (x + 30, y + 100)], fill=BLACK)
    d.rectangle([x + 59, y + 52, x + 69, y + 80], fill=YELLOW)
    d.ellipse([x + 58, y + 85, x + 70, y + 97], fill=YELLOW)
    x, y = cell(T.CHECKER)
    for r in range(4):
        for c in range(4):
            d.rectangle([x + c * 32, y + r * 32, x + c * 32 + 31, y + r * 32 + 31], fill=BLACK if (r + c) % 2 else WHITE)
    x, y = cell(T.FLAG)                                     # check mark on green
    d.rectangle([x, y, x + CELL - 1, y + CELL - 1], fill=(40, 170, 70))
    d.line([(x + 28, y + 66), (x + 54, y + 92), (x + 102, y + 34)], fill=WHITE, width=16, joint="curve")
    base = np.asarray(img, float) / 255
    base = np.clip(base * (0.97 + 0.06 * fbm(N, 16, 3, seed=5))[..., None], 0, 1)      # not dead flat
    metallic, rough = np.zeros((N, N)), np.full((N, N), 0.62)
    for i, (m, r) in METAL.items():
        x, y = cell(i)
        metallic[y:y + CELL, x:x + CELL], rough[y:y + CELL, x:x + CELL] = m, r
    return Material("sandbox_atlas", base=base, orm=orm(1.0, rough, metallic), metallic=1.0, roughness=1.0)


def tile(mesh, index):
    """Map a mesh's 0..1 UVs into one atlas tile (values outside 0..1 wrap first)."""
    uv = mesh.uv - np.floor(mesh.uv)
    uv = np.where(np.isclose(mesh.uv, 1.0), 1.0, uv)                 # keep an exact 1.0 at the far edge
    col, row = index % 4, index // 4
    m = MARGIN / CELL
    return mesh.with_uv((np.array([col, row]) + m + uv * (1 - 2 * m)) / 4)


def tile_by_normal(mesh, top, side):
    """Faces looking up or down take one tile, faces looking sideways another."""
    up = np.abs(mesh.n[:, 1]) > 0.5
    a, b = tile(mesh, top), tile(mesh, side)
    return mesh.with_uv(np.where(up[:, None], a.uv, b.uv))


def along(mesh, a, b):
    """Stand a mesh built along +Y from the origin so that its Y axis runs from point a toward b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    y = np.array([0.0, 1.0, 0.0])
    v = np.cross(y, d)
    s, c = np.linalg.norm(v), float(y @ d)
    if s < 1e-9:
        r = np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    else:
        k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        r = np.eye(3) + k + k @ k * ((1 - c) / s ** 2)
    return Mesh(mesh.v @ r.T + a, mesh.f, mesh.n @ r.T, mesh.uv)


def ball(r, sides=8, rings=4):
    """A low-poly sphere centred on the origin."""
    prof = [(r * np.sin(t), -r * np.cos(t)) for t in np.linspace(0, np.pi, rings + 1)]
    prof[0], prof[-1] = (0.0, -r), (0.0, r)
    return lathe(prof, sides)


def block_checks(x, y, z, tris_max=200, anchor="centre"):
    """Exact size (2 mm): the kit's pieces must sit flush on the grid."""
    return [size(x=x, y=y, z=z, tol=0.002), tris(max=tris_max), pivot(anchor), materials(1), texture_size(512)]
