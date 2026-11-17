"""Oak barrel: bulged staves, three iron hoops, plank heads set in below the rim.

Spec:
  kind: prop
  size: 0.66 m across the belly x 0.90 m tall
  pivot: centre of bounds (dynamic prop; the box collider is centred on the entity)
  budget: 900 triangles, one material, 1024 px textures
  materials: one atlas: staves and hoops wrap the side (v 0..0.75), head planks in the strip below
  features: 20 staves; hoops 45 mm wide standing 6 mm proud at 12 %, 50 % and 88 % of the height;
            heads recessed 30 mm inside a 20 mm rim
  use: tavern, cellar and dock dressing; chest-high beside a 1.8 m player; pushable
  engine: body dynamic, box collider (it does not roll: a box keeps it upright when pushed)
"""
from cadkit.game import *

KIND = "prop"
DESCRIPTION = "oak barrel with iron hoops, pushable"
PARAMS = dict(height=0.90, belly=0.33, end=0.27, staves=20, sides=20, hoop=0.045, proud=0.006,
              recess=0.03, rim=0.02, seed=5)
BUDGET = dict(tris=900, texture=1024, materials=1)
ENGINE = dict(body="dynamic", collider="box")
PRODUCT = dict(collection="dungeon_kit", licence="CC0-1.0", tags=["barrel", "prop"])
SIDE_V = 0.75                                   # the side uses the top three quarters of the atlas
HOOPS = (0.12, 0.50, 0.88)


def checks(p):
    return [size(x=2 * p.belly + 2 * p.proud, y=p.height, z=2 * p.belly + 2 * p.proud, tol=0.012),
            tris(max=900), pivot("centre"), materials(1), texture_size(1024),
            custom("staves tile round the barrel", lambda ctx: _wraps(ctx))]


def _wraps(ctx):
    """The seam at u=0 is a stave joint like the others: its step is no larger than theirs."""
    n, staves = 1024, ctx.params["staves"]
    side = np.asarray(ctx.model.materials[0].base)[: int(n * SIDE_V)]
    joints = [np.abs(side[:, i * n // staves] - side[:, i * n // staves - 1]).mean() for i in range(1, staves)]
    wrap = np.abs(side[:, 0] - side[:, -1]).mean()
    return wrap <= 1.5 * max(joints), f"wrap step {wrap:.3f}, other stave joints up to {max(joints):.3f}"


def radius(p, t):
    """Barrel radius at height fraction t: a parabola from the ends to the belly."""
    return p.end + (p.belly - p.end) * (1 - (2 * t - 1) ** 2)


def profile(p):
    """(radius, y) up the side, with a raised band at each hoop. y from -h/2 to h/2."""
    half = p.hoop / p.height / 2
    ts = {0.0, 1.0, 0.25, 0.75}
    for c in HOOPS:
        ts |= {c - half - 0.004, c - half, c + half, c + half + 0.004}
    pts = []
    for t in sorted(ts):
        on_hoop = any(c - half - 1e-9 <= t <= c + half + 1e-9 for c in HOOPS)
        pts.append((radius(p, t) + (p.proud if on_hoop else 0.0), (t - 0.5) * p.height))
    return pts


def atlas(p, n=1024):
    side_px = int(n * SIDE_V)
    rng = np.random.default_rng(p.seed)
    grain = 0.65 * streaks(n, "y", cells=160, stretch=8, seed=p.seed) + 0.35 * fbm(n, 8, seed=p.seed + 1)
    base = tint(grain, (0.36, 0.23, 0.12), (0.62, 0.43, 0.24))
    height = np.ones((n, n))
    metal = np.zeros((n, n))
    rough = 0.55 + 0.3 * grain
    # staves: one tone each, a dark joint between them (the image wraps: joint at column 0)
    for i in range(p.staves):
        x0, x1 = i * n // p.staves, (i + 1) * n // p.staves
        base[:side_px, x0:x1] *= 0.84 + 0.2 * rng.random()
        height[:side_px, x0:x0 + 3] = 0.0
        base[:side_px, x0:x0 + 3] *= 0.4
    # hoops: v runs from the top of the barrel (row 0) to the bottom (row side_px)
    scratch = streaks(n, "x", cells=200, stretch=6, seed=p.seed + 2)
    for c in HOOPS:
        half = p.hoop / p.height / 2
        y0, y1 = int((1 - c - half) * side_px), int((1 - c + half) * side_px)
        base[y0:y1] = tint(scratch[y0:y1], (0.16, 0.16, 0.17), (0.30, 0.30, 0.31))
        metal[y0:y1] = 1.0
        rough[y0:y1] = 0.42 + 0.3 * scratch[y0:y1]
        height[y0:y1] = 1.0
        for k in range(4):                                      # rivets
            cx, cy = int((k + 0.5) * n / 4), (y0 + y1) // 2
            yy, xx = np.ogrid[:n, :n]
            dot = (xx - cx) ** 2 + (yy - cy) ** 2 < 49
            height[dot] = 2.0
            base[dot] = (0.34, 0.34, 0.35)
    # head: planks across a square in the strip below the side
    head = slice(side_px, n)
    hw = n - side_px
    hgrain = 0.65 * streaks(n, "x", cells=160, stretch=8, seed=p.seed + 3)[head, :hw] + 0.35 * grain[head, :hw]
    base[head, :hw] = tint(hgrain, (0.33, 0.21, 0.11), (0.58, 0.40, 0.22))
    for i in range(1, 5):
        y = side_px + i * hw // 5
        height[y:y + 3, :hw] = 0.0
        base[y:y + 3, :hw] *= 0.4
    base[head, hw:] = (0.2, 0.13, 0.07)                         # unused: rim wood, so mips stay brown
    return Material("barrel_oak_iron", base=base,
                    orm=orm(occlusion_from_height(np.minimum(height, 1.0), 4, 1.2), np.clip(rough, 0, 1), metal),
                    normal=normal_from_height(height + 0.4 * grain, 4.0), metallic=1.0, roughness=1.0)


def build(p):
    h = p.height
    side = lathe(profile(p), p.sides, u_repeat=1.0, v_range=(0.0, SIDE_V))
    hw = 1 - SIDE_V                                            # head square: u 0..hw, v SIDE_V..1
    rect = (0.0, SIDE_V, hw, 1.0)
    r_in = p.end - p.rim
    parts = [side]
    for top in (True, False):
        s = 1 if top else -1
        y_rim, y_head = s * h / 2, s * (h / 2 - p.recess)
        # rim: flat ring from the stave edge in, then the inner wall down to the head
        ring = lathe([(p.end, y_rim), (r_in, y_rim), (r_in, y_head)][:: 1 if top else -1],
                     p.sides, v_range=(SIDE_V - 0.02, SIDE_V - 0.05), smooth=False)
        parts += [ring, disc(r_in, y_head, p.sides, up=top, uv_rect=rect)]
    return Model((merge(*parts), atlas(p)))
