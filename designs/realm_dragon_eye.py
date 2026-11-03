"""Dragon's Eye: a close-up reptilian eye with a slit pupil, framed in overlapping scales.

Spec:
  object:       dark-fantasy dragon eye (original art, no franchise) for hoodies, jacket
                backs, tote bags, book bags and patches
  overall:      `size` mm on the long side (95 for the 4x4 hoop, 160 for 5x7)
  fabric:       knits with cut-away; wovens and canvas with tear-away
  threads:      teal (scales and lids), pine (scale shadows, bean-stitch lid seams), yellow
                (inner iris), gold (middle iris), flame (outer iris), black (pupil, eye
                rim, lid line, border), white (glint): 7
  must have:    a 72 x 34 mm almond eye; a vertical slit pupil 7 x 30 mm; a three-tone
                iris (yellow starburst round the pupil, gold, orange at the rim), every
                patch filled at the angle radiating from the pupil; a white glint on the
                pupil's upper left; a heavy upper lid and a lighter lower lid of teal plates;
                rows of overlapping fish scales, each shadowed by a pine crescent 1.3-2.4 mm deep; a
                rough scalloped oval frame about 98 x 74 mm with a black satin border
  density:      every upper shape knocks out what it covers and every fill stops under
                the satins; max 3.5 layers
"""
import numpy as np
from shapely.geometry import LineString, Point

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Reptilian dragon eye with a slit pupil and a fiery iris, framed in scales"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Dragon's Eye Embroidery Design",
    "A close-up reptilian dragon eye with a slit pupil and a fiery gold iris, framed in teal scales",
    ["dragon eye", "dragon", "reptile eye", "dark fantasy", "high fantasy", "mythical creature",
     "dragon scales", "dragon embroidery"],
    "Something ancient is watching: a dragon's eye in close-up, its black slit pupil set in a "
    "fiery iris that burns from yellow to gold to orange, under heavy scaled lids and rows of "
    "overlapping teal scales.\n\n"
    "Great on hoodies, jacket backs, tote bags, book bags and patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 7, 18000)


RIM = 2.0          # black satin round the eye
LID_LINE = 1.6     # black satin round the lids
BORDER = 1.8       # black satin round the frame


def lens(a, b, x=0.0, y=0.0, vertical=False):
    """Pointed almond, half-width `a`, half-height `b` (the intersection of two circles)."""
    if vertical:
        a, b = b, a
    R = (a * a + b * b) / (2 * b)
    if vertical:
        return circle(x - (R - b), y, R, 256).intersection(circle(x + (R - b), y, R, 256))
    return circle(x, y - (R - b), R, 256).intersection(circle(x, y + (R - b), R, 256))


def frame_shape():
    """A rough oval with a scalloped edge, like scale tips round the rim."""
    t = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    r = 1.0 + 0.035 * np.abs(np.sin(11 * t))
    return poly(list(zip(49 * r * np.cos(t), 37 * r * np.sin(t))))


def sector(cx, cy, r, a0, a1):
    pts = [(cx, cy)] + [(cx + r * np.cos(np.radians(a)), cy + r * np.sin(np.radians(a)))
                        for a in np.linspace(a0, a1, 12)]
    return poly(pts)


def iris_parts(eye, pupil):
    """[(shape, tone, angle)]: the iris in wedges round the pupil, each filled along its
    own radius; yellow starburst inside, gold, orange at the rim."""
    n = 24
    parts = []
    for i in range(n):
        a0, a1 = i * 360 / n, (i + 1) * 360 / n
        mid = (a0 + a1) / 2
        wedge = sector(0, 0, 60, a0, a1).buffer(0.3).intersection(eye)   # neighbours overlap
        r_in = 11.0 if i % 2 == 0 else 8.0          # starburst edges
        r_mid = 18.0 if i % 2 == 0 else 15.5
        bands = [("yellow", circle(0, 0, r_in, 128)),
                 ("gold", circle(0, 0, r_mid, 128).difference(circle(0, 0, r_in, 128))),
                 ("flame", eye.difference(circle(0, 0, r_mid, 128)))]
        for tone, band in bands:
            g = wedge.intersection(band.buffer(0.2)).difference(pupil.buffer(-0.4))
            if g.area > 1:
                parts.append((g, tone, mid))
    return parts


