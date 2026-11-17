"""Mallard duck head bookend, after the classic mid-century cast-brass "Sarreid style"
duck head bookends (reference photos 1 and 4): a domed breast on a flat base, a slim
upright neck rising from a collar band, a rounded head with a recessed almond eye (a
round eyeball in a sunken socket, lids outlined by an engraved line; nothing proud), a raised round cheek patch, and a long flat bill with a ">"
notch at its base, a mouth line and a nostril slit. Every line is traced from a 1 mm
grid laid over a close-up of photo 4.
The back is flat so the books lean on it.

The side profile is not hand-drawn: FRONT/BACK (per mm of height) and BILL_TOP/BILL_BOT
(per mm of length) were measured from the silhouette of reference photo 4 (the
side-on shot), scaled so the casting is 165 mm (6.5 in) tall. The `profile` checks
re-measure the built mesh against those tables. Widths come from the listed 3 in
width and the front three-quarter photo 1.

Two styles:
  full  solid duck plus a thin plate ("tab") behind it that the books stand on, so
        their weight holds the bookend in place (like the steel tab on the originals).
  cast  a 2.5 mm shell, open at the bottom, that you fill with concrete for weight.
        A 3 mm inward lip round the bottom rim locks the concrete slug in.
        No tab by default (`--set cast_tab=true` adds one).
  `--set tab=false` gives the full style without its tab: a solid freestanding duck
  (output/duck_head_bookend_notab with --name).

The duck is mirror-symmetric left to right, so the same STL is both bookends of a
pair: stand the second one turned 180 deg (the `left/right symmetric` check proves it).

Spec:
  object:       duck head bookend (print two for a pair; identical by symmetry)
  overall:      165 mm tall, 100.4 mm back-to-bill-tip, 76 mm wide at the base; the full
                style adds a 68 x 37.5 x 2.4 mm tab behind the back under the -y half (total
                depth 168.4 mm); a pair's tabs interleave with 1 mm between
  reference:    vintage brass mallard duck head bookends: 6.5 in H x 3 in D x 3 in W each
                (chairish.com 19806281, "Sarreid style 1950s"); 6.5 in H x 4 in L
                (chairish.com bookends listing "Brass Duck Head Bookends, pair",
                3.5 x 4 x 6.5 in); photo 4 scaled to 6.5 in measures 100.7 mm (3.96 in) long
                and 72.6 mm (2.86 in) deep at the base, agreeing with both listings
  mates with:   books on the tab (full) / concrete fill (cast): ~140 cm3, ~0.3 kg
  orientation:  upright on its flat base; tree supports from the plate hold up the bill only
                (none on the breast); seam on the flat back, scarf seam (SLICE). Upright keeps
                the layers along the bill (lying on the back saves ~7% but the bill would
                snap across its layers, and the tab and cast styles cannot lie down)
  must have:    flat back 0 <= x (full width on the breast, a ~12 mm contact strip up the
                round neck, the head rounding off above it); collar band z 45.5-52 (breast shoulder below it, round-bottomed
                grooves 1.6 mm wide x 0.5 mm deep at z 47.6 and 50.6); almond eye x 30.8-51.6, z 145.6-155.6: recessed,
                nothing above the head surface: socket 1.8 mm deep (walls drafted 0.6:1), flush lid band ~1.5 mm
                wide outlined by a groove 2.2 mm outside the almond, corner grooves running on
                3 mm from its points, 9 x 7.2 mm eyeball at (40.6, 150.6) rising 1.5 mm off
                the socket floor (top 0.3 mm below the surface); raised cheek patch 23 x 21 mm
                (1.9 mm proud) at (40.3, 129.6); bill-base ">" notch (vertex 55, 138), mouth
                groove z 129.6 -> 125.9, nostril slit x 61.5-71.5; grooves 1.4 mm wide x
                0.6 mm deep, both sides
  cast style:   wall 2.5 mm; cavity under a 45 deg cone roof (apex z 64, in the neck) so
                it prints without support inside; 3 mm x 1.6 mm retention lip on the rim
  tolerances:   profile within 1.5 mm (mean) of the photo-4 tables

Units: mm. X runs from the flat back (x = 0) toward the bill tip, Y across, Z up.
"""
import numpy as np
from manifold3d import CrossSection, JoinType, Manifold, OpType

