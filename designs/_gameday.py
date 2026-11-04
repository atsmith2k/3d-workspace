"""Shared by the Game Day States collection (designs/gameday_*.py).

Each design is a state's name arched in our own block lettering (cadkit.stitch.lettering)
over the state's public-domain outline, in one two-colour colourway. Only state names,
outlines and colours: no school names, initials, nicknames, mascots, marks or school
typefaces, and colourways are named by colour, never by school. Listings and tags
follow the same rule.
"""
import numpy as np
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import checks as C
from cadkit.stitch.design import smooth_outline
from cadkit.stitch.lettering import block_text

from _fall import fit
from _states import state_shape

COLLECTION = "game-day-states"
COLLECTION_TITLE = "Game Day States"

# name: (title, primary: state fill + letter outlines, secondary: letters + state border,
#        accent: drop shadow)
COLOURWAYS = {
    "crimson_cream": ("Crimson & Cream", "#990000", "#efe3b9", "#2a1301"),
    "gold_black": ("Old Gold & Black", "#cfb991", "#000000", "#878787"),
    "blue_white": ("Royal Blue & White", "#0033a0", "#f0f0f0", "#293133"),
    "red_black": ("Red & Black", "#c8102e", "#000000", "#878787"),
    "scarlet_gray": ("Scarlet & Gray", "#ba0c2f", "#a7b1b7", "#293133"),
    "orange_navy": ("Orange & Navy", "#e84a27", "#13294b", "#878787"),
    "orange_white": ("Orange & White", "#ff8200", "#f0f0f0", "#58595b"),
    "burnt_orange_white": ("Burnt Orange & White", "#bf5700", "#f0f0f0", "#333f48"),
    # the other 44 states
    "crimson_white": ("Crimson & White", "#9e1b32", "#f0f0f0", "#2a1301"),
    "blue_gold": ("Blue & Gold", "#00539f", "#ffd200", "#1d252d"),
    "red_navy": ("Red & Navy", "#ce1126", "#14213d", "#878787"),
    "navy_gold": ("Navy & Gold", "#002855", "#eaaa00", "#878787"),
    "navy_white": ("Navy & White", "#0c2340", "#f0f0f0", "#7c878e"),
    "blue_orange": ("Blue & Orange", "#0021a5", "#fa4616", "#878787"),
    "green_white": ("Green & White", "#00573f", "#f0f0f0", "#293133"),
    "black_gold": ("Black & Gold", "#000000", "#ffcd00", "#878787"),
    "blue_crimson": ("Blue & Crimson", "#0051ba", "#e8000d", "#293133"),
    "purple_gold": ("Purple & Gold", "#461d7c", "#fdd023", "#878787"),
    "navy_light_blue": ("Navy & Light Blue", "#003263", "#b0d7ff", "#7c878e"),
    "red_gold": ("Red & Gold", "#e21833", "#ffd200", "#2a1301"),
    "maroon_white": ("Maroon & White", "#881c1c", "#f0f0f0", "#2a1301"),
    "navy_maize": ("Navy & Maize", "#00274c", "#ffcb05", "#878787"),
    "maroon_gold": ("Maroon & Gold", "#7a0019", "#ffcc33", "#2a1301"),
    "maroon_silver": ("Maroon & Silver", "#70122b", "#c0c4c8", "#2a1301"),
    "scarlet_cream": ("Scarlet & Cream", "#e41c38", "#fdf2d9", "#2a1301"),
    "navy_silver": ("Navy & Silver", "#003366", "#a7b1b7", "#878787"),
    "light_blue_navy": ("Light Blue & Navy", "#7bafd4", "#13294b", "#878787"),
    "green_gold": ("Green & Gold", "#154733", "#fee123", "#878787"),
    "orange_purple": ("Orange & Purple", "#f56600", "#522d80", "#878787"),
    "red_white": ("Red & White", "#c5050c", "#f0f0f0", "#2a1301"),
    "navy_orange": ("Navy & Orange", "#232d4b", "#e57200", "#878787"),
    "brown_gold": ("Brown & Gold", "#492f24", "#ffc425", "#878787"),
}

