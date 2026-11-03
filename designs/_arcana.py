"""Shared by the Arcana & Ink fantasy collection (designs/arcana_*.py).

The second fantasy collection, after Realms & Relics, made to look and sew differently:
redwork line art, Celtic satin interlace, stained-glass leading, tarot-card frames,
merit-badge patches, lettering pieces and contour/ripple fills. Same rules: original
art only, no franchise names or emblems. It shares the Realms & Relics thread palette
(one set of Brother cones for both), sizes, prices, `fit` and the standard checks.
"""
from _realms import (C_, PALETTE, SIZES, PRICE_USD, COMMERCIAL_PRICE_USD, NOMINAL,  # noqa: F401
                     fit, hoop_for, standard_checks)
from _realms import product as _product

COLLECTION = "arcana-and-ink"
COLLECTION_TITLE = "Arcana & Ink"


def product(title, summary, tags, description, mockups=("tshirt", "tote")):
    """A PRODUCT dict for an Arcana & Ink design (submitted to the shop as a draft)."""
    return _product(title, summary, tags, description, mockups, collection=COLLECTION)
