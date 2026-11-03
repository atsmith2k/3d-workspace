"""Shared by the Kingdoms & Shadow fantasy collection (designs/kingdom_*.py).

Epic high fantasy: elven realms, kingdoms of men, dwarven halls, dragons and the
gathering shadow. The third fantasy collection after Realms & Relics and Arcana & Ink,
with one look across its ten designs: deep navy, silver, gold, forest green and ember.
Every design is original art. No names, places, scripts, emblems or quotes from any
book or film: titles and tags use genre words only (elven, kingdom, dwarven, beacon,
dragon hoard, sailing west). Runes are genuine Elder Futhark letter shapes and spell
nothing.

It shares the Realms & Relics thread palette (one set of Brother cones for every
fantasy collection), sizes, prices, `fit` and the standard checks, plus a few drawing
helpers the designs share (tapered tubes, line trimming, resampling).
"""
import numpy as np
from shapely.geometry import LineString, Point

from _realms import (C_, PALETTE, SIZES, PRICE_USD, COMMERCIAL_PRICE_USD, NOMINAL,  # noqa: F401
                     fit, hoop_for, standard_checks)
from _realms import product as _product

COLLECTION = "kingdoms-and-shadow"
COLLECTION_TITLE = "Kingdoms & Shadow"

BASE_TAGS = ["high fantasy", "epic fantasy", "fantasy embroidery", "medieval fantasy"]


def product(title, summary, tags, description, mockups=("tshirt", "tote")):
    """A PRODUCT dict for a Kingdoms & Shadow design (submitted to the shop as a draft)."""
    return _product(title, summary, list(tags) + BASE_TAGS, description, mockups,
                    collection=COLLECTION)


def resample(path, step):
    """Evenly spaced points along a polyline."""
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.c_[np.interp(t, s, path[:, 0]), np.interp(t, s, path[:, 1])]


def tube(path, widths, step=0.4):
    """The area a tapered stroke covers: widths interpolated along the path."""
    from cadkit.stitch import union
    path = resample(path, step)
    w = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(widths)), widths)
    return union(*[Point(*q).buffer(r / 2, quad_segs=12) for q, r in zip(path, w)]).simplify(0.05)


def widths_along(path, *w):
    """Per-point widths for a satin, linearly through the given stops."""
    return np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(w)), w)


def trim_path(path, start=0.0, end=0.0):
    """Shorten a polyline by `start` mm at its start and `end` mm at its end."""
    ls = LineString(np.asarray(path, float))
    from shapely.ops import substring
    return np.asarray(substring(ls, start, ls.length - end).coords)


def pieces(g, min_len=1.5):
    """The LineStrings in a geometry longer than `min_len`, as point arrays."""
    if g.is_empty:
        return []
    out = []
    for q in getattr(g, "geoms", [g]):
        if q.geom_type == "LineString" and q.length > min_len:
            out.append(np.asarray(q.coords))
        elif hasattr(q, "geoms"):
            out += pieces(q, min_len)
    return out


def band(path, width, cap="flat"):
    """The area a satin of this width along `path` covers."""
    return LineString(np.asarray(path, float)).buffer(width / 2, cap_style=cap)
