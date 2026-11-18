"""Dirt path: two metres of trodden earth laid over the ground.

Spec:
  kind: environment
  size: about 1.35 x 0.03 x 2.00 m at its widest
  pivot: on Y=0, at the middle of its length; it runs along Z
  budget: 600 triangles, one material, 1024 px textures
  materials: packed soil, paler than the ground it crosses, darker in the ruts, few stones
  features: 30 mm proud of the ground it lies on, with edges that slope down to it; the
            edges wander, but each end is exactly 1.10 m wide and square, so pieces meet
            end to end on the grid; no underside (it is never seen)
  use: wilderness sub-pack; laid on nat_ground tiles, one per 2 m cell
  engine: no body (the ground under it is the collider)
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "dirt path, 2 m straight"
PARAMS = dict(width=1.10, wander=0.09, seed=6)
BUDGET = dict(BUDGET_OF["terrain"], materials=1)
ENGINE = dict(rest_y=0.0)
PRODUCT = product("wilderness", "terrain", "path", gameplay=dict(runs="z", ends_width=1.10))
ROWS, RISE, SKIRT = 9, 0.03, 0.06


def checks(p):
    def ends(ctx):
        v = ctx.model.parts[0][0].v
        top = v[v[:, 1] > RISE - 1e-6]
        w = [float(np.ptp(top[np.abs(top[:, 2] - z) < 1e-6][:, 0])) for z in (-GRID / 2, GRID / 2)]
        return all(abs(x - p.width) < 0.002 for x in w), f"ends are {w[0]:.3f} and {w[1]:.3f} m wide: pieces meet"

    def no_underside(ctx):
        m = ctx.model.parts[0][0]
        return m.n[:, 1].min() > -0.01, "no face looks down"
    return [size(x=(1.2, 1.5), y=RISE, z=GRID, tol=0.002), tris(max=BUDGET["tris"]), pivot((None, 0.0, 0.5)), materials(1),
            texture_size(1024), custom("ends meet", ends), custom("no underside", no_underside)]


def build(p):
    rng = np.random.default_rng(p.seed)
    z = np.linspace(-GRID / 2, GRID / 2, ROWS)
    fade = np.sin(np.linspace(0, np.pi, ROWS))                         # no wander at the ends
    left = -p.width / 2 + p.wander * fade * rng.uniform(-1, 1, ROWS)
    right = p.width / 2 + p.wander * fade * rng.uniform(-1, 1, ROWS)
    rows = [[(a - SKIRT, 0.0, zi), (a, RISE, zi), (b, RISE, zi), (b + SKIRT, 0.0, zi)] for zi, a, b in zip(z, left, right)]
    v = np.array(rows).reshape(-1, 3)
    f = []
    for i in range(ROWS - 1):
        for k in range(3):
            q, s = i * 4 + k, (i + 1) * 4 + k
            f += [(q, s, s + 1), (q, s + 1, q + 1)]
    f = np.array(f)
    m = flat(Mesh(v, f))
    if m.n[:, 1].mean() < 0:                                           # wound the other way: turn every face
        m = flat(Mesh(v, f[:, ::-1]))
    return Model((m.with_uv(np.c_[m.v[:, 0], -m.v[:, 2]] / TILE), trodden()))