from cadkit.checks import *
from cadkit.sdf import build_sdf

DESCRIPTION = "Mallard duck head bookend: solid with book tab, or a concrete-fill shell"

PRODUCT = dict(
    title="Mallard Duck Head Bookend ({style})",
    category="parts",
    tags=["bookend", "duck", "mallard", "mid-century", "decor", "library"],
    printers=["a1", "a1mini"],
    cast_material=None,
    post_processing=None,
    # likeness of a commercial vintage design; keep off the shop until that is cleared
    sellable=False,
)

LICENSE_NOTES = ("Shape and proportions are measured from photos of vintage mid-century "
                 "brass 'Sarreid style' mallard duck head bookends (6.5 in H x 4 in L x "
                 "3 in W per chairish.com listings 19806281 and the bookends category "
                 "listing). Personal use only until the design's rights have been checked.")

# Production print settings, applied by every `cad slice` / `--slice` / `cad publish`:
# tree supports only from the plate (none land on the breast; they hold up the bill), the
# flat back turned to the plate's back so `seam_position: back` hides the seam on the face
# the books cover, and a scarf seam so the start of each loop doesn't leave a bump.
SLICE = dict(supports=True, rotate=-90,
             process=dict(seam_position="back", seam_slope_type="external",
                          support_on_build_plate_only=1))

PARAMS = dict(
    style="full",          # "full" (solid + tab) or "cast" (shell for concrete)
    tab=True,              # full style: book tab
    cast_tab=False,        # cast style: book tab as well
    tab_length=68.0,       # behind the back face
    tab_width=76.0,        # full width of the base
    tab_split=True,        # tab under one half only (-y), so a pair's tabs slide past
                           # each other under narrow book runs instead of colliding
    tab_thickness=2.4,
    wall=2.5,              # cast style shell wall
    lip=3.0,               # cast style retention lip, inward
    lip_height=1.6,
    cone_apex=64.0,        # cast style cavity roof apex height
    groove=0.7,            # engraved line radius (width 2x, depth ~0.6)
    edge=0.6,              # SDF grid spacing (vertices are snapped onto the exact surface)
)

H = 165.0                  # overall height (6.5 in)
L = 100.4                  # back to bill tip

# ---------------------------------------------------------------- measured profile
# photo 4 silhouette, x (mm from the flat back) at z = 0, 1, 2 ... 165. Rows 126-144
# are the face line behind the bill (the bill is BILL_TOP/BILL_BOT).
FRONT = [70.9, 71.2, 71.6, 71.9, 71.8, 71.2, 70.6, 70.7, 71.3, 71.9, 72.3, 72.5, 72.6, 72.5,
         72.5, 72.4, 72.3, 71.9, 71.4, 70.9, 70.5, 70.2, 69.9, 69.5, 69.0, 68.4, 68.1, 67.7,
         67.1, 66.5, 66.0, 65.6, 65.1, 64.5, 63.9, 63.1, 62.4, 61.6, 60.8, 60.0, 59.2, 58.4,
         57.5, 56.7, 55.9, 55.4, 50.3, 50.3, 50.3, 50.3, 50.3, 50.3, 48.4, 47.2, 46.2, 45.5,
         45.0, 44.6, 44.1, 43.5, 43.0, 42.5, 42.1, 41.7, 41.3, 41.0, 40.6, 40.3, 39.9, 39.6,
         39.3, 39.0, 38.6, 38.3, 38.0, 37.7, 37.3, 37.0, 36.7, 36.5, 36.3, 36.1, 35.9, 35.6,
         35.5, 35.3, 35.1, 35.0, 34.9, 34.7, 34.6, 34.4, 34.3, 34.2, 34.2, 34.1, 34.1, 34.0,
         34.0, 34.0, 34.0, 34.1, 34.1, 34.2, 34.3, 34.4, 34.5, 34.6, 34.7, 34.9, 35.1, 35.3,
         35.5, 35.8, 36.3, 36.9, 37.9, 39.3, 41.0, 42.9, 44.8, 46.6, 48.3, 50.2, 52.3, 53.5,
         53.5, 53.2, 53.3, 53.8, 54.3, 54.8, 55.4, 55.9, 56.4, 56.9, 57.3, 57.7, 58.0, 58.4,
         58.7, 59.1, 59.4, 59.7, 60.0, 60.1, 60.2, 60.3, 60.2, 59.9, 59.5, 59.1, 58.7, 58.1,
         57.5, 56.8, 56.3, 55.7, 54.9, 54.1, 53.1, 51.8, 50.2, 48.2, 46.0, 44.1]
