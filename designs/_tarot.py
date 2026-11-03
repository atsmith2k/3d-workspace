"""The tarot-card frame shared by the Arcana & Ink tarot series (designs/arcana_tarot_*.py).

One card layout for every card, so they sell as a set: a 66 x 100 mm (nominal) portrait
card with a bone face, a gold satin double border (2.4 mm outer edge, 1.3 mm inner rule
with notched corners and a gold diamond in each notch), a 48 x 63 mm picture window
framed by a 1.3 mm gold rule, a chamfered plaque at the top with the roman numeral
between two gold diamonds, and a wider chamfered banner at the bottom with the card name
in our block lettering (6.8 mm caps nominal, about 6.1 mm at the 4x4 size). The plaques
are the card's dark colour with gold lettering; letter counters are left open (the
plaques are knocked out under each letter's solid outline).

A card sews in three passes: `sew_face` (bone), the scene and `sew_plaques` (in the
scene's dark colour block), then `sew_gold` last, after any gold in the scene.
"""
import numpy as np

from cadkit.stitch import *
from cadkit.stitch.lettering import block_text

W, H = 66.0, 100.0          # card
RIM = 2.4                   # outer gold border
RULE = 1.3                  # inner gold rule and picture frame
GAP = 1.6                   # bone between the two borders
NOTCH = 5.5                 # radius of the inner rule's notched corners
PIC_W, PIC_H = 48.0, 63.4   # picture window (frame centreline)
CAP = 6.8                   # lettering cap height (nominal)


def chamfered(w, h, c, x=0.0, y=0.0):
    """Rectangle w x h centred on (x, y) with its corners cut c mm."""
    a, b = w / 2, h / 2
    return poly([(x - a + c, y - b), (x + a - c, y - b), (x + a, y - b + c), (x + a, y + b - c),
                 (x + a - c, y + b), (x - a + c, y + b), (x - a, y + b - c), (x - a, y - b + c)])


def _diamond(x, y, a):
    return poly([(x + a, y), (x, y + a), (x - a, y), (x, y - a)])


def _centred_text(s, y, tracking=1.0):
    t = block_text(s, cap=CAP, stroke=2.3, tracking=tracking)
    x0, y0, x1, y1 = t.bounds
    return move(t, -(x0 + x1) / 2, y - (y0 + y1) / 2)


def _solid(t):
    return union(*[poly(list(g.exterior.coords)) for g in polygons_of(t)])


def frame(numeral, name):
    """Every shape of the card frame, as a dict."""
    F = {}
    card = rounded_rect(W, H, 4.0)
    F["card"] = card
    F["rim"] = rounded_rect(W - RIM, H - RIM, 4.0 - RIM / 2)          # outer border centreline
    ix, iy = W / 2 - RIM - GAP - RULE / 2, H / 2 - RIM - GAP - RULE / 2
    inner = rect(2 * ix, 2 * iy)
    corners = [(sx * ix, sy * iy) for sx in (-1, 1) for sy in (-1, 1)]
    for cx, cy in corners:
        inner = inner - circle(cx, cy, NOTCH, 96)
    F["inner"] = inner
    F["diamonds"] = [_diamond(cx - np.sign(cx) * 1.0, cy - np.sign(cy) * 1.0, 2.3) for cx, cy in corners]
    F["picture"] = rounded_rect(PIC_W, PIC_H, 1.0)                     # frame centreline
    F["scene"] = tuck(F["picture"], RULE)                              # where the scene sews
    top_y = PIC_H / 2 + 2.3 + 4.6
    F["plaque_top"] = chamfered(30, 9.2, 2.5, 0, top_y)
    F["plaque_bot"] = chamfered(52, 9.2, 2.5, 0, -top_y)
    F["numeral"] = _centred_text(numeral, top_y)
    F["name"] = _centred_text(name, -top_y, tracking=0.8)
    F["dots"] = [_diamond(s * 12.4, top_y, 1.25) for s in (-1, 1)]
    F["bands"] = union(F["rim"].exterior.buffer(RIM / 2), inner.exterior.buffer(RULE / 2),
                       F["picture"].exterior.buffer(RULE / 2))
    return F


def sew_face(d, F, color):
    """The bone card face: everything inside the outer border but the picture, the plaques
    and the corner diamonds, knocked out under the gold rules."""
    face = knockout(tuck(F["card"], RIM * 2), F["bands"], grow(F["picture"], RULE / 2),
                    F["plaque_top"], F["plaque_bot"], *F["diamonds"])
    d.fill(face, color, angle=90, spacing=0.4, name="card face")


def sew_plaques(d, F, color):
    """Numeral plaque and name banner in the card's dark colour, knocked out under the
    letter strokes only, so the counters are banner-coloured."""
    d.fill(knockout(F["plaque_top"], F["numeral"], *F["dots"]), color, angle=0,
           spacing=0.4, name="numeral plaque")
    d.fill(knockout(F["plaque_bot"], F["name"]), color, angle=0, spacing=0.4, name="name banner")


def sew_gold(d, F, color):
    """The gold frame and lettering, sewn last."""
    d.outline(F["picture"], color, width=RULE, name="picture frame")
    d.outline(F["inner"], color, width=RULE, name="inner border")
    for g in F["diamonds"]:
        d.fill(g, color, angle=0, name="corner diamond")
    d.outline(F["rim"], color, width=RIM, name="outer border")
    d.fill(F["numeral"], color, angle=0, spacing=0.35, name="numeral")
    for g in F["dots"]:
        d.fill(g, color, angle=0, name="numeral dot")
    d.fill(F["name"], color, angle=0, spacing=0.35, name="name")


def footprint(layer):
    """The fabric a scene layer covers (satin: its column, centred on the path)."""
    kind, geom, _, kw = layer
    if kind == "fill":
        return geom
    if kind == "satin":
        from shapely.geometry import LineString
        path, w = geom
        return LineString(np.asarray(path)).buffer(float(np.max(w)) / 2, cap_style="flat")
    return None


def sew_scene(d, F, layers, order, C, hooks=None):
    """Sew the picture. `layers` bottom to top as (kind, geom, colour, kwargs) with kind
    "fill", "satin" or "run"; every fill is clipped to the picture and knocked out under
    every fill and satin above it, so nothing stacks. Colours sew in `order` (one block
    each); `hooks[colour](d)` adds frame pieces to that colour's block."""
    hooks = hooks or {}
    scene = F["scene"]
    feet = [footprint(l) for l in layers]
    visible = []
    for i, (kind, geom, col, kw) in enumerate(layers):
        if kind == "fill":
            above = [f for f in feet[i + 1:] if f is not None]
            geom = knockout(geom & scene, *above)
        visible.append((kind, geom, col, kw))
    for col in order:
        for kind, geom, c, kw in visible:
            if c != col:
                continue
            kw = dict(kw)
            if kind == "fill":
                if geom.is_empty:
                    continue
                d.fill(geom, C[c], **kw)
            elif kind == "satin":
                d.satin(geom[0], geom[1], C[c], **kw)
            else:
                d.run(geom, C[c], **kw)
        if col in hooks:
            hooks[col](d)
