"""Shared by the Hearth & Snow winter / holiday collection (designs/hearth_*.py).

The second winter collection, after Frost & Fir (`designs/_winter.py`): twenty designs
picked from the 2026-11 market research (docs/research/2026-11-embroidery-hearth.md),
none repeating a Frost & Fir motif. The palette is Frost & Fir's plus two threads, so a
buyer of both collections needs one set of cones; every colour is an exact Brother
(PEC) thread. Each design draws its art in a 100 mm nominal space and calls
`fit(d, p.size, hoop)`, which rebuilds it at the requested size. Sizing and the standard
checks are the fall collection's (`_fall.fit`, `_fall.standard_checks`).

New designs go to the shop as drafts (`draft=True`): `publish-models.mts --draft` puts
them in the admin's Draft Products review queue rather than on sale.
"""
from _fall import NOMINAL, fit, standard_checks  # noqa: F401  (re-exported)
from _winter import PALETTE as _WINTER, holly_sprig, sew_bow  # noqa: F401  (re-exported)

COLLECTION = "hearth-and-snow"
COLLECTION_TITLE = "Hearth & Snow"

# name: (hex, Brother thread name)
PALETTE = dict(_WINTER, **{
    "charcoal": ("#293133", "Dark Gray"),
    "orange": ("#ff9900", "Orange"),
})
C_ = {k: v[0] for k, v in PALETTE.items()}

# Sizes every design ships in: (label, hoop, longest side in mm)
SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]

PRICE_USD = 3.99
COMMERCIAL_PRICE_USD = 12.99


def hoop_for(size):
    """The hoop field `fit` keeps a design inside at this size."""
    from cadkit.stitch import HOOPS
    return HOOPS["4x4"] if size <= 100 else HOOPS["5x7"]


def product(title, summary, tags, description, mockups=("tshirt", "tote"), base=None):
    """A PRODUCT dict for a Hearth & Snow design (collection, prices, base tags, draft)."""
    base = base or ["winter embroidery design", "christmas embroidery", "machine embroidery", "holiday"]
    return dict(title=title, summary=summary, tags=list(dict.fromkeys(list(tags) + base)),
                collection=COLLECTION, mockups=list(mockups), description=description,
                price_usd=PRICE_USD, commercial_price_usd=COMMERCIAL_PRICE_USD, draft=True)