# back edge: flat (0) up to z 119, then the back of the head rounds forward
BACK = [0.0] * 120 + [
    0.3, 0.3, 0.3, 0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 1.3, 1.4, 1.6, 1.8, 2.0, 2.2,
    2.4, 2.7, 3.0, 3.3, 3.7, 4.1, 4.5, 5.0, 5.5, 6.0, 6.6, 7.2, 8.0, 8.8, 9.7, 10.6, 11.7,
    12.8, 14.0, 15.3, 16.6, 18.0, 19.5, 21.3, 23.5, 26.0, 28.2, 29.6]
# bill top and bottom z at x = 52, 53 ... 100
BILL_X0 = 52.0
BILL_TOP = [147.3, 147.0, 146.6, 146.2, 145.8, 145.3, 144.9, 144.4, 144.0, 143.6, 143.3,
            142.8, 142.0, 141.0, 140.0, 139.2, 138.5, 137.8, 137.0, 136.3, 135.8, 135.4,
            134.9, 134.6, 134.3, 133.8, 133.2, 132.7, 132.5, 132.5, 132.3, 132.1, 131.8,
            131.4, 131.0, 130.8, 130.7, 130.5, 130.4, 130.0, 129.7, 129.4, 129.2, 128.9,
            128.6, 128.4, 128.1, 127.8, 127.5]
BILL_BOT = [124.6, 124.7, 124.8, 124.8, 124.8, 124.8, 124.9, 124.9, 125.0, 124.9, 124.9,
            124.9, 124.9, 124.9, 124.9, 124.8, 124.7, 124.6, 124.5, 124.4, 124.3, 124.2,
            124.1, 124.0, 123.9, 123.8, 123.7, 123.6, 123.5, 123.5, 123.4, 123.4, 123.4,
            123.5, 123.5, 123.5, 123.6, 123.7, 123.8, 123.8, 123.8, 123.8, 123.8, 123.8,
            123.8, 123.8, 123.9, 124.0, 124.1]
# half-widths above the breast (front view, photo 1); the breast's width follows its depth
# (BREAST_RATIO x FRONT, giving the listed 3 in at the base), the collar steps in at 45.5
BREAST_RATIO = (0.545, 0.47)       # at z 0 and z 45
WIDTH_Z = [45.6, 51.5, 53, 60, 80, 95, 110, 120, 130, 140, 150, 156, 160, 163, 165]
WIDTH = [24.0, 24.0, 23.0, 22.0, 20.2, 19.6, 20.0, 21.0, 22.0, 22.5, 22.0, 20.5, 17.5, 13.0, 4.0]
BILL_W_X = [52.0, 60.0, 75.0, 90.0, 97.0, L]
BILL_W = [12.0, 10.5, 8.5, 7.2, 6.4, 5.5]



def _dense(xs, ys, sigma, step=0.25):
    """Gaussian-smoothed table resampled on a fine grid with a cubic spline, so the
    1 mm steps of the photo measurement leave no rings on the surface."""
    from scipy.interpolate import CubicSpline
    from scipy.ndimage import gaussian_filter1d
    ys = gaussian_filter1d(np.asarray(ys, float), sigma, mode="nearest") if sigma else ys
    xd = np.arange(xs[0], xs[-1] + 1e-9, step)
    return xd, CubicSpline(xs, ys)(xd)


