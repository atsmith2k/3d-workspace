"""Ember Dragon: a fierce dragon head in profile breathing a plume of fire.

Spec:
  object:       tattoo-flash style dragon head (original art, no franchise) for tees,
                hoodies, jacket backs, tote bags and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      bone (horns, teeth), red (head, jaw, neck), rust (jaw frill, back spikes,
                neck scales, belly plates), ember (flame edge), flame (flame body),
                yellow (flame core, eye), black (mouth, pupil, nostril, outlines): 7
  must have:    head facing right with an open mouth; two horns swept back as tapered
                fills; a spiky frill behind the jaw and spikes down the back of the neck;
                rust belly plates and scale crescents on the neck; a yellow eye with a
                slit pupil under a heavy brow; fangs top and bottom; a three-tone flame
                plume leaving the mouth and widening forward and up into licking tongues;
                one black satin border 1.6 mm
                round the whole silhouette
  density:      every upper shape knocks out what it covers; max 3.5 layers
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
    return standard_checks(p, 7, 16000)


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
    for y in np.arange(-14, -52, -5.2):
        plates.append(band.intersection(rect(40, 3.8, -14, y - 1.9)))
    plates = [g for g in plates if g.area > 4]
    horns = [tube([(-12, 22), (-24, 31), (-36, 37), (-46, 42)], [4.8, 3.8, 2.3, 0.4]),
             tube([(-20, 16), (-32, 21), (-40, 23), (-48, 29)], [3.8, 3.0, 1.9, 0.4])]
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
    return dict(head=head, jaw=jaw, mouth=mouth, neck=neck, plates=plates, horns=horns,
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
    core = tube([(22, -2.2), (29, 0.2), (36, 5.5), (43, 12)], [1.0, 3.2, 5.0, 0.6]).intersection(shrink(body, 1.4))
    return outer, body, core


BORDER = 1.6       # black satin round the silhouette
LINE = 1.4         # black satin detail lines inside it


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
    lines = inner_lines(face, union(s["neck"], s["frill"])) + inner_lines(s["frill"], s["neck"].difference(face.buffer(0.2)))
    # every fill stops under the satins sewn over it (the border is centred on the edge)
    bands = union(silhouette.boundary.buffer(BORDER / 2),
                  *[LineString(l).buffer(LINE / 2, cap_style="flat") for l in lines])

    def fill(shape, color, **kw):
        g = knockout(shape, bands)
        if not g.is_empty:
            d.fill(g, C_[color], **kw)

    for g in s["horns"]:
        fill(knockout(g, face), "bone", angle=30, name="horn")
    fang_w = [np.linspace(3.0, 0.4, 8)] * 4
    fang_paths = [np.linspace(f[0], f[1], 8) for f in s["fangs"]]
    fangs = [spike(f[0], f[-1], 3.0).buffer(0.4) for f in fang_paths]
    for f, w in zip(fang_paths, fang_w):            # sewn first; the lips knock them out
        d.satin(f, w, C_["bone"], name="fang", underlay="center", taper=True)

    fill(knockout(s["head"], s["eye"], s["brow"], s["nostril"], flame, *fangs), "red", angle=-20, name="head")
    fill(knockout(s["jaw"], flame, *fangs), "red", angle=20, name="jaw")
    fill(knockout(s["neck"], face, s["frill"], plates, *s["scales"]), "red", angle=70, name="neck")

    fill(knockout(s["frill"], face), "rust", angle=-30, name="frill")
    for g in s["back"]:
        fill(knockout(g, s["neck"]), "rust", angle=0, name="spike")
    for g in s["plates"]:
        fill(g, "rust", angle=0, name="belly plate")
    for g in s["scales"]:
        fill(knockout(g, s["frill"], face), "rust", angle=0, underlay=False, name="scale")
    fill(s["brow"], "rust", angle=10, name="brow")

    fill(knockout(outer, mid), "ember", angle=45, name="flame edge")
    fill(knockout(mid, core), "flame", angle=-30, name="flame")
    fill(core, "yellow", angle=30, name="flame core")
    fill(knockout(s["eye"], s["pupil"]), "yellow", angle=0, underlay=False, name="eye")

    fill(knockout(gap, flame, *fangs), "black",
         angle=0, name="mouth")
    fill(s["pupil"], "black", angle=90, underlay=False, name="pupil")
    fill(s["nostril"], "black", angle=0, underlay=False, name="nostril")
    for path in lines:
        d.satin(path, LINE, C_["black"], name="edge line", underlay="center")
    d.outline(silhouette, C_["black"], width=BORDER, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
