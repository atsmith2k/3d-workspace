"""Shadow Keep: a dark castle on a jagged crag in front of a huge pale moon under a navy
night sky, with bats, as a round patch.

Spec:
  object:       gothic dark-fantasy castle scene (an original keep, no branding) for tees,
                hoodies, tote bags, jackets and round patches
  overall:      `size` mm across (95 for the 4x4 hoop, 160 for 5x7), round
  fabric:       knits with cut-away; canvas and wovens with tear-away
  threads:      navy (night sky), bone (moon), black (castle, crag, bats), charcoal
                (shaded faces of towers and spires), yellow (lit windows,
                stars), silver (frame ring): 6 colours
  must have:    a 92 mm round patch: the whole inside of the ring filled with navy sky at
                30 deg, a 2.8 mm silver satin ring; a 59 mm plain bone moon behind the castle; a castle silhouette about 56 mm wide in clean
                straight-edged polygons: a tall keep with an 18 mm spire, two towers with
                conical spires, a small spired tower, a square tower and crenellated
                curtain walls (merlons 3 mm, crenels 2.4 mm, no notch under 1.5 mm), spire
                tips cut flat at 1.4 mm, each tower's right face shaded charcoal; seven
                arched yellow windows (vertical satin columns); a jagged crag filling
                the bottom of the frame as one clean black silhouette; three bats with two
                scalloped three-point wings, body and ears, 13-18 mm wingspan; three stars
  density:      every fill knocked out under what sews over it and under the frame
                ring; max 3.5 layers
"""
import numpy as np
from shapely.geometry import Polygon

from cadkit.stitch import *

from _realms import C_, SIZES, fit, hoop_for, product, standard_checks

DESCRIPTION = "Dark castle on a jagged crag before a huge pale moon, with bats, as a round night-sky patch"
HOOP = "4x4"
PARAMS = dict(size=95.0)
PRODUCT = product(
    "Shadow Keep Embroidery Design",
    "A dark gothic castle on a jagged crag in front of a huge pale moon, with bats",
    ["gothic castle", "dark castle", "castle", "dark fantasy", "gothic", "full moon", "bats",
     "haunted castle", "vampire castle", "round patch", "halloween embroidery"],
    "A dark keep of spires, towers and battlements rises from a jagged crag, black against a "
    "huge pale moon and a deep navy night sky. A few windows still glow yellow, bats wheel "
    "overhead, and a silver ring frames the scene as a full round patch.\n\n"
    "Great on hoodies, tees, denim jackets, tote bags and round patches.",
    mockups=("tshirt", "tote"),
)


def checks(p):
    return standard_checks(p, 6, 24000)


R = 46.0            # frame ring radius
RING = 2.8
TIP = 1.4           # spire tips are cut flat this wide