_F = np.array(FRONT, float)
_F[:9] = _F[9]                                   # (shadowed rows; the foot is set below)
_ZB, _FB = _dense(np.arange(0.0, 46.0), _F[:46], 2.5)          # breast
# the photo's base rolls under below z 8 (x 71.6 at z 8, 67.3 at z 5, ~22 deg from flat);
# a 45 deg chamfer through the z 8 point is as close as it can come and still print
# without support (1.3 mm off at z 5)
_c = 63.6 + _ZB                                  # blended in (radius ~4) so it rolls, not steps
_h = np.clip(0.5 + 0.5 * (_FB - _c) / 4.0, 0.0, 1.0)
_FB = _c * _h + _FB * (1 - _h) - 4.0 * _h * (1 - _h)
_ZN, _FN = _dense(np.arange(46.0, 166.0), _F[46:], 0.8)        # collar, neck, head
_ZS = np.r_[_ZB, _ZN]
_FS = np.r_[_FB, _FN]
_ZK, _BS = _dense(np.arange(0.0, 166.0), BACK, 1.0)
_BX, _TOP = _dense(BILL_X0 + np.arange(len(BILL_TOP), dtype=float), BILL_TOP, 1.5)
_, _BOT = _dense(BILL_X0 + np.arange(len(BILL_BOT), dtype=float), BILL_BOT, 1.5)


def _width(zc, F):
    breast = F * np.interp(zc, [0.0, 45.0], BREAST_RATIO)
    return np.where(zc <= 45.5, breast, np.interp(zc, WIDTH_Z, WIDTH))


def _ell(px, py, a, b):
    """Approximate signed distance (positive inside) to an ellipse with semi-axes a, b."""
    u, v = px / a, py / b
    k0 = np.sqrt(u * u + v * v)
    k1 = np.sqrt((u / a) ** 2 + (v / b) ** 2) + 1e-9
    return -k0 * (k0 - 1.0) / k1


def _section(x, y, xb, F, b):
    """Ellipse spanning x in [xb, F] at this height, half-width b at its middle."""
    xc = (xb + F) / 2
    return _ell(x - xc, y, (F - xb) / 2, b)


NECK_BACK = 1.0     # the neck/head ellipse reaches this far behind the back plane: the neck
                    # stays round right to the back (as on the reference, reference photo 5)
                    # and the plane leaves only a ~12 mm contact strip for the books; it
                    # tapers to 0 at the crown, where BACK takes over


def _rows(x, y, z):
    """Breast, neck and head: an ellipse per height through the measured outline. The
    breast is a D (full-width flat back, a bookend's base); the collar, neck and head are
    one round section all the way up (no change of section type, so no crease), blended
    into the breast's rounded shoulder."""
    zb = np.clip(z, 0.0, 45.5)
    Fb = np.interp(zb, _ZB, _FB)
    breast = _section(x, y, -Fb, Fb, _width(zb, Fb))
    breast = -_smax(-breast, -(45.6 - z), 6.0)
    zn = np.clip(z, 46.0, H)
    Fn = np.interp(zn, _ZN, _FN)
    Bn = np.maximum(np.interp(zn, _ZK, _BS), 0.0)
    t = np.clip((zn - 132.0) / 20.0, 0.0, 1.0)
    e = NECK_BACK * (1.0 - t * t * (3 - 2 * t))
    neck = _section(x, y, Bn - e, Fn, _width(zn, Fn))
    # crown: a shallow paraboloid cap rounds the top rows (the photo's top 1-2 rows are
    # flat-ish where the outline tracing runs out) into a dome
    crown = H + 0.3 - z - np.where(x > 40.0, 0.025, 0.006) * (x - 40.0) ** 2 - 0.05 * y ** 2
    neck = -_smax(-neck, -crown, 4.0)
    neck = np.minimum(neck, z - 40.0)
    return _smax(breast, neck, 1.2)


def _bill(x, y, z):
    xq = np.clip(x, BILL_X0, L)
    top = np.interp(xq, _BX, _TOP)
    bot = np.interp(xq, _BX, _BOT)
    hw = np.interp(xq, BILL_W_X, BILL_W)
    tip = np.sqrt(np.clip(1.0 - (np.maximum(xq - (L - 1.9), 0.0) / 1.9) ** 2, 0.02, 1.0))   # blunt nail
    hh = (top - bot) / 2 * tip
    d = _ell(y, z - (top + bot) / 2, hw * tip, hh)
    return np.minimum(d, np.minimum(x - BILL_X0 + 3.0, L + 0.05 - x))


def _smax(a, b, k):
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0.0, 1.0)
    return a * h + b * (1 - h) + k * h * (1 - h)


COLLAR = (47.6, 50.6)     # collar groove centres
COLLAR_HALF = 0.8         # half-width: 1.6 mm wide, round-bottomed (2.7 grid cells, and
COLLAR_DEPTH = 0.5        # snapped exact, so no rope-like aliasing along the ring)


