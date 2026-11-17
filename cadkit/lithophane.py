"""Lithophanes: a photo in, a print-ready backlit panel, arc or lamp shade out.

    from cadkit.lithophane import *
    L = Lithophane("photos/dog.jpg", width=100, shape="flat")   # all options below
    part = L.solid()              # Manifold, upright in print pose, smooth face at y=0
    L.backlit_png("dog_backlit.png")   # what it looks like on a light box

Model scripts use `litho_params()`, `litho_build(p)`, `litho_checks(p)` and
`litho_extras(p, out, name)` (`cad litho photo.jpg` writes such a script for you).

Where the method comes from
---------------------------
The tone mapping is Cura's ImageReader plugin (Ultimaker, LGPLv3, the "lithophane"
import every Cura user has): image -> CIE luminance with sRGB gamma, an optional
box-blur smoothing pass, and its "light transmittance" model: Beer-Lambert absorption,
so a pixel of luminance Y gets the thickness whose transmitted light is Y:

    T(t) = tau ** t            tau = fraction of light one mm of filament lets through
    t    = t_min + ln(Y') / ln(tau),   Y' = T_min + (1 - T_min) * Y,  T_min = tau ** (t_max - t_min)

The formula is re-implemented here in numpy (no Cura code is copied) and kept as
`model="transmittance"`; Cura's "linear" model (thickness straight from brightness) is
`model="linear"`. The default, `model="perceptual"`, keeps Beer-Lambert for the
thickness but fixes what Cura's mapping does to the shadows: a print only spans ~5:1
in lit brightness, and squeezing linear luminance into that range crushes the darkest
third of the image into a few percent; mapping CIE lightness evenly instead keeps every
tone step a visible step.

What this adds over a slicer's image import
-------------------------------------------
- Correct colour handling: EXIF rotation, transparency over white, the exact sRGB
  transfer curve (Cura uses a 2.2 power) and Rec. 709 weights.
- Tone preparation: percentile auto-levels, a gamma knob, and pre-sharpening sized to
  the light diffusion in the plastic (light scatters sideways ~ half the wall
  thickness, which softens a lithophane; the unsharp mask puts that detail back).
- Print-ready shapes: flat panel printed upright (best quality: the relief is traced
  by the outer wall at nozzle resolution instead of being stepped in 0.2 mm layers)
  with an optional stand foot; an arc (self-standing) and a full cylinder (lamp shade,
  seamless); oval, circle, heart, hexagon and rounded outlines.
- Nozzle-aware relief: ridges and grooves narrower than the nozzle (sharpening halos,
  hairlines) cannot be traced by an extrusion line; a grey opening + closing at nozzle
  width flattens them instead of leaving the slicer to blob or drop them.
- A stiff frame that prints without supports: its inner edge is chamfered so the
  step from frame to picture never overhangs more than ~34 deg from vertical.
- Mesh: one watertight body by construction, then manifold's `simplify` merges the
  flat back, the frame and any featureless sky, so STLs stay small.
- A backlit simulation (`backlit_png`): Beer-Lambert transmission plus sideways
  scattering, warm LED tint, next to the target tones, so the result can be judged
  before printing.
- Bambu print setup (`LITHO_SLICE`): 100% infill, 0.12 mm layers, brim.
- Calibration: `models/lithophane_calibration.py` is a step wedge; photograph it on
  a light box and `cad litho calibrate photo.jpg` measures tau for your filament.
"""
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, Manifold, Mesh
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

__all__ = ["Lithophane", "LITHO_MIN_WALL", "litho_params", "litho_build", "litho_checks", "litho_extras",
           "LITHO_SLICE", "TRANSMITTANCE", "srgb_to_linear", "linear_to_srgb",
           "fit_transmittance", "SHAPES", "OUTLINES"]

ROOT = Path(__file__).resolve().parent.parent

# Fraction of light 1 mm of filament lets through. Cura's default is 50%; the white
# PLA values are starting points: print models/lithophane_calibration.py and run
# `cad litho calibrate` to measure your own spool.
TRANSMITTANCE = {
    "cura_default": 0.50,
    "pla_white": 0.50,
    "petg_white": 0.60,          # white PETG lets more light through than white PLA
    "elegoo_rapid_petg_white": 0.60,   # no published value: the petg_white estimate
    "pla_natural": 0.70,
}

