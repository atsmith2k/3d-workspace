"""5 in square cement paver mold with a raised D20 (icosahedron) dice relief.

Spec:
  object:       open-top mold for a square cement paver whose face shows a D20 die:
                the die's silhouette (a hexagon) stands proud of the paver face, the
                edges between its ten visible faces and the face numbers are grooved
                into it, like the classic D20 icon (black faces, white lines/numbers).
  overall:      size + 2*(wall + draft) square, floor + thickness tall; prints opening-up
  casting:      127 x 127 mm paver, `thickness` (19 mm, 3/4 in, shallower than the
                butterfly's 25.4) thick; die raised `detail_depth` (2 mm) above the face,
                edge grooves `line_width` (1.9 mm) wide and 1.4 mm deep, numbers grooved
                the same depth, mirrored on the mold floor so they read right on the paver
  orientation:  flat base on the bed, cavity opening up; supports expected: none
  must have:    5 mm floor, 4 mm walls with 2 deg draft, ribs with 10 deg draft so the
                cured paver releases; d20 layout derived from a true icosahedron viewed
                along a face normal (10 visible faces: centre 20, corners 6/10/15, pairs
                2/3, 16/11, 19/14 at the other three corners)
  tolerances:   none (no mating parts)

Units: mm. Z is up and the part sits on Z=0 in the orientation it should print.
"""
import math

import numpy as np

from cadkit.checks import *
from cadkit.relief import *

DESCRIPTION = "5 in square cement paver mold with a raised D20 dice relief"

PARAMS = dict(
    size=127.0,           # paver width (mm)
    thickness=19.0,       # paver thickness = cavity depth (3/4 in; butterfly was 25.4)
    floor=5.0,            # mold floor under the cavity
    wall=4.0,             # mold wall thickness
    wall_draft=2.0,       # degrees; cavity widens toward the opening
    detail_depth=2.0,     # die raised height on the paver face
    groove_depth=1.4,     # edge-line and number groove depth into the raised die
    line_width=1.9,       # edge groove width at the paver surface
    rib_draft=10.0,       # degrees on the ribs that form grooves
    die_radius=50.0,      # hexagon vertex radius of the die silhouette
    number_size=10.0,     # cap height of the face numbers (mm)
    center_number_size=15.0,
    number_bold=0.4,      # extra stroke width on the digits so the groove ribs stay > 1.2 mm
)

EMBED = 0.1
# how each number tilts to sit along its face, as on the reference icon (degrees CCW)
TILT = {"20": 0, "15": 0, "6": 30, "10": -30, "2": 45, "3": -45,
        "16": 90, "11": 60, "19": -90, "14": -60}
PHI = (1 + math.sqrt(5)) / 2


def checks(p):
    hexv = (0, p.die_radius)
    return [
        dims(x=p.size + 2 * (p.wall + draft_offset(p.thickness, p.wall_draft)),
             z=p.floor + p.thickness),
        thickness_at((0, 0, 0.5), p.floor - p.detail_depth - 0.2),   # floor under the die pocket
        empty((0, 0, p.floor - p.detail_depth + p.groove_depth + 0.5)),  # pocket open above the ribs
        solid((0, 0, p.floor - p.detail_depth - 0.5)),                # ...but floored
        solid((p.size / 2 - 3, p.size / 2 - 3, p.floor - 0.5)),       # plain floor outside the die
        empty((*hexv, p.floor + 5)),                                  # cavity above the art
        empty((0, 0, p.floor + p.thickness - 1)),                     # open at the top
        flat_base(p.size ** 2 * 0.9),
        no_overhang(),
        single_body(),
    ]