def body(x, y, z):
    """Positive inside the duck (no tab, no cavity), flat back at x = 0."""
    f = _smax(_rows(x, y, z), _bill(x, y, z), 4.0)
    for zg in COLLAR:          # collar grooves: a smooth round-bottomed profile, wide
        u = np.clip(np.abs(z - zg) / COLLAR_HALF, 0.0, 1.0)   # enough for the mesh grid
        f = f - COLLAR_DEPTH * 0.5 * (1.0 + np.cos(np.pi * u))
    return -_smax(-f, -x, 2.5)                                          # flat back, soft rim


def cast_field(p):
    def f(x, y, z):
        b = body(x, y, z)
        inner = b - p.wall
        cone = (p.cone_apex - z - np.sqrt((x - 22.0) ** 2 + y ** 2)) / np.sqrt(2.0)
        cav = np.minimum(inner, cone)
        # bottom lip: below lip_height the cavity only opens where it is lip mm deeper
        cav = np.minimum(cav, np.maximum(z - p.lip_height, b - p.wall - p.lip))
        return np.minimum(b, -cav)
    return f


# ---------------------------------------------------------------- engraving

def _surface(xz, side=1.0):
    """Project side-view points (x, z) onto the duck's surface at +y (side=1) or -y."""
    xz = np.asarray(xz, float)
    x, z = xz[:, 0], xz[:, 1]
    lo, hi = np.zeros(len(x)), np.full(len(x), 45.0)
    ok = body(x, lo, z) > 0
    for _ in range(40):
        mid = (lo + hi) / 2
        inside = body(x, mid, z) > 0
        lo = np.where(inside, mid, lo)
        hi = np.where(inside, hi, mid)
    return np.c_[x, side * lo, z][ok]


def _normal(pt, e=0.05):
    x, y, z = pt
    g = np.array([body(x + e, y, z) - body(x - e, y, z),
                  body(x, y + e, z) - body(x, y - e, z),
                  body(x, y, z + e) - body(x, y, z - e)])
    return -g / (np.linalg.norm(g) + 1e-12)          # outward


def _resample(ctrl, step=0.6):
    """Catmull-Rom through control points, resampled every ~step mm."""
    c = np.asarray(ctrl, float)
    c = np.vstack([c[0], c, c[-1]])
    out = []
    for i in range(1, len(c) - 2):
        p0, p1, p2, p3 = c[i - 1], c[i], c[i + 1], c[i + 2]
        n = max(2, int(np.linalg.norm(p2 - p1) / step))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(c[-2])
    return np.array(out)


# side-view lines (x from the back, z up), traced on a 1 mm grid over a 10x close-up of
# reference photo 4. Eye: an almond lid outline round a raised eyeball, a short tail
# off the back corner, no brow. Cheek: a raised round patch outlined over its top and
# back, with a short front edge. Bill: a ">" notch where it meets the face, a mouth
# groove low along the bill, a nostril slit high near the base.
LINES = {
    "cheek": [(50.4, 124.0), (50.6, 130.0), (49.6, 135.0), (45.0, 138.0), (40.0, 139.0),
              (35.0, 138.0), (31.0, 135.0), (30.0, 131.0), (30.5, 127.0), (33.0, 123.0),
              (36.0, 120.8)],
    "bill_base": [(60.0, 144.6), (57.5, 141.2), (55.0, 138.0), (55.6, 134.0), (56.5, 129.6)],
    "mouth": [(56.5, 129.6), (60.0, 129.2), (65.0, 128.5), (75.0, 127.5), (85.0, 126.5),
              (93.0, 126.0), (97.0, 125.9)],
    "nostril": [(61.5, 135.2), (65.0, 133.8), (68.5, 132.3), (71.5, 131.2)],
}
# The eye, traced from a 24 px/mm close-up of photo 4: a round eyeball sitting in a
# sunken almond socket, framed by thick rolled lids that meet in points at the front
# (toward the bill) and the back, each corner running on as a short groove.
EYE_UPPER = [(51.6, 148.9), (49.5, 151.3), (46.5, 153.9), (43.0, 155.3), (39.5, 155.6),
             (36.0, 154.6), (33.2, 152.0), (31.4, 149.4), (30.8, 147.6)]
