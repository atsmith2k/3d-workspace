"""Shared by the Festival of Lights Hanukkah collection (designs/lights_*.py).

Twelve Hanukkah machine-embroidery designs picked from the 2026-11 market research
(docs/research/2026-11-hanukkah.md). The Hearth & Snow menorah (`hearth_menorah`) was the
shop's only Hanukkah design; none of these repeats it. One look across the set: navy,
royal and sky blue, white and silver with gold accents and warm flame colours, plus the
food colours (latke brown, jam red) the snack designs need. Every colour is an exact
Brother (PEC) thread from the winter palettes, so buyers of those need no new cones.

All lettering is English (block letters from `cadkit.stitch.lettering` or `d.text`);
no Hebrew script, no religious text, no licensed characters. Each design draws its art
in a 100 mm nominal space and calls `fit(d, p.size, hoop_for(p.size))`. Sizing and the
standard checks are the fall collection's (`_fall.fit`, `_fall.standard_checks`).

New designs go to the shop as drafts (`draft=True`) for the admin's Draft Products queue.
"""
from _fall import NOMINAL, fit, standard_checks  # noqa: F401  (re-exported)

COLLECTION = "festival-of-lights"
COLLECTION_TITLE = "Festival of Lights"

# name: (hex, Brother thread name)
PALETTE = {
    "navy": ("#0e1f7c", "Prussian Blue"),
    "blue": ("#0a55a3", "Blue"),
    "sky": ("#2584bb", "Sky Blue"),
    "ice": ("#a8deeb", "Light Blue"),
    "white": ("#f0f0f0", "White"),
    "silver": ("#a8a8a8", "Silver"),
    "charcoal": ("#293133", "Dark Gray"),
    "gold": ("#e8a900", "Deep Gold"),
    "yellow": ("#ffd911", "Harvest Gold"),
    "orange": ("#ff9900", "Orange"),
    "red": ("#ed171f", "Red"),
    "berry": ("#b54b64", "Amber Red"),
    "green": ("#00673e", "Emerald Green"),
    "olive": ("#435607", "Dark Olive"),
    "leaf": ("#2f7e20", "Moss Green"),
    "ginger": ("#b27624", "Light Brown"),
    "cocoa": ("#2a1301", "Dark Brown"),
    "tan": ("#d0a660", "Khaki"),
    "cream": ("#efe3b9", "Beige"),
    "pink": ("#f993bc", "Pink"),
    "black": ("#000000", "Black"),
}
C_ = {k: v[0] for k, v in PALETTE.items()}

# Sizes every design ships in: (label, hoop, longest side in mm)
SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]

PRICE_USD = 3.99
COMMERCIAL_PRICE_USD = 12.99

BASE_TAGS = ["hanukkah embroidery design", "chanukah", "hanukkah", "machine embroidery",
             "jewish holiday", "holiday embroidery"]


def hoop_for(size):
    """The hoop field `fit` keeps a design inside at this size."""
    from cadkit.stitch import HOOPS
    return HOOPS["4x4"] if size <= 100 else HOOPS["5x7"]


def product(title, summary, tags, description, mockups=("tshirt", "tote")):
    """A PRODUCT dict for a Festival of Lights design (collection, prices, base tags, draft)."""
    return dict(title=title, summary=summary, tags=list(dict.fromkeys(list(tags) + BASE_TAGS)),
                collection=COLLECTION, mockups=list(mockups), description=description,
                price_usd=PRICE_USD, commercial_price_usd=COMMERCIAL_PRICE_USD, draft=True)