def d20_layout(radius):
    """Visible faces of an icosahedron viewed along a face normal, projected to 2D and
    scaled so the hexagonal outline has vertex radius `radius`.
    Returns (edges, faces): edges as ((x, y), (x, y)) pairs, faces as 3-point lists."""
    v = []
    for a in (-1, 1):
        for b in (-PHI, PHI):
            v += [(0, a, b), (a, b, 0), (b, 0, a)]
    v = np.array(v, float)
    v /= np.linalg.norm(v[0])
    dist = lambda i, j: np.linalg.norm(v[i] - v[j])
    edge = min(dist(i, j) for i in range(12) for j in range(i + 1, 12))
    near = lambda i, j: abs(dist(i, j) - edge) < 1e-6
    faces = [(i, j, k) for i in range(12) for j in range(i + 1, 12) for k in range(j + 1, 12)
             if near(i, j) and near(j, k) and near(i, k)]
    # rotate so the normal of face 0 points +Z
    n = v[list(faces[0])].mean(axis=0)
    n /= np.linalg.norm(n)
    axis = np.cross(n, [0, 0, 1.0])
    s, c = np.linalg.norm(axis), float(n[2])
    if s > 1e-9:
        axis /= s
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        v = v @ (np.eye(3) + s * K + (1 - c) * K @ K).T
    # spin about Z so the top face has a vertex pointing +Y
    top = v[list(faces[0])]
    ang = math.atan2(top[0, 1], top[0, 0])
    t = math.pi / 2 - ang
    v = v @ np.array([[math.cos(t), -math.sin(t), 0], [math.sin(t), math.cos(t), 0], [0, 0, 1]]).T
    xy = v[:, :2] * (radius / np.max(np.linalg.norm(v[:, :2], axis=1)))
    vis = []
    for f in faces:
        a, b, c3 = v[list(f)]
        nrm = np.cross(b - a, c3 - a)
        if nrm @ (a + b + c3) < 0:
            nrm = -nrm            # outward
        if nrm[2] > 1e-6:
            vis.append(f)
    edges = {tuple(sorted(e)) for f in vis for e in ((f[0], f[1]), (f[1], f[2]), (f[0], f[2]))}
    seg = [(tuple(xy[i]), tuple(xy[j])) for i, j in edges]
    tri = [[tuple(xy[i]) for i in f] for f in vis]
    return seg, tri


def outline(radius):
    return poly([(radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)))
                 for a in range(30, 390, 60)])


def labels(tris, radius):
    """Number every visible face by where its centroid sits (icon-style layout)."""
    def nearest(ang, cands):
        return min(cands, key=lambda a: abs((ang - a + 180) % 360 - 180))
    out = []
    for t in tris:
        cx, cy = sum(x for x, _ in t) / 3, sum(y for _, y in t) / 3
        r = math.hypot(cx, cy) / radius
        ang = (math.degrees(math.atan2(cy, cx)) + 360) % 360
        if r < 0.05:
            n = "20"
        elif r < 0.65:  # the three corner faces of the big inverted triangle (r ~ 0.54; pairs ~ 0.76)
            n = {150: "6", 30: "10", 270: "15"}[nearest(ang, (150, 30, 270))]
        else:           # the paired faces at the other three hexagon corners
            corner = nearest(ang, (90, 210, 330))
            ccw = ((ang - corner + 180) % 360 - 180) > 0
            n = {90: ("2", "3"), 210: ("11", "16"), 330: ("14", "19")}[corner][0 if ccw else 1]
        out.append((n, (cx, cy)))
    return out


def build(p):
    d = p.detail_depth
    g = p.groove_depth
    lean = draft_offset(p.thickness, p.wall_draft)
    rib_lean = draft_offset(g, p.rib_draft)

    cavity = grow(CrossSection.square((p.size - 6, p.size - 6), center=True), 3.0)
    shell = extrude(grow(cavity, lean + p.wall), p.floor + p.thickness)
    mold = shell - drafted(lambda f: grow(cavity, f * lean), p.floor, p.thickness + 1, steps=18)

    # the die silhouette stands proud of the paver: a drafted pocket in the mold floor
    die = outline(p.die_radius)
    mold -= drafted(lambda f: grow(die, -0.4 + f * 0.4), p.floor - d, d + 0.01, steps=4)

    segs, tris = d20_layout(p.die_radius)
    numbers = labels(tris, p.die_radius)
    inner = grow(die, -p.line_width)   # keep rib ends off the pocket wall

    glyphs = {n: text(n, p.center_number_size if n == "20" else p.number_size, bold=True)
              for n, _ in numbers}

    def ribs(widen):
        art = CrossSection()
        for a, b in segs:
            art += stroke([a, b], p.line_width + 2 * widen)
        for n, (cx, cy) in numbers:
            art += grow(glyphs[n], p.number_bold + widen).rotate(TILT[n]).translate((cx, cy))
        # the design is drawn as it should read on the paver; the mold floor is its mirror
        return art.mirror((1, 0)) ^ inner

    # ribs start EMBED below the pocket floor so the union has no coplanar faces
    mold += drafted(lambda f: ribs(-f * rib_lean), p.floor - d - EMBED, g + EMBED, steps=4)
    return mold