EYE_LOWER = [(51.6, 148.9), (48.5, 147.3), (45.0, 146.2), (41.0, 145.6), (37.0, 145.7),
             (33.5, 146.4), (30.8, 147.6)]
SOCKET_DEPTH = 1.8        # socket floor below the head surface
LID_GROOVE = 2.2          # engraved line outlining the lids, this far outside the almond:
                          # the lids are the flush band between it and the socket
EYE_TAILS = ((3.0, -0.3), (-2.8, -1.0))   # corner grooves running on from the front / back point
# raised features: (centre x, z), half-size along x and z, height above the surface,
# depth of the dome's equator below the surface (None: 2x height)
EYEBALL = ((40.6, 150.6), (4.5, 3.6), -0.3, SOCKET_DEPTH)
CHEEK = ((40.3, 129.6), (11.6, 10.6), 1.9, None)


def _frame(pt):
    """Local frame at a surface point: (along x, along z, outward normal)."""
    n = _normal(pt)
    t1 = np.array([1.0, 0.0, 0.0]) - n[0] * n
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)
    if t2[2] < 0:
        t2 = -t2
    return t1, t2, n


def _bump(xz, half, height, side, sunk=None):
    """A low dome on the surface: an ellipsoid whose equator lies `sunk` below the
    surface (default 2x height), so `height` shows above it."""
    s = _surface([xz], side)[0]
    t1, t2, n = _frame(s)
    sunk = 2.0 * height if sunk is None else sunk
    depth = sunk + height
    centre = s - sunk * n
    m = np.c_[t1 * half[0], t2 * half[1], n * depth, centre]       # 3x4: unit sphere -> dome
    return Manifold.sphere(1.0, 64).transform(m.tolist())


def _beads(ctrl, side, r, lift, closed=False):
    """Capsule chain of r-radius balls along a side-view line, centres `lift` above
    the surface (negative: sunk into it)."""
    pts = _surface(_resample(ctrl, 0.5), side)
    pts = [q + lift * _normal(q) for q in pts]
    if closed:
        pts.append(pts[0])
    ball = Manifold.sphere(r, 16)
    balls = [ball.translate(tuple(q)) for q in pts]
    return [Manifold.batch_hull([a, b]) for a, b in zip(balls, balls[1:])]


def _almond():
    """The eye's almond outline as a CrossSection in the side view (x, z)."""
    ring = _resample(EYE_UPPER, 0.3)[:-1].tolist() + _resample(EYE_LOWER[::-1], 0.3)[:-1].tolist()
    almond = CrossSection([ring])
    return almond if almond.area() > 0 else CrossSection([ring[::-1]])


def lid_outline():
    """Closed side-view line LID_GROOVE outside the almond, pointed at the corners."""
    ring = _almond().offset(LID_GROOVE, join_type=JoinType.Miter, miter_limit=3.0)
    return np.asarray(ring.to_polygons()[0])


def eye_tails():
    """Short grooves running on from the outline's front and back points."""
    ring = lid_outline()
    out = []
    for c, (dx, dz) in ((ring[np.argmax(ring[:, 0])], EYE_TAILS[0]),
                        (ring[np.argmin(ring[:, 0])], EYE_TAILS[1])):
        out.append([tuple(c), (c[0] + dx / 2, c[1] + dz / 2), (c[0] + dx, c[1] + dz)])
    return out


SOCKET_DRAFT = 0.6        # socket wall leans in this many mm per mm of depth, so its
                          # rim never overhangs the socket as a knife edge


def _almond_distance():
    """Signed side-view distance to the almond outline (positive inside), as f(x, z)."""
    from PIL import Image, ImageDraw
    from scipy.interpolate import RegularGridInterpolator
    from scipy.ndimage import distance_transform_edt
    ring = np.asarray(_almond().to_polygons()[0])
    h = 0.05
    xs = np.arange(ring[:, 0].min() - 4, ring[:, 0].max() + 4, h)
    zs = np.arange(ring[:, 1].min() - 4, ring[:, 1].max() + 4, h)
    img = Image.new("1", (len(xs), len(zs)), 0)      # column = x index, row = z index
    ImageDraw.Draw(img).polygon([((a - xs[0]) / h, (b - zs[0]) / h) for a, b in ring], fill=1)
    inside = np.asarray(img, bool).T                   # -> [x, z]
    d = (distance_transform_edt(inside) - distance_transform_edt(~inside)) * h
    f = RegularGridInterpolator((xs, zs), d, bounds_error=False, fill_value=-4.0)
    return lambda x, z: f(np.stack([x, z], -1))