# Thin-wall warning floor for lithophane models (MIN_WALL = LITHO_MIN_WALL): the white
# areas are min_t (0.6 mm) thin on purpose, and printable_relief keeps every relief
# crest at least a nozzle wide, but the wall sampler still reads 0.3-0.4 mm on the
# sloped shoulders of those crests. The `picture wall >= min_t` check holds the real
# minimum; anything under this floor would be a genuine defect.
LITHO_MIN_WALL = 0.25

SHAPES = ("flat", "arc", "cylinder")
# Sideways light spread in the plastic, as a fraction of the wall (Gaussian sigma).
# Used both to simulate the print and to size the pre-sharpening that undoes it.
SCATTER = 0.25
# Frame chamfer run per mm of thickness (1.2 = 40 deg from vertical, prints unsupported).
CHAMFER = 1.2
OUTLINES = ("rect", "rounded", "oval", "heart", "hexagon")

# Production print setup (models assign SLICE = LITHO_SLICE). Upright lithophanes are
# tall and thin: a brim holds them down, 100% infill makes the thickness, not the
# infill pattern, decide the brightness, 0.12 mm layers keep vertical detail fine.
LITHO_SLICE = dict(
    # A1 / A1 mini are bed slingers (the bed moves in Y). Models put the panel's thin
    # side along Y, so turn it 90 deg on the plate: the bed then shakes it along its
    # stiff width instead of rocking the thin sheet back and forth.
    rotate=90,
    layer_height=0.12,
    infill=100,
    # Bambu's default "grid" infill refuses 100%; zig-zag (rectilinear) is solid.
    # Walls only in practice: 4 loops (3.36 mm) cover a 3.2 mm picture, so every line runs
    # along the sheet (no infill strokes across it shoving it sideways or showing when
    # lit). resolution 0.1 merges sub-nozzle relief segments; no retraction on travels
    # under 3 mm. Measured on a 100 x 100 PETG panel and a 3-panel plate: ~10-25% faster
    # and a third fewer retractions than 2 walls + zig-zag.
    process={"brim_type": "outer_only", "brim_width": "6", "seam_position": "aligned",
             "sparse_infill_pattern": "zig-zag", "wall_loops": "4", "resolution": "0.1",
             "retraction_minimum_travel": "3"},
)


def srgb_to_linear(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lightness(y):
    """CIE L* (0..100) of relative luminance y."""
    y = np.asarray(y, float)
    return np.where(y > 216 / 24389, 116 * np.cbrt(y) - 16, y * 24389 / 27)


def inverse_lightness(L):
    L = np.asarray(L, float)
    return np.where(L > 8, ((L + 16) / 116) ** 3, L * 27 / 24389)


def _window(a, k, fn, anchor):
    """min/max over a k x k window; anchor 0 = window starts at the pixel, 1 = ends."""
    if k <= 1:
        return a
    lo, hi = (0, k - 1) if anchor == 0 else (k - 1, 0)
    q = np.pad(a, ((lo, hi), (lo, hi)), mode="edge")
    from numpy.lib.stride_tricks import sliding_window_view as win
    rows = fn(win(q, k, axis=0), axis=-1)            # separable: down the columns...
    return fn(win(rows, k, axis=1), axis=-1)         # ...then along the rows


def printable_relief(t, k):
    """Grey opening then closing with a k x k square (k = nozzle width in grid cells):
    ridges and grooves narrower than the nozzle, which no extrusion line can trace,
    are flattened to the nearest level the nozzle can draw."""
    if k <= 1:
        return t
    t = _window(_window(t, k, np.min, 0), k, np.max, 1)      # opening: thin ridges off
    return _window(_window(t, k, np.max, 0), k, np.min, 1)   # closing: thin grooves filled


def _box_blur(a, n):
    """Cura's smoothing: n passes of a 3x3 mean filter with edge padding."""
    for _ in range(int(n)):
        q = np.pad(a, 1, mode="edge")
        a = sum(q[1 + dy:q.shape[0] - 1 + dy, 1 + dx:q.shape[1] - 1 + dx]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
    return a


def _gauss(a, sigma_px):
    """Separable Gaussian blur on a float array, edges reflected."""
    if sigma_px <= 0.05:
        return a
    r = max(1, int(math.ceil(3 * sigma_px)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_px) ** 2)
    k /= k.sum()
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        q = np.pad(a, pad, mode="reflect" if a.shape[axis] > r else "edge")
        a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), axis, q)
    return a


