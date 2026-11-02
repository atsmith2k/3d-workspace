"""Artwork to embroidery: turn an illustration or photo into thread tones the way a
digitiser works from a reference. The subject is cut out of its background, its colours
are reduced to a few threads, each thread's area is cleaned up (speckle merged into its
neighbours, edges smoothed) and vectorised, and the hair / grain direction is read from
the image so every fill can run with it.

    art = Artwork("bear.png", width=95)                 # mm across the subject
    for tone in art.tones(8):                           # light to dark
        for piece, angle in art.by_flow(tone.shape, cell=7):
            d.fill(piece, tone.color, angle=angle)

Coordinates are mm, Y up, the subject's bounding box centred on the origin, so the
shapes combine with everything else in a design. `art.to_mm(x, y)` maps image pixels
(original image, y down) to the same frame, for placing things against the artwork.
"""
import re
from dataclasses import dataclass

import numpy as np
from PIL import Image
from scipy import ndimage
from shapely.geometry import Polygon
from shapely.ops import unary_union

from .shapes import polygons_of


@dataclass
class Tone:
    color: str          # '#rrggbb', the cluster's mean colour
    shape: object       # shapely (Multi)Polygon, mm
    lightness: float    # CIE L*, 0..100
    pixels: int


def _lab(rgb):
    """sRGB 0..255 (N, 3) -> CIE L*a*b* (D65)."""
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.c_[116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])]


