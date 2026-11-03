"""Dragon Constellation: a round night-sky patch with a flying dragon drawn as a star chart.

Spec:
  object:       a round night-sky patch with a dragon in flight drawn the way old star
                charts draw their constellations: a faint figure of the dragon (head with
                horn, neck, raised wing with two finger lines, body, two legs, a tail
                curling under) in thin lavender running stitch, gold four-point stars on
                its key joints, brighter silver lines linking the stars, white twinkles
                round it and a gold crescent moon; for patches, jackets, tees, totes and
                kids' room pillows
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       a patch on twill with tear-away (heavy cut-away for knits)
  threads:      navy (sky), lavender (dragon figure), white (twinkles), gold
                (constellation stars, moon), silver (star lines, border): 5 colours
  must have:    a 92 mm circle; navy sky in a tatami fill at a light 0.45 mm spacing
                (contour and circular fills were tried: Ink/Stitch left bare islands
                round the stars or skipped the tie-off); 2.6 mm silver satin border;
                the figure one continuous single run (2 mm stitches) round the whole
                dragon plus two wing-finger runs; 16 gold stars 2.2-3.6 mm on the joints;
                silver bean-stitch lines stopping 1.2 mm short of each star; 16 white
                twinkles 1.4-2.1 mm clear of the figure
  density:      the sky is knocked out under every star and the moon and tucked under
                the border; runs on the sky stay under 2.5 layers; max 3.5
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *

from _arcana import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Round night-sky patch with a flying dragon drawn as a star-chart constellation"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Dragon Constellation Embroidery Design",
    "A round night-sky patch with a flying dragon drawn as an old star-chart constellation",
    ["dragon", "constellation", "star map", "star chart", "night sky", "celestial embroidery",
     "patch", "stars", "moon"],
    "A dragon in flight across a round navy night sky, drawn the way the old star charts "
    "drew their constellations: a faint lavender figure of the dragon, gold four-point "
    "stars on its joints linked by bright silver lines, white twinkles scattered round "
    "and a gold crescent moon, all inside a silver satin border.\n\n"
    "Great on jacket patches, denim, tees, tote bags and pillows for a dragon-mad kid.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 5, 22000)


R = 46.0         # patch radius
BORDER = 2.6
MOON = (27.0, -24.0, 8.0)


# ---------- the dragon figure ----------

def _resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.c_[np.interp(t, s, path[:, 0]), np.interp(t, s, path[:, 1])]


def tube(path, widths):
    path = _resample(np.asarray(path, float), 0.15)
    w = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(widths)), widths)
    return union(*[Point(*q).buffer(r / 2, quad_segs=10) for q, r in zip(path, w)]).simplify(0.08)


SPINE = [(22.0, 16.0), (14.0, 11.0), (3.0, 5.0), (-6.0, 2.0), (-15.0, -2.0), (-24.0, -10.0),
         (-25.0, -22.0), (-15.0, -30.5), (-4.0, -30.0), (2.5, -23.0)]
SPINE_W = [5.5, 6.5, 9.0, 9.5, 8.5, 6.0, 4.5, 3.4, 2.4, 1.2]
HEAD = dict(x=22.0, y=16.0, deg=10.0, k=1.25)
WING_ROOT, ELBOW, WING_END = (5.0, 8.0), (-2.0, 22.0), (-12.0, 2.0)
WING_TIPS = [(-14.0, 38.0), (-26.0, 30.0), (-32.0, 16.0)]
SHIFT = (-3.5, -1.0)       # the whole figure sits a little left so the head clears the border
FINGERS = [((-2.0, 22.0), (-26.0, 30.0)), ((-2.0, 22.0), (-32.0, 16.0))]  # elbow -> tips


def _head_pt(x, y):
    a, k = np.radians(HEAD["deg"]), HEAD["k"]
    x, y = x * k, y * k
    return (HEAD["x"] + x * np.cos(a) - y * np.sin(a), HEAD["y"] + x * np.sin(a) + y * np.cos(a))


HEAD_OUTLINE = [(-3.0, 3.2), (2.0, 5.2), (6.0, 4.4), (10.0, 3.0), (14.0, 2.0), (15.2, 0.6),
                (13.8, -0.6), (9.0, -1.2), (8.0, -1.8), (4.0, -3.8), (-2.0, -3.8)]
MOUTH = [(13.2, -0.2), (10.0, -0.6), (7.6, -0.9)]


def wing_shape():
    """Bat wing: straight arm (root -> elbow -> tip), then scalloped membrane arcs between
    the finger tips back to the body."""
    pts = [np.array(WING_ROOT), np.array(ELBOW)]
    prev = np.array(WING_TIPS[0])
    pts.append(prev)
    for b in WING_TIPS[1:] + [WING_END]:
        b = np.array(b)
        m = (prev + b) / 2 + (np.array(ELBOW) - (prev + b) / 2) * 0.3
        t = np.linspace(0, 1, 10)[1:, None]
        pts += list((1 - t) ** 2 * prev + 2 * (1 - t) * t * m + t ** 2 * b)
        prev = b
    return poly(np.vstack(pts))


def figure():
    """The dragon's silhouette: body tube, head, horn, wing and legs as one shape."""
    body = tube(spline(SPINE, samples=10), SPINE_W)
    head = smooth([_head_pt(x, y) for x, y in HEAD_OUTLINE], samples=6)
    horn = union(tube(np.array([_head_pt(0.5, 3.6), _head_pt(-3.5, 6.6), _head_pt(-7.5, 8.2)]),
                      [2.4, 1.5, 0.9]),
                 tube(np.array([_head_pt(3.5, 4.6), _head_pt(1.5, 7.8), _head_pt(-1.5, 10.0)]),
                      [2.0, 1.3, 0.9]))
    wing = wing_shape()
    fore = tube(spline([(4.0, 1.0), (9.0, -6.0), (15.5, -8.0)], samples=8), [3.6, 2.4, 1.6])
    hind = tube(spline([(-14.0, -5.0), (-9.0, -13.0), (-3.0, -15.5)], samples=8), [4.0, 2.6, 1.6])
    return move(union(body, head, horn, wing, fore, hind), *SHIFT)


