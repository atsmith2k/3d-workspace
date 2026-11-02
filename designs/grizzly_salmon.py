"""Grizzly bear standing in a shallow creek, a sockeye salmon pinned under its near front
paw, boulders and current lines around its feet. No background: the fabric shows
everywhere the scene does not.

The bear is digitised from the user's reference illustration (REFERENCE below), the
way a digitiser works from artwork: cut out of its background, its colours reduced to
8 thread tones (k-means), each tone cleaned of specks and vectorised, and every tone
split into patches whose fill runs with the hair direction read from the image.

Spec:
  object:       realistic wildlife piece for a jacket back, tote, pillow or framed hoop art
  overall:      bear `width` mm wide (default 95), scene 1.19 x 1.07 width (113 x 101), hoop 5x7
  fabric:       medium woven (canvas, twill, denim) with tear-away; knits want cut-away
  threads:      1 creek blue (current lines), 2 boulder grey, 3 salmon red, 4 salmon olive
                (head), 5-12 the bear's 8 tones from the reference, lightest first (the
                lightest also lights the boulders), 13 amber irises (a bear tone again),
                14 cream catchlights and claws (the lightest tone again): 14 blocks,
                12 threads
  likeness:     from the reference: three-quarter stance, head turned to the viewer,
                light crown and face ruff, dark eye sockets with amber eyes, tan muzzle,
                dark nose, round ears with dark insides, golden streaks through the coat,
                dark legs and belly, pale claws; ground shadow replaced by the creek
  must have:    salmon ~40 mm under the near front paw, claws over it; boulders front left
                and right; amber irises (~1.8 mm) with a cream catchlight; blue ripple
                arcs (bean stitch) round each paw, stopping at the bear and salmon; pale claws, five per paw as on a real bear
                (the far hind paw shows four, its fifth hidden; the reference draws six
                on one paw): each a crescent hooked 45-60 deg, fanned 5-7 deg across the
                paw, the middle ones longest (front 4.6 mm, hind 2.8-3.0 mm), one tapered
                satin from 1.6 mm at the root to a 0.3 mm point (taper=True), dark
                toe-shadow fill between the claws (darkest tone),; fills follow the fur: each streak
                runs along its own hair direction (image structure tensor), areas over
                350 mm2 split into ~14 mm flow patches
  detail:       fur streaks keep tips down to 0.8 mm (thinner bits join the neighbour
                tone), so up to 8 mm2 of each fill may be under 1 mm wide
  economy:      tones overlap 0.25 mm and are never stacked; creek is current lines
                sewn first under everything; max 3.5 thread layers, <= 30000 stitches
"""
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch.artwork import Artwork, _lab

DESCRIPTION = "Grizzly bear in a creek, salmon under its paw, digitised from a reference illustration"
HOOP = "5x7"
REFERENCE = Path(__file__).with_name("grizzly_reference.png")
EYES = [(259.5, 100.6), (297.6, 102.2)]          # iris centres in the reference (px)
# Claws: a bear has five per paw, placed across each paw seen in the reference (which
# draws six on one paw); the far hind paw is turned away and shows four. Per paw:
# (x0, x1, y) root line in reference pixels, count, length mm, heading deg (design,
# -90 = straight down), hook deg (how far the claw curls over its length), fan deg.
PAWS = [
    ((66, 86, 326), 5, 3.0, -50, -45, 6),       # near hind: shorter
    ((135, 155, 313), 4, 2.8, -52, -45, 6),     # far hind: turned away, fifth hidden
    ((216, 246, 328), 5, 4.6, -40, -60, 7),     # near front: long, hooked over the salmon
    ((276, 305, 319), 5, 4.6, -72, -50, 5),     # right front: long, hanging
]


def claw(root, length, heading, hook, w0=1.6, tip=0.3):
    """One claw as a single satin crescent: the centreline curls by `hook` degrees
    from root to tip (more toward the end, like a real claw), the width runs from `w0`
    at the root down to a `tip` point, and a shadow line follows its underside (the
    side it curls toward). Returns (centreline, widths, shadow)."""
    n = 26
    t = np.linspace(0, 1, n)
    head = np.radians(heading + hook * t ** 1.5)
    step = length / (n - 1)
    pts = np.vstack([root, root + np.cumsum(np.c_[np.cos(head), np.sin(head)] * step, axis=0)[:-1]])
    widths = tip + (w0 - tip) * (1 - t) ** 0.7
    under = np.c_[np.cos(head - np.pi / 2), np.sin(head - np.pi / 2)] * np.sign(-hook or 1)
    shadow = (pts + under * (widths / 2 + 0.3)[:, None])[3:n - 3]
    return pts, widths, shadow