def eye_socket():
    """The sunken almond the eyeball sits in, both sides: inside the almond outline
    (shrinking SOCKET_DRAFT per mm of depth) and less than SOCKET_DEPTH below the surface."""
    d2 = _almond_distance()
    ring = np.asarray(_almond().to_polygons()[0])
    lo, hi = ring.min(0) - 1.0, ring.max(0) + 1.0

    def f(x, y, z):
        t = body(x, y, z)                         # ~depth below the surface
        return np.minimum(np.minimum(SOCKET_DEPTH - t, d2(x, z) - SOCKET_DRAFT * np.maximum(t, 0)),
                          t + 1.0)
    return build_sdf(f, (lo[0], -30.0, lo[1], hi[0], 30.0, hi[1]), edge=0.25, flat_bottom=False,
                     snap=True)


def details(p):
    """(cut, add): engraved grooves, the eye sockets, and the raised lids, eyeballs and
    cheek patches, both sides."""
    cuts, adds = [], []
    for side in (1.0, -1.0):
        for ctrl in LINES.values():
            cuts += _beads(ctrl, side, p.groove, -0.1)
        cuts += _beads(lid_outline(), side, p.groove, -0.1, closed=True)
        for tail in eye_tails():
            cuts += _beads(tail, side, p.groove, -0.1)
        for xz, half, height, sunk in (EYEBALL, CHEEK):
            adds.append(_bump(xz, half, height, side, sunk))
    return (eye_socket(), Manifold.batch_boolean(cuts, OpType.Add),
            Manifold.batch_boolean(adds, OpType.Add))


# ---------------------------------------------------------------- parts

def _tab_span(p):
    """(y0, y1) the tab covers: the -y half (0.5 mm short of the centre line, so the
    partner bookend's tab, turned 180 deg, passes it with 1 mm between) or the full width."""
    W = p.tab_width
    return (-W / 2, -0.5) if p.tab_split else (-W / 2, W / 2)


def tab(p):
    Lt, T = p.tab_length, p.tab_thickness
    y0, y1 = _tab_span(p)
    r = 6.0
    plate = (CrossSection.square((Lt + 1.0 - 2 * r, y1 - y0 - 2 * r)).translate((-Lt + r, y0 + r))
             .offset(r, join_type=JoinType.Round, circular_segments=48))
    plate = Manifold.extrude(plate, T)
    # 45 deg fillet where the tab meets the back, 3 mm, kept inside the base width
    w0, w1 = max(y0, -30.0), min(y1, 30.0)
    wedge = Manifold.extrude(CrossSection([[(0.2, T - 0.1), (0.2, T + 3.2), (-3.0, T - 0.1)]]), w1 - w0)
    wedge = wedge.rotate((90, 0, 0)).translate((0, w1, 0))
    return plate + wedge


def _has_tab(p):
    return (p.style == "full" and p.tab) or (p.style == "cast" and p.cast_tab)


def build(p):
    if p.style not in ("full", "cast"):
        raise ValueError("style must be 'full' or 'cast'")
    field = body if p.style == "full" else cast_field(p)
    m = build_sdf(field, (-1.0, -40.0, -0.5, L + 2.0, 40.0, H + 2.0), edge=p.edge, snap=True)
    socket, cut, add = details(p)
    m = ((m - socket) + add) - cut   # socket first, then eyeball and lids, then grooves
    if _has_tab(p):
        m = m + tab(p)
    # a groove grazing a slope can leave a zero-volume speck behind: keep the duck only
    return max(m.decompose(), key=lambda q: q.volume())


# ---------------------------------------------------------------- checks

def _hit(tm, origin, direction):
    """Distance along the ray to the first surface hit, or None."""
    loc, _, _ = tm.ray.intersects_location([origin], [direction])
    if not len(loc):
        return None
    return np.min((loc - origin) @ np.asarray(direction, float))


