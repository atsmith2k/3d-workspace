"""Shared by the Hearth & Hollow cozy pastoral fantasy collection (designs/hollow_*.py).

The third fantasy collection, after Realms & Relics and Arcana & Ink: the quiet side of
an epic: round-door hillside homes, pipes and smoke rings, kettles, gardens, foraging
baskets, walking sticks and village fairs. Original art and wording only: no franchise
names, places, characters, scripts or quotes, so titles and tags describe the genre
(cozy fantasy, cottagecore, halfling, storybook) and never someone's trademark.

(Named `_hollow` because `designs/_hearth.py` already belongs to the Hearth & Snow
winter collection.) It shares the Realms & Relics thread palette (one set of Brother
cones for all three fantasy collections), sizes, prices, `fit` and the standard checks.
"""
from cadkit.stitch import *

from _realms import (C_, PALETTE, SIZES, PRICE_USD, COMMERCIAL_PRICE_USD, NOMINAL,  # noqa: F401
                     fit, hoop_for, standard_checks)

COLLECTION = "hearth-and-hollow"
COLLECTION_TITLE = "Hearth & Hollow"


def product(title, summary, tags, description, mockups=("tshirt", "tote")):
    """A PRODUCT dict for a Hearth & Hollow design (submitted to the shop as a draft)."""
    base = ["cozy fantasy embroidery", "machine embroidery", "cottagecore", "storybook",
            "fantasy embroidery design", "halfling"]
    return dict(title=title, summary=summary, tags=list(dict.fromkeys(list(tags) + base)),
                collection=COLLECTION, mockups=list(mockups), description=description,
                price_usd=PRICE_USD, commercial_price_usd=COMMERCIAL_PRICE_USD, draft=True)


def centred(g, cx, cy):
    """The shape moved so its bounding box is centred on (cx, cy)."""
    x0, y0, x1, y1 = g.bounds
    return move(g, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)


def solid(shape):
    """The shape with its holes (letter counters) filled: a mask for knockouts."""
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(shape)])


def strip(path, widths):
    """A filled strip along a path: one width, or widths spread evenly along it."""
    import numpy as np
    path = np.asarray(path, float)
    w = np.atleast_1d(np.asarray(widths, float))
    w = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(w)), w) if len(w) > 1         else np.full(len(path), w[0])
    tan = np.gradient(path, axis=0)
    nrm = np.c_[-tan[:, 1], tan[:, 0]] / np.linalg.norm(tan, axis=1)[:, None]
    l, r = path + nrm * w[:, None] / 2, path - nrm * w[:, None] / 2
    return poly(list(map(tuple, l)) + list(map(tuple, r[::-1])))


def close_gaps(lower, *upper, r=1.2):
    """`lower` grown into the narrow slots (under 2r wide) between it and `upper`, so two
    shapes that cross at a shallow angle leave no sliver of bare fabric between them."""
    allg = union(lower, *upper)
    closed = allg.buffer(r, join_style="round").buffer(-r, join_style="round")
    pockets = closed.difference(allg)
    near = [g for g in polygons_of(pockets) if g.distance(lower) < 0.05]
    return union(lower, *near) if near else lower


def small_holes(*shapes, max_area=30.0):
    """Every enclosed pocket of fabric under `max_area` mm2 left between the shapes: give
    it to a backing fill (a shadow) so no tiny slot of bare fabric shows between them."""
    from shapely.geometry import Polygon
    u = union(*shapes)
    holes = [Polygon(r) for g in polygons_of(u) for r in g.interiors]
    holes = [h.difference(u) for h in holes if h.area <= max_area]
    return union(*[h for h in holes if not h.is_empty]) if holes else poly([])


def _element_area(el):
    import numpy as np
    if el.area is not None:
        return el.area
    if el.kind == "fill":
        return el.geom
    if el.kind == "satin":
        l, r = el.geom
        return poly([tuple(p) for p in np.vstack([l, r[::-1]])]).buffer(0)
    return None


def backfill(d, color, max_area=30.0, name="shadow"):
    """Fill every enclosed pocket of bare fabric (under `max_area` mm2) left between the
    design's fills and satins with `color`, sewn with the last element of that colour
    (no extra colour change). Use a shadow colour: the pockets read as depth."""
    from shapely.geometry import Polygon
    areas = [a for a in (_element_area(el) for el in d.elements) if a is not None]
    u = union(*areas)
    pockets = [Polygon(r).difference(u) for g in polygons_of(u) for r in g.interiors]
    pockets = [grow(p, 0.4) for p in pockets if 0.5 < p.area <= max_area]   # not pinholes at corners
    if not pockets:
        return
    last = max(i for i, el in enumerate(d.elements) if el.color == d.elements[i].color
               and el.color.lower() == color.lower())
    el = d.fill(union(*pockets), color, angle=0, name=name)
    d.elements.insert(last + 1, d.elements.pop())
