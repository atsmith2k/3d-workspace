"""Thread colours: hex, a few plain names, or a Brother (PEC) palette name; and the
nearest Brother palette colour for the report, so the user knows which spool to load."""
import re

from pyembroidery.EmbThreadPec import get_thread_set

PLAIN = {
    "black": "#000000", "white": "#ffffff", "red": "#c8102e", "navy": "#1f2a5a",
    "blue": "#1f5fbf", "sky": "#6cb4e4", "green": "#2e8b3a", "dark green": "#1d4d2b",
    "lime": "#9acd32", "yellow": "#ffd100", "gold": "#c9a227", "orange": "#ff7f1e",
    "pink": "#f4a6c1", "hot pink": "#e0457b", "purple": "#6a3d9a", "lavender": "#b9a3d6",
    "brown": "#7a4a2a", "tan": "#d2b48c", "grey": "#8a8d8f", "gray": "#8a8d8f",
    "silver": "#c0c0c0", "cream": "#f3e9d2", "teal": "#1a8a8a", "maroon": "#6d1a2a",
}

_PEC = [t for t in get_thread_set() if t is not None]


def _hex(t):
    return t.hex_color().lower()


def resolve_color(color):
    """'#c8102e', 'c8102e', 'navy' or a Brother name like 'Deep Rose' -> '#rrggbb'."""
    c = str(color).strip()
    if re.fullmatch(r"#?[0-9a-fA-F]{6}", c):
        return "#" + c.lstrip("#").lower()
    if c.lower() in PLAIN:
        return PLAIN[c.lower()]
    for t in _PEC:
        if (t.description or "").lower() == c.lower():
            return _hex(t)
    raise ValueError(f"unknown thread colour '{color}': use #rrggbb, one of "
                     f"{', '.join(PLAIN)} or a Brother palette name")


def rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lab(hexcolor):
    """sRGB '#rrggbb' -> CIE L*a*b* (D65)."""
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in rgb(hexcolor))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e94(c1, c2):
    """CIE94 colour difference between two hex colours (graphic arts weights)."""
    L1, a1, b1 = lab(c1)
    L2, a2, b2 = lab(c2)
    C1, C2 = (a1 * a1 + b1 * b1) ** 0.5, (a2 * a2 + b2 * b2) ** 0.5
    dH2 = max(0.0, (a1 - a2) ** 2 + (b1 - b2) ** 2 - (C1 - C2) ** 2)
    return ((L1 - L2) ** 2 + ((C1 - C2) / (1 + 0.045 * C1)) ** 2
            + dH2 / (1 + 0.015 * C1) ** 2) ** 0.5


def nearest_brother(hexcolor):
    """(name, '#rrggbb') of the closest Brother PEC palette thread (CIE94: unlike plain
    RGB distance it keeps a dark navy from matching grey)."""
    t = min(_PEC, key=lambda t: delta_e94(hexcolor, _hex(t)))
    return t.description, _hex(t)


CLOSE = 8.0         # CIE94 distance beyond which the palette has no real match


def thread_label(hexcolor):
    """'~ Brother Orange (dE 3.7)', or a note that the palette has nothing close, so the
    user buys the thread by colour instead of grabbing the wrong spool."""
    name, h = nearest_brother(hexcolor)
    de = delta_e94(hexcolor, h)
    if de <= CLOSE:
        return f"~ Brother {name} (dE {de:.1f})"
    return f"no close Brother match (nearest {name}, dE {de:.0f}): use the hex"