def _outline_polygon(kind, w, h, corner):
    """Outline in panel coordinates (x across, z up, origin at bottom centre)."""
    from shapely.geometry import Polygon, box
    if kind == "rect":
        return box(-w / 2, 0, w / 2, h)
    if kind == "rounded":
        r = min(corner, w / 2 - 0.01, h / 2 - 0.01)
        return box(-w / 2 + r, r, w / 2 - r, h - r).buffer(r, quad_segs=24)
    if kind == "oval":
        t = np.linspace(0, 2 * np.pi, 240, endpoint=False)
        return Polygon(np.c_[w / 2 * np.cos(t), h / 2 + h / 2 * np.sin(t)])
    if kind == "hexagon":
        t = np.radians(np.arange(6) * 60)
        return Polygon(np.c_[w / 2 * np.cos(t), h / 2 + h / 2 * np.sin(t)])
    if kind == "heart":
        from .stitch.shapes import heart
        g = heart(100.0)
        x0, y0, x1, y1 = g.bounds
        from shapely import affinity
        g = affinity.translate(g, -(x0 + x1) / 2, -y0)
        # stands upright, so cut the point off flat: base 8% up, then rescale to w x h
        cut = 0.08 * (y1 - y0)
        g = g.intersection(box(-1e3, cut, 1e3, 1e3))
        g = affinity.translate(g, 0, -cut)
        return affinity.scale(g, w / (x1 - x0), h / (y1 - y0 - cut), origin=(0, 0))
    raise ValueError(f"outline must be one of {OUTLINES}, got {kind!r}")


