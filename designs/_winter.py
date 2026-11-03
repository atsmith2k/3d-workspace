"""Shared by the Frost & Fir winter / Christmas collection (designs/winter_*.py).

One thread palette for all fifteen designs, every colour an exact Brother (PEC) thread
so the chart names a real spool: a buyer of the bundle needs one set of cones.
Each design draws its art in a 100 mm nominal space and calls `fit(d, p.size, hoop)`,
which rebuilds it at the requested size (re-stitched, not a scaled stitch file).
Sizing and the standard checks are the fall collection's (`_fall.fit`,
`_fall.standard_checks`), so both collections ship the same way.
"""
from _fall import NOMINAL, fit, standard_checks  # noqa: F401  (re-exported)

COLLECTION = "frost-and-fir"
COLLECTION_TITLE = "Frost & Fir"

# name: (hex, Brother thread name)
PALETTE = {
    "red": ("#ed171f", "Red"),
    "berry": ("#b54b64", "Amber Red"),
    "pine": ("#003822", "Deep Green"),
    "green": ("#00673e", "Emerald Green"),
    "leaf": ("#2f7e20", "Moss Green"),
    "white": ("#f0f0f0", "White"),
    "ice": ("#a8deeb", "Light Blue"),
    "sky": ("#2584bb", "Sky Blue"),
    "navy": ("#0e1f7c", "Prussian Blue"),
    "gold": ("#e8a900", "Deep Gold"),
    "pink": ("#f993bc", "Pink"),
    "blush": ("#fcbbc5", "Salmon Pink"),
    "ginger": ("#b27624", "Light Brown"),
    "cocoa": ("#2a1301", "Dark Brown"),
    "tan": ("#d0a660", "Khaki"),
    "cream": ("#efe3b9", "Beige"),
    "silver": ("#a8a8a8", "Silver"),
    "black": ("#000000", "Black"),
    "carrot": ("#fe9e32", "Tangerine"),
}
C_ = {k: v[0] for k, v in PALETTE.items()}

# Sizes every design ships in: (label, hoop, longest side in mm)
SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]

PRICE_USD = 3.99
COMMERCIAL_PRICE_USD = 12.99


def sew_bow(d, bow, color, knot_color, under=None):
    """Sew a `motifs.bow` (already placed): tails, then loops, then the knot on top,
    each knocked out under what follows, fill angles following the ribbon."""
    from cadkit.stitch import knockout
    lo, ro, knot, lt, rt = bow
    d.fill(knockout(lt, lo, ro, knot), color, angle=75, name="bow tail")
    d.fill(knockout(rt, lo, ro, knot), color, angle=105, name="bow tail")
    d.fill(knockout(lo, knot), color, angle=150, name="bow loop")
    d.fill(knockout(ro, knot), color, angle=30, name="bow loop")
    d.fill(knot, knot_color, angle=90, name="bow knot")


def holly_sprig(x, y, deg=0.0, length=16.0):
    """Two holly leaves in a V and three berries at (x, y), turned `deg`:
    (leaves [shapes], vein paths, berries [circles])."""
    import math

    import numpy as np
    from cadkit.stitch import circle, move, rotate
    from cadkit.stitch import motifs as M
    leaves, veins = [], []
    for a in (deg + 35, deg + 145):
        leaf = move(M.holly_leaf(length, length * 0.46, spikes=3), 1.5, 0)
        leaves.append(move(rotate(leaf, a, origin=(0, 0)), x, y))
        r = math.radians(a)
        rot = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
        veins.append((M.holly_vein(length) + np.array([1.5, 0])) @ rot.T + np.array([x, y]))
    berries = [circle(x + 2.4 * math.cos(math.radians(deg - 90 + 120 * k)),
                      y + 2.4 * math.sin(math.radians(deg - 90 + 120 * k)), 2.1) for k in range(3)]
    return leaves, veins, berries


def product(title, summary, tags, description, mockups=("tshirt", "tote")):
    """A PRODUCT dict for a Frost & Fir design (collection, prices and base tags filled in)."""
    base = ["christmas embroidery design", "winter embroidery", "machine embroidery", "holiday"]
    return dict(title=title, summary=summary, tags=list(dict.fromkeys(list(tags) + base)),
                collection=COLLECTION, mockups=list(mockups), description=description,
                price_usd=PRICE_USD, commercial_price_usd=COMMERCIAL_PRICE_USD)
