"""Gather Wreath: oak leaves and acorns round a vine ring, "gather" in script inside.

Spec:
  object:       wreath with a word for pillows, totes, table linens, wall hoops
  overall:      `size` mm across (95 for 4x4, 160 for 5x7), round
  fabric:       medium wovens (linen, cotton canvas) with tear-away; knits with cut-away
  threads:      moss (vine), rust, mustard, olive, caramel (oak leaves), bark (leaf
                veins, acorn caps, lettering), wheat (acorn nuts, cap scales), cranberry
                (berries): 8 colours
  must have:    12 overlapping oak leaves in four tones lying along the ring, each with a
                satin midrib and angled side veins; three acorn pairs with scale-textured caps; three berry clusters; `label` (default "gather") in script,
                about 0.45 of the size wide, inside the ring
  density:      leaves and acorns knocked out where hidden; max 3.5 layers
"""
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union

from cadkit.stitch import *
from cadkit.stitch import motifs as M

from _fall import C_, COLLECTION, SIZES, fit, standard_checks

DESCRIPTION = "Oak leaf and acorn wreath with 'gather' in script"
HOOP = "4x4"
PARAMS = dict(size=95.0, label="gather", font="Segoe Script", font_file="segoescb.ttf")
PRODUCT = dict(
    title="Gather Oak Leaf Wreath Embroidery Design",
    summary="Oak leaves, acorns and berries round a vine, 'gather' in script",
    tags=["fall embroidery", "fall wreath", "oak leaves", "acorn", "thanksgiving embroidery", "gather"],
    collection=COLLECTION,
    mockups=['tote', 'tshirt'],
    description=(
        "Twelve oak leaves in rust, gold, olive and caramel overlap their way round a fine vine ring, each with its own midrib and side veins. Three pairs of acorns with scaled caps and three cranberry clusters sit among them, and 'gather' is set in script in the centre.\n\nFor Thanksgiving table linens, pillows, totes and wall hoops."
    ),
)

R = 35.0            # wreath radius (nominal)


def checks(p):
    return standard_checks(p, 8, 22000)


def on_ring(g, ang, r=R, tilt=0.0):
    """Place a shape drawn pointing up (+y, base at the origin) on the ring at `ang`,
    lying along it (pointing the way round, counter-clockwise), tilted out by `tilt`."""
    t = math.radians(ang)
    return move(rotate(g, ang + tilt, origin=(0, 0)), r * math.cos(t), r * math.sin(t))


def leaf_veins(length, lobes):
    """(midrib path, side vein run) in leaf coordinates: the side veins are short
    strokes angled toward the tip, sewn as one zigzag that never repeats a hole."""
    mid = np.array([[0, length * 0.08], [0, length * 0.80]])
    run = [np.array([0.0, length * 0.12])]
    for k, f in enumerate((0.28, 0.44, 0.60)):
        for j, side in enumerate((1, -1)):
            y = length * (f + 0.03 * j)
            run += [np.array([0, y]), np.array([side * length * 0.20, y + length * 0.14]), np.array([0, y + 0.8])]
    return mid, np.array(run)


def lettering(p):
    fp = Path("C:/Windows/Fonts") / p.font_file if p.font_file else None
    fp = str(fp) if fp and fp.exists() else None
    t = text_shape(p.label, 20.0, font=p.font, bold=True, font_path=fp)
    x0, y0, x1, y1 = t.bounds
    t = scale(t, 44.0 / (x1 - x0))
    return centered(t)