SPLASH = [[(22, 333), (52, 328), (88, 333)], [(30, 338), (56, 336), (80, 339)],      # water arcs
          [(122, 322), (146, 318), (168, 323)], [(204, 340), (234, 335), (264, 340)],
          [(212, 345), (236, 343), (258, 346)], [(266, 330), (292, 326), (318, 331)],
          [(272, 335), (294, 333), (314, 336)]]

PARAMS = dict(
    width=95.0,            # bear width, mm; the creek and boulders scale with it
    tones=4,               # fur threads; texture comes from stitch direction, not colour
    smooth=3,              # mode-filter passes on the tone map (higher = simpler shapes)
    min_patch=14.0,        # mm2; smaller specks of a tone merge into their neighbours
    min_width=1.0,         # mm; thinner bits of a tone go to its neighbours
    patch=10.0,            # mm; fur is sewn in patches this size, each along its own hair
                           # direction, so one thread catches the light like many shades
    fur_stitch=4.0,        # mm; long, silky fill stitches (fewer penetrations)
    mid_spacing=0.48,      # mm; the mid tones are filled lighter (thread spread closes it)
    underlay_over=150.0,   # mm2; only fur pieces bigger than this get an underlay
    water="#7fa7c0",
    rock="#6b6a64",
    salmon="#c2352b",
    salmon_head="#5b6b34",
    ivory="#ddd3bf",       # claws, catchlights, boulder highlights
)


def ground_shadow(rgb, alpha):
    """Background for the reference: transparent pixels, plus the soft grey ground
    shadow under the paws (low chroma, mid lightness, below the paws' tops)."""
    L = _lab(rgb.reshape(-1, 3)).reshape(rgb.shape)
    chroma = np.hypot(L[..., 1], L[..., 2])
    rows = np.arange(rgb.shape[0])[:, None] * np.ones(rgb.shape[1])[None]
    up = rgb.shape[0] / 360
    shadow = (rows > 300 * up) & (chroma < 26) & (L[..., 0] > 35) & (L[..., 0] < 72)
    return (alpha <= 128) | shadow


def clean(shape, min_area=1.0):
    """Fill-ready: slivers under 0.4 mm smoothed off, outline simplified, crumbs dropped (Ink/Stitch's auto-fill can fail on
    razor-thin or self-touching pieces)."""
    g = shape.buffer(-0.2).buffer(0.2).simplify(0.05).buffer(0)
    if min_area >= 2.0:                                      # small props: no sub-1 mm tips
        g = g.buffer(-0.5).buffer(0.5)
    return unary_union([q for q in polygons_of(g) if q.area >= min_area])


def _props(art, k):
    """Rough outlines of the salmon and boulders, for closing slots against them."""
    at = lambda x, y: tuple(float(v) for v in art.to_mm(x, y))
    fish = Polygon([at(170, 330), at(240, 326), at(304, 336), at(240, 348), at(170, 346)])
    rocks = [Polygon([at(4, 352), at(12, 338), at(58, 338), at(68, 350), at(20, 364)]),
             Polygon([at(300, 352), at(310, 340), at(354, 342), at(360, 354), at(312, 364)])]
    return [fish.buffer(0.5 * k), *rocks]


def chain(pieces):
    """Order (shape, angle) pieces nearest-next from the first, so each fill starts
    beside the one before it (short travel, no trim between touching pieces)."""
    if not pieces:
        return []
    left = list(pieces)
    out = [left.pop(0)]
    while left:
        last = out[-1][0]
        i = min(range(len(left)), key=lambda j: last.distance(left[j][0]))
        out.append(left.pop(i))
    return out


def checks(p):
    return [
        size(w=1.185 * p.width, h=1.065 * p.width, tol=2.0),          # bear plus boulders
        hoop(),
        colors(10),
        max_density(3.5),
        long_stitches(7.0),
        min_feature(1.0, max_mm2=8.0),           # fur streaks taper to fine tips by design
        coverage(1.0),
        stitches(max=30000),
    ]