def _profile_front(ctx):
    """Front edge of the mesh (centre plane) at sampled heights vs the photo-4 FRONT table."""
    errs = []
    for z in list(range(8, 44, 4)) + list(range(56, 122, 4)) + list(range(148, 162, 3)):
        d = _hit(ctx.tm, (300.0, 0.0, z + 0.01), (-1.0, 0.0, 0.0))
        errs.append(300.0 - d - FRONT[z])
    e = np.abs(errs)
    return e.mean() < 1.0 and e.max() < 2.0,         f"front edge vs photo: mean {e.mean():.2f} mm, max {e.max():.2f} mm over {len(e)} heights"


def _profile_bill(ctx):
    """Bill top and bottom (centre plane) vs BILL_TOP / BILL_BOT."""
    errs = []
    for x in range(64, 97, 4):
        i = x - int(BILL_X0)
        top = 300.0 - _hit(ctx.tm, (x + 0.01, 0.0, 300.0), (0.0, 0.0, -1.0))
        bot = 100.0 + _hit(ctx.tm, (x + 0.01, 0.0, 100.0), (0.0, 0.0, 1.0))
        errs += [top - BILL_TOP[i], bot - BILL_BOT[i]]
    e = np.abs(errs)
    return e.mean() < 1.0 and e.max() < 2.0,         f"bill top/bottom vs photo: mean {e.mean():.2f} mm, max {e.max():.2f} mm"


def _symmetric(ctx):
    """Left/right mirror symmetry: one STL makes both bookends of a pair."""
    tm = ctx.tm
    rng = np.random.default_rng(1)
    lo, hi = tm.bounds.copy()
    lo[0], hi[0] = 0.0, L                    # the duck, not the tab
    pts = lo + rng.random((2000, 3)) * (hi - lo)
    agree = (tm.contains(pts) == tm.contains(pts * [1, -1, 1])).mean()
    return agree > 0.995, f"{agree * 100:.2f}% of 2000 sample points match their mirror"


def checks(p):
    has_tab = _has_tab(p)
    x_total = L + (p.tab_length if has_tab else 0.0)
    y_total = max(p.tab_width, 76.0) if has_tab and not p.tab_split else 76.0
    c = [
        dims(x=(x_total - 1.0, x_total + 1.0), y=(y_total - 1.5, y_total + 1.0), z=(H - 0.5, H + 0.5)),
        solid((25.0, 0.0, 150.0),          # head
              (90.0, 0.0, 127.0),          # bill near the tip
              (15.0, 0.0, 110.0)),         # neck
        thickness_at((90.0, 0.0, 127.0), 3.0),     # bill is not a sliver
        custom("profile front", _profile_front),
        custom("profile bill", _profile_bill),
        custom("left/right symmetric", _symmetric),
        single_body(),
        fits_bed(),
    ]
    if has_tab:
        ty = sum(_tab_span(p)) / 2
        c += [solid((-p.tab_length / 2, ty, p.tab_thickness / 2)),
              empty((-p.tab_length / 2, ty, p.tab_thickness + 0.5)),
              thickness_at((-p.tab_length / 2, ty, p.tab_thickness / 2), p.tab_thickness - 0.3)]
        if p.tab_split:     # the partner's tab lane (+y half) is clear
            c += [empty((-p.tab_length / 2, 10.0, p.tab_thickness / 2),
                        (-p.tab_length / 2, 0.2, p.tab_thickness / 2))]
    if p.style == "full":
        c += [solid((20.0, 0.0, 30.0), (20.0, 0.0, 85.0)), flat_base(3000.0)]
    else:
        c += [empty((22.0, 0.0, 0.5), (22.0, 0.0, 30.0), (22.0, 0.0, 55.0)),  # open, hollow
              solid((20.0, 0.0, 75.0)),                                       # roof closed
              solid((p.wall / 2, 0.0, 30.0)),                                 # back wall
              solid((60.4, 0.0, 0.8)),                                         # front lip
              thickness_at((p.wall / 2, 0.0, 30.0), 2.0),
              custom("cavity holds concrete", _cavity_ok)]
    return c


def _cavity_ok(ctx):
    outer = build_sdf(body, (-1.0, -40.0, -0.5, L + 2.0, 40.0, H + 2.0), edge=1.0).volume() / 1000.0
    cav = outer - ctx.tm.volume / 1000.0
    return cav > 100.0, f"cavity about {cav:.0f} cm3 (~{cav * 2.3 / 1000:.2f} kg of concrete)"
