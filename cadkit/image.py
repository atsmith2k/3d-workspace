"""Pictures in, geometry out: trace a logo or sketch into an outline, load an SVG, or
turn a photo into a heightmap relief (lithophane, stamped texture).

    from cadkit.image import *
    logo = trace("logo.png", width=60)            # CrossSection, 60 mm wide, centred
    art = svg_shape("drawing.svg", width=80)      # CrossSection from an SVG's paths
    relief = heightmap("photo.jpg", width=100, height=3, base=1)   # Manifold

CrossSections plug into cadkit.relief (extrude, grow, drafted, mirror_x...) and
build123d models can use `import_svg` directly. `cad trace image.png` runs the tracer
and writes the SVG plus an outline preview so the result can be checked first.
"""
import math
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold, Mesh
from PIL import Image, ImageFilter, ImageOps

__all__ = ["trace", "svg_shape", "heightmap", "to_binary"]


def to_binary(path, threshold=128, invert=False, max_px=1024):
    """Grayscale PIL image thresholded to black shapes on white. `invert` for light
    artwork on a dark background. Transparent pixels count as background."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im.convert("RGBA"))
        im = bg
    im = ImageOps.grayscale(im.convert("RGB"))
    if max(im.size) > max_px:
        im.thumbnail((max_px, max_px), Image.LANCZOS)
    if invert:
        im = ImageOps.invert(im)
    return im.point(lambda v: 0 if v < threshold else 255, "L")


def trace(path, width=None, height=None, threshold=128, invert=False, smooth=True,
          min_area=4.0, out_svg=None):
    """Trace the dark shapes of an image into a CrossSection scaled to `width` (or
    `height`) mm and centred on the origin. Holes (counters in letters) are kept.
    `min_area` drops specks smaller than that many mm2. Needs the vtracer package."""
    import vtracer
    bw = to_binary(path, threshold, invert)
    svg = vtracer.convert_pixels_to_svg(
        list(bw.convert("RGBA").getdata()), bw.size, colormode="binary",
        mode="spline" if smooth else "polygon", filter_speckle=4,
        corner_threshold=60, length_threshold=4.0, splice_threshold=45, path_precision=3)
    if out_svg:
        Path(out_svg).write_text(svg, encoding="utf-8")
    return _svg_text_to_cs(svg, width, height, min_area, bw.size)


def svg_shape(path, width=None, height=None, min_area=0.5, samples_per_mm=1.0):
    """CrossSection from the filled paths of an SVG file, scaled to `width` (or
    `height`) mm and centred. Even-odd fill, so nested paths become holes."""
    text = Path(path).read_text(encoding="utf-8")
    return _svg_text_to_cs(text, width, height, min_area, None, samples_per_mm)


def _svg_text_to_cs(svg_text, width, height, min_area, px_size, samples_per_mm=1.0):
    from svgpathtools import parse_path
    import re
    polys = []
    for d in re.findall(r'\bd="([^"]+)"', svg_text):
        try:
            p = parse_path(d)
        except Exception:
            continue
        for sub in p.continuous_subpaths():
            L = sub.length()
            if L <= 0:
                continue
            n = max(12, int(L * 0.5))
            pts = [sub.point(t) for t in np.linspace(0, 1, n, endpoint=False)]
            polys.append([(z.real, -z.imag) for z in pts])   # SVG y is down
    if not polys:
        raise ValueError("no paths found in the SVG")
    pts = np.array([q for poly in polys for q in poly])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    span = hi - lo
    if width:
        s = width / span[0]
    elif height:
        s = height / span[1]
    else:
        s = 1.0
    c = (lo + hi) / 2
    scaled = [[((x - c[0]) * s, (y - c[1]) * s) for x, y in poly] for poly in polys]
    cs = CrossSection(scaled, FillRule.EvenOdd)
    if min_area:
        keep = [p for p in cs.decompose() if p.area() >= min_area]
        cs = CrossSection.compose(keep) if keep else cs
    return cs.simplify(0.02)


def heightmap(path, width, height, base=1.0, invert=False, blur=0.0, max_px=400):
    """Relief slab: a flat base `base` mm thick with the image's brightness raised up
    to `height` mm on top (white = highest; `invert` for a lithophane, where dark
    areas should be thick). Returns a Manifold sitting on z=0, centred in XY."""
    im = ImageOps.grayscale(Image.open(path).convert("RGB"))
    if max(im.size) > max_px:
        im.thumbnail((max_px, max_px), Image.LANCZOS)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    z = np.asarray(im, float) / 255.0
    if invert:
        z = 1 - z
    z = np.flipud(z)                      # image row 0 is the top; our +y is up
    ny, nx = z.shape
    px = width / (nx - 1)
    xs = (np.arange(nx) - (nx - 1) / 2) * px
    ys = (np.arange(ny) - (ny - 1) / 2) * px
    X, Y = np.meshgrid(xs, ys)
    top = np.c_[X.ravel(), Y.ravel(), base + z.ravel() * height]
    idx = np.arange(nx * ny).reshape(ny, nx)
    a, b, c, d = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    tris = np.r_[np.c_[a, b, c], np.c_[a, c, d]]
    # perimeter ring (counter-clockwise seen from above), bottom copies, centre vertex
    ring = np.r_[idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]]
    n_top = len(top)
    bottom = top[ring].copy()
    bottom[:, 2] = 0.0
    centre = np.array([[0.0, 0.0, 0.0]])
    verts = np.r_[top, bottom, centre]
    m = len(ring)
    bi = n_top + np.arange(m)
    ci = n_top + m
    walls = []
    for k in range(m):
        t0, t1 = ring[k], ring[(k + 1) % m]
        b0, b1 = bi[k], bi[(k + 1) % m]
        walls += [[t0, b0, b1], [t0, b1, t1]]           # outward-facing quads
        walls.append([ci, b1, b0])                       # bottom fan, facing down
    tris = np.r_[tris, np.array(walls)]
    return Manifold(Mesh(vert_properties=verts.astype(np.float32), tri_verts=tris.astype(np.uint32)))
