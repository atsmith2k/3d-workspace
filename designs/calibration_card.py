"""Calibration card: one sew-out per (machine, fabric, stabiliser) that `cad stitch
calibrate photo.jpg` measures to fit the fabric profile's pull numbers
(cadkit/stitch/calibrate.py). Sewn WITHOUT pull compensation, so the shrinkage it shows
is the fabric's raw pull.

Spec:
  object:       calibration card, sewn on the fabric being calibrated, photographed flat
  overall:      96 x 96 mm stitched, hoop 4x4 (fiducial centres 88 mm apart)
  fabric:       the fabric being calibrated, with the stabiliser it will be sewn with
  threads:      ladder fills (red), then everything else in black (2 colours, 1 change)
  must have:    four 8 mm solid fiducial squares at (+-44, +-44), a 3 mm orientation
                marker at (-36, 36) beside the top-left one; 15 x 15 mm fill squares
                with rows at 0, 45 and 90 deg; satin bars 20 mm long, 1/2/3/4/6 mm wide,
                horizontal and vertical; two 20 mm running-stitch thread gauges; an
                overlap ladder (10 mm squares, 2 mm satin border, fill 0/0.2/0.4/0.6 mm
                under the border)
  compensation: pull=0.0 on every fill and satin (the profile must not touch them)
  density:      max 3.5 layers, <= 30000 stitches

LAYOUT (below) gives every feature's nominal geometry in mm, Y up, card centred on the
origin; calibrate.py reads it. Bump CARD_VERSION whenever the layout changes.
"""
from cadkit.stitch import *

DESCRIPTION = "Calibration card: fiducials, fill squares, satin ladder, overlap ladder"
HOOP = "4x4"
CARD_VERSION = 1

PARAMS = dict(
    ink="black",
    ladder="red",
)

FID = 8.0                      # fiducial square side
FID_AT = 44.0                  # fiducial centre offset from the origin
MARK = 3.0                     # orientation marker side
FILL_SIDE = 15.0
SATIN_LEN = 20.0
SATIN_WIDTHS = (1.0, 2.0, 3.0, 4.0, 6.0)
LADDER_SIDE = 10.0
LADDER_BORDER = 2.0
LADDER_OVERLAPS = (0.0, 0.2, 0.4, 0.6)
FILL_SPACING = 0.40


def _box(cx, cy, w, h):
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def _layout():
    L = {}
    # fiducials, counter-clockwise from the marked top-left one
    for key, (sx, sy) in dict(fid_tl=(-1, 1), fid_bl=(-1, -1), fid_br=(1, -1), fid_tr=(1, 1)).items():
        L[key] = dict(kind="fiducial", center=(sx * FID_AT, sy * FID_AT), size=FID,
                      bbox=_box(sx * FID_AT, sy * FID_AT, FID, FID), angle=45.0)
    L["marker"] = dict(kind="marker", center=(-36.0, 36.0), size=MARK,
                       bbox=_box(-36.0, 36.0, MARK, MARK), angle=45.0)
    # fill squares: rows at 0, 45, 90 deg
    for x, a in ((-22.0, 0.0), (0.0, 45.0), (22.0, 90.0)):
        L[f"fill_{int(a)}"] = dict(kind="fill", center=(x, 28.0), size=FILL_SIDE,
                                   bbox=_box(x, 28.0, FILL_SIDE, FILL_SIDE), angle=a,
                                   spacing=FILL_SPACING)
    # satin ladder: horizontal bars (stitches run in y, width measured in y) ...
    for w, y in zip(SATIN_WIDTHS, (14.0, 10.0, 5.0, -1.0, -9.0)):
        L[f"satin_h{w:g}"] = dict(kind="satin", center=(-26.0, y), width=w, length=SATIN_LEN,
                                  axis="x", bbox=_box(-26.0, y, SATIN_LEN, w))
    # ... and vertical bars (width measured in x)
    for w, x in zip(SATIN_WIDTHS, (-6.0, -2.0, 3.0, 9.0, 17.0)):
        L[f"satin_v{w:g}"] = dict(kind="satin", center=(x, 2.0), width=w, length=SATIN_LEN,
                                  axis="y", bbox=_box(x, 2.0, w, SATIN_LEN))
    # thread gauges: single running stitch lines (no pull: straight runs cancel)
    L["gauge_h"] = dict(kind="gauge", center=(-26.0, -17.0), length=20.0, axis="x",
                        bbox=_box(-26.0, -17.0, 20.0, 0.0))
    L["gauge_v"] = dict(kind="gauge", center=(32.0, 0.0), length=20.0, axis="y",
                        bbox=_box(32.0, 0.0, 0.0, 20.0))
    # overlap ladder (visual only)
    for o, x in zip(LADDER_OVERLAPS, (-27.0, -9.0, 9.0, 27.0)):
        L[f"ladder_{o:g}"] = dict(kind="ladder", center=(x, -30.0), size=LADDER_SIDE,
                                  overlap=o, border=LADDER_BORDER,
                                  bbox=_box(x, -30.0, LADDER_SIDE + LADDER_BORDER,
                                            LADDER_SIDE + LADDER_BORDER))
    return L


LAYOUT = _layout()


def checks(p):
    return [
        size(w=2 * FID_AT + FID, h=2 * FID_AT + FID, tol=1.0),
        hoop(),
        colors(2),
        max_density(3.5),
        long_stitches(7.0),
        min_feature(1.0),
        coverage(1.0),
        stitches(max=30000),
    ]


def _sq(f):
    x0, y0, x1, y1 = f["bbox"]
    return rect(x1 - x0, y1 - y0, (x0 + x1) / 2, (y0 + y1) / 2)


def design(p):
    d = Design()
    ladder = [f for f in LAYOUT.values() if f["kind"] == "ladder"]
    # ladder fills first (second colour), each reaching `overlap` under its border
    for f in ladder:
        sq = rect(f["size"], f["size"], *f["center"])
        inner = sq.buffer(-(f["border"] / 2 - f["overlap"]), join_style="mitre")
        d.fill(inner, p.ladder, angle=45, pull=0.0, name=f"ladder fill {f['overlap']:g}")
    for f in ladder:
        sq = rect(f["size"], f["size"], *f["center"])
        d.outline(sq, p.ink, width=f["border"], pull=0.0, name=f"ladder border {f['overlap']:g}")

    for k, f in LAYOUT.items():
        if f["kind"] in ("fiducial", "marker"):
            d.fill(_sq(f), p.ink, angle=f["angle"], pull=0.0, name=k)
        elif f["kind"] == "fill":
            d.fill(_sq(f), p.ink, angle=f["angle"], spacing=f["spacing"], pull=0.0, name=k)
        elif f["kind"] == "satin":
            cx, cy = f["center"]
            h = f["length"] / 2
            path = [(cx - h, cy), (cx + h, cy)] if f["axis"] == "x" else [(cx, cy - h), (cx, cy + h)]
            d.satin(path, f["width"], p.ink, pull=0.0, name=k)
        elif f["kind"] == "gauge":
            cx, cy = f["center"]
            h = f["length"] / 2
            path = [(cx - h, cy), (cx + h, cy)] if f["axis"] == "x" else [(cx, cy - h), (cx, cy + h)]
            d.run(path, p.ink, length=2.5, name=k)
    return d