class Lithophane:
    """Everything about one lithophane: tones, thickness map, solid and simulation.

    image        path to a photo (any format Pillow reads)
    width        outer width in mm (arc: length along the smooth face; cylinder:
                 the circumference, so diameter = width / pi)
    height       outer height in mm; None = from the image's aspect ratio. When both
                 are given the image is centre-cropped to fit.
    shape        "flat" (upright panel), "arc" (curved by `curve` degrees), "cylinder"
    min_t/max_t  thinnest (white) and thickest (black) picture wall, mm
    model        "perceptual" (default: lightness spread evenly over the printable lit
                 range, Beer-Lambert thickness), "transmittance" (Cura's light
                 transmittance model exactly) or "linear" (Cura's other option)
    transmittance  light through 1 mm (0..1) or a TRANSMITTANCE key
    border/frame_t  frame band width and thickness, mm (0 = no frame)
    outline      rect, rounded, oval, heart, hexagon (flat only)
    stand        flat only: depth of a foot along y, mm (0 = none; brim still holds it)
    res          grid spacing in mm (0.2 = half a nozzle; finer adds no detail)
    levels       auto-levels percentile clip (0 = off)
    gamma        >1 brightens the mid-tones, <1 darkens them
    sharpen      unsharp-mask amount that compensates diffusion (0 = off)
    smooth       Cura's box-blur passes (0 = off)
    invert       swap light and dark (negative)
    mirror       flip left-right (when the relief side will face the viewer)
    nozzle       relief features narrower than this are flattened (0 = keep all)
    detail       how sub-nozzle relief is handled: "open" flattens it (grey opening and
                 closing; safest walls), "soft" rounds it off with a quarter-nozzle blur
                 (keeps eyes and mouths on small faces), "none" leaves it to the slicer
    clarity      local-contrast boost (0 = off; 0.3-0.8 for small faces), over
                 `clarity_mm` neighbourhoods
    match        iterations solving for the wall whose lit, scattered image matches
                 the photo (0 = off; 15-25 typical; use with sharpen=0)
    crop         (left, top, right, bottom) fractions of the photo to use; may reach
                 past the edges (mirrored fill). Whatever is left is centre-fitted.
    """

    def __init__(self, image, width=100.0, height=None, shape="flat", curve=120.0,
                 min_t=0.6, max_t=3.0, model="perceptual", transmittance="pla_white",
                 border=3.0, frame_t=None, outline="rect", corner=6.0, stand=0.0,
                 res=0.2, levels=0.5, gamma=1.0, sharpen=0.6, smooth=0, invert=False,
                 mirror=False, nozzle=0.4, crop=(0.0, 0.0, 1.0, 1.0), clarity=0.0,
                 clarity_mm=3.0, match=0, detail="open"):
        if shape not in SHAPES:
            raise ValueError(f"shape must be one of {SHAPES}, got {shape!r}")
        if outline != "rect" and shape != "flat":
            raise ValueError("non-rectangular outlines are for flat lithophanes")
        if not 0.2 <= min_t < max_t:
            raise ValueError("need 0.2 <= min_t < max_t")
        self.path = Path(image)
        if not self.path.is_absolute() and not self.path.exists():
            self.path = ROOT / self.path
        self.tau = float(TRANSMITTANCE.get(transmittance, transmittance)) \
            if isinstance(transmittance, str) else float(transmittance)
        if not 0.01 < self.tau < 0.99:
            raise ValueError(f"transmittance per mm must be between 0.01 and 0.99, got {self.tau}")
        self.shape, self.curve, self.model = shape, float(curve), model
        self.min_t, self.max_t = float(min_t), float(max_t)
        self.border = float(border)
        self.frame_t = float(frame_t) if frame_t else (self.max_t + 1.0 if border else 0.0)
        self.outline, self.corner, self.stand = outline, float(corner), float(stand)
        self.levels, self.gamma, self.sharpen, self.smooth = levels, gamma, sharpen, smooth
        self.invert, self.mirror = invert, mirror
        self.nozzle = float(nozzle)
        self.crop = tuple(float(c) for c in crop) if crop else (0.0, 0.0, 1.0, 1.0)
        self.clarity, self.clarity_mm, self.match = float(clarity), float(clarity_mm), int(match)
        if detail not in ("open", "soft", "none"):
            raise ValueError(f"detail must be open, soft or none, got {detail!r}")
        self.detail = detail

        src = self._crop(self._load())
        aspect = src.size[1] / src.size[0]
        b = self.border
        # the top band also carries the chamfer that keeps its underside printable
        chamfer = CHAMFER * (self.frame_t - self.min_t) if b else 0.0
        side = 0.0 if shape == "cylinder" else b            # a cylinder wraps: no side bands
        self.width = float(width)
        if height:
            self.height = float(height)
        elif outline != "rect":                              # picture spans the outline box
            self.height = round(self.width * aspect, 1)
        else:
            self.height = round(2 * b + chamfer + (self.width - 2 * side) * aspect, 1)
        nb, nc = int(round(b / res)), int(math.ceil(chamfer / res))
        self.nx = max(int(round(self.width / res)) + 1, 2 * nb + 8)
        self.res = self.width / (self.nx - 1)
        self.ny = max(int(round(self.height / self.res)) + 1, 2 * nb + nc + 8)
        self.height = (self.ny - 1) * self.res
        self.nb, self.nc = nb, nc
        if outline != "rect":
            self.pad = (0, 0, 0, 0)                          # picture spans the outline box
        else:
            ns = 0 if shape == "cylinder" else nb
            self.pad = (ns, ns, nb, nb + nc)                 # left, right, bottom, top cells
        self.target = self._tones(src)                 # linear luminance on the grid, row 0 = bottom
        self.t_pic = self.thickness_of(self.target)   # picture wall alone, no frame
        if self.match:
            self.t_pic = self._match(self.t_pic)
        if self.detail == "open":
            self.t_pic = printable_relief(self.t_pic, int(round(self.nozzle / self.res)))
        elif self.detail == "soft":
            # round sub-nozzle detail off the way an extrusion line would draw it, instead
            # of deleting it: keeps eyes and mouths on small faces
            self.t_pic = _gauss(self.t_pic, self.nozzle / 4 / self.res)
        self.t = self._thickness()

    # ---- image -> tones -------------------------------------------------------------
    def _load(self):
        im = Image.open(self.path)
        im = ImageOps.exif_transpose(im)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            im = Image.alpha_composite(bg, im)
        return im.convert("RGB")

    def _match(self, t0):
        """Solve for the wall whose *lit* image matches the target. The light that comes
        through is blurred by scattering in the plastic (backlit()); instead of a fixed
        unsharp mask, iterate T <- clip(T + (want - blur(T)), T_min, 1) (projected Van
        Cittert deconvolution) so the blurred result converges on the wanted light, inside
        what the thickness range can make. Returns the thickness for that light."""
        t_min_rel = self.tau ** (self.max_t - self.min_t)
        want = self.tau ** (t0 - self.min_t)                     # light we want to see
        sigma = SCATTER * float(np.mean(t0)) / self.res
        T = want.copy()
        for _ in range(self.match):
            T = np.clip(T + (want - _gauss(T, sigma)), t_min_rel, 1.0)
        return self.min_t + np.log(T) / np.log(self.tau)

    def _crop(self, im):
        """Crop to `crop` = (left, top, right, bottom) as fractions of the photo. The box
        may reach past the edges (e.g. -0.08 or 1.08): that part is filled by mirroring
        the photo, so a wide group shot can be fitted to a square panel uncut."""
        x0, y0, x1, y1 = self.crop
        if (x0, y0, x1, y1) == (0.0, 0.0, 1.0, 1.0):
            return im
        W, H = im.size
        bx = [int(round(x0 * W)), int(round(y0 * H)), int(round(x1 * W)), int(round(y1 * H))]
        if bx[2] - bx[0] < 8 or bx[3] - bx[1] < 8:
            raise ValueError(f"crop {self.crop} leaves no picture")
        pl, pt = max(0, -bx[0]), max(0, -bx[1])
        pr, pb = max(0, bx[2] - W), max(0, bx[3] - H)
        if pl or pt or pr or pb:
            a = np.asarray(im)
            # extend the edge rows/columns outward, then blur only the added strips
            # into a soft tonal field (a mirror copy repeats the subject)
            a = np.pad(a, ((pt, pb), (pl, pr), (0, 0)), mode="edge")
            soft = np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(max(a.shape[:2]) / 25)))
            keep = np.zeros(a.shape[:2], bool)
            keep[pt:pt + H, pl:pl + W] = True
            a = np.where(keep[..., None], a, soft)
            im = Image.fromarray(a)
            bx = [bx[0] + pl, bx[1] + pt, bx[2] + pl, bx[3] + pt]
        return im.crop(tuple(bx))

    def _tones(self, src):
        """Linear luminance in [0, 1] for every grid point (picture area resampled,
        frame band padded with edge values; the frame overrides them anyway)."""
        l, r, bt, tp = self.pad
        nxi, nyi = self.nx - l - r, self.ny - bt - tp
        im = ImageOps.fit(src, (nxi, nyi), Image.LANCZOS, centering=(0.5, 0.5))
        if self.mirror:
            im = ImageOps.mirror(im)
        rgb = srgb_to_linear(np.asarray(im, float) / 255.0)
        y = rgb @ np.array([0.2126, 0.7152, 0.0722])            # Rec. 709 relative luminance
        p = linear_to_srgb(y)                                    # perceptual, for editing
        if self.levels:
            lo, hi = np.percentile(p, [self.levels, 100 - self.levels])
            if hi - lo > 1e-3:
                p = np.clip((p - lo) / (hi - lo), 0, 1)
        if self.gamma != 1.0:
            p = p ** (1.0 / self.gamma)
        if self.sharpen:
            # light scatters sideways about half the mean wall: undo that blur up front
            sigma = SCATTER * (self.min_t + self.max_t) / 2 / self.res
            p = np.clip(p + self.sharpen * (p - _gauss(p, sigma)), 0, 1)
        if self.clarity:
            # local contrast: features (eyes, mouths, hairlines) are pushed apart from
            # their surroundings so small faces use more of the narrow lit range
            p = np.clip(p + self.clarity * (p - _gauss(p, self.clarity_mm / self.res)), 0, 1)
        if self.smooth:
            p = _box_blur(p, self.smooth)
        if self.invert:
            p = 1 - p
        y = srgb_to_linear(p)
        y = np.flipud(y)                        # image row 0 is the top; grid row 0 is z=0
        l, r, bt, tp = self.pad
        return np.pad(y, ((bt, tp), (l, r)), mode="edge")

    def thickness_of(self, y):
        """Picture wall thickness for linear luminance y (0 black .. 1 white)."""
        y = np.clip(np.asarray(y, float), 0, 1)
        if self.model == "linear":
            return self.max_t - linear_to_srgb(y) * (self.max_t - self.min_t)
        t_min_rel = self.tau ** (self.max_t - self.min_t)     # darkest light the print can show
        if self.model == "perceptual":
            # squeeze CIE lightness evenly into the printable range, then invert Beer-
            # Lambert: in a ~5:1 lit range every tone step stays a visible step (Cura's
            # linear squeeze leaves the shadows within a few % of each other)
            lo = lightness(t_min_rel)
            mapped = inverse_lightness(lo + (100 - lo) * lightness(y) / 100)
        elif self.model == "transmittance":
            mapped = t_min_rel + (1 - t_min_rel) * y               # Cura's mapping, exactly
        else:
            raise ValueError(f"model must be perceptual, transmittance or linear, got {self.model!r}")
        return self.min_t + np.log(np.clip(mapped, t_min_rel, 1)) / np.log(self.tau)

    def _grid_xz(self):
        x = np.arange(self.nx) * self.res - self.width / 2
        z = np.arange(self.ny) * self.res
        return np.meshgrid(x, z)

    def _thickness(self):
        t = self.t_pic
        if not self.border:
            return t
        X, Z = self._grid_xz()
        if self.outline == "rect":
            # square frame bands at the sides and bottom; above the picture the top band
            # rises from the picture's own edge thickness at 1:CHAMFER (40 deg from
            # vertical) to frame_t, so its underside never overhangs and the picture
            # keeps its full area and tone
            if self.shape == "cylinder":
                d = Z
            else:
                d = np.minimum.reduce([X + self.width / 2, self.width / 2 - X, Z])
            # the bands are exactly frame_t, even where the picture is thicker: a panel
            # that slides into slots needs edges that fit the slot (frame_t < max_t)
            z_edge = (self.ny - 1 - self.pad[3]) * self.res
            out = np.where(Z > z_edge, np.minimum(self.frame_t, t + (Z - z_edge) / CHAMFER), t)
            return np.where(d <= self.border, self.frame_t, out)
        import shapely
        poly = _outline_polygon(self.outline, self.width, self.height, self.corner)
        d = shapely.distance(poly.boundary, shapely.points(X.ravel(), Z.ravel())).reshape(X.shape)
        band = d <= self.border
        # shaped outlines: wherever the band lies above the picture its underside faces
        # down, so chamfer down from it into the picture at 1:CHAMFER
        R = np.arange(self.ny)[:, None] * np.ones((1, self.nx))
        above = np.where(band, R, np.inf)
        nearest = np.minimum.accumulate(above[::-1], axis=0)[::-1]    # nearest band row at or above
        frame = np.where(band, self.frame_t, self.frame_t - (nearest - R) * self.res / CHAMFER)
        return np.maximum(t, np.nan_to_num(frame, neginf=0.0))

    # ---- geometry ---------------------------------------------------------------------
    def _surface(self, depth):
        """xyz of the grid at `depth` mm in from the smooth face."""
        X, Z = self._grid_xz()
        u = X + self.width / 2
        if self.shape == "flat":
            return np.stack([X, np.broadcast_to(depth, X.shape), Z], -1)
        theta = math.radians(self.curve) if self.shape == "arc" else 2 * math.pi
        R = self.width / theta
        if self.shape == "cylinder":            # last column would duplicate the first
            R = self.width / (2 * math.pi)
        phi = (self.width / 2 - u) / R          # viewer outside: image reads left to right
        r = R - depth
        return np.stack([r * np.sin(phi), r * np.cos(phi), Z], -1)

    def solid(self, simplify=0.025):
        ny, nx = self.ny, self.nx
        wrap = self.shape == "cylinder"
        cols = nx - 1 if wrap else nx           # cylinder: column nx-1 sits on column 0
        back = self._surface(0.0)[:, :cols]
        front = self._surface(self.t)[:, :cols]
        verts = np.r_[back.reshape(-1, 3), front.reshape(-1, 3)]
        n = ny * cols
        idx = np.arange(n).reshape(ny, cols)
        nxt = np.roll(idx, -1, axis=1) if wrap else idx[:, 1:]
        cur = idx if wrap else idx[:, :-1]
        a, b = cur[:-1].ravel(), nxt[:-1].ravel()
        c, d = nxt[1:].ravel(), cur[1:].ravel()
        quads_b = np.r_[np.c_[a, c, b], np.c_[a, d, c]]          # back faces
        quads_f = np.r_[np.c_[a, b, c], np.c_[a, c, d]] + n      # front faces, opposite winding
        sides = []
        if wrap:
            rings = [(idx[0], True), (idx[-1], False)]
            for ring, bottom in rings:
                r0, r1 = ring, np.roll(ring, -1)
                q = np.c_[r0, r1, r1 + n] if bottom else np.c_[r0, r1 + n, r1]
                q2 = np.c_[r0, r1 + n, r0 + n] if bottom else np.c_[r0, r0 + n, r1 + n]
                sides += [q, q2]
        else:
            ring = np.r_[idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]]
            r0, r1 = ring, np.roll(ring, -1)
            sides += [np.c_[r0, r1, r1 + n], np.c_[r0, r1 + n, r0 + n]]
        tris = np.r_[quads_b, quads_f, *sides]
        # orient outward: flip everything if the signed volume comes out negative
        v = verts[tris]
        vol = np.einsum("ij,ij->i", v[:, 0], np.cross(v[:, 1], v[:, 2])).sum() / 6
        if vol < 0:
            tris = tris[:, ::-1]
        m = Manifold(Mesh(vert_properties=verts.astype(np.float32),
                          tri_verts=np.ascontiguousarray(tris, dtype=np.uint32)))
        if m.is_empty():
            raise RuntimeError(f"lithophane mesh is not a valid solid ({m.status()})")
        if self.shape == "flat" and self.outline != "rect":
            m = m ^ self._outline_prism()
        if self.shape == "flat" and self.stand:
            m = m + self._stand()
        if simplify:
            m = m.simplify(simplify)
        return m

    def _outline_prism(self):
        poly = _outline_polygon(self.outline, self.width, self.height, self.corner)
        from shapely.geometry.polygon import orient
        cs = CrossSection([np.asarray(orient(poly, 1.0).exterior.coords)[:-1]])
        depth = self.frame_t + self.max_t + 10
        # extrude along z, then turn (+90 about x maps z to -y) so it runs through the panel
        return Manifold.extrude(cs, depth).translate((0, 0, -depth + 5)).rotate((90, 0, 0))

    def _stand(self):
        """Foot under the panel: `stand` mm deep in y, centred on the panel's mid wall."""
        foot_h = 4.0
        w = self.width if self.outline == "rect" else self.width * 0.6
        mid = self.frame_t / 2
        foot = Manifold.cube((w, self.stand, foot_h)).translate((-w / 2, mid - self.stand / 2, 0))
        return foot

    # ---- simulation -------------------------------------------------------------------
    def backlit(self, scatter=None):
        """Relative brightness on a light box: Beer-Lambert through the local wall,
        then sideways scattering ~ `scatter` x the mean wall. 1.0 = thinnest wall."""
        light = self.tau ** (self.t - self.min_t)
        sigma = (SCATTER if scatter is None else scatter) * float(np.mean(self.t_pic)) / self.res
        return np.clip(_gauss(light, sigma), 0, 1)

    def backlit_png(self, path, title=None, px=900):
        """Target tones next to the simulated backlit print, warm LED light."""
        warm = np.array([255, 238, 210]) / 255.0
        sim = np.flipud(self.backlit())
        tgt = np.flipud(self.target)
        if self.border:
            l, r, bt, tp = self.pad                       # frame = everything outside the picture
            m = np.ones_like(self.t, bool)
            m[bt:self.ny - tp, l:self.nx - r] = False
            if self.outline != "rect":
                m = self.t >= self.frame_t - 1e-6
            mask = np.flipud(m)
            tgt = np.where(mask, 0.0, tgt)
        def tile(a):
            rgb = linear_to_srgb(a[..., None] * warm) * 255
            im = Image.fromarray(rgb.astype(np.uint8))
            s = px / max(im.size)
            return im.resize((max(1, int(im.size[0] * s)), max(1, int(im.size[1] * s))), Image.LANCZOS)
        a, b = tile(tgt), tile(sim)
        pad, head = 24, 56
        W = a.size[0] + b.size[0] + 3 * pad
        H = max(a.size[1], b.size[1]) + head + 2 * pad
        sheet = Image.new("RGB", (W, H), (34, 34, 38))
        sheet.paste(a, (pad, head + pad))
        sheet.paste(b, (2 * pad + a.size[0], head + pad))
        dr = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except OSError:
            font = ImageFont.load_default()
        dr.text((pad, 12), title or self.path.name, fill=(240, 240, 240), font=font)
        dr.text((pad, head - 22), "target tones", fill=(190, 190, 190), font=font)
        dr.text((2 * pad + a.size[0], head - 22),
                f"simulated on a light box (tau {self.tau:.2f}/mm, {self.min_t:g}-{self.max_t:g} mm)",
                fill=(190, 190, 190), font=font)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        sheet.save(path)
        return Path(path)

    def summary(self):
        pic = self.t_pic
        contrast = self.tau ** (self.min_t - self.max_t)
        return [f"litho    {self.shape}, {self.width:.1f} x {self.height:.1f} mm, grid {self.nx} x {self.ny} "
                f"at {self.res:.2f} mm",
                f"litho    wall {pic.min():.2f}-{pic.max():.2f} mm ({self.model}, tau {self.tau:.2f}/mm), "
                f"lit contrast {contrast:.0f}:1, frame {self.frame_t:g} mm x {self.border:g} mm"]


