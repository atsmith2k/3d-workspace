"""Shared by the Realms & Relics fantasy collection (designs/realm_*.py).

High fantasy, dark fantasy and tabletop-adventure designs: wizards, dragons, runeblades,
burrow doors, potions and dice. Every design is original art: no franchise names,
characters, emblems or lettering (no "Lord of the Rings", "Middle-earth", "D&D",
Gondor, Shire...), so titles and tags describe the genre, not someone's trademark.

One thread palette for all fifteen designs, every colour an exact Brother (PEC) thread
so the chart names a real spool. Each design draws its art in a 100 mm nominal space
and calls `fit(d, p.size, hoop)`, which rebuilds it at the requested size (re-stitched,
not a scaled stitch file). Sizing and the standard checks are the fall collection's
(`_fall.fit`, `_fall.standard_checks`), so every collection ships the same way.
"""
from _fall import NOMINAL, fit, standard_checks  # noqa: F401  (re-exported)

COLLECTION = "realms-and-relics"
COLLECTION_TITLE = "Realms & Relics"

# name: (hex, Brother thread name)
PALETTE = {
    "black": ("#000000", "Black"),
    "charcoal": ("#293133", "Dark Gray"),
    "pewter": ("#4f5556", "Pewter"),
    "gray": ("#878787", "Gray"),
    "silver": ("#a8a8a8", "Silver"),
    "white": ("#f0f0f0", "White"),
    "bone": ("#efe3b9", "Beige"),
    "gold": ("#e8a900", "Deep Gold"),
    "brass": ("#ba9800", "Brass"),
    "yellow": ("#ffd911", "Harvest Gold"),
    "red": ("#ed171f", "Red"),
    "ember": ("#fe370f", "Vermilion"),
    "flame": ("#ff9900", "Orange"),
    "rust": ("#d15400", "Clay Brown"),
    "wine": ("#b54b64", "Amber Red"),
    "purple": ("#4e2990", "Purple"),
    "violet": ("#6a1c8a", "Violet"),
    "lilac": ("#915fac", "Lilac"),
    "lavender": ("#b2afd4", "Lavender"),
    "navy": ("#0e1f7c", "Prussian Blue"),
    "blue": ("#0a55a3", "Blue"),
    "sky": ("#2584bb", "Sky Blue"),
    "ice": ("#a8deeb", "Light Blue"),
    "teal": ("#008777", "Teal Green"),
    "peacock": ("#134a46", "Peacock Blue"),
    "seafoam": ("#a8ddc4", "Seacrest"),
    "pine": ("#003822", "Deep Green"),
    "green": ("#00673e", "Emerald Green"),
    "moss": ("#2f7e20", "Moss Green"),
    "leaf": ("#66ba49", "Leaf Green"),
    "olive": ("#435607", "Dark Olive"),
    "bark": ("#2a1301", "Dark Brown"),
    "wood": ("#b27624", "Light Brown"),
    "khaki": ("#d0a660", "Khaki"),
}
C_ = {k: v[0] for k, v in PALETTE.items()}

# Sizes every design ships in: (label, hoop, longest side in mm)
SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]

PRICE_USD = 3.99
COMMERCIAL_PRICE_USD = 12.99


def hoop_for(size):
    """The hoop field `fit` keeps a design inside at this size."""
    from cadkit.stitch import HOOPS
    return HOOPS["4x4"] if size <= 100 else HOOPS["5x7"]


def product(title, summary, tags, description, mockups=("tshirt", "tote")):
    """A PRODUCT dict for a Realms & Relics design (collection, prices and base tags filled in).
    New designs go to the shop as drafts for review (`draft=True`)."""
    base = ["fantasy embroidery design", "machine embroidery", "fantasy", "rpg", "geek embroidery"]
    return dict(title=title, summary=summary, tags=list(dict.fromkeys(list(tags) + base)),
                collection=COLLECTION, mockups=list(mockups), description=description,
                price_usd=PRICE_USD, commercial_price_usd=COMMERCIAL_PRICE_USD, draft=True)