def lid_seams(lid, n, cy):
    """Seams between the lid plates: lines radiating from (0, cy) across the lid band,
    stopped 1.4 mm short of its edges (the black lines there)."""
    x0, y0, x1, y1 = lid.bounds
    inner = lid.buffer(-1.4)
    out = []
    for x in np.linspace(x0 + 7, x1 - 7, n - 1):
        u = np.array([x, (y1 if cy < 0 else y0)]) - (0, cy)
        u = u / np.linalg.norm(u)
        seg = LineString([(0, cy), tuple(np.array((0, cy)) + u * 120)]).intersection(inner)
        for g in getattr(seg, "geoms", [seg]):
            if g.geom_type == "LineString" and g.length > 2:
                out.append(np.asarray(g.coords))
    return out


def scale_shadows(area):
    """Fish scales: per row, the dark crevice under the scalloped lower edge of that
    row's round scales (the row above laps over the row below), deepest under the
    middle of each scale, 1.3 mm at the cusps. One continuous band per row."""
    r, dx, dy = 7.0, 10.6, 6.6
    bands = []
    for row, y in enumerate(np.arange(-42, 46, dy)):
        xs = np.arange(-64, 66, dx) + (dx / 2 if row % 2 else 0)
        x = np.linspace(-60, 60, 900)
        k = np.clip(np.round((x - xs[0]) / dx), 0, len(xs) - 1).astype(int)
        u = np.clip(np.abs(x - xs[k]) / (dx / 2), 0, 1)          # 0 mid scale, 1 at a cusp
        top = y - np.sqrt(np.clip(r * r - (x - xs[k]) ** 2, 0, None))
        w = 1.3 + 1.1 * (1 - u ** 2)
        band = poly(list(zip(x, top)) + list(zip(x[::-1], (top - w)[::-1]))).buffer(0)
        g = band.intersection(area)
        if not g.is_empty:
            bands.append(g)
    return bands


def art():
    d = Design()
    eye = lens(36, 17)
    pupil = lens(3.6, 15, vertical=True)
    glint = union(ellipse(-6.2, 6.5, 2.6, 2.0), circle(-3.4, 10.2, 1.1, 32))
    upper = eye.buffer(9.5).intersection(rect(140, 60, 0, 30))
    lower = eye.buffer(4.5).intersection(rect(140, 60, 0, -30))
    lids = union(upper, lower).buffer(1.5).buffer(-1.5).difference(eye)
    frame = frame_shape()
    lid_ring = union(eye, lids)

    # every fill stops under the black satins sewn over it
    bands = union(frame.exterior.buffer(BORDER / 2), eye.exterior.buffer(RIM / 2),
                  lid_ring.exterior.buffer(LID_LINE / 2))

    def fill(shape, color, **kw):
        g = knockout(shape, bands)
        if not g.is_empty:
            d.fill(g, C_[color], **kw)

    field = frame.difference(lid_ring)
    shadows = scale_shadows(field)
    fill(knockout(field, *shadows), "teal", angle=35, spacing=0.45, name="scales")
    fill(lids, "teal", angle=-35, spacing=0.45, name="lids")
    for g in shadows:
        fill(g, "pine", angle=0, underlay=False, name="scale shadow")
    for path in (lid_seams(lids.intersection(rect(140, 60, 0, 30)), 9, -22) +
                 lid_seams(lids.intersection(rect(140, 60, 0, -30)), 7, 30)):
        d.run(path, C_["pine"], bean=1, name="lid seam")

    parts = iris_parts(eye, pupil)
    for tone in ("yellow", "gold", "flame"):
        for g, t, a in parts:
            if t == tone:
                fill(knockout(g, glint), tone, angle=a, name=f"iris {tone}")
    fill(knockout(pupil, glint), "black", angle=90, name="pupil")
    d.outline(eye, C_["black"], width=RIM, name="eye rim")
    d.outline(lid_ring, C_["black"], width=LID_LINE, name="lid line")
    d.outline(frame, C_["black"], width=BORDER, name="border")
    fill(glint, "white", angle=45, underlay=False, name="glint")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