# ---- model-script glue ----------------------------------------------------------------

def litho_params(image, **over):
    """Default PARAMS for a lithophane model; every Lithophane option is tunable."""
    p = dict(image=str(image), width=100.0, height=0.0, shape="flat", curve=120.0,
             min_t=0.6, max_t=3.0, model="perceptual", transmittance=0.5,
             border=3.0, frame_t=0.0, outline="rect", corner=6.0, stand=0.0, res=0.2,
             levels=0.5, gamma=1.0, sharpen=0.6, smooth=0, invert=False, mirror=False,
             nozzle=0.4, crop=(0.0, 0.0, 1.0, 1.0), clarity=0.0, clarity_mm=3.0, match=0,
             detail="open")
    p.update(over)
    return p


_KEYS = ("width", "height", "shape", "curve", "min_t", "max_t", "model", "transmittance",
         "border", "frame_t", "outline", "corner", "stand", "res", "levels", "gamma",
         "sharpen", "smooth", "invert", "mirror", "nozzle", "crop", "clarity", "clarity_mm",
         "match", "detail")


@lru_cache(maxsize=4)
def _cached(image, items):
    kw = dict(items)
    kw["height"] = kw["height"] or None
    kw["frame_t"] = kw["frame_t"] or None
    return Lithophane(image, **kw)


