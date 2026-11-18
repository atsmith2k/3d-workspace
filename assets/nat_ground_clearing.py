"""Clearing ground: a round piece of open ground 40 m across, flat in the middle and rising to
a low bank at its rim.

Spec:
  kind: environment
  size: 40 x about 2.2 x 40 m
  pivot: the centre of the flat middle, on the walking surface (Y=0)
  budget: 600 triangles, one material, 1024 px textures
  materials: trodden earth and dying grass, repeating every 4 m
  features: dead flat within 9 m of the centre (a building kit on the 2 m grid stands on it);
            beyond that it rolls and climbs to a bank about 2 m high at the rim, so from eye
            height the ground ends in a rise against trees, not in a cut edge against the sky;
            smooth-shaded; no underside and no skirt (nat_treeline stands on the rim)
  use: wilderness sub-pack: the floor of a scene set in a clearing. One piece and three
       textures where twenty-five 8 m tiles would cost a hundred and fifty: a Cinder world
       holds about 250
  engine: body static, auto collider (a mesh: the bank is walkable)
"""
from _frp_nature import *

KIND = "environment"
DESCRIPTION = "round clearing ground, 40 m, flat middle and a low bank"
PARAMS = dict(radius=20.0, flat=9.0, bank=2.0, seed=5)
BUDGET = dict(BUDGET_OF["terrain"], materials=1)
ENGINE = dict(body="static", collider="auto", rest_y=0.0)
PRODUCT = product("wilderness", "terrain", "ground", "clearing", gameplay=dict(flat_radius=9.0, rim_radius=20.0))

RINGS = (3.0, 6.0, 9.0, 11.0, 13.0, 15.0, 17.0, 18.5, 20.0)
SEGMENTS = 30


def height(p, x, z):
    """The ground's height at (x, z): zero inside the flat, then a rolling climb to the bank."""
    r = np.hypot(x, z)
    t = np.clip((r - p.flat) / (p.radius - p.flat), 0, 1)
    climb = t * t * (3 - 2 * t)
    roll = fbm3(np.stack([x, 0 * x, z], -1), 7.0, 3, p.seed) - 0.5
    return climb * (p.bank * 0.8 + 1.6 * roll * p.bank * 0.5) + climb * 0.2 * p.bank * t


def checks(p):
    def flat_middle(ctx):
        v = ctx.model.parts[0][0].v
        mid = v[np.hypot(v[:, 0], v[:, 2]) <= p.flat + 1e-6]
        return np.abs(mid[:, 1]).max() < 1e-9, f"{len(mid)} vertices within {p.flat:.0f} m of the centre are at Y=0"

    def banked(ctx):
        v = ctx.model.parts[0][0].v
        rim = v[np.hypot(v[:, 0], v[:, 2]) > p.radius - 0.01]
        return rim[:, 1].min() > 0.8, f"the rim stands {rim[:, 1].min():.1f} to {rim[:, 1].max():.1f} m above the middle"

    def no_underside(ctx):
        return ctx.model.parts[0][0].n[:, 1].min() > 0.3, "every face looks up"
    return [size(x=2 * p.radius, y=(1.2, 3.2), z=2 * p.radius, tol=0.3), tris(max=BUDGET["tris"]), pivot((0.5, 0.0, 0.5), tol=0.2),
            materials(1), texture_size(1024), custom("flat middle", flat_middle), custom("bank at the rim", banked),
            custom("no underside", no_underside)]


def build(p):
    ang = np.linspace(0, 2 * np.pi, SEGMENTS, endpoint=False)
    v = [(0.0, 0.0, 0.0)]
    for r in RINGS:
        v += [(r * np.cos(a), 0.0, r * np.sin(a)) for a in ang]
    v = np.array(v)
    v[:, 1] = height(p, v[:, 0], v[:, 2])
    f = [(0, 1 + (k + 1) % SEGMENTS, 1 + k) for k in range(SEGMENTS)]
    for i in range(len(RINGS) - 1):
        a0, b0 = 1 + i * SEGMENTS, 1 + (i + 1) * SEGMENTS
        for k in range(SEGMENTS):
            k1 = (k + 1) % SEGMENTS
            f += [(a0 + k, a0 + k1, b0 + k1), (a0 + k, b0 + k1, b0 + k)]
    f = np.array(f)
    m = Mesh(v, f)
    if m.n[:, 1].mean() < 0:
        m = Mesh(v, f[:, ::-1])
    return Model((m.with_uv(np.c_[m.v[:, 0], -m.v[:, 2]] / GROUND_TILE), ground()))