def _crenels(x0, x1, y, h=2.6, merlon=3.0, gap=2.4):
    """Merlons along the top of a wall from x0 to x1 at height y, centred on the wall."""
    n = int((x1 - x0 + gap) // (merlon + gap))
    span = n * merlon + (n - 1) * gap
    x = x0 + (x1 - x0 - span) / 2
    out = []
    for _ in range(n):
        out.append(Polygon([(x, y - 0.5), (x + merlon, y - 0.5), (x + merlon, y + h), (x, y + h)]))
        x += merlon + gap
    return union(*out)


def _spire(x0, x1, y, h, eave=1.4):
    """Conical roof with its tip cut flat TIP mm wide."""
    xm = (x0 + x1) / 2
    a, b = x0 - eave, x1 + eave
    f = 1 - TIP / (b - a)
    return Polygon([(a, y - 0.3), (b, y - 0.3), (xm + TIP / 2, y + h * f), (xm - TIP / 2, y + h * f)])


def tower(x0, x1, y0, y1, spire=None):
    """(body+roof, shaded right face) of a tower; spire height or None for battlements."""
    body = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    w = x1 - x0
    xm = (x0 + x1) / 2
    face = Polygon([(x1 - w * 0.3, y0), (x1, y0), (x1, y1), (x1 - w * 0.3, y1)])
    if spire:
        roof = _spire(x0, x1, y1, spire)
        f = 1 - 3.5 / spire
        shade = union(face, Polygon([(xm + 0.6, y1 + 0.4), (x1 + 0.7, y1 + 0.4),
                                     (xm + 0.6 + (x1 + 0.7 - xm - 0.6) * (1 - f), y1 + spire * f)]))
        return union(body, roof), shade
    return union(body, _crenels(x0, x1, y1)), face


def window(x, y, w=2.6, h=4.6):
    return union(rect(w, h - w / 2, x, y - w / 4), circle(x, y + h / 2 - w / 2, w / 2, 32))


def window_satin(x, y, w=2.6, h=4.6):
    """(path, widths) of an arched window sewn as one vertical satin column: straight
    sides, then the widths follow the round arch (clean edges where a tiny fill frays)."""
    r = w / 2
    yb, yt = y - h / 2 + 0.15, y + h / 2 - 0.35
    yc = y + h / 2 - r
    ys = np.linspace(yb, yt, 16)
    ws = np.where(ys <= yc, w, 2 * np.sqrt(np.clip(r ** 2 - (ys - yc) ** 2, 0, None)))
    return np.c_[np.full_like(ys, x), ys], np.maximum(ws, 0.9)


def bat(x, y, span=16.0, flip=False):
    """A bat facing the viewer: two wings with three scalloped points each, a small body
    and two ears; `span` mm wingspan."""
    wing = [(0.9, 1.5), (3.0, 3.0), (5.2, 3.9), (9.0, 3.2),          # leading edge to the tip
            (7.6, 1.6), (7.0, -0.4),                                  # first scallop, 2nd point
            (5.6, 0.6), (4.4, -1.4),                                  # second scallop, 3rd point
            (3.2, -0.2), (0.9, -1.0)]
    left = [(-px, py) for px, py in reversed(wing)]
    wings = poly(wing) | poly(left)
    body = ellipse(0, -0.2, 1.5, 2.4, 48) | circle(0, 2.3, 1.25, 48)
    ears = Polygon([(-1.25, 2.6), (-0.95, 4.4), (-0.15, 3.2)]) | Polygon([(1.25, 2.6), (0.95, 4.4), (0.15, 3.2)])
    g = union(wings, body, ears).buffer(0.15).buffer(-0.15)
    k = span / 18.0
    g = scale(g, k * (-1 if flip else 1), k, origin=(0, 0))
    return move(g, x, y)


def sparkle(x, y, r):
    return star(4, r, r * 0.28, x, y, rot=90)


def art():
    d = Design()
    inner = circle(0, 0, R - RING / 2 + 0.4, res=240)     # fills stop 0.4 under the ring
    moon = circle(3, 9.5, 29.5, res=220)

    crag = poly([(-50, -28), (-41, -22), (-35, -25), (-29, -16.5), (-20, -18.5), (-9, -15.8),
                 (3, -17.5), (13, -15.8), (23, -18.5), (28.5, -14.5), (34, -22), (41, -19.5),
                 (50, -26), (50, -55), (-50, -55)]) & inner
    parts = [tower(-6, 6, -23, 22, spire=18),
             tower(-21, -12.5, -23, 11, spire=15),
             tower(12, 19.5, -23, 7, spire=13),
             tower(-28.5, -22.5, -24, 1, spire=9),
             tower(19.5, 25.5, -23, -3)]
    walls = union(Polygon([(-22.6, -23), (12.1, -23), (12.1, -1), (-22.6, -1)]),
                  _crenels(-12.5, 12, -1), _crenels(-22.6, -12.5, -1))
    castle = union(walls, *[g for g, _ in parts]).buffer(0)
    shades = [s for _, s in parts]
    win_at = [(-1.2, 12), (-1.2, 3.5), (-17.6, 2), (14.9, -1), (-9, -8), (8, -10), (-26.2, -9)]
    windows = [window(x, y) for x, y in win_at]
    bats = [bat(-25.5, 20, 17.5), bat(-35, 6, 13, flip=True), bat(15, 27, 16)]
    stars = [sparkle(-37, -7, 3.0), sparkle(38, 9, 2.8), sparkle(-24, 33, 2.6)]

    silhouette = union(castle, crag)
    shade_all = union(*shades)
    win_all = union(*windows)

    # navy sky: everything inside the ring not covered by something sewn later
    d.fill(knockout(inner, moon, silhouette, *bats, *stars), C_["navy"], angle=30, name="sky")
    # bone moon
    d.fill(knockout(moon, silhouette, *bats), C_["bone"], angle=-20, spacing=0.45, name="moon")
    # black: crag, castle (vertical rows keep tower edges clean), bats along the wings
    d.fill(knockout(crag, castle), C_["black"], angle=60, name="crag")
    d.fill(knockout(castle, shade_all, win_all), C_["black"], angle=90, name="castle")
    for b in bats:
        d.fill(b, C_["black"], angle=0, name="bat")
    # charcoal: shaded faces
    for s in shades:
        d.fill(knockout(s & castle, win_all), C_["charcoal"], angle=90, name="shade")
    # yellow windows and stars
    for x, y in win_at:
        pth, ws = window_satin(x, y)
        d.satin(pth, ws, C_["yellow"], name="window", taper=True)
    for s in stars:
        d.fill(s, C_["yellow"], angle=45, name="star")
    # silver frame ring
    d.outline(circle(0, 0, R, res=240), C_["silver"], width=RING, name="frame")
    return d


def design(p):
    return fit(art(), p.size, hoop_for(p.size))