# each group module (designs/_gameday_<group>.py) adds its own states' colourways
import importlib as _il
from pathlib import Path as _Path
for _p in sorted(_Path(__file__).parent.glob("_gameday_*.py")):
    COLOURWAYS.update(getattr(_il.import_module(_p.stem), "COLOURWAYS", {}))

SIZES = [("4x4", "4x4", 95.0), ("5x7", "5x7", 160.0)]

LETTER_W = 86.0      # arch chord in the 100 mm nominal space
ARCH_R = 70.0        # arch radius
PLATE = 1.4          # plate margin round the letters
EDGE = 1.2           # satin edge round the plate
SHADOW = (0.0, -1.6) # shadow offset: mostly down, so the strip runs unbroken along the word
CLOSE = 3.2          # gaps between letters narrower than 2 x CLOSE are bridged by the plate
BORDER = 2.0         # satin border round the state
GAP = 3.5            # clear space between the letters and the state
CAP_MAX = 17.0       # cap height limits in the nominal space
CAP_MIN = 13.5


def _warp(g, r):
    """Bend a shape laid along y=0 onto an arc of radius r (centre below)."""
    def bend(coords):
        c = np.asarray(coords)
        t = c[:, 0] / r
        return np.c_[(r + c[:, 1]) * np.sin(t), (r + c[:, 1]) * np.cos(t) - r]
    out = []
    for pg in polygons_of(g.segmentize(0.4)):
        out.append(Polygon(bend(pg.exterior.coords), [bend(i.coords) for i in pg.interiors]))
    return unary_union(out)


def lettering(label):
    """(letters, band): the arched word, and the solid band from its baseline to its cap
    line, first letter to last, for the plate (so no pocket beside a T, L or Y opens a
    gap in the plate's edge)."""
    t = centered(block_text(label, 10.0, tracking=2.2))
    x0, _, x1, _ = t.bounds
    k = min(LETTER_W / (x1 - x0), CAP_MAX / 10.0)     # short names stop at CAP_MAX
    ky = max(k, CAP_MIN / 10.0)                        # long names are set condensed
    arch = lambda g: move(_warp(scale(g, k, ky), ARCH_R), 0, 30)
    return arch(t), arch(box(*t.bounds))


def state_under(state, letters, max_w=84.0, max_h=56.0):
    """The state outline as large as fits max_w x max_h, raised until it sits GAP mm
    under the arched letters (a tall state nests into the arch, a wide one sits below)."""
    s = state_shape(state, 50.0)
    x0, y0, x1, y1 = s.bounds
    s = scale(s, min(max_w / (x1 - x0), max_h / (y1 - y0)))
    keep = letters.buffer(PLATE + abs(SHADOW[1]) + BORDER / 2 + GAP)
    lo, hi = -120.0, 40.0                     # dy that clears / dy that overlaps
    for _ in range(30):
        mid = (lo + hi) / 2
        if move(s, 0, mid).intersects(keep):
            hi = mid
        else:
            lo = mid
    return move(s, 0, lo)