def design(p):
    art = Artwork(REFERENCE, width=p.width, background=ground_shadow)
    tones = art.tones(p.tones, smooth=p.smooth, min_area=p.min_patch, overlap=0.25, min_width=p.min_width)
    bear = unary_union([t.shape for t in tones])
    # the narrow tips of the gaps between the legs read as stray slots once sewn: close
    # anything under ~2.6 mm wide inside the silhouette with the darkest tone (shadow)
    scene = unary_union([bear, *_props(art, p.width / 95.0)])
    holes = unary_union([Polygon(q.exterior) for q in polygons_of(scene)]).difference(scene)
    tips = scene.buffer(1.3).buffer(-1.3).difference(scene).intersection(holes)
    tips = unary_union([q for q in polygons_of(tips) if q.area > 0.2])
    if not tips.is_empty:
        tones[-1].shape = tones[-1].shape.union(tips.buffer(0.25)).intersection(bear.union(tips))
        bear = bear.union(tips)
    k = p.width / 95.0

    def at(x, y):
        """Reference pixel (360 px image, y down) -> mm."""
        return tuple(float(v) for v in art.to_mm(x, y))

    def pts(seq):
        return np.array([at(x, y) for x, y in seq])

    # salmon lying under the near front paw, head to the right
    t = np.linspace(0, 1, 44)
    c = pts(np.c_[176 + 128 * t, 338 - 5 * np.sin(t * np.pi) + 3 * t])
    half = (0.4 + 3.6 * np.sin(np.clip(t * 1.08 + 0.02, 0, 1) * np.pi) ** 0.7) * k
    half[-6:] = np.linspace(half[-7], 1.4 * k, 6)
    tang = np.gradient(c, axis=0)
    nrm = np.c_[-tang[:, 1], tang[:, 0]]
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    fish = Polygon(np.vstack([c + nrm * half[:, None], (c - nrm * half[:, None])[::-1]])).buffer(0.3 * k)
    tail = Polygon(pts([(178, 338), (166, 330), (170, 338), (166, 346)])).buffer(0.3)
    fish = fish.union(tail).buffer(0)
    head_cut = Polygon(pts([(284, 300), (320, 300), (320, 380), (284, 380)]))
    fish_eye = circle(*at(296, 337.5), 0.65 * k)

    # claws: fanned across each paw, middle ones longest
    claws, toe_shadows = [], []
    for (x0, x1, y), count, length, heading, hook, fan in PAWS:
        mid = (count - 1) / 2
        paw = []
        for i, x in enumerate(np.linspace(x0, x1, count)):
            f = 1 - 0.15 * abs(i - mid) / max(mid, 1)
            c = claw(np.array(at(x, y)), length * f * k, heading + (i - mid) * fan, hook)
            claws.append(c)
            paw.append(LineString(c[0]).buffer(0.8 * k))
        # the dark gaps between the claws (the reference shades them): the claws' hull,
        # pulled back from the tips, under the claws and off the fur
        hull = unary_union(paw).convex_hull.intersection(unary_union(paw).buffer(1.0 * k).buffer(-0.4 * k))
        toe_shadows.append(hull)
    # the claws' own outlines: the fur and toe shadow are knocked out under them (one layer)
    claw_area = unary_union([unary_union([Point(q).buffer(w * k / 2) for q, w in zip(c, ws)])
                             for c, ws, _ in claws]).buffer(-0.3)
    toe_shadows = [t.difference(claw_area) for t in toe_shadows]

    # boulders, front left and front right, sitting in the creek
    rocks = [smooth(pts([(4, 352), (12, 338), (34, 334), (58, 338), (68, 350), (56, 362), (20, 364)]), 10),
             smooth(pts([(300, 352), (310, 340), (332, 336), (354, 342), (360, 354), (344, 364), (312, 364)]), 10)]
    rocks = [r.buffer(0) for r in rocks]
    rock_all = unary_union(rocks)
    rock_hi = unary_union([r.difference(move(r, 0.9 * k, -2.2 * k)) for r in rocks]).buffer(-0.3).buffer(0.3)

    d = Design()
    d.sew_jumps_mm = 8.0          # moves between neighbouring fur patches: travel, not trims
    # 1 creek: current lines across the bottom, sewn first and covered by the bear and
    # boulders; they stop at the salmon and claws, where three layers already meet
    busy = unary_union([claw_area, fish]).buffer(0.6)
    for i, y in enumerate([326, 336, 346, 356, 366]):
        xs = np.linspace(-10 + (i % 2) * 8, 370 - (i % 3) * 6, 30)
        row = pts(np.c_[xs, y + 2.2 * np.sin(xs * 0.06 + i) + 1.0 * np.sin(xs * 0.17)])
        line = LineString(row if i % 2 == 0 else row[::-1]).difference(busy)
        for j, piece in enumerate(getattr(line, "geoms", [line])):
            if piece.length > 2.0:
                d.run(np.asarray(piece.coords), p.water, length=2.5, name=f"current {i + 1}.{j + 1}")
    # ripple arcs round the paws, stopping short of the bear, claws and salmon (a
    # triple stitch under them would only add density)
    keep_off = unary_union([bear, claw_area, fish]).buffer(0.6)
    for i, arc in enumerate(SPLASH):
        line = LineString(spline(pts(arc), 8)).difference(keep_off)
        for j, piece in enumerate(getattr(line, "geoms", [line])):
            if piece.length > 2.0:
                d.run(np.asarray(piece.coords), p.water, length=1.6, bean=1, name=f"ripple arc {i + 1}.{j + 1}")
    # 2 boulders (grey body; the lit top sews with the bear's lightest tone)
    d.fill(clean(rock_all.difference(rock_hi).difference(bear).difference(fish), 2.0), p.rock, angle=-15,
           name="boulders")
    # 3-4 salmon, under the paw: the bear's tones sew over it
    under = bear.buffer(-0.2)
    under = under.union(claw_area)                         # the claws sit on the salmon
    d.fill(clean(fish.difference(head_cut).difference(under), 2.0), p.salmon, angle=-6, spacing=0.38, name="salmon")
    d.fill(clean(fish.intersection(head_cut).difference(under), 2.0), p.salmon_head, angle=60, spacing=0.38,
           name="salmon head")
    # 5-8 the bear, lightest tone first. Each tone is sewn as small patches that each run
    # along the local hair direction: in thread, a change of direction reads as a change
    # of shade (the sheen moves), so a few threads carry the coat's texture. Patches are
    # chained nearest-first, so touching patches sew on without trims.
    for n, tone in enumerate(tones):
        mid_tone = 0 < n < len(tones) - 1
        pieces = []
        for island in polygons_of(clean(tone.shape)):
            parts = (art.by_flow(island, cell=p.patch * k, merge_deg=10) if island.area > 30 * k * k
                     else [(island, art.angle_in(island))])
            for piece, ang in parts:
                piece = clean(piece.difference(claw_area))
                if not piece.is_empty:
                    pieces.append((piece, ang))
        whole = tone.shape.difference(claw_area)
        for j, (piece, ang) in enumerate(chain(pieces)):
            piece = clean(piece.buffer(0.25).intersection(whole))       # seams overlap, never gap
            d.fill(piece, tone.color, angle=ang, spacing=p.mid_spacing if mid_tone else 0.42,
                   stitch=p.fur_stitch, underlay=piece.area > p.underlay_over * k * k, fill_underlay_row_spacing_mm=2.6,
                   name=f"tone {n + 1}.{j + 1}")
        if n == len(tones) - 1:
            d.fill(fish_eye.difference(under), tone.color, angle=0, name="salmon eye")
            for i, toes in enumerate(toe_shadows):               # dark between the claws
                toes = clean(toes.difference(bear.buffer(-0.25)), 2.0)
                if not toes.is_empty:
                    d.fill(toes, tone.color, angle=90, spacing=0.42, underlay=False, name=f"toe shadow {i + 1}")
    # 12 amber irises over the dark eye sockets (the reference's eyes are amber)
    amber = min(tones, key=lambda t: abs(t.lightness - 64)).color
    for i, (x, y) in enumerate(EYES):
        d.fill(ellipse(*at(x, y), 0.9 * k, 0.72 * k), amber, angle=20, spacing=0.35, underlay=False,
               name=f"iris {i + 1}")
    # ivory: catchlights, claws, boulder highlights
    cream = p.ivory
    for i, (x, y) in enumerate(EYES):
        cx, cy = at(x, y)
        d.run(np.array([(cx + 0.15 * k, cy + 0.25 * k), (cx + 0.55 * k, cy + 0.4 * k)]), cream, length=0.5,
              name=f"catchlight {i + 1}")
    for i, (centre, widths, _) in enumerate(claws):
        d.satin(centre, widths * k, cream, underlay="none", taper=True, spacing=0.35, name=f"claw {i + 1}")
    d.fill(clean(rock_hi.difference(bear).difference(fish), 1.0), cream, angle=-15, spacing=0.45,
           name="boulder highlights")
    return d