# constellation joints on the figure: name -> (x, y, star radius)
STARS = {
    "snout": (*_head_pt(12.8, 0.6), 2.6), "eye": (*_head_pt(4.0, 1.0), 3.2),
    "horn": (*_head_pt(-5.0, 7.2), 2.2), "neck": (14.0, 11.0, 2.8),
    "shoulder": (3.0, 5.0, 3.6), "hip": (-15.0, -2.0, 3.2), "tail1": (-24.0, -10.0, 2.8),
    "tail2": (-25.0, -22.0, 2.6), "tail3": (-15.0, -30.5, 2.4), "tail4": (2.5, -23.0, 2.2),
    "elbow": (-2.0, 22.0, 2.6), "wingtip": (-14.0, 38.0, 3.4), "wing3": (-32.0, 16.0, 2.6),
    "forefoot": (15.5, -8.0, 2.2), "hindfoot": (-3.0, -15.5, 2.2),
}
STARS = {k: (x + SHIFT[0], y + SHIFT[1], r) for k, (x, y, r) in STARS.items()}
LINES = [("snout", "eye"), ("eye", "horn"), ("eye", "neck"), ("neck", "shoulder"),
         ("shoulder", "hip"), ("hip", "tail1"), ("tail1", "tail2"), ("tail2", "tail3"),
         ("tail3", "tail4"), ("shoulder", "elbow"), ("elbow", "wingtip"), ("elbow", "wing3"),
         ("wing3", "hip"), ("shoulder", "forefoot"), ("hip", "hindfoot")]


def sparkle(x, y, r):
    """Four-point star, points up/down/left/right."""
    return star(4, r, r * 0.34, x, y, rot=90)


def moon():
    x, y, r = MOON
    return circle(x, y, r) - circle(x + 0.42 * r, y + 0.30 * r, 0.86 * r)


def _seg(a, b, gap=1.2):
    """The line between two stars, stopping `gap` mm short of each star's points."""
    (xa, ya, ra), (xb, yb, rb) = STARS[a], STARS[b]
    pa, pb = np.array([xa, ya]), np.array([xb, yb])
    u = (pb - pa) / np.linalg.norm(pb - pa)
    return np.array([pa + u * (ra * 0.6 + gap), pb - u * (rb * 0.6 + gap)])


def twinkles(fig):
    """White twinkles scattered over the open sky, clear of the dragon and moon."""
    rng = np.random.default_rng(11)
    keep_out = union(fig.buffer(2.5), *[circle(x, y, r + 3.0) for x, y, r in STARS.values()],
                     moon().buffer(3.5))
    out = []
    for _ in range(6000):
        x, y = rng.uniform(-R, R, 2)
        r = rng.uniform(1.4, 2.1)
        if np.hypot(x, y) > R - BORDER - 4.5:
            continue
        g = sparkle(x, y, r)
        if g.buffer(1.0).intersects(keep_out) or any(g.distance(o) < 6.0 for o in out):
            continue
        out.append(g)
        if len(out) == 16:
            break
    return out


def art():
    d = Design()
    patch = circle(0, 0, R, res=240)
    fig = figure()
    gold = [sparkle(x, y, r) for x, y, r in STARS.values()]
    white = twinkles(fig)
    sky = knockout(tuck(patch, BORDER), *gold, *white, moon()).simplify(0.1)
    d.fill(sky, C_["navy"], spacing=0.45, angle=-20, method="auto_fill", name="night sky")
    # the faint figure: one continuous single run round the dragon, two wing fingers
    for ring_pts in outline_paths(fig):
        d.run(ring_pts, C_["lavender"], length=2.0, name="dragon figure", trim_after=True)
    edge = fig.exterior.buffer(0.9)
    for a, b in FINGERS:
        a, b = np.add(a, SHIFT), np.add(b, SHIFT)
        for seg in [LineString(spline([tuple(a), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 1.5), tuple(b)],
                                      samples=8)).difference(edge)]:
            for piece in getattr(seg, "geoms", [seg]):
                if piece.length > 2.0:
                    d.run(np.asarray(piece.coords), C_["lavender"], length=2.0, name="wing finger",
                          trim_after=True)
    mouth = np.array([_head_pt(x, y) for x, y in MOUTH]) + SHIFT
    d.run(mouth, C_["lavender"], length=1.5, name="mouth", trim_after=True)
    for g in white:
        d.fill(g, C_["white"], angle=45, spacing=0.4, underlay=False, name="twinkle")
    d.fill(moon(), C_["gold"], angle=60, name="moon")
    for g in gold:
        d.fill(g, C_["gold"], angle=45, spacing=0.4, underlay=False, name="star")
    for a, b in LINES:
        d.run(_seg(a, b), C_["silver"], bean=1, length=1.8, name=f"{a}-{b}", trim_after=True)
    d.outline(patch, C_["silver"], width=BORDER, name="border")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
