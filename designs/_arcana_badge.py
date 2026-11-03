"""Shared frame for the Arcana & Ink adventurer merit-badge patches (arcana_*_badge.py).

Every badge in the series has the same frame, drawn in the collection's 100 mm nominal
space (`fit` scales it to 90 mm at 4x4, 120 mm at 5x7):

- a round patch, border centreline radius `RC`, satin border `BORDER` wide (3 mm at 4x4)
  sewn last as one continuous ring;
- a backdrop sewn as a circular (spiral) fill, tucked under the border;
- a ribbon banner that follows the bottom of the patch, its ends tucked behind darker
  folds that run into the border, with the class name set along the arc in our block
  lettering (`LETTER_CAP` nominal, 8.5 mm at 4x4) and knocked out of the banner.
"""
import math

from shapely.geometry import Point

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

RO = 50.0                    # outer edge of the patch (nominal)
BORDER = 3.3                 # satin border width (3.0 mm at 4x4)
RC = RO - BORDER / 2         # border centreline
DISC = circle(0, 0, RC, res=256)
INNER = tuck(DISC, BORDER)   # where fills may run (0.6 mm under the border)

# banner: an arc concentric with (0, BAN_CY), following the bottom of the patch
BAN_CY = 80.0
BAN_R0 = BAN_CY + 23.5       # top edge at x=0 -> y=-23.5
BAN_R1 = BAN_CY + 37.5       # bottom edge at x=0 -> y=-37.5
BAN_HALF = 15.5              # main band half angle, degrees (ends ~x=+-30)
FOLD_DROP = 2.6              # the folds sit this much lower than the band
LETTER_CAP = 9.4
LETTER_STROKE = 2.1
LETTER_SPACING = 0.4         # rows; 0.35 turns get merged by the 0.4 mm minimum stitch
LETTER_TRACK = 1.5           # extra gap between letters, mm along the arc


def _arc_band(r0, r1, a0, a1, cy, res=2.0):
    """Annular sector of the circle centred (0, cy), angles from straight down, degrees."""
    n = max(4, int(abs(a1 - a0) / res))
    outer, inner = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        outer.append((r1 * math.sin(a), cy - r1 * math.cos(a)))
        inner.append((r0 * math.sin(a), cy - r0 * math.cos(a)))
    return poly(outer + inner[::-1])


def banner_main():
    return _arc_band(BAN_R0, BAN_R1, -BAN_HALF, BAN_HALF, BAN_CY) & INNER


def banner_folds():
    """The two ribbon ends: lower than the band, from under its ends out to the border."""
    l = _arc_band(BAN_R0, BAN_R1, -60, -(BAN_HALF - 3), BAN_CY - FOLD_DROP)
    r = _arc_band(BAN_R0, BAN_R1, BAN_HALF - 3, 60, BAN_CY - FOLD_DROP)
    return (l | r) & INNER


def banner_all():
    return banner_main() | banner_folds()


def lettering(word):
    """The word set along the banner's centre arc, each letter upright to the arc."""
    return union(*[g for g, _ in letters_on_arc(word)])


def sew_letters(d, word, color):
    """One fill per letter, rows square to that letter (crisp edges on a tilted glyph)."""
    for g, a in letters_on_arc(word):
        d.fill(g, color, angle=a, spacing=LETTER_SPACING, name="lettering")


def letters_on_arc(word):
    """[(glyph, angle deg)] along the banner's centre arc."""
    rm = (BAN_R0 + BAN_R1) / 2
    glyphs = []
    for ch in word:
        g = block_text(ch, cap=LETTER_CAP, stroke=LETTER_STROKE, tracking=0)
        x0, y0, x1, y1 = g.bounds
        glyphs.append((g, x1 - x0))
    total = sum(w for _, w in glyphs) + LETTER_TRACK * (len(glyphs) - 1)
    s = -total / 2
    out = []
    for g, w in glyphs:
        mid = s + w / 2
        a = mid / rm                       # radians along the arc
        x0, y0, x1, y1 = g.bounds
        g = move(g, -(x0 + x1) / 2, -(y0 + y1) / 2)
        g = rotate(g, math.degrees(a))
        out.append((move(g, rm * math.sin(a), BAN_CY - rm * math.cos(a)), math.degrees(a)))
        s += w + LETTER_TRACK
    return out


def solid(shape):
    """The shape with its holes (letter counters) filled: a mask for knockouts."""
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(shape)])


def backdrop(d, color, above, spacing=0.42, name="backdrop", angle=0, **ink):
    """The patch backdrop as one spiral fill, knocked out under everything on top."""
    parts = sorted(polygons_of(knockout(INNER, *above)), key=lambda g: -g.area)
    # the main sky spirals round a centre hidden under the emblem; the strip under the
    # banner (and any small pockets) runs in contour rows along the border instead of
    # showing a second whorl
    d.fill(parts[0], color, method="circular_fill", spacing=spacing, angle=angle, name=name, **ink)
    for g in parts[1:]:
        if g.area > 30:
            d.fill(g, color, method="contour_fill", spacing=0.36, angle=0, name=name + " rim")
        else:
            d.fill(g, color, angle=0, spacing=spacing, name=name + " pocket")


def sew_banner(d, word, ribbon, fold, letters, above=()):
    """Folds, then the band (letters knocked out), then the lettering."""
    txt = lettering(word)
    main = banner_main()
    d.fill(knockout(banner_folds(), main, *above), fold, angle=60, name="banner folds")
    d.fill(knockout(main, txt, *above, overlap=0.3), ribbon, angle=0, name="banner")
    sew_letters(d, word, letters)
    return txt


def sew_border(d, color):
    d.outline(DISC, color, width=BORDER, name="border")


def clip(shape):
    """Anything that runs to the edge stops 0.6 mm under the border."""
    return shape & INNER