def art(state, colourway, label=None, satin=1.0, banner=False, close=CLOSE, smooth=1.0, letter_angle=80, shadow_trim=0.5, shadow_angle=0, thin=0.0, island=0.0, border=1.0, channel=0.0, raw_necks=False, plate_angle=95):
    """`banner`: the plate is a solid arched band from baseline to cap line (a rocker)
    instead of hugging the letters. `close` bridges wider gaps (Texas: 4.6, so the
    pocket under the T's arm does not break the plate's edge). `smooth` rounds off coastline
    detail a satin border cannot follow (Alaska: 2.5). `letter_angle`, `shadow_angle`, `plate_angle` and `shadow_trim` (how thin a
    shadow point is dropped) move fill rows off a corner where they pile up (`plate_angle` also
    moves the plate fill's travel, which runs out and back along the same holes under the edge). `thin`: islands and necks
    narrower than 2 x thin: islands are grown by `island` mm so they hold a fill and a
    border, the rest are sewn solid in the border colour, so no fill shows outside a border. `border`
    scales the state's satin border (a slimmer one for small islands and lacy coasts); `channel` closes water
    narrower than 2 x channel."""
    bw = BORDER * border
    _, primary, secondary, accent = COLOURWAYS[colourway]
    letters, band = lettering(label or state.replace("_", " ").upper())
    raw = state_under(state, letters)
    if channel:   # close water narrower than 2 x channel (a bay slot two borders cannot keep open)
        raw = raw.buffer(channel).buffer(-channel)
    st = smooth_outline(raw, smooth)   # one edge for fill and border
    bits = None
    if thin:
        # Every piece keeps a border round its fill. Islands too small to hold both are
        # grown until they do (a map exaggerates them too); ones still too small, and
        # necks narrower than 2 x thin, are sewn solid in the border colour.
        opening = lambda g: g.buffer(-thin, join_style="mitre", mitre_limit=5).buffer(thin, join_style="mitre", mitre_limit=5)
        core = opening(st)
        body = unary_union([q for q in polygons_of(core) if q.area > 4.0])
        islands = [q for q in polygons_of(raw) if not q.intersects(body)]
        src = raw if raw_necks else st          # raw: necks smoothing would cut (Alaska's panhandle strip)
        necks = [q for q in polygons_of(src.difference(core).buffer(-0.05)) if q.area > 0.3 and q.distance(body) < 0.2
                 and (not raw_necks or q.buffer(-0.3).is_empty is False)]
        grown = [smooth_outline(q.buffer(island), 0.5) for q in islands]
        holds = lambda g: not g.buffer(-(bw * satin + 0.5)).is_empty      # room for a fill inside the border
        held = [g for g in grown if holds(g)]
        st = unary_union([body] + held)
        dots = [g.buffer(0.3) for g in grown if not holds(g) and g.area > 0.6]
        bits = unary_union(dots + [q.buffer(0.55) for q in necks]) if dots or necks else None
    # Layered like tackle twill: the letters sit on one connected plate of the primary
    # colour (gaps between letters and the counters closed), the plate gets a satin
    # edge, and the shadow is the plate's offset. Plate, edge and shadow each sew in one
    # piece, and the colours run accent, primary, secondary: 3 blocks, few trims.
    word = unary_union([Polygon(pg.exterior) for pg in polygons_of(letters)] + ([band] if banner else []))
    word = word.buffer(close, join_style="mitre").buffer(-close, join_style="mitre")
    plate = word.buffer(PLATE, join_style="mitre", mitre_limit=2.0)
    plate = plate.buffer(1.6).buffer(-1.6)            # close notches with narrow mouths
    plate = unary_union([Polygon(pg.exterior) for pg in polygons_of(plate)])     # no pinholes
    peek = knockout(move(plate, *SHADOW), plate, overlap=0.0)   # meets the plate under its edge satin
    peek = peek.buffer(-shadow_trim).buffer(shadow_trim)             # drop slivers too thin to sew
    d = Design()
    d.hide_jumps_mm = 40.0
    d.fill(left_to_right(peek), accent, angle=shadow_angle, spacing=0.45, stitch=3.5, underlay=False, name="shadow")
    d.fill(tuck(st, bw), primary, angle=45, spacing=0.45, stitch=3.5, name="state")
    d.fill(knockout(tuck(plate, EDGE), letters, overlap=0.3), primary, angle=plate_angle, spacing=0.42, name="plate")
    d.outline(plate, primary, width=EDGE * satin, spacing=0.45, name="plate edge")
    d.outline(st, secondary, width=bw * satin, spacing=0.42, clean=0, name="state border")
    if bits is not None:          # border colour, reaching 0.25 mm under the border it joins
        bits = bits.difference(st.buffer(bw * satin / 2 - 0.25))
        bits = unary_union([q for q in polygons_of(bits.buffer(-0.4).buffer(0.4)) if q.area > 0.6])
        if not bits.is_empty:
            d.fill(left_to_right(bits), secondary, angle=135, spacing=0.45, stitch=3.0, name="state slivers")
    d.fill(left_to_right(letters), secondary, angle=letter_angle, spacing=0.42, stitch=3.5, name="letters")
    return d