def art(p):
    d = Design()
    tones = [C_["rust"], C_["mustard"], C_["olive"], C_["caramel"]]
    leaves = []                                  # (tone, placed transform args, shape)
    for i in range(12):
        ang = 90 + i * 30
        length = 21 + (i % 3) * 1.5
        tilt = 22 if i % 2 else -12             # alternately out and in from the ring
        r = R + (1.0 if i % 2 else -1.0)
        leaves.append(dict(tone=tones[i % 4], ang=ang, tilt=tilt, r=r, length=length,
                           shape=on_ring(M.oak_leaf(length, 4), ang, r, tilt)))
    acorns = []
    for ang in (90, 210, 330):
        for da, dr, rot in ((-4, 3.0, 18), (5, 2.0, -20)):
            nut, cap, stem = M.acorn(14.0)
            t = math.radians(ang + da)
            pos = ((R + dr) * math.cos(t), (R + dr) * math.sin(t))
            f = lambda g, pos=pos, a=ang - 90 + rot: move(rotate(g, a, origin=(0, 0)), *pos)
            acorns.append((f(nut), f(cap), f(stem)))
    acorn_all = unary_union([unary_union([n, c]) for n, c, _ in acorns])

    d.run(circle_path(0, 0, R, res=180), C_["moss"], bean=1, length=2.0, name="vine")
    # each leaf lies over the one before it round the ring; acorns sit on top of all
    n = len(leaves)
    for i, lf in enumerate(leaves):
        lf["vis"] = knockout(lf["shape"], leaves[(i + 1) % n]["shape"], acorn_all, overlap=0.0)
    for tone in tones:
        for lf in leaves:
            if lf["tone"] == tone and not lf["vis"].is_empty:
                d.fill(lf["vis"], tone, angle=lf["ang"] + lf["tilt"] + 90 + 35, name="oak leaf")
    for lf in leaves:
        mid, run = leaf_veins(lf["length"], 4)
        t = math.radians(lf["ang"])
        place = lambda pts: np.asarray(rotate(pts, lf["ang"] + lf["tilt"], origin=(0, 0))) + (lf["r"] * math.cos(t), lf["r"] * math.sin(t))
        keep = lf["vis"].buffer(-0.4)
        for path, kind in ((place(run), "run"), (place(mid), "mid")):
            clip = LineString(path).intersection(keep)
            for part in getattr(clip, "geoms", [clip]):
                if part.geom_type != "LineString" or part.length < 2:
                    continue
                pts = np.asarray(part.coords)
                if kind == "mid":
                    d.run(pts, C_["bark"], bean=1, length=1.4, name="midrib")
                else:
                    d.run(pts, C_["bark"], length=1.3, name="side veins")
    for nut, cap, stem in acorns:
        d.fill(cap, C_["bark"], angle=10, spacing=0.38, name="acorn cap")
        d.run(stem, C_["bark"], bean=1, length=1.0, name="acorn stem")
    d.fill(lettering(p), C_["bark"], angle=70, spacing=0.36, name="lettering")
    for nut, cap, stem in acorns:                # nuts touch their caps edge to edge
        d.fill(knockout(nut, cap, overlap=0.0), C_["wheat"], angle=80, name="acorn")
    for (nut, cap, stem), (ang, rot) in zip(acorns, [(a, r) for a in (90, 210, 330) for r in (18, -20)]):
        # two rows of scale arcs on the cap, a highlight stroke on the nut
        frame = lambda pts, a=ang - 90 + rot, c=cap: pts
        cx0, cy0, cx1, cy1 = cap.bounds
        c = cap.centroid
        rows = []
        for row, dy in enumerate((-0.9, 1.0)):
            xs = np.linspace(-6, 6, 7) + (0.85 if row else 0)
            pts = []
            for x in xs:
                pts += [(x - 0.85, dy), (x, dy - 0.9), (x + 0.85, dy)]
            rows.append(np.array(pts) if row == 0 else np.array(pts)[::-1])
        hatch = np.vstack(rows)
        hatch = np.asarray(rotate(hatch, ang - 90 + rot, origin=(0, 0))) + (c.x, c.y)
        clip = LineString(hatch).intersection(cap.buffer(-0.7))
        for part in getattr(clip, "geoms", [clip]):
            if part.geom_type == "LineString" and part.length > 1.5:
                d.run(np.asarray(part.coords), C_["wheat"], length=1.0, name="cap scales")
    for ang in (150, 270, 30):
        t = math.radians(ang)
        cx, cy = (R + 0.5) * math.cos(t), (R + 0.5) * math.sin(t)
        pts = [(cx + 1.9 * math.cos(math.radians(a)), cy + 1.9 * math.sin(math.radians(a))) for a in (90, 210, 330)]
        d.fill(M.dots(pts, 1.45), C_["cranberry"], angle=0, underlay=False, spacing=0.35, name="berries")
    return d


def design(p):
    return fit(art(p), p.size, HOOPS.get(HOOP) if p.size <= 100 else HOOPS["5x7"])