def lithophane_of(p):
    return _cached(p.image, tuple((k, getattr(p, k)) for k in _KEYS))


def litho_build(p):
    L = lithophane_of(p)
    for line in L.summary():
        print("  " + line)
    return L.solid()


def litho_checks(p):
    """Size, one body, the frame and the thinnest picture wall where they should be."""
    from . import checks as C
    L = lithophane_of(p)
    out = [C.single_body(), C.custom("picture wall >= min_t", _wall_check(L))]
    if L.shape == "flat":
        out.insert(0, C.dims(x=L.width, z=L.height))
        if L.border and L.outline != "heart":
            # frame present at full thickness in the bottom and top bands
            y = L.frame_t - 0.2
            out.append(C.solid((0, y, L.border / 2), (0, y, L.height - L.border / 2)))
    elif L.shape == "arc":
        out.insert(0, C.dims(z=L.height))
    else:
        D = L.width / math.pi
        out.insert(0, C.dims(x=(D - 0.6, D + 0.6), z=L.height))
    return out


def _wall_check(L):
    def fn(ctx):
        lo = float(L.t_pic.min())
        return lo >= L.min_t - 0.01, f"thinnest picture wall {lo:.2f} mm (min_t {L.min_t:g})"
    return fn


def litho_extras(p, out, name):
    """Extra build output: <name>_backlit.png (target vs simulated light box view)."""
    L = lithophane_of(p)
    png = L.backlit_png(Path(out) / f"{name}_backlit.png", title=f"{name}: {Path(p.image).name}")
    return [png], L.summary()


