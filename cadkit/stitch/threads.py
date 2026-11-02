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


def nearest_brother(hexcolor):
    """(name, '#rrggbb') of the closest Brother PEC palette thread (redmean distance)."""
    r, g, b = rgb(hexcolor)

    def dist(t):
        r2, g2, b2 = rgb(_hex(t))
        rm = (r + r2) / 2
        return (2 + rm / 256) * (r - r2) ** 2 + 4 * (g - g2) ** 2 + (2 + (255 - rm) / 256) * (b - b2) ** 2
    t = min(_PEC, key=dist)
    return t.description, _hex(t)