class Artwork:
    def __init__(self, path, width, upscale=3, alpha=128, background=None, crop=None):
        """`width`: mm across the subject. `upscale` resamples the image first so traced
        edges come out smooth. The subject is every opaque pixel that is not near-white;
        `background(rgb, alpha) -> bool mask` overrides that. `crop` = (x0, y0, x1, y1)
        in original pixels keeps only that part of the image."""
        im = Image.open(path).convert("RGBA")
        if crop:
            im = im.crop(crop)
        self.src_size = im.size
        self.up = upscale
        im = im.resize((im.size[0] * upscale, im.size[1] * upscale), Image.LANCZOS)
        a = np.asarray(im).astype(float)
        self.rgb, self.alpha = a[..., :3], a[..., 3]
        if background is not None:
            self.mask = ~background(self.rgb, self.alpha)
        else:
            self.mask = (self.alpha > alpha) & ~(self.rgb.min(-1) > 228)
        ys, xs = np.nonzero(self.mask)
        self.x0, self.x1, self.y0, self.y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        self.mm = width / (self.x1 - self.x0)            # mm per upscaled pixel
        self.cx, self.cy = (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2
        self._crop = crop
        self._flow = None

    # ---------- coordinates ----------
    def px_to_mm(self, x, y):
        """Upscaled pixel -> mm (Y up)."""
        return (np.asarray(x) - self.cx) * self.mm, (self.cy - np.asarray(y)) * self.mm

    def to_mm(self, x, y):
        """Original image pixel -> mm, for placing things against the artwork."""
        ox, oy = (self._crop[:2] if self._crop else (0, 0))
        return self.px_to_mm((np.asarray(x) - ox) * self.up, (np.asarray(y) - oy) * self.up)

    @property
    def size(self):
        return (self.x1 - self.x0) * self.mm, (self.y1 - self.y0) * self.mm

    # ---------- tones ----------
    def labels(self, k=8, smooth=2, min_area=3.0, seed=0, colors=None, min_width=1.0):
        """Label map (-1 = background) of `k` colour clusters (k-means in Lab), mode
        filtered `smooth` times, parts of a tone narrower than `min_width` mm handed to
        the neighbouring tones (a fill cannot sew them), and islands under `min_area`
        mm2 merged into the neighbour they touch most. `colors` (hex list) fixes the
        palette instead."""
        m = self.mask
        px = self.rgb[m]
        if colors:
            centres = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in colors], float)
            d = ((_lab(px)[:, None, :] - _lab(centres)[None]) ** 2).sum(-1)
            lab_px = d.argmin(1)
        else:
            from sklearn.cluster import KMeans
            L = _lab(px)
            rng = np.random.default_rng(seed)
            sample = L[rng.choice(len(L), min(len(L), 60000), replace=False)]
            km = KMeans(k, n_init=4, random_state=seed).fit(sample)
            lab_px = km.predict(L)
            centres = np.array([px[lab_px == i].mean(0) if (lab_px == i).any() else [0, 0, 0] for i in range(k)])
        lab = np.full(m.shape, -1, int)
        lab[m] = lab_px
        n = len(centres)
        for _ in range(smooth):                                  # majority (mode) filter
            votes = np.stack([ndimage.uniform_filter((lab == i).astype(np.float32), 5) for i in range(n)])
            new = votes.argmax(0)
            lab = np.where(m, new, -1)
        if min_width:                                            # no tone thinner than min_width
            r = max(1, int(round(min_width / 2 / self.mm)))
            disk = np.hypot(*np.mgrid[-r:r + 1, -r:r + 1]) <= r
            for _ in range(2):
                thin = np.zeros_like(m)
                for i in range(n):
                    region = lab == i
                    thin |= region & ~ndimage.binary_opening(region, structure=disk)
                if not thin.any():
                    break
                keep = np.where(thin, -1, lab)
                votes = np.stack([ndimage.uniform_filter((keep == i).astype(np.float32), 2 * r + 3)
                                  for i in range(n)])
                lab = np.where(thin & m, votes.argmax(0), lab)
        min_px = min_area / self.mm ** 2
        for _ in range(3):                                       # merge specks into neighbours
            changed = False
            for i in range(n):
                comp, nc = ndimage.label(lab == i)
                if not nc:
                    continue
                sizes = ndimage.sum(np.ones_like(comp), comp, range(1, nc + 1))
                slices = ndimage.find_objects(comp)
                for j in np.nonzero(sizes < min_px)[0]:
                    sl = tuple(slice(max(0, s.start - 2), s.stop + 2) for s in slices[j])
                    piece = comp[sl] == j + 1
                    ring = ndimage.binary_dilation(piece, iterations=2) & ~piece
                    around = lab[sl][ring]
                    around = around[around != i]
                    if len(around):
                        vals, cnt = np.unique(around, return_counts=True)
                        lab[sl][piece] = vals[cnt.argmax()]
                        changed = True
            if not changed:
                break
        self._centres = centres
        return lab, centres

    def tones(self, k=8, smooth=2, min_area=3.0, seed=0, colors=None, overlap=0.25, min_width=1.0):
        """Thread tones in sewing order, lightest first: each a Tone with its colour and
        fill shape. Each tone reaches `overlap` mm under the tones sewn after it (never
        over the ones before), so no fabric shows between them and nothing is doubled
        more than that strip."""
        lab, centres = self.labels(k, smooth, min_area, seed, colors, min_width)
        out = []
        for i, c in enumerate(centres):
            region = lab == i
            if region.sum() == 0:
                continue
            shape = self.vectorise(region)
            if shape.is_empty:
                continue
            hexc = "#%02x%02x%02x" % tuple(int(round(v)) for v in c)
            out.append(Tone(hexc, shape, float(_lab(c[None])[0, 0]), int(region.sum())))
        out.sort(key=lambda t: -t.lightness)
        if overlap:
            body = self.outline().buffer(0.05)
            earlier = Polygon()
            for t in out:
                raw = t.shape
                t.shape = raw.buffer(overlap, join_style="round").intersection(body).difference(earlier).buffer(0)
                earlier = earlier.union(raw)
        return out

    def outline(self):
        if not hasattr(self, "_outline"):
            m = ndimage.binary_opening(self.mask, iterations=1)
            self._outline = self.vectorise(m)
        return self._outline

    def vectorise(self, region):
        """Boolean pixel mask -> shapely shape in mm (holes kept), smoothed by vtracer."""
        import vtracer
        h, w = region.shape
        img = np.where(region, 0, 255).astype(np.uint8)
        rgba = np.dstack([img, img, img, np.full_like(img, 255)])
        svg = vtracer.convert_pixels_to_svg([tuple(p) for p in rgba.reshape(-1, 4)], (w, h),
                                            colormode="binary", mode="spline", filter_speckle=2,
                                            corner_threshold=60, length_threshold=3.5,
                                            splice_threshold=45, path_precision=2)
        from svgpathtools import parse_path
        polys = []
        for m_ in re.finditer(r'<path[^>]*?\bd="([^"]+)"[^>]*?>', svg):
            tag = m_.group(0)
            t = re.search(r'translate\(([-\d.]+)[ ,]+([-\d.]+)\)', tag)
            tx, ty = (float(t.group(1)), float(t.group(2))) if t else (0.0, 0.0)
            for sub in parse_path(m_.group(1)).continuous_subpaths():
                L = sub.length()
                if L <= 0:
                    continue
                n = max(10, int(L * 0.6))
                z = np.array([sub.point(s) for s in np.linspace(0, 1, n, endpoint=False)])
                x, y = self.px_to_mm(z.real + tx, z.imag + ty)
                p = Polygon(np.c_[x, y]).buffer(0)
                if not p.is_empty:
                    polys.append(p)
        # even-odd: nested rings are holes
        shape = Polygon()
        for p in sorted(polys, key=lambda q: -q.area):
            shape = shape.symmetric_difference(p)
        return shape.buffer(0)

    # ---------- direction of the hair / grain ----------
    def flow(self, sigma=1.2, rho=5.0):
        """(angle_deg, coherence) per upscaled pixel: the direction strokes run in the
        image (structure tensor; perpendicular to the luminance gradient), in design
        convention (degrees counter-clockwise from +X, Y up)."""
        if self._flow is None:
            lum = self.rgb @ np.array([0.299, 0.587, 0.114])
            s = sigma * self.up
            gx = ndimage.gaussian_filter(lum, s, order=(0, 1))
            gy = ndimage.gaussian_filter(lum, s, order=(1, 0))
            r = rho * self.up
            jxx = ndimage.gaussian_filter(gx * gx, r)
            jyy = ndimage.gaussian_filter(gy * gy, r)
            jxy = ndimage.gaussian_filter(gx * gy, r)
            theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy)        # gradient direction, image axes
            hair = theta + np.pi / 2                             # strokes run across the gradient
            coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
            self._flow = (np.degrees(-hair), coh)               # image y is down: flip
        return self._flow

    def angle_in(self, shape, default=90.0):
        """Coherence-weighted mean hair direction inside a shape (degrees, mod 180)."""
        ang, coh = self.flow()
        x0, y0, x1, y1 = shape.bounds
        c0 = int(np.clip(x0 / self.mm + self.cx, 0, ang.shape[1] - 1))
        c1 = int(np.clip(x1 / self.mm + self.cx, 0, ang.shape[1] - 1)) + 1
        r0 = int(np.clip(self.cy - y1 / self.mm, 0, ang.shape[0] - 1))
        r1 = int(np.clip(self.cy - y0 / self.mm, 0, ang.shape[0] - 1)) + 1
        from shapely import contains_xy
        yy, xx = np.mgrid[r0:r1, c0:c1]
        mx, my = self.px_to_mm(xx + 0.5, yy + 0.5)
        inside = contains_xy(shape, mx, my)
        if not inside.any():
            return default
        a = np.radians(ang[r0:r1, c0:c1][inside]) * 2
        w = coh[r0:r1, c0:c1][inside] + 1e-3
        return float(np.degrees(np.arctan2((w * np.sin(a)).sum(), (w * np.cos(a)).sum()) / 2)) % 180

    def by_flow(self, shape, cell=7.0, min_area=1.5, merge_deg=12.0):
        """Split a shape into roughly `cell` mm patches, each with the local hair
        direction: [(piece, angle)]. Neighbouring patches whose angles differ by less
        than `merge_deg` are joined (fewer fills, fewer trims)."""
        from shapely.geometry import box
        x0, y0, x1, y1 = shape.bounds
        pieces = []
        for gx in np.arange(x0, x1, cell):
            for gy in np.arange(y0, y1, cell):
                piece = shape.intersection(box(gx, gy, gx + cell, gy + cell))
                for q in polygons_of(piece):
                    if q.area >= 0.05:
                        pieces.append(q)
        # tiny pieces join their biggest neighbour
        big = [p for p in pieces if p.area >= min_area]
        small = [p for p in pieces if p.area < min_area]
        for s in small:
            near = [i for i, b in enumerate(big) if b.distance(s) < 0.05]
            if near:
                i = max(near, key=lambda i: big[i].area)
                big[i] = big[i].union(s)
        groups = [(p, self.angle_in(p)) for p in big]
        merged = True
        while merged:                                        # join similar neighbours
            merged = False
            for i in range(len(groups)):
                for j in range(i + 1, len(groups)):
                    (a, aa), (b, ab) = groups[i], groups[j]
                    diff = abs((aa - ab + 90) % 180 - 90)
                    if diff < merge_deg and a.distance(b) < 0.05:
                        u = unary_union([a, b])
                        groups[i] = (u, self.angle_in(u))
                        groups.pop(j)
                        merged = True
                        break
                if merged:
                    break
        return groups