def build(state, colourway, size, hoop="4x4", label=None, **style):
    """The design at `size` mm. Satin edges grow with the square root of the scale, not
    linearly: a 3.4 mm border on the 5x7 would fan and pile up on tight curves."""
    hoop_wh = HOOPS.get(hoop) if size <= 100 else HOOPS["5x7"]
    x0, y0, x1, y1 = art(state, colourway, label, **style).bounds()
    k = size / max(x1 - x0, y1 - y0)
    if hoop_wh:
        k = min(k, (max(hoop_wh) - 10) / max(x1 - x0, y1 - y0), (min(hoop_wh) - 10) / min(x1 - x0, y1 - y0))
    return fit(art(state, colourway, label, satin=k ** -0.5, **style), size, hoop_wh)


def left_to_right(g):
    return MultiPolygon(sorted(polygons_of(g), key=lambda q: q.centroid.x))


def blocks(colourway):
    return 3


def standard_checks(p, colourway, max_stitches=14000):
    return [
        C.size(w=(20, p.size + 1.5), h=(20, p.size + 1.5)),
        C.hoop(),
        C.colors(blocks(colourway)),
        C.max_density(3.5),
        C.long_stitches(7.0),
        C.min_feature(1.0),
        C.coverage(1.0),
        C.stitches(max=max_stitches * (p.size / 95.0) ** 2),
        C.jump_threads(3.0, 0),
    ]


def product(state, colourway, label=None, banner=False):
    """`label` is a city set over its state outline ('Louisville' over Kentucky)."""
    name = (label or state.replace("_", " ")).title()
    shape = state.replace("_", " ").title() if label else "state"
    cw = COLOURWAYS[colourway][0]
    return dict(
        title=f"{name} Game Day {'Arched Banner' if banner else 'Block Letter'} Embroidery Design, {cw}",
        summary=(f"'{name.upper()}' in athletic block letters on an arched banner over the {shape}, in {cw.lower()}"
                 if banner else f"'{name.upper()}' arched in athletic block letters over the {shape}, in {cw.lower()}"),
        tags=[f"{name.lower()} embroidery", "game day embroidery", "state embroidery design",
              "block letter", cw.lower().replace(" & ", " and ")] + (["arched banner", "rocker patch"] if banner else []),
        collection=COLLECTION,
        bundles=[f"{COLLECTION}-{'arched-banner' if banner else 'block-letter'}"],   # per-style bundles
        mockups=["tshirt", "cap"],
        draft=True,                       # new designs go to the shop's review queue
        description=(
            f"{name.upper()} arched across the top in heavy athletic block letters, set on "
            + ("a solid satin-edged arched banner (a rocker) with a drop shadow," if banner else
               "a satin-edged plate with a drop shadow,")
            + f" over a satin-bordered {name if not label else state.replace("_", " ").title()} state silhouette, in "
            f"{cw.lower()}.\n\nFor game-day sweatshirts, caps, totes and stadium blankets. The "
            "lettering is our own alphabet, drawn for embroidery, and the state outline comes "
            "from public-domain US Census boundaries. Not affiliated with or endorsed by any "
            "school, college or athletic conference."
        ),
    )