# ---- calibration ----------------------------------------------------------------------

def fit_transmittance(photo, steps, crop=None, axis="x"):
    """tau per mm from a backlit photo of the calibration wedge, cropped to the steps.

    `steps` are the step thicknesses in order along `axis` (left to right or bottom to
    top). Each band's median linear luminance is fitted to log(I) = a + t*log(tau)."""
    im = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    if crop:
        im = im.crop(crop)
    y = srgb_to_linear(np.asarray(im, float) / 255.0) @ np.array([0.2126, 0.7152, 0.0722])
    if axis == "y":
        y = np.flipud(y).T
    n = len(steps)
    w = y.shape[1] / n
    vals = []
    for i in range(n):
        band = y[:, int(i * w + 0.2 * w):int((i + 1) * w - 0.2 * w)]
        band = band[int(0.2 * band.shape[0]):int(0.8 * band.shape[0])]
        vals.append(float(np.median(band)))
    vals = np.array(vals)
    t = np.asarray(steps, float)
    ok = (vals > 0.003) & (vals < 0.995)        # drop clipped steps
    if ok.sum() < 3:
        raise ValueError("fewer than 3 usable steps (photo over- or under-exposed?)")
    slope, icpt = np.polyfit(t[ok], np.log(vals[ok]), 1)
    tau = float(np.exp(slope))
    fit = np.exp(icpt + slope * t)
    return tau, vals, fit, ok
