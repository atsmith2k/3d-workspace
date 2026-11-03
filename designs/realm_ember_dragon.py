"""Ember Dragon: a fierce dragon head in profile breathing a plume of fire.

Spec:
  object:       tattoo-flash style dragon head (original art, no franchise) for tees,
                hoodies, jacket backs, tote bags and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      bone (fangs, horns, frill spines), khaki (horn shading, growth rings),
                red (head, jaw, neck), rust (shadow under the jaw and the brow, brow
                ridge, cheek and snout ridges, shadow band along the frill, neck scale
                crevices, back spikes, belly plates, tongue), ember (flame edge), flame
                (frill, flame body, belly-plate highlights, embers), yellow (inner flame
                tongues and hot core, eye, embers), black (mouth, pupil, nostril, head
                edge lines, border): 8
  must have:    head facing right with an open mouth, a rust tongue and four bone
                fangs (tapered satins); two ridged horns, lit bone over a khaki
                underside with 1.4 mm khaki growth rings; an orange fanned frill with
                bone spines over a rust shadow band on the neck; staggered rows of
                overlapping neck scales (rust crevices on red, 2.9 mm scales at the jaw
                growing to ~6.8 mm at the base) and belly plates with 1.4 mm orange
                highlight satins; a yellow slit-pupil eye under a rust brow ridge;
                a layered flame plume leaving the mouth (vermilion edge, orange layer
                2.4 mm in, yellow inner tongues 6 mm in and a tapered hot core) with
                three teardrop embers; a black satin border 1.6 mm round the silhouette
                and 1.4 mm black lines where the head laps the neck
  detail:       every detail satin and fill is 1.4 mm or more in the 100 mm drawing,
                so 1 mm or more once fitted to the 4x4
  density:      every upper shape knocks out what it covers and every fill stops under
                the satins; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Fierce dragon head in profile breathing a plume of fire"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Ember Dragon Embroidery Design",
    "A fierce red dragon head in profile breathing a plume of orange and yellow fire",
    ["dragon", "fire dragon", "dragon head", "fire breathing dragon", "high fantasy",
     "mythical creature", "tattoo flash", "dragon embroidery"],
    "A fierce red dragon in profile, horns swept back and jaw frill bristling, breathing a "
    "roaring plume of fire in three shades of flame. Rust belly plates, scaled neck and a bold "
    "black outline give it the punch of old-school tattoo flash.\n\n"
    "Great on hoodies, tees, jacket backs, tote bags and patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 8, 16000)


def tube(points, radii, samples=12):
    """A shape swept along a smooth path through `points`, radius interpolated along
    its length from `radii` (one per control point)."""
    path = spline(np.asarray(points, float), samples)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    ctrl = np.asarray(points, float)
    # radius at each control point, placed at the nearest path sample
    idx = [int(np.argmin(np.linalg.norm(path - c, axis=1))) for c in ctrl]
    r = np.interp(seg, seg[idx], radii)
    parts = []
    for i in range(len(path) - 1):
        a, b = circle(*path[i], max(r[i], 0.05), 32), circle(*path[i + 1], max(r[i + 1], 0.05), 32)
        parts.append(union(a, b).convex_hull)
    return union(*parts)


def spike(base, tip, w):
    """A pointed spike: a triangle from a base of width `w` centred on `base` to `tip`."""
    base, tip = np.asarray(base, float), np.asarray(tip, float)
    u = (tip - base) / np.linalg.norm(tip - base)
    n = np.array([-u[1], u[0]])
    return poly([tuple(base + n * w / 2), tuple(tip), tuple(base - n * w / 2)])


def _path_frame(path):
    """(points, unit tangents, unit left normals) along a sampled path."""
    t = np.gradient(path, axis=0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    return path, t, np.c_[-t[:, 1], t[:, 0]]


def inner_lines(shape, inside, keep=1.6):
    """The parts of `shape`'s edge that run inside `inside`, stopped `keep` mm clear of
    its border (so they never pile into the outline): satin detail lines."""
    cut = shape.boundary.intersection(inside.buffer(-keep))
    geoms = getattr(cut, "geoms", [cut])
    return [np.asarray(g.coords) for g in geoms if g.geom_type == "LineString" and g.length > 6]


NECK_FRONT = [(-18, -12), (-16, -22), (-14, -36), (-11, -50)]
NECK_BACK = [(-30, 14), (-40, 2), (-46, -16), (-45, -34), (-40, -50)]


def shapes():
    head = smooth([(-26, 22), (-14, 27), (-4, 23), (4, 18), (16, 13), (24, 10), (26, 6),
                   (22, 2.5), (8, 2), (-6, 3), (-14, 1), (-22, -6), (-30, 2)], 10).buffer(0)
    jaw = smooth([(-14, 1), (-4, -3), (8, -7), (17, -9.5), (18, -12.5), (8, -15.5),
                  (-6, -14), (-18, -11), (-22, -4)], 10).buffer(0)
    mouth = poly([(-17, 1), (-10, 4.5), (8, 5.5), (23, 5.5), (21, -11.5), (6, -9.0), (-10, -3.5)])
    neck = poly(list(spline(np.array(NECK_BACK), 10)) + list(spline(np.array(NECK_FRONT[::-1]), 10))).buffer(0)
    # belly plates: a band along the front of the neck, cut into plates 1.4 mm apart
    band = LineString(spline(np.array(NECK_FRONT), 10)).buffer(6.5).intersection(neck)
    plates = []
    for y in np.arange(-13.4, -52, -5.2):
        plates.append(band.intersection(rect(40, 3.8, -14, y - 1.9)))
    plates = [g for g in plates if g.area > 4]
    horn_axes = [[(-12, 22), (-24, 31), (-36, 37), (-46, 42)], [(-20, 16), (-32, 21), (-40, 23), (-48, 29)]]
    horns = [tube(horn_axes[0], [4.8, 3.8, 2.3, 0.4]), tube(horn_axes[1], [3.8, 3.0, 1.9, 0.4])]
    hub = np.array([-17.0, -3.0])
    fan = []
    for k, a in enumerate(np.linspace(150, 240, 9)):
        rr = 23.0 if k % 2 == 0 else 13.0
        fan.append(hub + rr * np.array([np.cos(np.radians(a)), np.sin(np.radians(a))]))
    frill = poly([tuple(hub + (2, 6))] + [tuple(v) for v in fan] + [tuple(hub + (6, -2))])
    back = []
    path, tan, nrm = _path_frame(spline(np.array(NECK_BACK), 20))
    for i in np.linspace(12, len(path) - 14, 4).astype(int):
        base = path[i] + nrm[i] * 1.5            # left of the downward path = inside
        back.append(spike(base, path[i] - nrm[i] * 7.5 + tan[i] * 3.5, 6))
    eye = rotate(ellipse(-2, 13, 3.6, 2.0), -12, origin=(-2, 13))
    pupil = ellipse(-1.8, 13, 0.7, 1.9)
    brow = smooth([(-9, 15), (-2, 18.5), (6, 16), (1, 15.6), (-4, 16)], 6).buffer(0)
    nostril = rotate(ellipse(20.5, 8, 1.8, 1.0), 20, origin=(20.5, 8))
    # fangs: tapered satins from inside the lip to a point in the open mouth
    fangs = [line((13.6, 4.4), (13.0, -2.6)), line((5.6, 4.4), (5.0, -1.2)),
             line((10.4, -8.6), (11.2, -2.8)), line((2.0, -7.0), (2.7, -2.6))]
    scales = []
    for row, y in enumerate(np.arange(-8, -50, -5.0)):
        for x in np.arange(-44, -14, 5.4) + (2.7 if row % 2 else 0):
            scales.append(circle(x, y, 2.6, 32).difference(circle(x, y + 1.7, 2.6, 32)))
    keep = neck.difference(band.buffer(1.0)).buffer(-2.0)
    scales = [g.intersection(keep) for g in scales]
    scales = [g for g in scales if g.area > 3.5]
    tips = [fan[k] for k in range(0, len(fan), 2)]
    tongue = tube([(-8, 0.2), (-1, -2.0), (6, -3.6), (10, -4.4)], [1.9, 1.9, 1.6, 1.0])
    return dict(head=head, jaw=jaw, mouth=mouth, neck=neck, plates=plates, horns=horns,
                horn_axes=horn_axes, hub=hub, tips=tips, tongue=tongue,
                frill=frill, back=back, eye=eye, pupil=pupil, brow=brow, nostril=nostril,
                fangs=fangs, scales=scales)


def flame_shapes():
    """A breath plume leaving the mouth, widening forward and a little up into licking
    tongues: (outer, body, core) for the ember edge, orange body and yellow core."""
    axis = [(19, -2.5), (28, 0), (37, 6), (44, 13)]
    plume = tube(axis, [3.0, 7.0, 11.0, 12.5])
    end, up = np.array(axis[-1]), np.radians(42)
    tongues = []
    # wavy tongues licking forward off the leading edge, the middle ones longest
    for deg, L, w, flick in [(-62, 10, 8.0, -1), (-30, 14, 9.0, 1), (0, 17, 9.5, -1),
                             (30, 14, 9.0, 1), (62, 10, 8.0, -1)]:
        a = up + np.radians(deg)
        u = np.array([np.cos(a), np.sin(a)])
        n = np.array([-u[1], u[0]]) * flick
        base = end + u * 7.0
        tongues.append(tube([tuple(base), tuple(base + u * L * 0.35 + n * 1.6),
                             tuple(base + u * L * 0.7 - n * 1.0), tuple(base + u * L + n * 1.8)],
                            [w / 2, w / 2.4, w / 4, 0.3]))
    # licks off the top and bottom of the plume, swept forward
    for base, tip, w in [((29, 6), (29, 15), 5.0), ((27, -6), (33, -12), 4.5),
                         ((38, -2), (47, -7), 5.5)]:
        midp = (np.add(base, tip) / 2) + np.array([-1.0, 0.0])
        tongues.append(tube([base, tuple(midp), tip], [w / 2, w / 3.2, 0.3]))
    outer = union(plume, *tongues)
    body = shrink(outer, 2.4)
    # inner tongues echo the outline (orange 2.4 mm in, yellow 5 mm in), plus a tapered
    # yellow hot core running from the mouth along the plume
    core = tube([(21, -2.3), (28, -0.4), (35, 4.2), (42, 10.5)], [0.9, 2.6, 3.4, 0.5])
    core = union(core, shrink(outer, 6.0)).intersection(shrink(body, 1.4))
    return outer, body, core


BORDER = 1.6       # black satin round the silhouette
LINE = 1.4         # black satin detail lines inside it
DETAIL_W = 1.4       # khaki / orange detail satins (>= 1 mm once fitted to the 4x4)


def _along(path, f):
    """(point, unit tangent, unit normal) a fraction `f` along a sampled path."""
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    i = int(np.clip(np.searchsorted(seg, f * seg[-1]), 1, len(path) - 1))
    t = path[i] - path[i - 1]
    t = t / np.linalg.norm(t)
    return path[i], t, np.array([-t[1], t[0]])


def _clip(path, area, min_len=2.5):
    cut = LineString(path).intersection(area)
    return [np.asarray(g.coords) for g in getattr(cut, "geoms", [cut])
            if g.geom_type == "LineString" and g.length > min_len]


def _band(path, w):
    return LineString(path).buffer(w / 2, cap_style="flat")


def _tband(path, widths):
    """The area a tapered satin covers (widths per path point), for knocking fills out."""
    path = np.asarray(path, float)
    w = np.broadcast_to(np.asarray(widths, float), (len(path),))
    return union(*[union(circle(*path[i], w[i] / 2, 24), circle(*path[i + 1], w[i + 1] / 2, 24)).convex_hull
                   for i in range(len(path) - 1)])


def neck_scales(area):
    """Overlapping neck scales: per row, the rust crevice under the scalloped lower edge
    of that row's round scales (the row above laps over the row below), deepest under
    the middle of each scale. Scales are small near the jaw and grow down the neck."""
    bands = []
    y, row = -9.0, 0
    while y > -54:
        r = 2.9 + 0.09 * (-9.0 - y)                  # 2.9 mm at the jaw, ~6.8 at the base
        dx = 1.55 * r
        xs = np.arange(-60, 0, dx) + (dx / 2 if row % 2 else 0)
        x = np.linspace(-56, -4, 600)
        k = np.clip(np.round((x - xs[0]) / dx), 0, len(xs) - 1).astype(int)
        u = np.clip(np.abs(x - xs[k]) / (dx / 2), 0, 1)
        top = y - np.sqrt(np.clip(r * r - (x - xs[k]) ** 2, 0, None))
        w = 1.4 + 0.35 * r * (1 - u ** 2)
        band = poly(list(zip(x, top)) + list(zip(x[::-1], (top - w)[::-1]))).buffer(0)
        g = band.intersection(area).buffer(-0.7).buffer(0.7)
        bands += [q for q in polygons_of(g) if q.area > 2.5]
        y -= 0.95 * r
        row += 1
    return bands


def art():
    d = Design()
    s = shapes()
    outer, mid, core = flame_shapes()
    flame = outer
    face = union(s["head"], s["jaw"])
    horns = union(*s["horns"])
    plates = union(*s["plates"])
    dragon = union(face, s["neck"], horns, s["frill"], *s["back"])
    gap = s["mouth"].difference(face.buffer(-0.01))
    silhouette = union(dragon, flame, gap)       # the open mouth is black fill, not border
    # black lines where the head laps over the neck and frill (the frill reads against the
    # neck by colour and a rust shadow band along its edge)
    lines = inner_lines(face, union(s["neck"], s["frill"]))
    inside = silhouette.buffer(-(BORDER / 2 + 0.2))       # detail satins end just under the border
    clear_lines = union(*[_band(l, LINE + 3.2) for l in lines])

    # horn growth rings (khaki) across each horn, clear of the head
    rings = []
    for axis, fs in zip(s["horn_axes"], [(0.34, 0.52, 0.7), (0.4, 0.62)]):
        path = spline(np.array(axis), 12)
        for f in fs:
            c, t, n = _along(path, f)
            rings += _clip(np.array([c - n * 6, c + n * 6]),
                           inside.intersection(horns).difference(face.buffer(1.6)))
    # frill spines (bone) from where they leave the head to just short of each tip
    spines = []
    for tip in s["tips"]:
        u = (tip - s["hub"]) / np.linalg.norm(tip - s["hub"])
        seg = np.array([s["hub"], tip - u * 7.0])   # stop where the point is still wide
        area = s["frill"].buffer(-0.6).difference(face.buffer(3.0)).difference(clear_lines)
        spines += _clip(seg, area, 4.0)
    # belly plate highlights (orange) under each plate's top edge
    highs = []
    for g in s["plates"]:
        x0, y0, x1, y1 = g.bounds
        highs += _clip(np.array([(x0, y1 - 1.0), (x1, y1 - 1.0)]), g.buffer(-0.9).intersection(inside), 2.5)
    # brow ridge and short tapered scale ridges on the cheek, jaw and snout (rust)
    brow = spline(np.array([(-10, 15.0), (-4, 18.2), (3, 17.6), (8, 15.4)]), 8)
    ridges = [spline(np.array(p_), 6) for p_ in (
        [(-11, 9.5), (-15, 11.5), (-19, 14.5)], [(-9, 4.8), (-14, 6.2), (-18.5, 8.6)],
        [(9, 11.8), (13, 10.6), (16.5, 9.4)])]

    spine_w = [np.linspace(2.4, 1.4, len(q)) for q in spines]
    brow_w = np.linspace(1.6, 2.6, len(brow)) * np.r_[np.ones(len(brow) - 6), np.linspace(1, 0.6, 6)]
    ridge_w = [np.linspace(2.4, 0.6, len(r)) for r in ridges]
    satin_bands = ([_band(r, DETAIL_W) for r in rings] + [_tband(q, w) for q, w in zip(spines, spine_w)] +
                   [_band(h, DETAIL_W) for h in highs] + [_tband(brow, brow_w)] +
                   [_tband(r, w) for r, w in zip(ridges, ridge_w)] + [_band(l, LINE) for l in lines])
    # every fill stops under the satins sewn over it (the border is centred on the edge)
    bands = union(silhouette.boundary.buffer(BORDER / 2), *satin_bands)

    def fill(shape, color, **kw):
        g = knockout(shape, bands)
        if not g.is_empty:
            d.fill(g, C_[color], **kw)

    # shading (rust): the horns' undersides are khaki; the jaw's underside, a cheek
    # shadow behind the mouth, a shadow under the brow, and a band along the frill edge
    horn_shade = [g.difference(move(g, 0, 2.4)) for g in s["horns"]]
    jaw_shadow = s["jaw"].difference(move(s["jaw"], 0, 3.2))
    brow_shadow = s["head"].intersection(ellipse(-1.5, 15.6, 6.5, 2.3)).difference(s["eye"].buffer(0.6))
    frill_shadow = s["neck"].intersection(s["frill"].buffer(2.8)).difference(union(face, s["frill"]))
    belly = union(*s["plates"]).buffer(2.0)
    scale_area = s["neck"].difference(union(face, s["frill"].buffer(2.0), belly)).intersection(inside.buffer(-1.2))
    scales = neck_scales(scale_area)
    shade = union(jaw_shadow, brow_shadow)
    fang_paths = [np.linspace(f[0], f[1], 8) for f in s["fangs"]]
    fangs = [spike(f[0], f[-1], 3.0).buffer(0.4) for f in fang_paths]
    # embers drifting off the plume: teardrops, round end first, tail trailing back
    sparks = []
    for x, y, deg, L, c in [(60, 36, 250, 5.5, "yellow"), (52, 42, 200, 5.0, "flame"),
                            (60, -14, 150, 6.0, "yellow"), (50, -22, 130, 5.0, "flame")]:
        a = np.radians(deg)
        g = tube([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], [1.9, 0.4])
        if g.distance(silhouette) > 2.0:
            sparks.append((g, c))

    # 1 bone: fangs, horns' lit side, frill spines
    for f in fang_paths:            # sewn first; the lips knock them out
        d.satin(f, np.linspace(3.0, 0.4, 8), C_["bone"], name="fang", underlay="center", taper=True)
    for g, sh in zip(s["horns"], horn_shade):
        fill(knockout(g, face, sh), "bone", angle=30, name="horn")
    for q, w in zip(spines, spine_w):
        d.satin(q, w, C_["bone"], name="frill spine", underlay="center")
    # 2 khaki: horns' shaded underside and growth rings
    for sh in horn_shade:
        fill(knockout(sh, face), "khaki", angle=-20, name="horn shade")
    for r in rings:
        d.satin(r, DETAIL_W, C_["khaki"], name="horn ring", underlay="center")
    # 3 red: head, jaw, neck
    fill(knockout(s["head"], s["eye"], s["nostril"], shade, flame, *fangs), "red", angle=-20, name="head")
    fill(knockout(s["jaw"], flame, shade, *fangs), "red", angle=20, name="jaw")
    fill(knockout(s["neck"], face, s["frill"], plates, frill_shadow, *scales), "red", angle=70, name="neck")
    # 4 rust: shading, frill, back spikes, belly plates, neck scale crevices, ridges, tongue
    fill(knockout(shade, s["eye"], flame, *fangs), "rust", angle=-40, name="face shadow")
    fill(knockout(frill_shadow, plates, *scales), "rust", angle=40, name="frill shadow")
    for g in s["back"]:
        fill(knockout(g, s["neck"]), "rust", angle=0, name="spike")
    for g in s["plates"]:
        fill(g, "rust", angle=0, name="belly plate")
    for g in scales:
        fill(g, "rust", angle=0, underlay=False, name="scale")
    d.satin(brow, brow_w, C_["rust"], name="brow ridge", underlay="center")
    for r, w in zip(ridges, ridge_w):
        d.satin(r, w, C_["rust"], name="scale ridge", underlay="center", taper=True)
    fill(knockout(s["tongue"], *fangs), "rust", angle=10, name="tongue")
    # 5 ember: flame edge
    fill(knockout(outer, mid), "ember", angle=45, name="flame edge")
    # 6 flame: the frill (bright against the rust shadow on the neck), flame body,
    # plate highlights, sparks
    fill(knockout(s["frill"], face), "flame", angle=-30, name="frill")
    fill(knockout(mid, core), "flame", angle=-30, name="flame")
    for h in highs:
        d.satin(h, DETAIL_W, C_["flame"], name="plate highlight", underlay="center")
    for g, c in sparks:
        if c == "flame":
            fill(g, "flame", angle=0, underlay=False, name="spark")
    # 7 yellow: inner flame tongues and the hot core, eye, sparks
    fill(core, "yellow", angle=30, name="flame core")
    fill(knockout(s["eye"], s["pupil"]), "yellow", angle=0, underlay=False, name="eye")
    for g, c in sparks:
        if c == "yellow":
            fill(g, "yellow", angle=0, underlay=False, name="spark")
    # 8 black: mouth, pupil, nostril, edge lines, border
    fill(knockout(gap, flame, s["tongue"], *fangs), "black", angle=0, name="mouth")
    fill(s["pupil"], "black", angle=90, underlay=False, name="pupil")
    fill(s["nostril"], "black", angle=0, underlay=False, name="nostril")
    for path in lines:
        d.satin(path, LINE, C_["black"], name="edge line", underlay="center")
    d.outline(silhouette, C_["black"], width=BORDER, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
