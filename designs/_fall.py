"""Shared by the Harvest Hollow fall collection (designs/fall_*.py).

One thread palette for all ten designs, every colour an exact Brother (PEC) thread so
the chart names a real spool: a buyer of the bundle needs one set of 13 cones.
Each design draws its art in a 100 mm nominal space and calls `fit(d, p.size)`,
which rebuilds it at the requested size (re-stitched, not a scaled stitch file).
"""
from cadkit.stitch import checks as C

COLLECTION = "harvest-hollow"
COLLECTION_TITLE = "Harvest Hollow"

# name: (hex, Brother thread name)
PALETTE = {
    "rust": ("#d15400", "Clay Brown"),
    "pumpkin": ("#feb343", "Pumpkin"),
    "mustard": ("#e8a900", "Deep Gold"),
    "caramel": ("#b27624", "Light Brown"),
    "bark": ("#2a1301", "Dark Brown"),
    "olive": ("#435607", "Dark Olive"),
    "moss": ("#7d6f00", "Russet Brown"),
    "wheat": ("#d0a660", "Khaki"),
    "cream": ("#efe3b9", "Beige"),
    "white": ("#f0f0f0", "White"),
    "charcoal": ("#293133", "Dark Gray"),
    "cranberry": ("#b54b64", "Amber Red"),
    "red": ("#ed171f", "Red"),
}
C_ = {k: v[0] for k, v in PALETTE.items()}

# Sizes every design ships in: (label, hoop, longest side in mm)
SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]

NOMINAL = 100.0


def fit(d, size, hoop_wh=None):
    """Scale the nominal art so its longest side is `size` mm (or the hoop field less
    5 mm a side, whichever is smaller) and centre it on the origin. Machines rotate a
    design 90 deg on screen, so a wide design may use the hoop's long side."""
    x0, y0, x1, y1 = d.bounds()
    w, h = x1 - x0, y1 - y0
    k = size / max(w, h)
    if hoop_wh:
        k = min(k, (max(hoop_wh) - 10) / max(w, h), (min(hoop_wh) - 10) / min(w, h))
    return d.scaled(k, -(x0 + x1) / 2 * k, -(y0 + y1) / 2 * k)


def standard_checks(p, n_colors, max_stitches, between_mm2=None):
    """What every collection design must pass, at every size."""
    return [
        C.size(w=(20, p.size + 1.5), h=(20, p.size + 1.5)),
        C.hoop(),
        C.colors(n_colors),
        C.max_density(3.5),
        C.long_stitches(7.0),
        C.min_feature(1.0),
        C.coverage(1.0, between_mm2),
        C.stitches(max=max_stitches * (p.size / 95.0) ** 2),
        C.jump_threads(3.0, 0),
    ]
